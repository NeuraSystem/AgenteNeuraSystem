"""
Gestor de Categorías Humanas para AgenteIng
Organiza la información como lo haría una persona real con categorías intuitivas.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Set, Any, Tuple
from pathlib import Path
from dataclasses import dataclass

from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class CategoryConfig:
    """Configuración de una categoría"""
    name: str
    display_name: str
    description: str
    enabled: bool = True
    subcategories: List[str] = None
    
    def __post_init__(self):
        if self.subcategories is None:
            self.subcategories = ['documentos', 'conversaciones']

class CategoryManager:
    """
    Gestor de Categorías Humanas
    
    Organiza la información en categorías que son naturales para las personas:
    - Categorías base: Personal, Familiar, Social (siempre activas)
    - Categorías opcionales: Laboral, Escolar, Deportiva, Religión (configurables)
    """
    
    def __init__(self, data_path: str = "data/categories"):
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # Definir categorías base (siempre activas)
        self.base_categories = {
            'personal': CategoryConfig(
                name='personal',
                display_name='Personal',
                description='Información personal, gustos, rutinas, hobbies',
                enabled=True
            ),
            'familiar': CategoryConfig(
                name='familiar',
                display_name='Familiar',
                description='Familia, eventos familiares, relaciones familiares',
                enabled=True
            ),
            'social': CategoryConfig(
                name='social',
                display_name='Social',
                description='Amigos, eventos sociales, relaciones sociales',
                enabled=True
            )
        }
        
        # Definir categorías opcionales (configurables por usuario)
        self.optional_categories = {
            'laboral': CategoryConfig(
                name='laboral',
                display_name='Laboral',
                description='Trabajo, proyectos, colegas, reuniones de trabajo',
                enabled=False
            ),
            'escolar': CategoryConfig(
                name='escolar',
                display_name='Escolar',
                description='Estudios, tareas, exámenes, universidad',
                enabled=False
            ),
            'deportiva': CategoryConfig(
                name='deportiva',
                display_name='Deportiva',
                description='Ejercicio, deportes, fitness, rutinas de entrenamiento',
                enabled=False
            ),
            'religion': CategoryConfig(
                name='religion',
                display_name='Religión',
                description='Creencias, prácticas espirituales, eventos religiosos',
                enabled=False
            )
        }
        
        # Cargar configuración personalizada
        self._load_user_configuration()
        
        # Crear estructura de directorios
        self._ensure_directory_structure()
        
        logger.info("Gestor de Categorías Humanas inicializado")

    def _load_user_configuration(self) -> None:
        """Carga la configuración personalizada del usuario"""
        try:
            config_file = self.data_path / "user_categories.json"
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                
                # Actualizar categorías opcionales según configuración del usuario
                for category_name, config in user_config.get('optional_categories', {}).items():
                    if category_name in self.optional_categories:
                        self.optional_categories[category_name].enabled = config.get('enabled', False)
                
                logger.info("Configuración de usuario cargada exitosamente")
            else:
                # Crear configuración por defecto
                self._save_user_configuration()
                
        except Exception as e:
            logger.error(f"Error cargando configuración de usuario: {e}")

    def _save_user_configuration(self) -> None:
        """Guarda la configuración personalizada del usuario"""
        try:
            config_file = self.data_path / "user_categories.json"
            
            config_data = {
                'base_categories': {
                    name: {
                        'display_name': cat.display_name,
                        'description': cat.description,
                        'enabled': cat.enabled
                    }
                    for name, cat in self.base_categories.items()
                },
                'optional_categories': {
                    name: {
                        'display_name': cat.display_name,
                        'description': cat.description,
                        'enabled': cat.enabled
                    }
                    for name, cat in self.optional_categories.items()
                }
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error guardando configuración de usuario: {e}")

    def _ensure_directory_structure(self) -> None:
        """Crea la estructura de directorios para todas las categorías activas"""
        for category in self.get_active_categories():
            category_path = self.data_path / category.name
            category_path.mkdir(exist_ok=True)
            
            # Crear subcarpetas automáticas
            for subcategory in category.subcategories:
                (category_path / subcategory).mkdir(exist_ok=True)
            
            # Crear archivo de índice si no existe
            index_file = category_path / "index.json"
            if not index_file.exists():
                with open(index_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'category': category.name,
                        'created': datetime.now().isoformat(),
                        'items': [],
                        'stats': {
                            'total_items': 0,
                            'documentos': 0,
                            'conversaciones': 0
                        }
                    }, f, indent=2, ensure_ascii=False)

    def get_active_categories(self) -> List[CategoryConfig]:
        """Obtiene todas las categorías activas (base + opcionales habilitadas)"""
        active = list(self.base_categories.values())
        active.extend([cat for cat in self.optional_categories.values() if cat.enabled])
        return active

    def get_all_categories(self) -> Dict[str, CategoryConfig]:
        """Obtiene todas las categorías (activas e inactivas)"""
        all_categories = self.base_categories.copy()
        all_categories.update(self.optional_categories)
        return all_categories

    def enable_optional_category(self, category_name: str) -> bool:
        """Habilita una categoría opcional"""
        if category_name in self.optional_categories:
            self.optional_categories[category_name].enabled = True
            self._ensure_directory_structure()
            self._save_user_configuration()
            logger.info(f"Categoría '{category_name}' habilitada")
            return True
        
        logger.warning(f"Categoría '{category_name}' no encontrada en categorías opcionales")
        return False

    def disable_optional_category(self, category_name: str) -> bool:
        """Deshabilita una categoría opcional (no elimina datos)"""
        if category_name in self.optional_categories and category_name not in self.base_categories:
            self.optional_categories[category_name].enabled = False
            self._save_user_configuration()
            logger.info(f"Categoría '{category_name}' deshabilitada")
            return True
        
        logger.warning(f"No se puede deshabilitar la categoría '{category_name}'")
        return False

    def add_to_category(self, category: str, content_type: str, data: Dict[str, Any]) -> bool:
        """
        Añade contenido a una categoría específica
        
        Args:
            category: Nombre de la categoría
            content_type: Tipo de contenido ('documentos' o 'conversaciones')
            data: Datos del contenido
            
        Returns:
            True si se añadió exitosamente
        """
        try:
            # Verificar que la categoría existe y está activa
            active_categories = {cat.name: cat for cat in self.get_active_categories()}
            if category not in active_categories:
                logger.warning(f"Categoría '{category}' no está activa")
                return False
            
            # Verificar tipo de contenido válido
            if content_type not in ['documentos', 'conversaciones']:
                logger.warning(f"Tipo de contenido '{content_type}' no válido")
                return False
            
            # Preparar datos del item
            item_data = {
                'id': data.get('id', f"{category}_{content_type}_{int(datetime.now().timestamp() * 1000)}"),
                'timestamp': datetime.now().isoformat(),
                'content_type': content_type,
                'data': data
            }
            
            # Añadir al índice de la categoría
            self._add_to_category_index(category, item_data)
            
            # Guardar archivo específico del item
            self._save_item_file(category, content_type, item_data)
            
            logger.info(f"Contenido añadido a categoría '{category}' tipo '{content_type}'")
            return True
            
        except Exception as e:
            logger.error(f"Error añadiendo contenido a categoría: {e}")
            return False

    def _add_to_category_index(self, category: str, item_data: Dict[str, Any]) -> None:
        """Añade un item al índice de la categoría"""
        index_file = self.data_path / category / "index.json"
        
        try:
            # Cargar índice existente
            with open(index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
            
            # Añadir nuevo item
            index['items'].append({
                'id': item_data['id'],
                'timestamp': item_data['timestamp'],
                'content_type': item_data['content_type'],
                'preview': self._generate_preview(item_data['data'])
            })
            
            # Actualizar estadísticas
            index['stats']['total_items'] += 1
            index['stats'][item_data['content_type']] += 1
            
            # Guardar índice actualizado
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error actualizando índice de categoría {category}: {e}")

    def _save_item_file(self, category: str, content_type: str, item_data: Dict[str, Any]) -> None:
        """Guarda el archivo específico del item"""
        content_dir = self.data_path / category / content_type
        item_file = content_dir / f"{item_data['id']}.json"
        
        try:
            with open(item_file, 'w', encoding='utf-8') as f:
                json.dump(item_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error guardando archivo de item: {e}")

    def _generate_preview(self, data: Dict[str, Any]) -> str:
        """Genera un preview del contenido para el índice"""
        content = data.get('content', '')
        if isinstance(content, str):
            # Limitar a primeras 100 caracteres
            preview = content.strip()[:100]
            if len(content) > 100:
                preview += "..."
            return preview
        
        # Para otros tipos de contenido
        return f"Contenido de tipo {data.get('type', 'desconocido')}"

    def get_category_contents(self, category: str, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene el contenido de una categoría
        
        Args:
            category: Nombre de la categoría
            content_type: Tipo específico ('documentos' o 'conversaciones') o None para todos
            
        Returns:
            Lista de items de la categoría
        """
        try:
            index_file = self.data_path / category / "index.json"
            if not index_file.exists():
                return []
            
            with open(index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
            
            items = index.get('items', [])
            
            # Filtrar por tipo si se especifica
            if content_type:
                items = [item for item in items if item.get('content_type') == content_type]
            
            return items
            
        except Exception as e:
            logger.error(f"Error obteniendo contenido de categoría {category}: {e}")
            return []

    def get_item_details(self, category: str, item_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene los detalles completos de un item específico"""
        try:
            # Buscar en ambos tipos de contenido
            for content_type in ['documentos', 'conversaciones']:
                item_file = self.data_path / category / content_type / f"{item_id}.json"
                if item_file.exists():
                    with open(item_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo detalles del item {item_id}: {e}")
            return None

    def search_across_categories(self, query: str, categories: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Busca contenido a través de múltiples categorías
        
        Args:
            query: Término de búsqueda
            categories: Categorías específicas a buscar (None para todas)
            
        Returns:
            Lista de resultados encontrados
        """
        results = []
        search_categories = categories or [cat.name for cat in self.get_active_categories()]
        
        try:
            query_lower = query.lower()
            
            for category in search_categories:
                items = self.get_category_contents(category)
                for item in items:
                    # Buscar en preview
                    if query_lower in item.get('preview', '').lower():
                        # Obtener detalles completos
                        details = self.get_item_details(category, item['id'])
                        if details:
                            results.append({
                                'category': category,
                                'item': details,
                                'match_type': 'preview'
                            })
            
            logger.info(f"Búsqueda '{query}' encontró {len(results)} resultados")
            return results
            
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            return []

    def get_category_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas de todas las categorías activas"""
        stats = {}
        
        for category in self.get_active_categories():
            try:
                index_file = self.data_path / category.name / "index.json"
                if index_file.exists():
                    with open(index_file, 'r', encoding='utf-8') as f:
                        index = json.load(f)
                    stats[category.name] = index.get('stats', {})
                else:
                    stats[category.name] = {
                        'total_items': 0,
                        'documentos': 0,
                        'conversaciones': 0
                    }
            except Exception as e:
                logger.error(f"Error obteniendo estadísticas de {category.name}: {e}")
                stats[category.name] = {'error': str(e)}
        
        return stats

    def suggest_category_for_content(self, content: str) -> Tuple[str, float]:
        """
        Sugiere una categoría para contenido dado
        
        Returns:
            Tuple de (categoría_sugerida, confianza)
        """
        # Este método será mejorado por el analizador de contenido
        # Por ahora, lógica básica de palabras clave
        
        content_lower = content.lower()
        category_scores = {}
        
        # Palabras clave por categoría
        keywords = {
            'personal': ['yo', 'mi', 'me gusta', 'rutina', 'hobby', 'personal', 'prefiero'],
            'familiar': ['familia', 'esposa', 'esposo', 'hijo', 'hija', 'madre', 'padre', 'hermano', 'aniversario'],
            'social': ['amigo', 'amiga', 'fiesta', 'reunión', 'evento', 'conocido', 'social'],
            'laboral': ['trabajo', 'oficina', 'jefe', 'empresa', 'proyecto', 'reunión laboral', 'colega'],
            'escolar': ['clase', 'universidad', 'estudio', 'examen', 'tarea', 'profesor', 'estudiante'],
            'deportiva': ['ejercicio', 'gym', 'deporte', 'entrenar', 'fitness', 'correr'],
            'religion': ['iglesia', 'oración', 'fe', 'religión', 'espiritual', 'dios']
        }
        
        # Calcular puntuaciones
        for category, words in keywords.items():
            score = sum(1 for word in words if word in content_lower)
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            max_score = category_scores[best_category]
            confidence = min(0.8, max_score * 0.15)  # Normalizar confianza
            return best_category, confidence
        
        # Default
        return 'personal', 0.1

    def remove_item(self, category: str, item_id: str) -> bool:
        """Elimina un item de una categoría"""
        try:
            # Buscar y eliminar archivo del item
            for content_type in ['documentos', 'conversaciones']:
                item_file = self.data_path / category / content_type / f"{item_id}.json"
                if item_file.exists():
                    item_file.unlink()
                    
                    # Actualizar índice
                    self._remove_from_category_index(category, item_id)
                    
                    logger.info(f"Item {item_id} eliminado de categoría {category}")
                    return True
            
            logger.warning(f"Item {item_id} no encontrado en categoría {category}")
            return False
            
        except Exception as e:
            logger.error(f"Error eliminando item {item_id}: {e}")
            return False

    def _remove_from_category_index(self, category: str, item_id: str) -> None:
        """Elimina un item del índice de la categoría"""
        try:
            index_file = self.data_path / category / "index.json"
            
            with open(index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
            
            # Encontrar y eliminar item
            original_items = index['items']
            index['items'] = [item for item in original_items if item['id'] != item_id]
            
            # Actualizar estadísticas si se eliminó algo
            if len(index['items']) < len(original_items):
                index['stats']['total_items'] -= 1
                # Buscar el tipo de contenido eliminado para actualizar stats específicas
                # (simplificado por ahora)
            
            # Guardar índice actualizado
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error actualizando índice tras eliminación: {e}")