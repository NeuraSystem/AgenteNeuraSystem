"""
Extractor para archivos de texto plano (.txt).
"""

import aiofiles
from pathlib import Path
from typing import Dict, Any
import logging
import chardet

from .base_extractor import BaseExtractor

logger = logging.getLogger(__name__)

class TXTExtractor(BaseExtractor):
    """
    Extractor para archivos de texto plano.
    Maneja diferentes encodings automáticamente.
    """
    
    def __init__(self):
        super().__init__()
        self.supported_formats = [".txt", ".md", ".log", ".csv"]
    
    async def extract(self, file_path: Path) -> Dict[str, Any]:
        """
        Extrae contenido de archivo de texto.
        
        Args:
            file_path: Ruta al archivo .txt
            
        Returns:
            Dict con contenido y metadata
        """
        try:
            # Validar archivo
            if not self.validate_file(file_path):
                raise ValueError(f"Archivo inválido: {file_path}")
            
            # Detectar encoding
            encoding = await self._detect_encoding(file_path)
            logger.info(f"Detectado encoding {encoding} para {file_path}")
            
            # Leer contenido
            async with aiofiles.open(file_path, 'r', encoding=encoding) as file:
                content = await file.read()
            
            # Limpiar contenido
            content = self._clean_text(content)
            
            # Crear metadata
            metadata = self.create_metadata(file_path, {
                "encoding": encoding,
                "line_count": content.count('\n') + 1,
                "char_count": len(content),
                "estimated_tokens": self.estimate_tokens(content)
            })
            
            # Crear chunks básicos (por párrafos)
            chunks = self._create_chunks(content)
            
            return {
                "content": content,
                "metadata": metadata,
                "chunks": chunks
            }
            
        except Exception as e:
            logger.error(f"Error extrayendo archivo TXT {file_path}: {e}")
            raise
    
    async def _detect_encoding(self, file_path: Path) -> str:
        """
        Detecta el encoding del archivo.
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            str: Encoding detectado
        """
        try:
            # Leer una muestra del archivo
            with open(file_path, 'rb') as file:
                raw_data = file.read(10000)  # Primeros 10KB
            
            # Detectar encoding
            result = chardet.detect(raw_data)
            encoding = result.get('encoding', 'utf-8')
            
            # Fallback a UTF-8 si la confianza es muy baja
            if result.get('confidence', 0) < 0.7:
                encoding = 'utf-8'
            
            return encoding
            
        except Exception as e:
            logger.warning(f"Error detectando encoding, usando UTF-8: {e}")
            return 'utf-8'
    
    def _clean_text(self, text: str) -> str:
        """
        Limpia y normaliza el texto.
        
        Args:
            text: Texto crudo
            
        Returns:
            str: Texto limpio
        """
        # Remover caracteres de control (excepto saltos de línea y tabs)
        cleaned = ''.join(char for char in text 
                         if char.isprintable() or char in '\n\t')
        
        # Normalizar saltos de línea
        cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remover líneas vacías múltiples
        lines = cleaned.split('\n')
        clean_lines = []
        prev_empty = False
        
        for line in lines:
            line = line.strip()
            is_empty = len(line) == 0
            
            if not (is_empty and prev_empty):
                clean_lines.append(line)
            
            prev_empty = is_empty
        
        return '\n'.join(clean_lines)
    
    def _create_chunks(self, content: str) -> list:
        """
        Crea chunks básicos dividiendo por párrafos.
        
        Args:
            content: Contenido completo
            
        Returns:
            List de chunks
        """
        chunks = []
        paragraphs = content.split('\n\n')
        
        chunk_id = 0
        position = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if len(paragraph) > 0:
                chunk_id += 1
                
                chunks.append({
                    "content": paragraph,
                    "chunk_id": f"txt_chunk_{chunk_id}",
                    "metadata": {
                        "type": "paragraph",
                        "position": position,
                        "length": len(paragraph),
                        "tokens": self.estimate_tokens(paragraph)
                    }
                })
                
                position += len(paragraph) + 2  # +2 por los \n\n
        
        return chunks