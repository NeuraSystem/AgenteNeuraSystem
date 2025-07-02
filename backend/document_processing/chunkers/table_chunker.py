"""
Chunker especializado para contenido tabular (Excel, tablas de Word).
"""

import pandas as pd
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class TableChunker:
    """
    Chunker especializado para datos tabulares.
    Fragmenta tablas preservando estructura y relaciones.
    """
    
    def __init__(self, 
                 max_rows_per_chunk: int = 50,
                 include_headers: bool = True):
        """
        Inicializa el chunker de tablas.
        
        Args:
            max_rows_per_chunk: Máximo de filas por chunk
            include_headers: Si incluir headers en cada chunk
        """
        self.max_rows_per_chunk = max_rows_per_chunk
        self.include_headers = include_headers
    
    def chunk_table_data(self, 
                        table_data: List[List[str]], 
                        table_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Fragmenta datos tabulares en chunks manejables.
        
        Args:
            table_data: Datos de la tabla como lista de listas
            table_metadata: Metadata de la tabla original
            
        Returns:
            Lista de chunks con datos tabulares
        """
        if not table_data or len(table_data) == 0:
            return []
        
        # Detectar headers
        headers = table_data[0] if self.include_headers else None
        data_rows = table_data[1:] if headers else table_data
        
        if len(data_rows) <= self.max_rows_per_chunk:
            # Tabla pequeña: un solo chunk
            return self._create_single_table_chunk(table_data, table_metadata)
        else:
            # Tabla grande: fragmentar por filas
            return self._create_table_chunks(headers, data_rows, table_metadata)
    
    def chunk_dataframe(self, 
                       df: pd.DataFrame, 
                       source_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Fragmenta DataFrame en chunks.
        
        Args:
            df: DataFrame a fragmentar
            source_metadata: Metadata del documento origen
            
        Returns:
            Lista de chunks
        """
        if df.empty:
            return []
        
        chunks = []
        total_rows = len(df)
        
        # Información de columnas para contexto
        column_info = self._analyze_columns(df)
        
        # Fragmentar por filas
        for start_idx in range(0, total_rows, self.max_rows_per_chunk):
            end_idx = min(start_idx + self.max_rows_per_chunk, total_rows)
            chunk_df = df.iloc[start_idx:end_idx]
            
            # Incluir headers si es necesario
            if self.include_headers and start_idx > 0:
                # Para chunks que no son el primero, incluir header
                chunk_df = pd.concat([df.head(1), chunk_df])
            
            # Convertir a texto estructurado
            chunk_text = self._dataframe_to_text(chunk_df, column_info)
            
            chunk = {
                "content": chunk_text,
                "chunk_id": f"table_chunk_{start_idx // self.max_rows_per_chunk + 1}",
                "metadata": {
                    "type": "table_data",
                    "chunk_index": start_idx // self.max_rows_per_chunk,
                    "row_range": [start_idx, end_idx - 1],
                    "total_rows": total_rows,
                    "columns": list(df.columns),
                    "column_info": column_info,
                    "source": source_metadata or {}
                }
            }
            
            chunks.append(chunk)
        
        return chunks
    
    def _create_single_table_chunk(self, 
                                  table_data: List[List[str]], 
                                  table_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Crea un solo chunk para tabla pequeña.
        """
        text_content = self._table_data_to_text(table_data)
        
        return [{
            "content": text_content,
            "chunk_id": "table_chunk_1",
            "metadata": {
                "type": "complete_table",
                "chunk_index": 0,
                "chunk_count": 1,
                "row_count": len(table_data),
                "col_count": len(table_data[0]) if table_data else 0,
                "source": table_metadata or {}
            }
        }]
    
    def _create_table_chunks(self, 
                           headers: List[str], 
                           data_rows: List[List[str]], 
                           table_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Crea múltiples chunks para tabla grande.
        """
        chunks = []
        total_chunks = (len(data_rows) + self.max_rows_per_chunk - 1) // self.max_rows_per_chunk
        
        for chunk_idx in range(total_chunks):
            start_row = chunk_idx * self.max_rows_per_chunk
            end_row = min(start_row + self.max_rows_per_chunk, len(data_rows))
            
            # Datos del chunk
            chunk_rows = data_rows[start_row:end_row]
            
            # Incluir headers si es necesario
            if self.include_headers and headers:
                chunk_data = [headers] + chunk_rows
            else:
                chunk_data = chunk_rows
            
            text_content = self._table_data_to_text(chunk_data)
            
            chunk = {
                "content": text_content,
                "chunk_id": f"table_chunk_{chunk_idx + 1}",
                "metadata": {
                    "type": "table_chunk",
                    "chunk_index": chunk_idx,
                    "chunk_count": total_chunks,
                    "row_range": [start_row, end_row - 1],
                    "total_data_rows": len(data_rows),
                    "has_headers": self.include_headers and headers is not None,
                    "source": table_metadata or {}
                }
            }
            
            chunks.append(chunk)
        
        return chunks
    
    def _table_data_to_text(self, table_data: List[List[str]]) -> str:
        """
        Convierte datos tabulares a texto estructurado.
        """
        if not table_data:
            return ""
        
        text_lines = []
        
        for row_idx, row in enumerate(table_data):
            # Limpiar celdas
            clean_cells = [str(cell).strip() if cell is not None else "" for cell in row]
            
            # Formatear fila
            if row_idx == 0 and self.include_headers:
                # Header row
                text_lines.append("Columnas: " + " | ".join(clean_cells))
                text_lines.append("-" * 50)
            else:
                # Data row
                text_lines.append(" | ".join(clean_cells))
        
        return "\n".join(text_lines)
    
    def _dataframe_to_text(self, df: pd.DataFrame, column_info: Dict) -> str:
        """
        Convierte DataFrame a texto estructurado.
        """
        text_parts = []
        
        # Información de columnas
        text_parts.append(f"Tabla con {len(df)} filas y {len(df.columns)} columnas")
        
        # Descripción de columnas
        col_descriptions = []
        for col in df.columns:
            col_type = column_info.get(col, {}).get("type", "texto")
            col_descriptions.append(f"{col} ({col_type})")
        
        text_parts.append("Columnas: " + ", ".join(col_descriptions))
        text_parts.append("")
        
        # Datos
        for idx, row in df.iterrows():
            row_data = []
            for col in df.columns:
                value = row[col]
                if pd.isna(value):
                    row_data.append("[vacío]")
                else:
                    row_data.append(str(value).strip())
            
            text_parts.append(f"Fila {idx + 1}: " + " | ".join(row_data))
        
        return "\n".join(text_parts)
    
    def _analyze_columns(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """
        Analiza tipos y características de columnas.
        """
        column_info = {}
        
        for col in df.columns:
            col_data = df[col].dropna()
            
            if col_data.empty:
                col_type = "vacío"
            elif col_data.dtype in ['int64', 'float64']:
                col_type = "numérico"
            elif pd.api.types.is_datetime64_any_dtype(col_data):
                col_type = "fecha"
            else:
                col_type = "texto"
            
            column_info[col] = {
                "type": col_type,
                "non_null_count": len(col_data),
                "unique_count": len(col_data.unique()) if len(col_data) > 0 else 0
            }
        
        return column_info