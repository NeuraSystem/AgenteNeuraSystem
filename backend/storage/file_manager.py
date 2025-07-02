"""
Gestión de archivos para memoria episódica.
- Organización por fecha optimizada para Windows
- Escritura asíncrona con encoding UTF-8
- Rotación automática
- Backup y compresión
- Soporte completo Windows 10/11
"""

import os
import aiofiles
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
import logging

# Configurar encoding UTF-8 para Windows
import sys
if sys.platform.startswith('win'):
    import codecs

logger = logging.getLogger(__name__)

class FileManager:
    """
    Gestor de archivos para conversaciones organizadas por fecha.
    Basado en mejores prácticas de gestión de logs y persistencia.
    """
    
    def __init__(self, base_path: str = r".\data"):
        # Usar Path para compatibilidad Windows
        self.base_path = Path(base_path).resolve()
        self.conversations_path = self.base_path / "episodic_memory" / "conversations"
        self.metadata_path = self.base_path / "episodic_memory" / "metadata"
        self.max_file_size = 10 * 1024 * 1024  # 10MB por archivo
        
        # Crear directorios si no existen
        self._ensure_directories()
        logger.info(f"FileManager inicializado en: {self.base_path}")
    
    def _ensure_directories(self):
        """Crea estructura de directorios necesaria."""
        directories = [
            self.conversations_path,
            self.metadata_path,
            self.base_path / "episodic_memory" / "embeddings",
            self.base_path / "semantic_memory" / "concepts",
            self.base_path / "semantic_memory" / "concept_embeddings",
            self.base_path / "semantic_memory" / "extraction_history",
            self.base_path / "relational_maps",
            self.base_path / "external_knowledge" / "uploaded_docs",
            self.base_path / "external_knowledge" / "doc_embeddings",
            self.base_path / "external_knowledge" / "doc_concepts"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directory ensured: {directory}")
        
        logger.info(f"✅ Estructura de directorios Windows creada exitosamente")
    
    async def save_conversation_message(
        self, 
        message: str, 
        message_type: str, 
        timestamp: Optional[datetime] = None
    ) -> str:
        """
        Guarda un mensaje de conversación en el archivo correspondiente por fecha.
        
        Args:
            message: Contenido del mensaje
            message_type: 'USER' o 'BOT'
            timestamp: Momento del mensaje (default: ahora)
            
        Returns:
            str: ID del mensaje guardado
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Archivo por fecha
        date_str = timestamp.strftime("%Y-%m-%d")
        file_path = self.conversations_path / f"{date_str}.txt"
        
        # Formato del mensaje
        time_str = timestamp.strftime("%H:%M:%S")
        message_line = f"[{time_str}] {message_type}: {message}\n"
        
        # ID único del mensaje
        message_id = f"{date_str}_{time_str}_{message_type}"
        
        try:
            # Verificar rotación si el archivo es muy grande
            if file_path.exists() and file_path.stat().st_size > self.max_file_size:
                await self._rotate_file(file_path)
            
            # Escribir mensaje de forma asíncrona
            async with aiofiles.open(file_path, "a", encoding="utf-8") as f:
                await f.write(message_line)
            
            logger.info(f"Message saved: {message_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            raise e
    
    async def _rotate_file(self, file_path: Path):
        """Rota archivo cuando excede el tamaño máximo."""
        timestamp = datetime.now().strftime("%H%M%S")
        new_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        new_path = file_path.parent / new_name
        
        # Mover archivo actual
        file_path.rename(new_path)
        logger.info(f"File rotated: {file_path} -> {new_path}")
    
    async def read_conversation_day(self, date: datetime) -> List[str]:
        """
        Lee todas las conversaciones de un día específico.
        
        Args:
            date: Fecha de las conversaciones a leer
            
        Returns:
            List[str]: Lista de líneas de conversación
        """
        date_str = date.strftime("%Y-%m-%d")
        file_path = self.conversations_path / f"{date_str}.txt"
        
        if not file_path.exists():
            return []
        
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()
                return content.strip().split('\n') if content.strip() else []
        except Exception as e:
            logger.error(f"Error reading conversation day {date_str}: {e}")
            return []
    
    async def get_recent_messages(self, days: int = 7, limit: int = 100) -> List[dict]:
        """
        Obtiene mensajes recientes de los últimos N días.
        
        Args:
            days: Número de días hacia atrás
            limit: Límite máximo de mensajes
            
        Returns:
            List[dict]: Lista de mensajes con metadata
        """
        messages = []
        current_date = datetime.now()
        
        for i in range(days):
            date = current_date - timedelta(days=i)
            day_messages = await self.read_conversation_day(date)
            
            for line in day_messages:
                if len(messages) >= limit:
                    return messages
                
                # Parsear línea: [HH:MM:SS] TYPE: mensaje
                if line.strip() and line.startswith('['):
                    try:
                        time_end = line.find(']')
                        time_str = line[1:time_end]
                        
                        type_start = time_end + 2
                        type_end = line.find(':', type_start)
                        message_type = line[type_start:type_end]
                        
                        content = line[type_end + 2:]
                        
                        # Crear timestamp completo
                        message_datetime = datetime.combine(
                            date.date(),
                            datetime.strptime(time_str, "%H:%M:%S").time()
                        )
                        
                        messages.append({
                            'timestamp': message_datetime,
                            'type': message_type,
                            'content': content,
                            'date': date.strftime("%Y-%m-%d")
                        })
                    except Exception as e:
                        logger.warning(f"Error parsing line: {line} - {e}")
                        continue
        
        # Ordenar por timestamp (más reciente primero)
        messages.sort(key=lambda x: x['timestamp'], reverse=True)
        return messages
    
    async def count_messages_today(self) -> int:
        """Cuenta mensajes del día actual."""
        today_messages = await self.read_conversation_day(datetime.now())
        return len([msg for msg in today_messages if msg.strip()])
    
    async def cleanup_old_files(self, days_to_keep: int = 365):
        """
        Limpia archivos antiguos según política de retención.
        
        Args:
            days_to_keep: Días de archivos a mantener
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for file_path in self.conversations_path.glob("*.txt"):
            try:
                # Extraer fecha del nombre del archivo
                date_str = file_path.stem.split('_')[0]  # En caso de archivos rotados
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                if file_date < cutoff_date:
                    file_path.unlink()
                    logger.info(f"Cleaned up old file: {file_path}")
            except Exception as e:
                logger.warning(f"Error processing file {file_path}: {e}")