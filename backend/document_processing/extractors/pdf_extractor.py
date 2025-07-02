"""
Extractor para archivos PDF usando PyPDF2.
"""

import PyPDF2
from pathlib import Path
from typing import Dict, Any, List
import logging
import re

from .base_extractor import BaseExtractor

logger = logging.getLogger(__name__)

class PDFExtractor(BaseExtractor):
    """
    Extractor para archivos PDF usando PyPDF2.
    Maneja PDFs con texto extraíble.
    """
    
    def __init__(self):
        super().__init__()
        self.supported_formats = [".pdf"]
    
    async def extract(self, file_path: Path) -> Dict[str, Any]:
        """
        Extrae contenido de archivo PDF.
        
        Args:
            file_path: Ruta al archivo .pdf
            
        Returns:
            Dict con contenido y metadata
        """
        try:
            # Validar archivo
            if not self.validate_file(file_path):
                raise ValueError(f"Archivo PDF inválido: {file_path}")
            
            # Abrir PDF
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Verificar si el PDF está encriptado
                if pdf_reader.is_encrypted:
                    logger.warning(f"PDF encriptado: {file_path}")
                    # Intentar desencriptar con contraseña vacía
                    if not pdf_reader.decrypt(""):
                        raise ValueError("PDF encriptado con contraseña")
                
                # Extraer texto de todas las páginas
                pages_content = []
                full_content = ""
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        page_text = self._clean_text(page_text)
                        
                        pages_content.append({
                            "page": page_num,
                            "content": page_text,
                            "char_count": len(page_text)
                        })
                        
                        full_content += f"\n[PÁGINA {page_num}]\n{page_text}\n"
                        
                    except Exception as e:
                        logger.warning(f"Error extrayendo página {page_num}: {e}")
                        pages_content.append({
                            "page": page_num,
                            "content": "",
                            "error": str(e)
                        })
                
                # Limpiar contenido completo
                full_content = self._clean_text(full_content)
                
                # Crear metadata
                pdf_info = pdf_reader.metadata
                metadata = self.create_metadata(file_path, {
                    "page_count": len(pdf_reader.pages),
                    "encrypted": pdf_reader.is_encrypted,
                    "char_count": len(full_content),
                    "estimated_tokens": self.estimate_tokens(full_content),
                    "pdf_info": {
                        "title": pdf_info.get("/Title", "") if pdf_info else "",
                        "author": pdf_info.get("/Author", "") if pdf_info else "",
                        "subject": pdf_info.get("/Subject", "") if pdf_info else "",
                        "creator": pdf_info.get("/Creator", "") if pdf_info else ""
                    }
                })
                
                # Crear chunks por página
                chunks = self._create_chunks(pages_content)
                
                return {
                    "content": full_content,
                    "metadata": metadata,
                    "chunks": chunks
                }
                
        except Exception as e:
            logger.error(f"Error extrayendo PDF {file_path}: {e}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """
        Limpia texto extraído de PDF.
        
        Args:
            text: Texto crudo del PDF
            
        Returns:
            str: Texto limpio
        """
        if not text:
            return ""
        
        # Remover caracteres de control
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]', '', text)
        
        # Normalizar espacios en blanco
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Normalizar saltos de línea
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remover espacios al inicio y final de líneas
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text.strip()
    
    def _create_chunks(self, pages_content: List[Dict]) -> List[Dict]:
        """
        Crea chunks basados en páginas y párrafos.
        
        Args:
            pages_content: Lista de contenido por página
            
        Returns:
            List de chunks
        """
        chunks = []
        chunk_id = 0
        
        for page_data in pages_content:
            page_num = page_data["page"]
            content = page_data["content"]
            
            if not content or len(content.strip()) == 0:
                continue
            
            # Dividir página en párrafos
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            
            for para_idx, paragraph in enumerate(paragraphs):
                if len(paragraph) > 50:  # Solo párrafos significativos
                    chunk_id += 1
                    
                    chunks.append({
                        "content": paragraph,
                        "chunk_id": f"pdf_chunk_{chunk_id}",
                        "metadata": {
                            "type": "paragraph",
                            "page": page_num,
                            "paragraph_index": para_idx + 1,
                            "length": len(paragraph),
                            "tokens": self.estimate_tokens(paragraph)
                        }
                    })
        
        return chunks