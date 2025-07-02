"""
Sistema de memoria contextual que vincula conversaciones con documentos.
Mantiene referencias persistentes entre chats y documentos para mejorar continuidad.
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
import logging
import hashlib

logger = logging.getLogger(__name__)

class DocumentContextualMemory:
    """
    Sistema de memoria que vincula conversaciones con documentos específicos.
    Mantiene contexto entre sesiones y sugiere documentos relevantes.
    """
    
    def __init__(self, storage_path: str = "./data/contextual_memory"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Archivos de persistencia
        self.conversation_docs_file = self.storage_path / "conversation_documents.json"
        self.document_topics_file = self.storage_path / "document_topics.json"
        self.user_preferences_file = self.storage_path / "user_preferences.json"
        
        # Cache en memoria
        self.conversation_documents = {}  # conversation_id -> {doc_ids, topics, timestamp}
        self.document_topics = {}         # document_id -> {topics, keywords, usage_count}
        self.user_preferences = {}        # user patterns and preferences
        
        # Cargar datos persistentes
        asyncio.create_task(self._load_persistent_data())
        
        logger.info(f"DocumentContextualMemory inicializado en: {self.storage_path}")
    
    async def _load_persistent_data(self):
        """Carga datos persistentes desde archivos."""
        try:
            # Cargar conversación-documentos
            if self.conversation_docs_file.exists():
                with open(self.conversation_docs_file, 'r', encoding='utf-8') as f:
                    self.conversation_documents = json.load(f)
            
            # Cargar temas de documentos
            if self.document_topics_file.exists():
                with open(self.document_topics_file, 'r', encoding='utf-8') as f:
                    self.document_topics = json.load(f)
            
            # Cargar preferencias de usuario
            if self.user_preferences_file.exists():
                with open(self.user_preferences_file, 'r', encoding='utf-8') as f:
                    self.user_preferences = json.load(f)
            
            logger.info(f"Datos persistentes cargados: {len(self.conversation_documents)} conversaciones, {len(self.document_topics)} documentos")
            
        except Exception as e:
            logger.warning(f"Error cargando datos persistentes: {e}")
    
    async def _save_persistent_data(self):
        """Guarda datos persistentes a archivos."""
        try:
            # Guardar conversación-documentos
            with open(self.conversation_docs_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_documents, f, indent=2, ensure_ascii=False)
            
            # Guardar temas de documentos
            with open(self.document_topics_file, 'w', encoding='utf-8') as f:
                json.dump(self.document_topics, f, indent=2, ensure_ascii=False)
            
            # Guardar preferencias de usuario
            with open(self.user_preferences_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_preferences, f, indent=2, ensure_ascii=False)
            
            logger.debug("Datos persistentes guardados exitosamente")
            
        except Exception as e:
            logger.error(f"Error guardando datos persistentes: {e}")
    
    def generate_conversation_id(self, user_message: str) -> str:
        """
        Genera ID único para conversación basado en contenido y timestamp.
        
        Args:
            user_message: Mensaje del usuario
            
        Returns:
            ID único de conversación
        """
        timestamp = datetime.now().isoformat()
        content_hash = hashlib.md5(f"{user_message[:100]}{timestamp}".encode()).hexdigest()[:8]
        return f"conv_{content_hash}"
    
    async def link_conversation_to_documents(self, 
                                           conversation_id: str,
                                           document_ids: List[str],
                                           user_message: str,
                                           topics: List[str] = None):
        """
        Vincula una conversación con documentos específicos.
        
        Args:
            conversation_id: ID de la conversación
            document_ids: Lista de IDs de documentos usados
            user_message: Mensaje del usuario para análisis de temas
            topics: Temas identificados (opcional)
        """
        try:
            if not document_ids:
                return
            
            # Extraer temas del mensaje si no se proporcionan
            if not topics:
                topics = self._extract_topics_from_message(user_message)
            
            # Actualizar vinculación conversación-documentos
            self.conversation_documents[conversation_id] = {
                "document_ids": list(set(document_ids)),  # Eliminar duplicados
                "topics": topics,
                "user_message": user_message[:200],  # Primer parte del mensaje
                "timestamp": datetime.now().isoformat(),
                "usage_count": self.conversation_documents.get(conversation_id, {}).get("usage_count", 0) + 1
            }
            
            # Actualizar información de temas por documento
            for doc_id in document_ids:
                if doc_id not in self.document_topics:
                    self.document_topics[doc_id] = {
                        "topics": [],
                        "keywords": [],
                        "usage_count": 0,
                        "last_used": datetime.now().isoformat()
                    }
                
                # Agregar nuevos temas
                current_topics = set(self.document_topics[doc_id]["topics"])
                current_topics.update(topics)
                self.document_topics[doc_id]["topics"] = list(current_topics)
                self.document_topics[doc_id]["usage_count"] += 1
                self.document_topics[doc_id]["last_used"] = datetime.now().isoformat()
            
            # Guardar cambios
            await self._save_persistent_data()
            
            logger.info(f"Conversación {conversation_id} vinculada con {len(document_ids)} documentos")
            
        except Exception as e:
            logger.error(f"Error vinculando conversación a documentos: {e}")
    
    def _extract_topics_from_message(self, message: str) -> List[str]:
        """
        Extrae temas/palabras clave del mensaje del usuario.
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Lista de temas identificados
        """
        import re
        
        message_lower = message.lower()
        topics = []
        
        # Patrones de temas comunes
        topic_patterns = {
            'precio': r'\b(precio|costo|vale|cuesta|cuanto)\b',
            'motorola': r'\bmotorola\b',
            'pantalla': r'\b(pantalla|screen|display)\b',
            'modelo': r'\b(modelo|version|tipo)\b',
            'comparacion': r'\b(comparar|versus|vs|diferencia|mejor)\b',
            'calculo': r'\b(total|suma|ambos|todos|juntos)\b',
            'especificacion': r'\b(especificación|característica|detalle)\b'
        }
        
        for topic, pattern in topic_patterns.items():
            if re.search(pattern, message_lower):
                topics.append(topic)
        
        # Extraer posibles nombres de modelos (secuencias alfanuméricas)
        model_matches = re.findall(r'\b[A-Z]\d+[A-Z]*\d*\b|\b[EG]\d+\b', message, re.IGNORECASE)
        for match in model_matches:
            topics.append(f"modelo_{match.lower()}")
        
        return topics[:5]  # Máximo 5 temas
    
    async def suggest_relevant_documents(self, 
                                       current_message: str,
                                       limit: int = 3) -> List[Dict[str, Any]]:
        """
        Sugiere documentos relevantes basado en historial y mensaje actual.
        
        Args:
            current_message: Mensaje actual del usuario
            limit: Número máximo de sugerencias
            
        Returns:
            Lista de documentos sugeridos con scores de relevancia
        """
        try:
            current_topics = self._extract_topics_from_message(current_message)
            if not current_topics:
                return []
            
            document_scores = {}
            
            # Analizar documentos por relevancia de temas
            for doc_id, doc_info in self.document_topics.items():
                score = 0.0
                
                # Score por coincidencia de temas
                doc_topics = set(doc_info.get("topics", []))
                current_topics_set = set(current_topics)
                topic_overlap = len(doc_topics.intersection(current_topics_set))
                
                if topic_overlap > 0:
                    score += topic_overlap * 0.4
                
                # Score por frecuencia de uso
                usage_count = doc_info.get("usage_count", 0)
                score += min(usage_count * 0.1, 0.3)  # Máximo 0.3 por uso frecuente
                
                # Score por recencia de uso
                last_used_str = doc_info.get("last_used")
                if last_used_str:
                    try:
                        last_used = datetime.fromisoformat(last_used_str)
                        days_since_use = (datetime.now() - last_used).days
                        recency_score = max(0, 0.2 - (days_since_use * 0.02))  # Decae con tiempo
                        score += recency_score
                    except:
                        pass
                
                if score > 0:
                    document_scores[doc_id] = score
            
            # Convertir a lista ordenada
            suggestions = []
            for doc_id, score in sorted(document_scores.items(), key=lambda x: x[1], reverse=True):
                suggestions.append({
                    "document_id": doc_id,
                    "relevance_score": score,
                    "topics": self.document_topics[doc_id].get("topics", []),
                    "usage_count": self.document_topics[doc_id].get("usage_count", 0),
                    "last_used": self.document_topics[doc_id].get("last_used"),
                    "reason": self._generate_suggestion_reason(current_topics, self.document_topics[doc_id])
                })
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Error sugiriendo documentos relevantes: {e}")
            return []
    
    def _generate_suggestion_reason(self, current_topics: List[str], doc_info: Dict) -> str:
        """
        Genera razón textual de por qué se sugiere un documento.
        
        Args:
            current_topics: Temas del mensaje actual
            doc_info: Información del documento
            
        Returns:
            Razón textual de la sugerencia
        """
        doc_topics = set(doc_info.get("topics", []))
        current_topics_set = set(current_topics)
        overlap = doc_topics.intersection(current_topics_set)
        
        if overlap:
            return f"Temas relacionados: {', '.join(list(overlap)[:3])}"
        elif doc_info.get("usage_count", 0) > 2:
            return "Documento usado frecuentemente"
        else:
            return "Potencialmente relevante"
    
    async def get_conversation_context(self, 
                                     conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene contexto completo de una conversación.
        
        Args:
            conversation_id: ID de la conversación
            
        Returns:
            Contexto de la conversación o None
        """
        return self.conversation_documents.get(conversation_id)
    
    async def get_recent_conversations(self, 
                                     days: int = 7, 
                                     limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene conversaciones recientes con contexto de documentos.
        
        Args:
            days: Días hacia atrás para buscar
            limit: Número máximo de conversaciones
            
        Returns:
            Lista de conversaciones recientes
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_conversations = []
            
            for conv_id, conv_data in self.conversation_documents.items():
                try:
                    conv_time = datetime.fromisoformat(conv_data.get("timestamp", ""))
                    if conv_time >= cutoff_date:
                        recent_conversations.append({
                            "conversation_id": conv_id,
                            "timestamp": conv_data.get("timestamp"),
                            "document_count": len(conv_data.get("document_ids", [])),
                            "topics": conv_data.get("topics", []),
                            "message_preview": conv_data.get("user_message", "")
                        })
                except:
                    continue
            
            # Ordenar por timestamp descendente
            recent_conversations.sort(key=lambda x: x["timestamp"], reverse=True)
            return recent_conversations[:limit]
            
        except Exception as e:
            logger.error(f"Error obteniendo conversaciones recientes: {e}")
            return []
    
    async def cleanup_old_data(self, days: int = 30):
        """
        Limpia datos antiguos para mantener el sistema eficiente.
        
        Args:
            days: Días de retención de datos
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Limpiar conversaciones antiguas
            old_conversations = []
            for conv_id, conv_data in self.conversation_documents.items():
                try:
                    conv_time = datetime.fromisoformat(conv_data.get("timestamp", ""))
                    if conv_time < cutoff_date:
                        old_conversations.append(conv_id)
                except:
                    old_conversations.append(conv_id)  # Eliminar entradas malformadas
            
            for conv_id in old_conversations:
                del self.conversation_documents[conv_id]
            
            if old_conversations:
                logger.info(f"Limpiadas {len(old_conversations)} conversaciones antiguas")
                await self._save_persistent_data()
            
        except Exception as e:
            logger.error(f"Error en limpieza de datos: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la memoria contextual.
        
        Returns:
            Dict con estadísticas
        """
        total_conversations = len(self.conversation_documents)
        total_documents = len(self.document_topics)
        
        # Documentos más usados
        most_used_docs = sorted(
            self.document_topics.items(),
            key=lambda x: x[1].get("usage_count", 0),
            reverse=True
        )[:5]
        
        return {
            "total_conversations": total_conversations,
            "total_tracked_documents": total_documents,
            "most_used_documents": [
                {
                    "document_id": doc_id,
                    "usage_count": info.get("usage_count", 0),
                    "topics": info.get("topics", [])[:3]
                }
                for doc_id, info in most_used_docs
            ],
            "storage_path": str(self.storage_path)
        }