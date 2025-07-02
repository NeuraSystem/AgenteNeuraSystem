"""
Chunker inteligente para texto con optimización de rendimiento.
Fragmenta texto preservando contexto semántico.
"""

import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class TextChunker:
    """
    Chunker inteligente que fragmenta texto preservando contexto semántico.
    Optimizado para el hardware del usuario (rendimiento).
    """
    
    def __init__(self, 
                 max_chunk_size: int = 1000,
                 overlap_size: int = 100,
                 min_chunk_size: int = 100):
        """
        Inicializa el chunker.
        
        Args:
            max_chunk_size: Máximo de tokens por chunk
            overlap_size: Solapamiento entre chunks
            min_chunk_size: Mínimo de tokens por chunk
        """
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        self.min_chunk_size = min_chunk_size
        
        # Patrones para detectar límites semánticos
        self.sentence_endings = re.compile(r'[.!?]+\s+')
        self.paragraph_breaks = re.compile(r'\n\s*\n')
        self.section_headers = re.compile(r'\n#{1,6}\s+.+\n|^\d+\.\s+.+$', re.MULTILINE)
    
    def chunk_text(self, 
                   text: str, 
                   source_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Fragmenta texto en chunks inteligentes.
        
        Args:
            text: Texto a fragmentar
            source_metadata: Metadata del documento original
            
        Returns:
            Lista de chunks con metadata
        """
        if not text or len(text.strip()) == 0:
            return []
        
        # Estrategia de chunking basada en tamaño del texto
        text_tokens = self._estimate_tokens(text)
        
        if text_tokens <= self.max_chunk_size:
            # Texto pequeño: un solo chunk
            return self._create_single_chunk(text, source_metadata)
        else:
            # Texto grande: chunking inteligente
            return self._create_smart_chunks(text, source_metadata)
    
    def _create_single_chunk(self, 
                           text: str, 
                           source_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Crea un solo chunk para texto pequeño.
        """
        return [{
            "content": text.strip(),
            "chunk_id": "single_chunk_1",
            "metadata": {
                "chunk_index": 0,
                "chunk_count": 1,
                "tokens": self._estimate_tokens(text),
                "length": len(text),
                "type": "single",
                "source": source_metadata or {}
            }
        }]
    
    def _create_smart_chunks(self, 
                           text: str, 
                           source_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Crea chunks inteligentes preservando contexto semántico.
        """
        # Detectar secciones naturales
        sections = self._detect_sections(text)
        
        chunks = []
        chunk_index = 0
        
        for section in sections:
            section_text = section["content"]
            section_tokens = self._estimate_tokens(section_text)
            
            if section_tokens <= self.max_chunk_size:
                # Sección cabe en un chunk
                if section_tokens >= self.min_chunk_size:
                    chunks.append(self._create_chunk(
                        section_text, chunk_index, section["metadata"], source_metadata
                    ))
                    chunk_index += 1
            else:
                # Sección necesita subdivisión
                sub_chunks = self._split_large_section(section_text, section["metadata"])
                for sub_chunk in sub_chunks:
                    sub_chunk["metadata"]["chunk_index"] = chunk_index
                    sub_chunk["metadata"]["source"] = source_metadata or {}
                    chunks.append(sub_chunk)
                    chunk_index += 1
        
        # Añadir información global
        for chunk in chunks:
            chunk["metadata"]["chunk_count"] = len(chunks)
        
        return chunks
    
    def _detect_sections(self, text: str) -> List[Dict[str, Any]]:
        """
        Detecta secciones naturales en el texto.
        """
        sections = []
        
        # Dividir por párrafos dobles primero
        paragraphs = self.paragraph_breaks.split(text)
        
        current_section = ""
        section_type = "paragraph"
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # Detectar si es encabezado de sección
            if self.section_headers.search(paragraph):
                # Guardar sección anterior si existe
                if current_section:
                    sections.append({
                        "content": current_section.strip(),
                        "metadata": {"type": section_type}
                    })
                
                # Iniciar nueva sección
                current_section = paragraph
                section_type = "section"
            else:
                # Añadir párrafo a sección actual
                if current_section:
                    current_section += "\n\n" + paragraph
                else:
                    current_section = paragraph
        
        # Añadir última sección
        if current_section:
            sections.append({
                "content": current_section.strip(),
                "metadata": {"type": section_type}
            })
        
        return sections if sections else [{"content": text, "metadata": {"type": "full_text"}}]
    
    def _split_large_section(self, text: str, section_metadata: Dict) -> List[Dict[str, Any]]:
        """
        Divide secciones grandes en chunks más pequeños.
        """
        chunks = []
        sentences = self.sentence_endings.split(text)
        
        current_chunk = ""
        chunk_index = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Calcular tamaño si añadimos esta oración
            test_chunk = current_chunk + " " + sentence if current_chunk else sentence
            
            if self._estimate_tokens(test_chunk) <= self.max_chunk_size:
                current_chunk = test_chunk
            else:
                # Guardar chunk actual si tiene contenido suficiente
                if current_chunk and self._estimate_tokens(current_chunk) >= self.min_chunk_size:
                    chunks.append(self._create_chunk(
                        current_chunk, chunk_index, section_metadata
                    ))
                    chunk_index += 1
                    
                    # Iniciar nuevo chunk con solapamiento
                    overlap_text = self._get_overlap_text(current_chunk)
                    current_chunk = overlap_text + " " + sentence
                else:
                    current_chunk = test_chunk
        
        # Añadir último chunk
        if current_chunk and self._estimate_tokens(current_chunk) >= self.min_chunk_size:
            chunks.append(self._create_chunk(
                current_chunk, chunk_index, section_metadata
            ))
        
        return chunks
    
    def _get_overlap_text(self, text: str) -> str:
        """
        Obtiene texto de solapamiento del final del chunk.
        """
        words = text.split()
        if len(words) <= 20:  # Si es muy corto, usar todo
            return text
        
        # Usar últimas ~15 palabras como solapamiento
        overlap_words = words[-15:]
        return " ".join(overlap_words)
    
    def _create_chunk(self, 
                     content: str, 
                     chunk_index: int, 
                     section_metadata: Dict = None,
                     source_metadata: Dict = None) -> Dict[str, Any]:
        """
        Crea un chunk con metadata completa.
        """
        return {
            "content": content.strip(),
            "chunk_id": f"chunk_{chunk_index + 1}",
            "metadata": {
                "chunk_index": chunk_index,
                "tokens": self._estimate_tokens(content),
                "length": len(content),
                "type": "smart_chunk",
                "section": section_metadata or {},
                "source": source_metadata or {}
            }
        }
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estima tokens usando aproximación simple (~4 chars por token).
        """
        return len(text) // 4