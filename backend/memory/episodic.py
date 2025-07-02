"""
Módulo de memoria episódica para el chatbot.
- Implementa ConversationBufferWindowMemory de LangChain para mantener el contexto conversacional reciente.
- EXTENDIDO: Persistencia por fecha, gestión de archivos, y vectorización por lotes.
- Compatible con sistema de memoria avanzada.
- Optimizado para Windows 10/11 con encoding UTF-8
"""

import os
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import HumanMessage, AIMessage

# Configurar encoding UTF-8 para Windows
import sys
if sys.platform.startswith('win'):
    import codecs

# Importar storage managers
from storage.file_manager import FileManager
from storage.vector_manager import VectorManager

import logging
logger = logging.getLogger(__name__)

class EpisodicMemoryManager:
    """
    Gestor avanzado de memoria episódica que extiende funcionalidad básica.
    Mantiene compatibilidad con implementación actual.
    """
    
    def __init__(self, buffer_size: int = 10, enable_persistence: bool = True):
        # Memoria LangChain original (MANTENER compatibilidad)
        self.langchain_memory = ConversationBufferWindowMemory(
            k=buffer_size,
            return_messages=True
        )
        
        # Nuevas funcionalidades
        self.file_manager = FileManager() if enable_persistence else None
        self.vector_manager = VectorManager() if enable_persistence else None
        self.buffer_size = buffer_size
        self.message_count = 0
        self.batch_threshold = int(os.getenv("MEMORY_BATCH_SIZE", "10"))
        self.pending_messages = []  # Buffer para vectorización
        
    async def add_conversation_turn(self, user_message: str, ai_response: str) -> str:
        """
        Añade un turno completo de conversación (usuario + IA).
        
        Args:
            user_message: Mensaje del usuario
            ai_response: Respuesta de la IA
            
        Returns:
            str: ID del episodio guardado
        """
        timestamp = datetime.now()
        
        # 1. Agregar a memoria LangChain (funcionalidad original)
        self.langchain_memory.chat_memory.add_user_message(user_message)
        self.langchain_memory.chat_memory.add_ai_message(ai_response)
        
        # 2. Persistir en archivo si está habilitado
        episode_id = None
        if self.file_manager:
            try:
                # Guardar mensaje del usuario
                await self.file_manager.save_conversation_message(
                    user_message, "USER", timestamp
                )
                
                # Guardar respuesta de la IA
                episode_id = await self.file_manager.save_conversation_message(
                    ai_response, "BOT", timestamp
                )
                
            except Exception as e:
                # No fallar si hay error de persistencia
                logger.warning(f"Error saving to file: {e}")
        
        # 3. Agregar mensajes al buffer de vectorización
        if self.vector_manager:
            self.pending_messages.extend([
                {
                    'type': 'USER',
                    'content': user_message,
                    'timestamp': timestamp,
                    'date': timestamp.strftime("%Y-%m-%d")
                },
                {
                    'type': 'BOT', 
                    'content': ai_response,
                    'timestamp': timestamp,
                    'date': timestamp.strftime("%Y-%m-%d")
                }
            ])
        
        # 4. Incrementar contador para trigger de vectorización
        self.message_count += 2  # Usuario + IA = 2 mensajes
        
        # 5. Trigger de vectorización si alcanza umbral
        if self.message_count >= self.batch_threshold:
            await self._trigger_vectorization()
            self.message_count = 0
        
        return episode_id or f"episode_{timestamp.strftime('%Y%m%d_%H%M%S')}"
    
    async def _trigger_vectorization(self):
        """
        Vectoriza lote de mensajes y los guarda en ChromaDB.
        """
        if not self.vector_manager or not self.pending_messages:
            logger.warning("Trigger vectorización: No hay vector manager o mensajes pendientes")
            return
        
        try:
            logger.info(f"🧠 Vectorizando batch de {len(self.pending_messages)} mensajes...")
            
            # Vectorizar batch usando VectorManager
            batch_id = await self.vector_manager.vectorize_conversation_batch(
                self.pending_messages.copy()
            )
            
            if batch_id:
                logger.info(f"✅ Batch vectorizado exitosamente: {batch_id}")
                # Limpiar buffer después del éxito
                self.pending_messages.clear()
            else:
                logger.error("❌ Error vectorizando batch, mensajes preservados")
                
        except Exception as e:
            logger.error(f"❌ Error en trigger vectorización: {e}")
            # Mantener mensajes en buffer para reintento
    
    def get_conversation_context(self) -> List[Any]:
        """
        Obtiene contexto de conversación actual (compatibilidad).
        
        Returns:
            List: Mensajes de la memoria LangChain
        """
        return self.langchain_memory.chat_memory.messages
    
    async def get_recent_history(self, days: int = 7, limit: int = 50) -> List[Dict]:
        """
        Obtiene historial reciente de conversaciones.
        
        Args:
            days: Días hacia atrás
            limit: Límite de mensajes
            
        Returns:
            List[Dict]: Mensajes con metadata
        """
        if not self.file_manager:
            return []
        
        return await self.file_manager.get_recent_messages(days, limit)
    
    async def search_episodic_memory(self, query: str, days: int = 30) -> List[Dict]:
        """
        Búsqueda simple en memoria episódica (texto).
        
        Args:
            query: Término de búsqueda
            days: Días hacia atrás para buscar
            
        Returns:
            List[Dict]: Mensajes que contienen el término
        """
        if not self.file_manager:
            return []
        
        recent_messages = await self.file_manager.get_recent_messages(days, 1000)
        
        # Búsqueda simple por contenido
        results = []
        for msg in recent_messages:
            if query.lower() in msg['content'].lower():
                results.append(msg)
        
        return results
    
    async def search_semantic_memory(self, query: str, n_results: int = 3) -> List[Dict]:
        """
        Búsqueda semántica en vectores de conversaciones.
        
        Args:
            query: Consulta de búsqueda
            n_results: Número de resultados
            
        Returns:
            List[Dict]: Resultados semánticos relevantes
        """
        if not self.vector_manager:
            return []
        
        try:
            results = await self.vector_manager.search_semantic(query, n_results)
            
            # Formatear para uso en memoria
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'content': result['document'],
                    'similarity': result['similarity'],
                    'batch_id': result['id'],
                    'date': result['metadata'].get('date', 'unknown'),
                    'message_count': result['metadata'].get('message_count', 0)
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda semántica: {e}")
            return []

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de memoria.
        
        Returns:
            Dict: Estadísticas de uso de memoria
        """
        stats = {
            "langchain_buffer_size": len(self.langchain_memory.chat_memory.messages),
            "max_buffer_size": self.buffer_size,
            "message_count_current_batch": self.message_count,
            "batch_threshold": self.batch_threshold,
            "persistence_enabled": self.file_manager is not None,
            "vectorization_enabled": self.vector_manager is not None,
            "pending_messages": len(self.pending_messages)
        }
        
        # Agregar stats de ChromaDB si disponible
        if self.vector_manager:
            try:
                vector_stats = self.vector_manager.get_collection_stats()
                stats["vector_storage"] = vector_stats
            except Exception as e:
                stats["vector_storage"] = {"error": str(e)}
        
        return stats
    
    async def close_conversation(self):
        """
        Cierra la conversación actual y fuerza vectorización de mensajes pendientes.
        Útil para asegurar que todos los mensajes se vectoricen al finalizar una sesión.
        """
        if self.pending_messages:
            logger.info(f"🔄 Cerrando conversación: vectorizando {len(self.pending_messages)} mensajes pendientes")
            await self._trigger_vectorization()
        else:
            logger.info("🔄 Conversación cerrada: sin mensajes pendientes")
    
    async def force_vectorization(self):
        """
        Fuerza vectorización manual de todos los mensajes pendientes.
        Útil para debugging o para asegurar vectorización antes de operaciones críticas.
        """
        if self.pending_messages:
            logger.info(f"🔧 Vectorización forzada: procesando {len(self.pending_messages)} mensajes")
            await self._trigger_vectorization()
        else:
            logger.info("🔧 Vectorización forzada: sin mensajes pendientes")

# Función original (MANTENER compatibilidad)
def crear_memoria_episodica(buffer_size: int = 10, persist_path: Optional[str] = None) -> ConversationBufferWindowMemory:
    """
    Función original para compatibilidad con código existente.
    Parámetros:
        buffer_size (int): Número de mensajes a recordar (ventana de contexto).
        persist_path (str, opcional): Ruta para persistir la memoria (ahora implementado).
    Retorna:
        ConversationBufferWindowMemory: Objeto de memoria listo para usar.
    """
    return ConversationBufferWindowMemory(k=buffer_size) 