"""
Clase base para extractores de documentos.
Define la interfaz común para todos los extractores.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class BaseExtractor(ABC):
    """
    Clase base abstracta para extractores de documentos.
    """
    
    def __init__(self):
        self.supported_formats = []
        self.max_file_size = 50 * 1024 * 1024  # 50MB por defecto
    
    @abstractmethod
    async def extract(self, file_path: Path) -> Dict[str, Any]:
        """
        Extrae contenido del archivo.
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            Dict con estructura:
            {
                "content": "Texto extraído",
                "metadata": {
                    "file_type": "pdf|docx|xlsx|txt",
                    "file_size": 1234,
                    "pages": 5,
                    "extraction_method": "pyPDF2",
                    "structure_info": {...}
                },
                "chunks": [
                    {
                        "content": "Fragmento de texto",
                        "chunk_id": "chunk_1",
                        "metadata": {
                            "page": 1,
                            "position": 0,
                            "length": 100
                        }
                    }
                ]
            }
        """
        pass
    
    def validate_file(self, file_path: Path) -> bool:
        """
        Valida que el archivo sea procesable.
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            bool: True si es válido
        """
        try:
            # Verificar que existe
            if not file_path.exists():
                logger.error(f"Archivo no existe: {file_path}")
                return False
            
            # Verificar tamaño
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size:
                logger.error(f"Archivo muy grande: {file_size} bytes (máximo: {self.max_file_size})")
                return False
            
            # Verificar extensión
            file_extension = file_path.suffix.lower()
            if file_extension not in self.supported_formats:
                logger.error(f"Formato no soportado: {file_extension}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validando archivo {file_path}: {e}")
            return False
    
    def create_metadata(self, file_path: Path, additional_info: Dict = None) -> Dict[str, Any]:
        """
        Crea metadata básica del archivo.
        
        Args:
            file_path: Ruta al archivo
            additional_info: Información adicional específica del formato
            
        Returns:
            Dict con metadata
        """
        try:
            stat = file_path.stat()
            
            metadata = {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "file_type": file_path.suffix.lower().replace(".", ""),
                "file_size": stat.st_size,
                "modified_time": stat.st_mtime,
                "extraction_method": self.__class__.__name__,
                "extractor_version": "1.0"
            }
            
            # Añadir información adicional específica del formato
            if additional_info:
                metadata.update(additional_info)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error creando metadata para {file_path}: {e}")
            return {}
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estima la cantidad de tokens en el texto.
        Usa aproximación simple: ~4 caracteres por token.
        
        Args:
            text: Texto a analizar
            
        Returns:
            int: Número estimado de tokens
        """
        return len(text) // 4