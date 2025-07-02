"""
Gestor principal de documentos.
Coordina extracción, chunking y almacenamiento de documentos.
"""

import asyncio
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import json
from datetime import datetime

from .extractors import PDFExtractor, DOCXExtractor, XLSXExtractor, TXTExtractor
from .chunkers import TextChunker, TableChunker
from .document_vector_manager import DocumentVectorManager

logger = logging.getLogger(__name__)

class DocumentManager:
    """
    Gestor principal que coordina todo el procesamiento de documentos.
    """
    
    def __init__(self, storage_path: str = "./data/documents"):
        self.storage_path = Path(storage_path)
        self.uploads_path = self.storage_path / "uploads"
        self.processed_path = self.storage_path / "processed"
        self.temp_path = self.storage_path / "temp"
        
        # Crear directorios
        self._ensure_directories()
        
        # Inicializar extractores
        self.extractors = {
            ".pdf": PDFExtractor(),
            ".txt": TXTExtractor(),
            ".md": TXTExtractor(),
            ".docx": DOCXExtractor(),
            ".xlsx": XLSXExtractor(),
            ".xls": XLSXExtractor()
        }
        
        # Inicializar chunkers
        self.text_chunker = TextChunker(
            max_chunk_size=1000,  # Optimizado para tu PC
            overlap_size=100,
            min_chunk_size=100
        )
        self.table_chunker = TableChunker(
            max_rows_per_chunk=50,
            include_headers=True
        )
        
        # Inicializar gestor de vectores para documentos
        self.vector_manager = DocumentVectorManager()
        
        # Cache de documentos procesados
        self.document_cache = {}
        
        logger.info(f"DocumentManager inicializado en: {self.storage_path}")
    
    def _ensure_directories(self):
        """Crea estructura de directorios necesaria."""
        for path in [self.uploads_path, self.processed_path, self.temp_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    async def process_document(self, 
                             file_path: Path, 
                             document_id: str = None) -> Dict[str, Any]:
        """
        Procesa un documento completo: extracción + chunking.
        
        Args:
            file_path: Ruta al archivo
            document_id: ID opcional del documento
            
        Returns:
            Dict con resultado del procesamiento
        """
        try:
            # Generar ID si no se proporciona
            if not document_id:
                document_id = str(uuid.uuid4())
            
            logger.info(f"Procesando documento {document_id}: {file_path}")
            
            # Validar archivo
            if not file_path.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
            
            file_extension = file_path.suffix.lower()
            if file_extension not in self.extractors:
                raise ValueError(f"Formato no soportado: {file_extension}")
            
            # 1. Extraer contenido
            extractor = self.extractors[file_extension]
            extraction_result = await extractor.extract(file_path)
            
            # 2. Chunking inteligente
            chunks = await self._process_chunks(extraction_result, document_id)
            
            # 3. Crear documento procesado
            processed_document = {
                "document_id": document_id,
                "file_name": file_path.name,
                "file_path": str(file_path),
                "file_type": file_extension.replace(".", ""),
                "processed_at": datetime.now().isoformat(),
                "extraction_result": extraction_result,
                "chunks": chunks,
                "status": "processed",
                "chunk_count": len(chunks),
                "total_tokens": sum(chunk.get("metadata", {}).get("tokens", 0) for chunk in chunks)
            }
            
            # 4. Vectorizar chunks (integración con sistema de embeddings)
            vectorization_success = await self.vector_manager.vectorize_document_chunks(
                document_id, chunks, extraction_result["metadata"]
            )
            
            if vectorization_success:
                processed_document["vectorized"] = True
                processed_document["vectorized_at"] = datetime.now().isoformat()
                logger.info(f"Documento {document_id} vectorizado exitosamente")
            else:
                processed_document["vectorized"] = False
                logger.warning(f"Error vectorizando documento {document_id}")
            
            # 5. Guardar documento procesado
            await self._save_processed_document(document_id, processed_document)
            
            # 6. Añadir a cache
            self.document_cache[document_id] = processed_document
            
            logger.info(f"Documento {document_id} procesado exitosamente: {len(chunks)} chunks")
            
            return processed_document
            
        except Exception as e:
            logger.error(f"Error procesando documento {file_path}: {e}")
            raise
    
    async def _process_chunks(self, 
                            extraction_result: Dict[str, Any], 
                            document_id: str) -> List[Dict[str, Any]]:
        """
        Procesa chunks según el tipo de contenido.
        """
        chunks = []
        content = extraction_result.get("content", "")
        metadata = extraction_result.get("metadata", {})
        
        # Determinar estrategia de chunking
        file_type = metadata.get("file_type", "")
        
        if file_type in ["xlsx", "xls"]:
            # Para Excel: usar chunks tabulares si están disponibles
            original_chunks = extraction_result.get("chunks", [])
            for chunk in original_chunks:
                chunk_type = chunk.get("metadata", {}).get("type")
                if chunk_type in ["spreadsheet", "spreadsheet_row"]:  # ✅ Incluir nueva estrategia
                    # Ya está chunkeado apropiadamente por el extractor
                    chunk["metadata"]["document_id"] = document_id
                    chunks.append(chunk)
        else:
            # Para texto: usar chunking inteligente
            text_chunks = self.text_chunker.chunk_text(content, metadata)
            for chunk in text_chunks:
                chunk["metadata"]["document_id"] = document_id
                chunks.append(chunk)
        
        return chunks
    
    async def _save_processed_document(self, 
                                     document_id: str, 
                                     document_data: Dict[str, Any]):
        """
        Guarda documento procesado en almacenamiento persistente.
        """
        try:
            file_path = self.processed_path / f"{document_id}.json"
            
            # Preparar datos para serialización
            serializable_data = self._make_serializable(document_data)
            
            # Guardar como JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Documento guardado en: {file_path}")
            
        except Exception as e:
            logger.error(f"Error guardando documento {document_id}: {e}")
            raise
    
    def _make_serializable(self, data: Any) -> Any:
        """
        Convierte datos a formato serializable JSON.
        """
        if isinstance(data, dict):
            return {k: self._make_serializable(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._make_serializable(item) for item in data]
        elif isinstance(data, (str, int, float, bool)) or data is None:
            return data
        else:
            return str(data)
    
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene documento procesado por ID.
        """
        # Buscar en cache primero
        if document_id in self.document_cache:
            return self.document_cache[document_id]
        
        # Buscar en almacenamiento
        file_path = self.processed_path / f"{document_id}.json"
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    document = json.load(f)
                
                # Añadir a cache
                self.document_cache[document_id] = document
                return document
                
            except Exception as e:
                logger.error(f"Error cargando documento {document_id}: {e}")
        
        return None
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """
        Lista todos los documentos procesados.
        """
        documents = []
        
        for file_path in self.processed_path.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    document = json.load(f)
                
                # Solo metadata básica para el listado
                documents.append({
                    "document_id": document.get("document_id"),
                    "file_name": document.get("file_name"),
                    "file_type": document.get("file_type"),
                    "processed_at": document.get("processed_at"),
                    "chunk_count": document.get("chunk_count", 0),
                    "status": document.get("status", "unknown")
                })
                
            except Exception as e:
                logger.warning(f"Error leyendo documento {file_path}: {e}")
        
        # Ordenar por fecha de procesamiento (más reciente primero)
        documents.sort(key=lambda x: x.get("processed_at", ""), reverse=True)
        
        return documents
    
    async def get_document_chunks(self, 
                                document_id: str, 
                                chunk_type: str = None) -> List[Dict[str, Any]]:
        """
        Obtiene chunks de un documento específico.
        
        Args:
            document_id: ID del documento
            chunk_type: Filtro por tipo de chunk (opcional)
            
        Returns:
            Lista de chunks
        """
        document = await self.get_document(document_id)
        if not document:
            return []
        
        chunks = document.get("chunks", [])
        
        # Filtrar por tipo si se especifica
        if chunk_type:
            chunks = [
                chunk for chunk in chunks 
                if chunk.get("metadata", {}).get("type") == chunk_type
            ]
        
        return chunks
    
    async def search_documents(self,
                             query: str,
                             document_id: Optional[str] = None,
                             limit: int = 5) -> List[Dict[str, Any]]:
        """
        Busca contenido en documentos vectorizados.
        
        Args:
            query: Consulta de búsqueda
            document_id: ID de documento específico (opcional)
            limit: Número máximo de resultados
            
        Returns:
            Lista de resultados con contenido y metadata
        """
        try:
            results = await self.vector_manager.search_documents(query, document_id, limit)
            
            # Enriquecer resultados con información adicional del documento
            for result in results:
                doc_id = result.get("document_id")
                if doc_id and doc_id in self.document_cache:
                    document = self.document_cache[doc_id]
                    result["document_info"] = {
                        "file_name": document.get("file_name"),
                        "file_type": document.get("file_type"),
                        "processed_at": document.get("processed_at")
                    }
            
            return results
            
        except Exception as e:
            logger.error(f"Error en búsqueda de documentos: {e}")
            return []
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Elimina documento procesado y sus vectores.
        """
        try:
            # Eliminar vectores primero
            vector_deleted = await self.vector_manager.delete_document_vectors(document_id)
            
            # Eliminar archivo de documento procesado
            file_path = self.processed_path / f"{document_id}.json"
            file_deleted = False
            if file_path.exists():
                file_path.unlink()
                file_deleted = True
            
            # Remover de cache
            if document_id in self.document_cache:
                del self.document_cache[document_id]
            
            success = vector_deleted or file_deleted
            if success:
                logger.info(f"Documento {document_id} eliminado (vectores: {vector_deleted}, archivo: {file_deleted})")
            
            return success
            
        except Exception as e:
            logger.error(f"Error eliminando documento {document_id}: {e}")
            return False
    
    def get_supported_formats(self) -> List[str]:
        """
        Obtiene lista de formatos soportados.
        """
        return list(self.extractors.keys())