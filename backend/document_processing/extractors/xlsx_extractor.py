"""
Extractor para archivos Excel XLSX usando pandas.
Estrategia: "Una Fila = Un Documento" para RAG optimizado.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
import logging
import numpy as np

from .base_extractor import BaseExtractor

logger = logging.getLogger(__name__)

class XLSXExtractor(BaseExtractor):
    """
    Extractor para archivos Excel XLSX optimizado para RAG.
    Implementa la estrategia "Una Fila = Un Documento" para máxima precisión.
    """
    
    def __init__(self):
        super().__init__()
        self.supported_formats = [".xlsx", ".xls"]
        self.max_rows_per_sheet = 10000  # Límite de seguridad
        self.max_cols_per_sheet = 50     # Límite de columnas
    
    async def extract(self, file_path: Path) -> Dict[str, Any]:
        """
        Extrae contenido de archivo XLSX usando estrategia "Una Fila = Un Documento".
        
        Args:
            file_path: Ruta al archivo .xlsx
            
        Returns:
            Dict con contenido y metadata optimizado para RAG
        """
        try:
            # Validar archivo
            if not self.validate_file(file_path):
                raise ValueError(f"Archivo XLSX inválido: {file_path}")
            
            # Cargar todas las hojas del archivo
            logger.info(f"🔄 Procesando archivo XLSX: {file_path.name}")
            xls = pd.ExcelFile(file_path)
            
            all_chunks = []
            total_rows = 0
            sheet_summaries = []
            
            # Procesar cada hoja
            for sheet_name in xls.sheet_names:
                try:
                    logger.info(f"📊 Procesando hoja: {sheet_name}")
                    
                    # Leer la hoja con pandas
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    # Aplicar límites de seguridad
                    if df.shape[0] > self.max_rows_per_sheet:
                        logger.warning(f"⚠️ Hoja {sheet_name} tiene {df.shape[0]} filas, limitando a {self.max_rows_per_sheet}")
                        df = df.head(self.max_rows_per_sheet)
                    
                    if df.shape[1] > self.max_cols_per_sheet:
                        logger.warning(f"⚠️ Hoja {sheet_name} tiene {df.shape[1]} columnas, limitando a {self.max_cols_per_sheet}")
                        df = df.iloc[:, :self.max_cols_per_sheet]
                    
                    # Crear chunks por fila usando la nueva estrategia
                    sheet_chunks = self._create_row_based_chunks(df, sheet_name, file_path.name)
                    all_chunks.extend(sheet_chunks)
                    total_rows += len(sheet_chunks)
                    
                    # Resumen de la hoja
                    sheet_summaries.append(f"Hoja '{sheet_name}': {len(sheet_chunks)} filas procesadas")
                    logger.info(f"✅ Hoja {sheet_name}: {len(sheet_chunks)} documentos creados")
                    
                except Exception as e:
                    logger.warning(f"❌ Error procesando hoja {sheet_name}: {e}")
                    sheet_summaries.append(f"Hoja '{sheet_name}': Error - {str(e)}")
            
            # Crear contenido general de resumen
            full_content = f"Archivo Excel: {file_path.name}\n"
            full_content += f"Total de documentos creados: {total_rows}\n"
            full_content += f"Hojas procesadas: {len(xls.sheet_names)}\n"
            full_content += "\n".join(sheet_summaries)
            
            # Crear metadata optimizada (solo tipos primitivos para ChromaDB)
            metadata = self.create_metadata(file_path, {
                "processing_strategy": "one_row_one_document",
                "sheet_count": len(xls.sheet_names),
                "sheet_names": ", ".join(xls.sheet_names),  # ✅ Convertir lista a string
                "total_documents": total_rows,
                "total_rows": total_rows,
                "char_count": len(full_content),
                "estimated_tokens": self.estimate_tokens(full_content)
            })
            
            logger.info(f"🎉 Procesamiento completado: {total_rows} documentos de {len(xls.sheet_names)} hojas")
            
            return {
                "content": full_content,
                "metadata": metadata,
                "chunks": all_chunks
            }
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo XLSX {file_path}: {e}")
            raise
    
    def _create_row_based_chunks(self, df: pd.DataFrame, sheet_name: str, file_name: str) -> List[Dict[str, Any]]:
        """
        Implementa la estrategia "Una Fila = Un Documento".
        Cada fila se convierte en un documento independiente con metadatos ricos.
        
        Args:
            df: DataFrame de la hoja
            sheet_name: Nombre de la hoja
            file_name: Nombre del archivo
            
        Returns:
            Lista de chunks (documentos)
        """
        chunks = []
        
        if df.empty:
            logger.warning(f"⚠️ Hoja {sheet_name} está vacía, omitiendo...")
            return chunks
        
        # Detectar si hay encabezados (primera fila contiene strings no numéricos)
        has_headers = self._detect_headers(df)
        
        # Si hay encabezados, usar la primera fila como nombres de columnas
        if has_headers and len(df) > 1:
            df.columns = df.iloc[0].astype(str).str.strip()
            df = df.iloc[1:].reset_index(drop=True)  # Remover fila de encabezados
            logger.info(f"📋 Encabezados detectados en {sheet_name}: {list(df.columns)}")
        else:
            # Generar nombres de columnas genéricos
            df.columns = [f"Columna_{i+1}" for i in range(len(df.columns))]
            logger.info(f"📋 Sin encabezados en {sheet_name}, usando nombres genéricos")
        
        # Crear un documento por cada fila
        for index, row in df.iterrows():
            # Construir contenido textual de la fila con formato estructurado
            row_content_parts = []
            non_empty_values = 0
            
            for col_name, cell_value in row.items():
                if pd.notna(cell_value) and str(cell_value).strip():
                    clean_value = str(cell_value).strip()
                    row_content_parts.append(f"'{col_name}': '{clean_value}'")
                    non_empty_values += 1
            
            # Solo crear documento si la fila tiene datos significativos
            if non_empty_values > 0:
                # Formato de contenido optimizado para búsqueda semántica
                page_content = f"Hoja: '{sheet_name}'. Fila: {index + 2}. {', '.join(row_content_parts)}"
                
                # Metadatos ricos para filtrado y trazabilidad
                chunk_metadata = {
                    "type": "spreadsheet_row",
                    "file_name": file_name,
                    "sheet_name": sheet_name,
                    "row_number": index + 2,  # +2 para contar encabezados y índice 0
                    "original_row_index": index,
                    "non_empty_fields": non_empty_values,
                    "total_fields": len(row),
                    "fill_ratio": round(non_empty_values / len(row), 2),
                    "length": len(page_content),
                    "tokens": self.estimate_tokens(page_content)
                }
                
                # Crear el chunk
                chunk = {
                    "content": page_content,
                    "chunk_id": f"xlsx_row_{sheet_name}_{index + 2}",
                    "metadata": chunk_metadata
                }
                
                chunks.append(chunk)
        
        logger.info(f"📊 Hoja {sheet_name}: {len(chunks)} documentos creados de {len(df)} filas")
        return chunks
    
    def _detect_headers(self, df: pd.DataFrame) -> bool:
        """
        Detecta si la primera fila contiene encabezados.
        
        Args:
            df: DataFrame a analizar
            
        Returns:
            bool: True si la primera fila parece contener encabezados
        """
        if df.empty or len(df) < 2:
            return False
        
        # Analizar la primera fila
        first_row = df.iloc[0].astype(str)
        
        # Criterios para detectar encabezados:
        # 1. Mayoría de valores no son números puros
        # 2. No hay valores vacíos o NaN excesivos
        # 3. Los valores parecen nombres de columnas
        
        non_numeric_count = 0
        valid_values = 0
        
        for val in first_row:
            if pd.notna(val) and str(val).strip():
                valid_values += 1
                # Verificar si NO es un número puro
                clean_val = str(val).strip().replace('.', '').replace('-', '').replace(',', '')
                if not clean_val.isdigit():
                    non_numeric_count += 1
        
        # Si más del 70% de valores válidos no son números, probablemente son encabezados
        if valid_values > 0:
            non_numeric_ratio = non_numeric_count / valid_values
            return non_numeric_ratio > 0.7
        
        return False
    
