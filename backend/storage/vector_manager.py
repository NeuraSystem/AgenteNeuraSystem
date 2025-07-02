"""
Gestor de vectores para embeddings y ChromaDB.
- Arquitectura de Colecciones Múltiples: documents, conversations, profile
- Integración híbrida: Local + Gemini embeddings
- Optimizado para Windows 10/11
- Búsqueda semántica avanzada
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

# Configurar encoding UTF-8 para Windows
import sys
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

logger = logging.getLogger(__name__)

class VectorManager:
    """
    Gestor de vectores que maneja embeddings y ChromaDB.
    Implementa una arquitectura de colecciones múltiples para una recuperación de información especializada.
    """
    
    COLLECTION_NAMES = ["documents", "conversations", "profile"]

    def __init__(self):
        self.embedding_provider = os.getenv("EMBEDDING_PROVIDER", "hybrid")
        self.primary_embedding = "local"
        self.fallback_embedding = "gemini"
        
        self.local_model_path = os.getenv("LOCAL_MODEL_PATH", "paraphrase-multilingual-MiniLM-L12-v2")
        self.local_cache_dir = Path(os.getenv("LOCAL_CACHE_DIR", r".\models\embeddings")).resolve()
        
        self.gemini_model = os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        
        self.persist_dir = Path(os.getenv("CHROMADB_PERSIST_DIR", r".\data\chromadb")).resolve()
        
        self.chroma_client = None
        self.collections: Dict[str, Any] = {}
        self.local_embedder = None
        self.gemini_embedder = None
        
        self._initialize_embedding_clients()
        self._initialize_chromadb()
    
    def _initialize_embedding_clients(self):
        """Inicializa clientes de embeddings (Local + Gemini)."""
        if self.primary_embedding == "local" or self.fallback_embedding == "local":
            try:
                from sentence_transformers import SentenceTransformer
                self.local_cache_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"🔄 Descargando modelo local: {self.local_model_path}")
                self.local_embedder = SentenceTransformer(
                    self.local_model_path,
                    cache_folder=str(self.local_cache_dir)
                )
                logger.info("✅ Modelo local inicializado exitosamente")
            except Exception as e:
                logger.error(f"❌ Error cargando modelo local: {e}")
                self.local_embedder = None
        
        if self.primary_embedding == "gemini" or self.fallback_embedding == "gemini":
            if self.gemini_api_key:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=self.gemini_api_key)
                    logger.info("✅ Gemini embeddings inicializado")
                    self.gemini_embedder = genai
                except Exception as e:
                    logger.error(f"❌ Error inicializando Gemini: {e}")
                    self.gemini_embedder = None
            else:
                logger.warning("⚠️ Gemini API key no configurada")
    
    def _initialize_chromadb(self):
        """Inicializa ChromaDB y las colecciones especializadas."""
        try:
            import chromadb
            from chromadb.config import Settings
            
            self.persist_dir.mkdir(parents=True, exist_ok=True)
            
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.persist_dir),
                settings=Settings(anonymized_telemetry=False)
            )
            
            for name in self.COLLECTION_NAMES:
                self.collections[name] = self.chroma_client.get_or_create_collection(
                    name=name,
                    metadata={"description": f"Colección para {name}"}
                )
                logger.info(f"✅ Colección '{name}' cargada/creada exitosamente.")
            
            logger.info(f"✅ ChromaDB inicializado en: {self.persist_dir}")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando ChromaDB: {e}")
            self.chroma_client = None
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Genera embedding híbrido: Local primero, Gemini como fallback."""
        if self.primary_embedding == "local" and self.local_embedder:
            try:
                return self.local_embedder.encode([text])[0].tolist()
            except Exception as e:
                logger.warning(f"⚠️ Error en embedding local, usando fallback: {e}")
        
        if self.fallback_embedding == "gemini" and self.gemini_embedder:
            try:
                result = self.gemini_embedder.embed_content(
                    model=f"models/{self.gemini_model}",
                    content=text,
                    task_type="retrieval_document"
                )
                return result['embedding']
            except Exception as e:
                logger.error(f"❌ Error en Gemini embedding: {e}")
        
        logger.error("❌ No hay embedders disponibles para generar el embedding.")
        return None

    async def add_documents(self, collection_name: str, documents: List[str], metadatas: List[Dict], ids: List[str]):
        """
        Vectoriza y guarda un lote de documentos en una colección específica.
        """
        if collection_name not in self.collections:
            logger.error(f"❌ Colección '{collection_name}' no existe.")
            return None
        
        collection = self.collections[collection_name]
        
        try:
            embeddings = []
            for doc in documents:
                embedding = await self.generate_embedding(doc)
                if embedding:
                    embeddings.append(embedding)
                else:
                    # Si un embedding falla, no podemos continuar
                    logger.error(f"Fallo al generar embedding para un documento en el lote. Abortando.")
                    return None
            
            collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"✅ {len(documents)} documentos añadidos a la colección '{collection_name}'.")
            return ids
            
        except Exception as e:
            logger.error(f"❌ Error añadiendo documentos a '{collection_name}': {e}")
            return None

    async def search(self, collection_name: str, query: str, n_results: int = 5, where_filter: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Búsqueda semántica en una colección específica.
        """
        if collection_name not in self.collections:
            logger.error(f"❌ Colección '{collection_name}' no existe para la búsqueda.")
            return []
        
        collection = self.collections[collection_name]
        
        try:
            query_embedding = await self.generate_embedding(query)
            if not query_embedding:
                logger.error(f"❌ No se pudo generar embedding para query: '{query}'")
                return []
            
            # DEBUG: Verificar embedding de query
            logger.info(f"🔍 DEBUG - Query embedding generado para '{query}': dimensión {len(query_embedding)}")
            logger.info(f"🔍 DEBUG - Embedding preview: {query_embedding[:5]}... (primeros 5 valores)")
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter,
                include=['metadatas', 'documents', 'distances']
            )
            
            formatted_results = []
            if results and results['ids'] and len(results['ids'][0]) > 0:
                logger.info(f"🔍 DEBUG - Resultados ChromaDB para '{query}':")
                for i in range(len(results['ids'][0])):
                    distance = results['distances'][0][i]
                    # CRITICAL FIX: Usar fórmula correcta para distancia euclidiana
                    # ChromaDB devuelve distancias euclideanas que pueden ser > 1
                    # Convertir a similitud usando: 1 / (1 + distance)
                    similarity = 1.0 / (1.0 + distance)
                    document_preview = results['documents'][0][i][:100] if results['documents'][0][i] else "N/A"
                    
                    # DEBUG CRÍTICO: Log detallado de cada resultado
                    logger.info(f"   Resultado {i+1}:")
                    logger.info(f"     - ID: {results['ids'][0][i]}")
                    logger.info(f"     - Distance: {distance}")
                    logger.info(f"     - Similarity: {similarity:.6f}")
                    logger.info(f"     - Document preview: {document_preview}...")
                    
                    result = {
                        'id': results['ids'][0][i],
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': distance,
                        'similarity': similarity
                    }
                    formatted_results.append(result)
            
            logger.info(f"✅ Búsqueda en '{collection_name}': {len(formatted_results)} resultados para '{query}'")
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda en '{collection_name}': {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de todas las colecciones."""
        stats = {
            "chromadb_available": self.chroma_client is not None,
            "embedding_provider": self.embedding_provider,
            "collections": {}
        }
        
        for name, collection in self.collections.items():
            try:
                count = collection.count()
                stats["collections"][name] = {
                    "name": name,
                    "document_count": count,
                    "status": "active"
                }
            except Exception as e:
                stats["collections"][name] = {"status": "error", "error": str(e)}
        
        return stats
    
    async def cleanup_old_vectors(self, collection_name: str, days_to_keep: int = 365):
        """Limpia vectores antiguos de una colección específica."""
        if collection_name not in self.collections:
            logger.error(f"❌ Colección '{collection_name}' no existe para limpieza.")
            return

        collection = self.collections[collection_name]
        
        try:
            from datetime import timedelta
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
            
            all_results = collection.get(include=['metadatas'])
            
            ids_to_delete = [
                all_results['ids'][i]
                for i, metadata in enumerate(all_results['metadatas'])
                if metadata.get('timestamp', '') < cutoff_date
            ]
            
            if ids_to_delete:
                collection.delete(ids=ids_to_delete)
                logger.info(f"✅ Limpieza en '{collection_name}': {len(ids_to_delete)} vectores antiguos eliminados")
            
        except Exception as e:
            logger.error(f"❌ Error en limpieza de vectores en '{collection_name}': {e}")
