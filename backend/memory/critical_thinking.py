"""
Sistema de Pensamiento Crítico Persistente para AgenteIng
Funciona como un buffer temporal que analiza conversaciones y documentos
antes de decidir dónde almacenarlos permanentemente.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from utils.logger import get_logger
from .category_manager import CategoryManager
from .episodic import EpisodicMemoryManager

logger = get_logger(__name__)

@dataclass
class MemoryItem:
    """Elemento de memoria temporal para análisis"""
    id: str
    content: str
    type: str  # 'conversation', 'document', 'user_info'
    timestamp: datetime
    confidence: float = 0.0
    suggested_category: Optional[str] = None
    metadata: Dict[str, Any] = None
    processed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItem':
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if data['metadata'] is None:
            data['metadata'] = {}
        return cls(**data)

class CriticalThinking:
    """
    Sistema de Pensamiento Crítico Persistente
    
    Mantiene un buffer temporal de información que requiere análisis
    antes de ser almacenada permanentemente en el sistema de memoria.
    """
    
    def __init__(self, data_path: str = "data/critical_thinking"):
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # Buffer temporal de elementos pendientes de análisis
        self.temporal_buffer: List[MemoryItem] = []
        
        # Umbrales de confianza
        self.DOCUMENT_CONFIDENCE_THRESHOLD = 0.85  # Muy cuidadoso con documentos
        self.CONVERSATION_CONFIDENCE_THRESHOLD = 0.15  # Relajado con conversaciones
        
        # Límites del buffer
        self.MAX_BUFFER_SIZE = 50
        self.MAX_BUFFER_TIME = timedelta(hours=2)  # Procesar después de 2 horas
        
        self.category_manager = CategoryManager()
        self.episodic_memory = EpisodicMemoryManager()
        
        # Cargar buffer existente
        self._load_buffer()
        
        logger.info("Sistema de Pensamiento Crítico Persistente inicializado")

    def add_to_analysis(self, content: str, content_type: str, metadata: Dict[str, Any] = None) -> str:
        """
        Añade contenido al buffer temporal para análisis
        
        Args:
            content: Contenido a analizar
            content_type: Tipo ('conversation', 'document', 'user_info')
            metadata: Metadatos adicionales
            
        Returns:
            ID del elemento añadido
        """
        if metadata is None:
            metadata = {}
            
        item = MemoryItem(
            id=f"{content_type}_{int(time.time() * 1000)}",
            content=content,
            type=content_type,
            timestamp=datetime.now(),
            metadata=metadata
        )
        
        # Análisis inicial rápido
        self._quick_analysis(item)
        
        self.temporal_buffer.append(item)
        logger.info(f"Añadido al buffer de análisis: {item.id} (tipo: {content_type})")
        
        # Verificar si necesitamos procesar el buffer
        self._check_buffer_limits()
        
        # Guardar estado
        self._save_buffer()
        
        return item.id

    def _quick_analysis(self, item: MemoryItem) -> None:
        """
        Análisis rápido inicial del contenido
        Determina categoría sugerida y confianza básica
        """
        try:
            # Análisis básico de palabras clave para categorización
            content_lower = item.content.lower()
            
            # Detectar categorías por palabras clave
            category_keywords = {
                'personal': ['yo', 'mi', 'me gusta', 'rutina', 'hobby', 'personal', 'prefiero'],
                'familiar': ['familia', 'esposa', 'esposo', 'hijo', 'hija', 'madre', 'padre', 'hermano', 'aniversario'],
                'social': ['amigo', 'amiga', 'fiesta', 'reunión', 'evento', 'conocido', 'social'],
                'laboral': ['trabajo', 'oficina', 'jefe', 'empresa', 'proyecto', 'reunión laboral', 'colega'],
                'escolar': ['clase', 'universidad', 'estudio', 'examen', 'tarea', 'profesor', 'estudiante'],
                'deportiva': ['ejercicio', 'gym', 'deporte', 'entrenar', 'fitness', 'correr'],
                'religion': ['iglesia', 'oración', 'fe', 'religión', 'espiritual', 'dios']
            }
            
            best_category = None
            best_score = 0
            
            for category, keywords in category_keywords.items():
                score = sum(1 for keyword in keywords if keyword in content_lower)
                if score > best_score:
                    best_score = score
                    best_category = category
            
            # Calcular confianza basada en la presencia de palabras clave
            if best_category and best_score > 0:
                item.suggested_category = best_category
                # Confianza básica: más palabras clave = mayor confianza
                base_confidence = min(0.8, best_score * 0.2)
                
                # Ajustar según tipo de contenido
                if item.type == 'document':
                    # Documentos requieren mayor análisis
                    item.confidence = base_confidence * 0.7
                elif item.type == 'conversation':
                    # Conversaciones son más flexibles
                    item.confidence = min(0.9, base_confidence * 1.3)
                else:
                    item.confidence = base_confidence
            else:
                item.suggested_category = 'personal'  # Default
                item.confidence = 0.1  # Baja confianza sin palabras clave
                
            logger.debug(f"Análisis rápido para {item.id}: categoría={item.suggested_category}, confianza={item.confidence:.2f}")
            
        except Exception as e:
            logger.error(f"Error en análisis rápido: {e}")
            item.suggested_category = 'personal'
            item.confidence = 0.1

    def _check_buffer_limits(self) -> None:
        """Verifica límites del buffer y procesa si es necesario"""
        now = datetime.now()
        
        # Verificar límite de tamaño
        if len(self.temporal_buffer) >= self.MAX_BUFFER_SIZE:
            logger.info(f"Buffer alcanzó tamaño máximo ({self.MAX_BUFFER_SIZE}), procesando...")
            self._process_buffer()
            return
            
        # Verificar límite de tiempo
        old_items = [
            item for item in self.temporal_buffer 
            if now - item.timestamp > self.MAX_BUFFER_TIME and not item.processed
        ]
        
        if old_items:
            logger.info(f"Encontrados {len(old_items)} elementos antiguos, procesando...")
            self._process_specific_items(old_items)

    def _process_buffer(self) -> None:
        """Procesa todos los elementos pendientes en el buffer"""
        unprocessed = [item for item in self.temporal_buffer if not item.processed]
        self._process_specific_items(unprocessed)

    def _process_specific_items(self, items: List[MemoryItem]) -> None:
        """Procesa elementos específicos del buffer"""
        for item in items:
            try:
                self._process_item(item)
                item.processed = True
            except Exception as e:
                logger.error(f"Error procesando {item.id}: {e}")
        
        # Limpiar elementos procesados antiguos
        self._cleanup_processed_items()
        self._save_buffer()

    def _process_item(self, item: MemoryItem) -> None:
        """
        Procesa un elemento individual según sus umbrales de confianza
        """
        threshold = (
            self.DOCUMENT_CONFIDENCE_THRESHOLD 
            if item.type == 'document' 
            else self.CONVERSATION_CONFIDENCE_THRESHOLD
        )
        
        if item.confidence >= threshold:
            # Confianza suficiente, almacenar automáticamente
            self._store_in_permanent_memory(item)
            logger.info(f"Elemento {item.id} almacenado automáticamente (confianza: {item.confidence:.2f})")
        else:
            # Confianza insuficiente, marcar para revisión manual
            self._mark_for_manual_review(item)
            logger.info(f"Elemento {item.id} marcado para revisión manual (confianza: {item.confidence:.2f})")

    def _store_in_permanent_memory(self, item: MemoryItem) -> None:
        """Almacena el elemento en memoria permanente"""
        try:
            # Determinar la categoría final
            category = item.suggested_category or 'personal'
            
            # Crear entrada para memoria episódica
            memory_data = {
                'content': item.content,
                'category': category,
                'type': item.type,
                'timestamp': item.timestamp.isoformat(),
                'confidence': item.confidence,
                'metadata': item.metadata or {}
            }
            
            # Almacenar en memoria episódica
            self.episodic_memory.store_memory(
                content=item.content,
                metadata=memory_data
            )
            
            # Registrar en gestor de categorías
            self.category_manager.add_to_category(
                category=category,
                content_type=item.type,
                data=memory_data
            )
            
            logger.info(f"Elemento {item.id} almacenado en categoría '{category}'")
            
        except Exception as e:
            logger.error(f"Error almacenando elemento {item.id}: {e}")

    def _mark_for_manual_review(self, item: MemoryItem) -> None:
        """Marca elemento para revisión manual"""
        try:
            review_file = self.data_path / "pending_review.json"
            
            # Cargar elementos pendientes existentes
            pending_items = []
            if review_file.exists():
                with open(review_file, 'r', encoding='utf-8') as f:
                    pending_items = json.load(f)
            
            # Añadir nuevo elemento
            pending_items.append(item.to_dict())
            
            # Guardar
            with open(review_file, 'w', encoding='utf-8') as f:
                json.dump(pending_items, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Elemento {item.id} marcado para revisión manual")
            
        except Exception as e:
            logger.error(f"Error marcando elemento para revisión: {e}")

    def get_pending_review_items(self) -> List[Dict[str, Any]]:
        """Obtiene elementos pendientes de revisión manual"""
        try:
            review_file = self.data_path / "pending_review.json"
            if review_file.exists():
                with open(review_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error obteniendo elementos pendientes: {e}")
            return []

    def approve_pending_item(self, item_id: str, category: str) -> bool:
        """Aprueba un elemento pendiente y lo almacena en la categoría especificada"""
        try:
            pending_items = self.get_pending_review_items()
            
            # Encontrar el elemento
            item_data = None
            remaining_items = []
            
            for item in pending_items:
                if item['id'] == item_id:
                    item_data = item
                else:
                    remaining_items.append(item)
            
            if not item_data:
                logger.warning(f"Elemento pendiente {item_id} no encontrado")
                return False
            
            # Recrear el elemento con la categoría aprobada
            memory_item = MemoryItem.from_dict(item_data)
            memory_item.suggested_category = category
            memory_item.confidence = 1.0  # Aprobación manual = máxima confianza
            
            # Almacenar en memoria permanente
            self._store_in_permanent_memory(memory_item)
            
            # Actualizar lista de pendientes
            review_file = self.data_path / "pending_review.json"
            with open(review_file, 'w', encoding='utf-8') as f:
                json.dump(remaining_items, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Elemento {item_id} aprobado y almacenado en categoría '{category}'")
            return True
            
        except Exception as e:
            logger.error(f"Error aprobando elemento {item_id}: {e}")
            return False

    def _cleanup_processed_items(self) -> None:
        """Limpia elementos procesados antiguos del buffer"""
        cutoff_time = datetime.now() - timedelta(days=1)
        
        original_size = len(self.temporal_buffer)
        self.temporal_buffer = [
            item for item in self.temporal_buffer
            if not item.processed or item.timestamp > cutoff_time
        ]
        
        cleaned = original_size - len(self.temporal_buffer)
        if cleaned > 0:
            logger.info(f"Limpiados {cleaned} elementos procesados antiguos del buffer")

    def _save_buffer(self) -> None:
        """Guarda el estado actual del buffer"""
        try:
            buffer_file = self.data_path / "temporal_buffer.json"
            buffer_data = [item.to_dict() for item in self.temporal_buffer]
            
            with open(buffer_file, 'w', encoding='utf-8') as f:
                json.dump(buffer_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error guardando buffer: {e}")

    def _load_buffer(self) -> None:
        """Carga el estado del buffer desde disco"""
        try:
            buffer_file = self.data_path / "temporal_buffer.json"
            if buffer_file.exists():
                with open(buffer_file, 'r', encoding='utf-8') as f:
                    buffer_data = json.load(f)
                
                self.temporal_buffer = [
                    MemoryItem.from_dict(item_data) 
                    for item_data in buffer_data
                ]
                
                logger.info(f"Buffer cargado con {len(self.temporal_buffer)} elementos")
            
        except Exception as e:
            logger.error(f"Error cargando buffer: {e}")
            self.temporal_buffer = []

    def get_buffer_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del buffer"""
        unprocessed = [item for item in self.temporal_buffer if not item.processed]
        pending_review = len(self.get_pending_review_items())
        
        return {
            'total_items': len(self.temporal_buffer),
            'unprocessed_items': len(unprocessed),
            'pending_review_items': pending_review,
            'buffer_age_hours': (
                (datetime.now() - min(item.timestamp for item in self.temporal_buffer)).total_seconds() / 3600
                if self.temporal_buffer else 0
            )
        }

    def force_process_all(self) -> None:
        """Fuerza el procesamiento de todos los elementos pendientes"""
        logger.info("Forzando procesamiento de todos los elementos pendientes...")
        self._process_buffer()