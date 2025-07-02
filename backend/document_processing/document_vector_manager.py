"""
Gestor de vectores para documentos.
Integra el sistema de documentos con ChromaDB y embeddings.
"""

import asyncio
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

# Importar sistema de vectores existente
from storage.vector_manager import VectorManager
from .semantic_reranker import SemanticReRanker

logger = logging.getLogger(__name__)

class DocumentVectorManager:
    """
    Gestor especializado para vectorización de documentos.
    Extiende VectorManager para manejar chunks de documentos.
    """
    
    def __init__(self):
        # Usar el VectorManager existente
        self.vector_manager = VectorManager()
        # CRITICAL FIX: Usar las mismas colecciones que HybridRetrievalSystem
        self.document_collection_name = "documents"
        self.document_metadata_collection_name = "documents"  # Usamos la misma colección
        
        # 🔥 NUEVO: Inicializar re-ranker semántico
        self.semantic_reranker = SemanticReRanker()
        
        # Inicializar colecciones como None - se inicializarán on-demand
        self.document_collection = None
        self.metadata_collection = None
        self._initialization_lock = asyncio.Lock()
    
    async def _ensure_collections_initialized(self):
        """
        Asegura que las colecciones estén inicializadas usando un lock para thread-safety.
        """
        if self.document_collection is not None and self.metadata_collection is not None:
            return  # Ya inicializadas
        
        async with self._initialization_lock:
            # Double-check después del lock
            if self.document_collection is not None and self.metadata_collection is not None:
                return
            
            try:
                # Asegurar que el VectorManager esté inicializado
                if not self.vector_manager.chroma_client:
                    logger.info("🔧 Inicializando ChromaDB desde DocumentVectorManager")
                    self.vector_manager._initialize_chromadb()
                
                # CRITICAL FIX: Asegurar que los embedders estén inicializados
                if not self.vector_manager.local_embedder and not self.vector_manager.gemini_embedder:
                    logger.warning("🔧 Re-inicializando embedders en DocumentVectorManager")
                    self.vector_manager._initialize_embedding_clients()
                
                # CRITICAL FIX: Usar la colección que ya existe en VectorManager
                if self.document_collection_name in self.vector_manager.collections:
                    self.document_collection = self.vector_manager.collections[self.document_collection_name]
                    logger.info(f"✅ Usando colección existente '{self.document_collection_name}' del VectorManager")
                else:
                    logger.error(f"❌ Colección '{self.document_collection_name}' no existe en VectorManager")
                    logger.info(f"Colecciones disponibles: {list(self.vector_manager.collections.keys())}")
                    return
                
                # CRITICAL FIX: Usar la misma colección para metadata (simplificado)
                self.metadata_collection = self.document_collection
                logger.info(f"✅ Usando la misma colección para metadata: '{self.document_collection_name}'")
                
            except Exception as e:
                logger.error(f"Error inicializando colecciones de documentos: {e}")
                self.document_collection = None
                self.metadata_collection = None
                raise
    
    async def vectorize_document_chunks(self, 
                                      document_id: str,
                                      chunks: List[Dict[str, Any]],
                                      document_metadata: Dict[str, Any]) -> bool:
        """
        Vectoriza todos los chunks de un documento.
        
        Args:
            document_id: ID del documento
            chunks: Lista de chunks del documento
            document_metadata: Metadata del documento
            
        Returns:
            bool: True si la vectorización fue exitosa
        """
        try:
            # Asegurar que las colecciones estén inicializadas
            await self._ensure_collections_initialized()
            
            if not self.document_collection:
                logger.error("❌ CRITICAL: Colección de documentos no disponible - DocumentVectorManager no sincronizado con VectorManager")
                return False
            
            logger.info(f"🔄 Vectorizando {len(chunks)} chunks del documento {document_id}")
            
            # 🔍 DEBUG: Log estructura de los primeros chunks
            if chunks:
                first_chunk = chunks[0]
                logger.info(f"🔍 DEBUG - Estructura primer chunk:")
                logger.info(f"   - Content preview: {first_chunk.get('content', '')[:100]}...")
                logger.info(f"   - Chunk ID: {first_chunk.get('chunk_id', 'N/A')}")
                logger.info(f"   - Metadata keys: {list(first_chunk.get('metadata', {}).keys())}")
            
            # Procesar chunks en lotes para optimizar rendimiento
            batch_size = 5  # Procesar máximo 5 chunks simultáneamente
            successful_chunks = 0
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                batch_results = await self._vectorize_chunk_batch(document_id, batch, document_metadata)
                successful_chunks += sum(batch_results)
                
                # Pequeña pausa para no sobrecargar el sistema
                await asyncio.sleep(0.1)
            
            # Vectorizar metadata del documento
            await self._vectorize_document_metadata(document_id, document_metadata)
            
            logger.info(f"🎉 Vectorización completada: {successful_chunks}/{len(chunks)} chunks exitosos")
            
            if successful_chunks == 0:
                logger.error("❌ NINGÚN CHUNK SE VECTORIZÓ EXITOSAMENTE - Revisar errores anteriores")
            elif successful_chunks < len(chunks):
                logger.warning(f"⚠️ Solo {successful_chunks} de {len(chunks)} chunks se vectorizaron correctamente")
            
            return successful_chunks > 0
            
        except Exception as e:
            logger.error(f"Error vectorizando documento {document_id}: {e}")
            return False
    
    async def _vectorize_chunk_batch(self,
                                   document_id: str,
                                   chunks: List[Dict[str, Any]],
                                   document_metadata: Dict[str, Any]) -> List[bool]:
        """
        CRITICAL FIX: Vectoriza chunks usando VectorManager.add_documents para sincronización.
        """
        documents = []
        metadatas = []
        ids = []
        valid_chunks = []
        
        # Preparar datos para vectorización en lote
        for chunk in chunks:
            try:
                content = chunk.get("content", "")
                chunk_id = chunk.get("chunk_id", "")
                chunk_metadata = chunk.get("metadata", {})
                
                if not content or len(content.strip()) < 10:
                    continue
                
                # Crear ID único para el chunk
                unique_id = f"{document_id}_{chunk_id}"
                
                # Metadata completa del chunk
                full_metadata = {
                    "document_id": document_id,
                    "chunk_id": chunk_id,
                    "chunk_index": chunk_metadata.get("chunk_index", 0),
                    "file_name": document_metadata.get("file_name", ""),
                    "file_type": document_metadata.get("file_type", ""),
                    "processed_at": datetime.now().isoformat(),
                    "tokens": chunk_metadata.get("tokens", 0),
                    "length": len(content),
                    "chunk_type": chunk_metadata.get("type", "text")
                }
                
                # Añadir metadata específica del tipo de chunk
                if "page" in chunk_metadata:
                    full_metadata["page"] = chunk_metadata["page"]
                if "sheet_name" in chunk_metadata:
                    full_metadata["sheet_name"] = chunk_metadata["sheet_name"]
                if "row_number" in chunk_metadata:
                    full_metadata["row_number"] = chunk_metadata["row_number"]
                
                # ✅ Sanitizar metadatos antes de enviar a ChromaDB
                sanitized_metadata = self._sanitize_metadata_for_chromadb(full_metadata)
                
                documents.append(content)
                metadatas.append(sanitized_metadata)
                ids.append(unique_id)
                valid_chunks.append(chunk)
                
            except Exception as e:
                logger.warning(f"Error preparando chunk {chunk.get('chunk_id', 'unknown')}: {e}")
        
        # CRITICAL FIX: Usar VectorManager.add_documents para sincronización
        if documents:
            try:
                logger.info(f"🔄 Usando VectorManager.add_documents para {len(documents)} chunks en colección '{self.document_collection_name}'")
                result_ids = await self.vector_manager.add_documents(
                    collection_name=self.document_collection_name,
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                
                if result_ids:
                    logger.info(f"✅ {len(result_ids)} chunks vectorizados exitosamente vía VectorManager")
                    # Crear lista de resultados que coincida con chunks originales
                    results = []
                    valid_index = 0
                    for chunk in chunks:
                        content = chunk.get("content", "")
                        if content and len(content.strip()) >= 10:
                            results.append(True)
                            valid_index += 1
                        else:
                            results.append(False)
                    return results
                else:
                    logger.error("❌ VectorManager.add_documents retornó None")
                    return [False] * len(chunks)
                    
            except Exception as e:
                logger.error(f"❌ Error en VectorManager.add_documents: {e}")
                return [False] * len(chunks)
        
        return [False] * len(chunks)
    
    async def _vectorize_document_metadata(self,
                                         document_id: str,
                                         document_metadata: Dict[str, Any]):
        """
        Vectoriza metadata del documento para búsqueda.
        """
        try:
            # Crear resumen textual del documento para vectorizar
            summary_parts = [
                f"Documento: {document_metadata.get('file_name', 'Sin nombre')}",
                f"Tipo: {document_metadata.get('file_type', 'Desconocido')}",
                f"Tamaño: {document_metadata.get('file_size', 0)} bytes"
            ]
            
            # Añadir información específica según el tipo
            if document_metadata.get("file_type") == "pdf":
                if "page_count" in document_metadata:
                    summary_parts.append(f"Páginas: {document_metadata['page_count']}")
                
                pdf_info = document_metadata.get("pdf_info", {})
                if pdf_info.get("title"):
                    summary_parts.append(f"Título: {pdf_info['title']}")
                if pdf_info.get("author"):
                    summary_parts.append(f"Autor: {pdf_info['author']}")
            
            elif document_metadata.get("file_type") in ["xlsx", "xls"]:
                if "sheet_count" in document_metadata:
                    summary_parts.append(f"Hojas: {document_metadata['sheet_count']}")
                if "sheet_names" in document_metadata:
                    sheet_names = document_metadata['sheet_names']
                    if isinstance(sheet_names, list):
                        summary_parts.append(f"Nombres de hojas: {', '.join(sheet_names)}")
                    else:
                        summary_parts.append(f"Nombres de hojas: {sheet_names}")
            
            summary_text = "\n".join(summary_parts)
            
            # Generar embedding para el resumen
            embedding = await self.vector_manager.generate_embedding(summary_text)
            if embedding:
                # ✅ Sanitizar metadatos para ChromaDB (solo tipos primitivos)
                sanitized_metadata = self._sanitize_metadata_for_chromadb(document_metadata)
                
                metadata_record = {
                    "document_id": document_id,
                    "type": "document_metadata",
                    **sanitized_metadata,
                    "summary": summary_text,
                    "indexed_at": datetime.now().isoformat()
                }
                
                self.metadata_collection.add(
                    embeddings=[embedding],
                    documents=[summary_text],
                    metadatas=[metadata_record],
                    ids=[f"metadata_{document_id}"]
                )
                
                logger.debug(f"Metadata del documento {document_id} vectorizada")
        
        except Exception as e:
            logger.warning(f"Error vectorizando metadata del documento {document_id}: {e}")
    
    def _sanitize_metadata_for_chromadb(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitiza metadatos para ChromaDB convirtiendo listas y objetos complejos a strings.
        ChromaDB solo acepta: str, int, float, bool, None
        
        Args:
            metadata: Metadatos originales
            
        Returns:
            Dict con metadatos sanitizados
        """
        sanitized = {}
        
        for key, value in metadata.items():
            if value is None:
                sanitized[key] = None
            elif isinstance(value, (str, int, float, bool)):
                sanitized[key] = value
            elif isinstance(value, list):
                # Convertir listas a strings separados por coma
                sanitized[key] = ", ".join(str(item) for item in value)
            elif isinstance(value, dict):
                # Convertir diccionarios a string JSON simple
                try:
                    sanitized[key] = str(value)
                except:
                    sanitized[key] = f"dict_with_{len(value)}_items"
            else:
                # Convertir cualquier otro tipo a string
                sanitized[key] = str(value)
        
        return sanitized
    
    async def search_documents(self,
                             query: str,
                             document_id: Optional[str] = None,
                             limit: int = 5) -> List[Dict[str, Any]]:
        """
        Busca en documentos vectorizados.
        
        Args:
            query: Consulta de búsqueda
            document_id: ID de documento específico (opcional)
            limit: Número máximo de resultados
            
        Returns:
            Lista de resultados de búsqueda
        """
        try:
            # Asegurar que las colecciones estén inicializadas
            await self._ensure_collections_initialized()
            
            if not self.document_collection:
                return []
            
            # Generar embedding de la consulta
            logger.info(f"🔍 Generando embedding para consulta: '{query}'")
            query_embedding = await self.vector_manager.generate_embedding(query)
            if not query_embedding:
                logger.error(f"❌ No se pudo generar embedding para: '{query}'")
                return []
            logger.info(f"✅ Embedding generado correctamente, dimensión: {len(query_embedding)}")
            
            # Construir filtros
            where_filter = {}
            if document_id:
                where_filter["document_id"] = document_id
            
            # Realizar búsqueda
            results = self.document_collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_filter if where_filter else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Formatear resultados
            formatted_results = []
            for i in range(len(results["documents"][0])):
                result = {
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "similarity": float(results["distances"][0][i]),
                    "document_id": results["metadatas"][0][i].get("document_id"),
                    "chunk_id": results["metadatas"][0][i].get("chunk_id"),
                    "file_name": results["metadatas"][0][i].get("file_name")
                }
                formatted_results.append(result)
            
            # 🔥 NUEVO: Aplicar re-ranking semántico
            if formatted_results and len(formatted_results) > 1:
                logger.info(f"Aplicando re-ranking semántico a {len(formatted_results)} resultados")
                reranked_results = self.semantic_reranker.rerank_results(
                    query=query, 
                    results=formatted_results, 
                    limit=limit
                )
                logger.info(f"Re-ranking completado. Score mejorado: {reranked_results[0].get('rerank_score', 0):.3f}")
                return reranked_results
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error en búsqueda de documentos: {e}")
            return []
    
    async def delete_document_vectors(self, document_id: str) -> bool:
        """
        Elimina todos los vectores de un documento.
        
        Args:
            document_id: ID del documento
            
        Returns:
            bool: True si la eliminación fue exitosa
        """
        try:
            # Asegurar que las colecciones estén inicializadas
            await self._ensure_collections_initialized()
            
            if not self.document_collection or not self.metadata_collection:
                return False
            
            # Obtener IDs de chunks del documento
            chunk_results = self.document_collection.get(
                where={"document_id": document_id},
                include=["documents"]
            )
            
            if chunk_results["ids"]:
                # Eliminar chunks
                self.document_collection.delete(ids=chunk_results["ids"])
                logger.info(f"Eliminados {len(chunk_results['ids'])} chunks del documento {document_id}")
            
            # Eliminar metadata
            try:
                self.metadata_collection.delete(ids=[f"metadata_{document_id}"])
                logger.info(f"Metadata del documento {document_id} eliminada")
            except:
                pass  # Metadata podría no existir
            
            return True
            
        except Exception as e:
            logger.error(f"Error eliminando vectores del documento {document_id}: {e}")
            return False