"""
Extractores de contenido para diferentes formatos de documento.
"""

from .base_extractor import BaseExtractor
from .pdf_extractor import PDFExtractor
from .docx_extractor import DOCXExtractor
from .xlsx_extractor import XLSXExtractor
from .txt_extractor import TXTExtractor

__all__ = ["BaseExtractor", "PDFExtractor", "DOCXExtractor", "XLSXExtractor", "TXTExtractor"]