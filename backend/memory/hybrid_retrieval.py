
"""
Sistema de Recuperación Híbrido para ChatIng 2.0

Implementa la arquitectura de recuperación en dos pasos acordada:
1.  **Fase de Descubrimiento:** Búsqueda amplia y rápida en todas las colecciones para detectar señales.
2.  **Fase de Búsqueda Dirigida:** Búsquedas profundas y precisas en las colecciones identificadas como relevantes.
"""

import asyncio
import logging
import hashlib
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from storage.vector_manager import VectorManager

logger = logging.getLogger(__name__)

class HybridRetrievalSystem:
    def __init__(self, vector_manager: VectorManager):
        self.vector_manager = vector_manager
        self.collections = self.vector_manager.collections.keys()
        # Umbrales ajustados para distancias euclideanas con fórmula 1/(1+distance)
        self.DISCOVERY_THRESHOLD = 0.08  # Para distancias ~11-12, similarity ≈ 0.08
        self.FALLBACK_THRESHOLD = 0.04   # Umbral de emergencia para fallback (0.045 > 0.04)
        self.MIN_RESULTS_FOR_CONTEXT = 1  # Mínimo de resultados para generar contexto
        
        # Sistema de cache simple para mejorar performance
        self._cache = {}
        self.CACHE_TTL = 300  # 5 minutos de TTL para cache
        self.MAX_CACHE_SIZE = 100 

    def _get_cache_key(self, query: str) -> str:
        """Genera una clave de cache para la query."""
        return hashlib.md5(query.lower().strip().encode()).hexdigest()
    
    def _clean_cache(self):
        """Limpia entradas expiradas del cache."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self._cache.items()
            if current_time - timestamp > self.CACHE_TTL
        ]
        for key in expired_keys:
            del self._cache[key]
    
    async def search(self, query: str) -> str:
        """
        Realiza una búsqueda híbrida completa y devuelve un contexto ensamblado.
        Incluye sistema de cache para mejorar performance.
        """
        # Verificar cache primero
        cache_key = self._get_cache_key(query)
        current_time = time.time()
        
        if cache_key in self._cache:
            cached_result, timestamp = self._cache[cache_key]
            if current_time - timestamp <= self.CACHE_TTL:
                logger.info(f"🚀 Resultado obtenido desde cache para: '{query[:50]}...'")
                return cached_result
        
        try:
            # Paso 1: Fase de Descubrimiento
            discovery_signals = await self._discovery_phase(query)

            # Paso 2: Fase de Búsqueda Dirigida
            final_context = await self._targeted_phase(query, discovery_signals)
            
            # Guardar en cache
            self._clean_cache()
            if len(self._cache) >= self.MAX_CACHE_SIZE:
                # Eliminar entrada más antigua si el cache está lleno
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
                del self._cache[oldest_key]
            
            self._cache[cache_key] = (final_context, current_time)
            
            return final_context
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda híbrida: {e}")
            return f"Error al buscar información: {str(e)}. Por favor intenta reformular tu pregunta."

    async def _discovery_phase(self, query: str) -> Dict[str, Any]:
        """
        Realiza una búsqueda rápida en todas las colecciones para detectar señales de relevancia.
        Devuelve un diccionario con la fuerza de la señal y los mejores resultados para cada colección.
        """
        logger.info(f"🚀 Iniciando Fase de Descubrimiento para la consulta: '{query}'")
        
        if not query or not query.strip():
            logger.warning("Query vacía recibida en discovery_phase")
            return {}
        
        tasks = []
        collection_names = list(self.collections)
        
        for collection_name in collection_names:
            # Búsqueda rápida con 2 resultados para mejor evaluación de señal
            tasks.append(self._safe_search(collection_name, query, n_results=2))

        try:
            results_per_collection = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"❌ Error en discovery_phase: {e}")
            return {}
        
        signals = {}
        for i, collection_name in enumerate(collection_names):
            collection_results = results_per_collection[i]
            
            # Manejar excepciones por colección
            if isinstance(collection_results, Exception):
                logger.warning(f"⚠️ Error en colección '{collection_name}': {collection_results}")
                signals[collection_name] = {
                    'strength': 0.0,
                    'preview_results': [],
                    'error': str(collection_results)
                }
                continue
            
            if collection_results and isinstance(collection_results, list):
                # Calcular fuerza de señal promediando los mejores resultados
                similarities = [res.get('similarity', 0.0) for res in collection_results[:2] if isinstance(res, dict)]
                signal_strength = sum(similarities) / len(similarities) if similarities else 0.0
                signals[collection_name] = {
                    'strength': signal_strength,
                    'preview_results': collection_results[:1],  # Guardar el mejor resultado
                    'total_found': len(collection_results)
                }
                logger.info(f"   - Señal detectada en '{collection_name}': {signal_strength:.3f} ({len(collection_results)} resultados)")
            else:
                signals[collection_name] = {
                    'strength': 0.0,
                    'preview_results': [],
                    'total_found': 0
                }
        
        return signals
    
    async def _safe_search(self, collection_name: str, query: str, n_results: int = 5) -> List[Dict]:
        """Wrapper para búsquedas con manejo de errores robusto."""
        try:
            return await self.vector_manager.search(collection_name, query, n_results)
        except Exception as e:
            logger.error(f"❌ Error en búsqueda en colección '{collection_name}': {e}")
            return []

    async def _targeted_phase(self, query: str, signals: Dict[str, Any]) -> str:
        """
        Realiza búsquedas profundas en las colecciones que superaron el umbral de descubrimiento.
        Incluye fallback inteligente para casos de umbral no alcanzado.
        """
        logger.info("🎯 Iniciando Fase de Búsqueda Dirigida...")
        
        if not signals:
            logger.warning("No hay señales para procesar en targeted_phase")
            return "No se pudo procesar la búsqueda. Por favor intenta con una consulta diferente."
        
        collection_results = {}

        # Primera pasada: colecciones que superan el umbral principal
        primary_collections = []
        for collection_name, signal_data in signals.items():
            if not isinstance(signal_data, dict):
                continue
            
            signal_strength = signal_data.get('strength', 0.0)
            if signal_strength >= self.DISCOVERY_THRESHOLD:
                logger.info(f"   - Colección '{collection_name}' superó el umbral principal ({signal_strength:.3f} >= {self.DISCOVERY_THRESHOLD})")
                primary_collections.append((collection_name, signal_data))

        # Si hay colecciones principales, usar búsqueda profunda
        if primary_collections:
            try:
                targeted_searches = [
                    self._safe_search(collection_name, query, n_results=5)
                    for collection_name, _ in primary_collections
                ]
                
                search_results_per_collection = await asyncio.gather(*targeted_searches, return_exceptions=True)
                
                for i, (collection_name, _) in enumerate(primary_collections):
                    result = search_results_per_collection[i]
                    if isinstance(result, Exception):
                        logger.warning(f"⚠️ Error en búsqueda profunda en '{collection_name}': {result}")
                        # Usar preview results como fallback
                        signal_data = signals[collection_name]
                        collection_results[collection_name] = signal_data.get('preview_results', [])
                    else:
                        collection_results[collection_name] = result if isinstance(result, list) else []
                        
            except Exception as e:
                logger.error(f"❌ Error en búsquedas dirigidas: {e}")
                # Fallback a preview results
                for collection_name, signal_data in primary_collections:
                    collection_results[collection_name] = signal_data.get('preview_results', [])
        
        # Fallback inteligente: si no hay suficientes resultados, usar umbral más bajo
        total_results = sum(len(results) for results in collection_results.values() if isinstance(results, list))
        if total_results < self.MIN_RESULTS_FOR_CONTEXT:
            logger.info(f"   - Pocos resultados encontrados ({total_results}). Activando fallback inteligente...")
            
            for collection_name, signal_data in signals.items():
                if not isinstance(signal_data, dict):
                    continue
                    
                signal_strength = signal_data.get('strength', 0.0)
                if (signal_strength >= self.FALLBACK_THRESHOLD and 
                    collection_name not in collection_results and
                    not signal_data.get('error')):  # Evitar colecciones con errores
                    
                    logger.info(f"   - Colección '{collection_name}' incluida en fallback ({signal_strength:.3f} >= {self.FALLBACK_THRESHOLD})")
                    
                    # Usar resultados de preview si están disponibles
                    preview_results = signal_data.get('preview_results', [])
                    if preview_results:
                        collection_results[collection_name] = preview_results
                    else:
                        # Intentar búsqueda fallback
                        fallback_result = await self._safe_search(collection_name, query, n_results=2)
                        collection_results[collection_name] = fallback_result
        
        # Filtrar resultados vacíos
        collection_results = {
            name: results for name, results in collection_results.items()
            if results and isinstance(results, list) and len(results) > 0
        }
        
        if not collection_results:
            logger.info("   - No se encontró información relevante en ninguna colección.")
            return "No se encontró información relevante en la base de conocimiento para responder a esta consulta. Intenta reformular tu pregunta o usar términos más específicos."

        # Ensamblar el contexto final
        try:
            return self._assemble_enhanced_context(collection_results, signals)
        except Exception as e:
            logger.error(f"❌ Error ensamblando contexto: {e}")
            return "Se encontró información relevante pero hubo un error al procesarla. Por favor intenta nuevamente."

    def _assemble_enhanced_context(self, collection_results: Dict[str, List[Dict]], signals: Dict[str, Any]) -> str:
        """
        Ensambla los resultados en un contexto enriquecido con metadatos y scores.
        """
        logger.info("🧩 Ensamblando contexto enriquecido...")
        
        if not collection_results:
            return "No se encontraron resultados para mostrar."
        
        final_context = "📋 Contexto Relevante Encontrado:\n\n"
        
        try:
            # Ordenar colecciones por fuerza de señal (más relevantes primero)
            sorted_collections = sorted(
                collection_results.items(),
                key=lambda x: signals.get(x[0], {}).get('strength', 0.0),
                reverse=True
            )
            
            total_results = 0
            for collection_name, results in sorted_collections:
                if not results or not isinstance(results, list):
                    continue
                    
                signal_data = signals.get(collection_name, {})
                signal_strength = signal_data.get('strength', 0.0)
                final_context += f"📂 **{collection_name.upper()}** (relevancia: {signal_strength:.3f})\n"
                
                valid_results = 0
                for i, res in enumerate(results[:3]):  # Limitar a 3 resultados por colección
                    if not isinstance(res, dict):
                        continue
                        
                    document_content = res.get('document', 'Contenido no disponible')
                    similarity = res.get('similarity', 0.0)
                    metadata = res.get('metadata', {})
                    
                    # Validar y limpiar contenido
                    if not document_content or not isinstance(document_content, str):
                        document_content = 'Contenido no disponible'
                    
                    clean_content = document_content.replace('\n', ' ').strip()
                    if len(clean_content) > 300:
                        clean_content = clean_content[:300] + "..."
                    
                    final_context += f"  {valid_results + 1}. [{similarity:.3f}] {clean_content}"
                    
                    # Añadir metadatos relevantes si están disponibles
                    if isinstance(metadata, dict) and metadata.get('timestamp'):
                        try:
                            timestamp = metadata['timestamp']
                            if isinstance(timestamp, str):
                                # Manejar diferentes formatos de timestamp
                                timestamp = timestamp.replace('Z', '+00:00')
                                dt = datetime.fromisoformat(timestamp)
                                final_context += f" [📅 {dt.strftime('%Y-%m-%d')}]"
                        except Exception as e:
                            logger.debug(f"Error parseando timestamp: {e}")
                    
                    final_context += "\n"
                    valid_results += 1
                
                if valid_results > 0:
                    final_context += "\n"
                    total_results += valid_results
            
            # Añadir resumen al final
            if total_results > 0:
                final_context += f"\n🔍 **Resumen**: Se encontraron {total_results} resultados relevantes en {len([name for name, results in sorted_collections if results])} colecciones."
            else:
                final_context = "No se encontraron resultados válidos para mostrar."
            
            logger.info(f"✅ Contexto ensamblado: {total_results} resultados válidos")
            return final_context.strip()
            
        except Exception as e:
            logger.error(f"❌ Error ensamblando contexto enriquecido: {e}")
            # Fallback simple
            simple_context = "📋 Información encontrada:\n\n"
            try:
                for collection_name, results in collection_results.items():
                    if results and isinstance(results, list):
                        simple_context += f"**{collection_name.upper()}**:\n"
                        for res in results[:2]:
                            if isinstance(res, dict) and res.get('document'):
                                content = str(res['document'])[:200]
                                simple_context += f"- {content}...\n"
                        simple_context += "\n"
                return simple_context.strip()
            except:
                return "Se encontró información relevante pero hubo un error al formatearla."

