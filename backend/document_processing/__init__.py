"""
Módulo de procesamiento de documentos para ChatIng.
- Extractores para PDF, DOCX, XLSX, TXT
- Chunking inteligente de contenido
- Análisis estructural con LLM
- Integración con sistema de embeddings
"""

from .document_manager import DocumentManager
from .extractors import PDFExtractor, DOCXExtractor, XLSXExtractor, TXTExtractor

__all__ = [
    "DocumentManager", 
    "PDFExtractor", 
    "DOCXExtractor", 
    "XLSXExtractor", 
    "TXTExtractor"
]