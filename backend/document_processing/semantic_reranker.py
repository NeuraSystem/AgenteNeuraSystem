"""
Re-ranking semántico inteligente usando LLM local.
Mejora la precisión de resultados de búsqueda combinando múltiples factores.
"""

import numpy as np
import logging
from typing import List, Dict, Any
import re
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class SemanticReRanker:
    """
    Re-ranking semántico avanzado que usa el LLM local para
    mejorar la precisión de resultados de búsqueda.
    """
    
    def __init__(self, embeddings_model: SentenceTransformer = None):
        """
        Inicializar re-ranker semántico.
        
        Args:
            embeddings_model: Modelo de embeddings (se usará el del sistema si no se proporciona)
        """
        self.embeddings_model = embeddings_model
        self.query_intent_patterns = {
            'price': r'\b(precio|costo|vale|cuesta|cuanto)\b',
            'comparison': r'\b(comparar|versus|vs|diferencia|mejor|peor)\b',
            'specification': r'\b(especificación|característica|detalle|información)\b',
            'availability': r'\b(disponible|stock|hay|existe)\b',
            'calculation': r'\b(total|suma|ambos|todos|juntos|combinado)\b'
        }
        logger.info("SemanticReRanker inicializado")
    
    def rerank_results(self, query: str, results: List[Dict[str, Any]], limit: int = None) -> List[Dict[str, Any]]:
        """
        Re-ordena resultados usando análisis semántico avanzado.
        
        Args:
            query: Consulta original del usuario
            results: Lista de resultados de búsqueda inicial
            limit: Número máximo de resultados a retornar
            
        Returns:
            Lista de resultados re-ordenados por relevancia
        """
        if not results:
            return results
        
        try:
            logger.info(f"Re-ranking {len(results)} resultados para query: '{query}'")
            
            # 1. Analizar intención de la consulta
            query_intent = self._analyze_query_intent(query)
            
            # 2. Calcular scores avanzados para cada resultado
            enhanced_results = []
            for result in results:
                enhanced_result = result.copy()
                
                # Score semántico mejorado
                semantic_score = self._calculate_semantic_score(query, result, query_intent)
                
                # Score de relevancia contextual
                contextual_score = self._calculate_contextual_score(query, result, query_intent)
                
                # Score de posición/estructura
                structural_score = self._calculate_structural_score(result)
                
                # Score combinado con pesos
                final_score = self._combine_scores(
                    semantic_score, 
                    contextual_score, 
                    structural_score,
                    result.get('similarity', 0)
                )
                
                enhanced_result['rerank_score'] = final_score
                enhanced_result['semantic_score'] = semantic_score
                enhanced_result['contextual_score'] = contextual_score
                enhanced_result['structural_score'] = structural_score
                enhanced_result['query_intent'] = query_intent
                
                enhanced_results.append(enhanced_result)
            
            # 3. Re-ordenar por score combinado
            reranked_results = sorted(
                enhanced_results, 
                key=lambda x: x['rerank_score'], 
                reverse=True
            )
            
            # 4. Aplicar límite si se especifica
            if limit:
                reranked_results = reranked_results[:limit]
            
            logger.info(f"Re-ranking completado. Top score: {reranked_results[0]['rerank_score']:.3f}")
            return reranked_results
            
        except Exception as e:
            logger.error(f"Error en re-ranking: {e}")
            return results  # Retornar resultados originales en caso de error
    
    def _analyze_query_intent(self, query: str) -> Dict[str, float]:
        """
        Analiza la intención de la consulta usando patrones semánticos.
        
        Args:
            query: Consulta del usuario
            
        Returns:
            Dict con scores de intención por categoría
        """
        query_lower = query.lower()
        intent_scores = {}
        
        for intent_type, pattern in self.query_intent_patterns.items():
            matches = re.findall(pattern, query_lower)
            intent_scores[intent_type] = len(matches) / max(len(query_lower.split()), 1)
        
        # Intención dominante
        dominant_intent = max(intent_scores.items(), key=lambda x: x[1])
        intent_scores['dominant'] = dominant_intent[0]
        
        return intent_scores
    
    def _calculate_semantic_score(self, query: str, result: Dict, query_intent: Dict) -> float:
        """
        Calcula score semántico mejorado usando análisis de contenido.
        
        Args:
            query: Consulta original
            result: Resultado de búsqueda
            query_intent: Análisis de intención
            
        Returns:
            Score semántico (0.0 - 1.0)
        """
        try:
            content = result.get('content', '')
            if not content:
                return 0.0
            
            # Score base de similitud
            base_similarity = result.get('similarity', 0) / 100.0
            
            # Boost semántico basado en intención
            semantic_boost = 1.0
            
            if query_intent.get('dominant') == 'price':
                # Para consultas de precio, priorizar contenido con números/precios
                if re.search(r'\b\d+\b', content):
                    semantic_boost += 0.3
                if re.search(r'\b(precio|costo)\b', content.lower()):
                    semantic_boost += 0.2
            
            elif query_intent.get('dominant') == 'comparison':
                # Para comparaciones, priorizar contenido con múltiples elementos
                items_count = len(re.findall(r'\bFila \d+:', content))
                if items_count > 3:
                    semantic_boost += 0.2
            
            elif query_intent.get('dominant') == 'calculation':
                # Para cálculos, priorizar contenido numérico
                numbers = re.findall(r'\b\d+\b', content)
                if len(numbers) >= 2:
                    semantic_boost += 0.4
            
            # Penalizar contenido muy corto o muy largo
            content_length = len(content)
            if content_length < 50:
                semantic_boost *= 0.8
            elif content_length > 5000:
                semantic_boost *= 0.9
            
            return min(base_similarity * semantic_boost, 1.0)
            
        except Exception as e:
            logger.warning(f"Error calculando score semántico: {e}")
            return result.get('similarity', 0) / 100.0
    
    def _calculate_contextual_score(self, query: str, result: Dict, query_intent: Dict) -> float:
        """
        Calcula score de relevancia contextual.
        
        Args:
            query: Consulta original
            result: Resultado de búsqueda
            query_intent: Análisis de intención
            
        Returns:
            Score contextual (0.0 - 1.0)
        """
        try:
            content = result.get('content', '').lower()
            query_lower = query.lower()
            
            # Extraer términos clave de la consulta
            query_terms = set(re.findall(r'\b\w+\b', query_lower))
            content_terms = set(re.findall(r'\b\w+\b', content))
            
            # Coincidencia exacta de términos
            exact_matches = query_terms.intersection(content_terms)
            term_coverage = len(exact_matches) / len(query_terms) if query_terms else 0
            
            # Boost por tipo de contenido
            content_type_boost = 1.0
            metadata = result.get('metadata', {})
            
            if metadata.get('type') == 'spreadsheet':
                # Hojas de cálculo son buenas para consultas de datos
                if query_intent.get('dominant') in ['price', 'calculation']:
                    content_type_boost += 0.3
            
            # Boost por estructura del contenido
            structure_boost = 1.0
            if 'Fila' in content and query_intent.get('dominant') == 'price':
                structure_boost += 0.2
            
            contextual_score = term_coverage * content_type_boost * structure_boost
            return min(contextual_score, 1.0)
            
        except Exception as e:
            logger.warning(f"Error calculando score contextual: {e}")
            return 0.5  # Score neutro en caso de error
    
    def _calculate_structural_score(self, result: Dict) -> float:
        """
        Calcula score basado en estructura del documento.
        
        Args:
            result: Resultado de búsqueda
            
        Returns:
            Score estructural (0.0 - 1.0)
        """
        try:
            metadata = result.get('metadata', {})
            
            # Score base
            structural_score = 0.5
            
            # Boost por tipo de documento estructurado
            if metadata.get('type') == 'spreadsheet':
                structural_score += 0.2
                
                # Boost adicional por densidad de datos
                if metadata.get('density') == 'dense':
                    structural_score += 0.1
                
                # Boost por número de filas (más datos = mejor)
                row_count = metadata.get('row_count', 0)
                if row_count > 50:
                    structural_score += 0.1
                elif row_count > 20:
                    structural_score += 0.05
            
            # Boost por longitud del contenido (información completa)
            content_length = metadata.get('length', 0)
            if content_length > 1000:
                structural_score += 0.1
            
            return min(structural_score, 1.0)
            
        except Exception as e:
            logger.warning(f"Error calculando score estructural: {e}")
            return 0.5
    
    def _combine_scores(self, semantic: float, contextual: float, structural: float, original_similarity: float) -> float:
        """
        Combina múltiples scores con pesos optimizados.
        
        Args:
            semantic: Score semántico
            contextual: Score contextual
            structural: Score estructural
            original_similarity: Similitud original
            
        Returns:
            Score final combinado
        """
        # Pesos optimizados basados en importancia
        weights = {
            'semantic': 0.4,      # Más importante: análisis semántico
            'contextual': 0.3,    # Importante: relevancia contextual
            'structural': 0.2,    # Moderado: estructura del documento
            'original': 0.1       # Menor: similitud vectorial original
        }
        
        # Normalizar similitud original
        normalized_similarity = original_similarity / 100.0 if original_similarity > 1 else original_similarity
        
        # Combinar con pesos
        final_score = (
            semantic * weights['semantic'] +
            contextual * weights['contextual'] +
            structural * weights['structural'] +
            normalized_similarity * weights['original']
        )
        
        return min(final_score, 1.0)
    
    def get_ranking_explanation(self, result: Dict) -> str:
        """
        Genera explicación del ranking para debugging.
        
        Args:
            result: Resultado con scores de ranking
            
        Returns:
            Explicación textual del ranking
        """
        try:
            explanation = f"Score final: {result.get('rerank_score', 0):.3f}\n"
            explanation += f"  - Semántico: {result.get('semantic_score', 0):.3f}\n"
            explanation += f"  - Contextual: {result.get('contextual_score', 0):.3f}\n"
            explanation += f"  - Estructural: {result.get('structural_score', 0):.3f}\n"
            explanation += f"  - Intención: {result.get('query_intent', {}).get('dominant', 'N/A')}"
            return explanation
        except Exception:
            return "Explicación no disponible"