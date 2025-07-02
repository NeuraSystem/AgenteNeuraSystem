"""
Asistente Proactivo para AgenteIng
Detecta automáticamente eventos importantes y ofrece recordatorios y ayuda proactiva.
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict

from utils.logger import get_logger
from .category_manager import CategoryManager
from .critical_thinking import CriticalThinking

logger = get_logger(__name__)

@dataclass
class ProactiveAlert:
    """Alerta proactiva del asistente"""
    id: str
    type: str  # 'reminder', 'suggestion', 'warning', 'opportunity'
    category: str
    priority: int  # 1=alta, 2=media, 3=baja
    title: str
    message: str
    context: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime] = None
    shown: bool = False
    dismissed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProactiveAlert':
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data['expires_at']:
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        return cls(**data)

class ProactiveAssistant:
    """
    Asistente Proactivo
    
    Analiza la información almacenada en las categorías para detectar:
    - Eventos importantes próximos (aniversarios, cumpleaños)
    - Patrones de comportamiento (rutinas, hábitos)
    - Oportunidades de ayuda contextual
    - Recordatorios inteligentes
    """
    
    def __init__(self, data_path: str = "data/proactive"):
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        self.category_manager = CategoryManager()
        self.critical_thinking = CriticalThinking()
        
        # Alertas activas
        self.active_alerts: List[ProactiveAlert] = []
        
        # Patrones de eventos importantes
        self.event_patterns = self._load_event_patterns()
        
        # Estado del usuario (cansancio, ocupado, etc.)
        self.user_state = self._load_user_state()
        
        # Cargar alertas existentes
        self._load_alerts()
        
        logger.info("Asistente Proactivo inicializado")

    def _load_event_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Carga patrones de eventos importantes"""
        return {
            'aniversarios': {
                'keywords': ['aniversario', 'nos casamos', 'boda', 'matrimonio'],
                'patterns': [
                    r'aniversario\s+(?:de\s+)?(?:bodas?\s+)?(?:el\s+)?(\d{1,2})\s+de\s+(\w+)',
                    r'nos\s+casamos\s+(?:el\s+)?(\d{1,2})\s+de\s+(\w+)',
                    r'(\d{1,2})/(\d{1,2})/(\d{4})\s+.*(?:boda|matrimonio|aniversario)'
                ],
                'advance_days': [30, 7, 1],  # Recordar con 30, 7 y 1 día de anticipación
                'category': 'familiar'
            },
            'cumpleanos': {
                'keywords': ['cumpleaños', 'nació', 'nacimiento', 'birthday'],
                'patterns': [
                    r'cumpleaños\s+(?:de\s+\w+\s+)?(?:el\s+)?(\d{1,2})\s+de\s+(\w+)',
                    r'nació\s+(?:el\s+)?(\d{1,2})\s+de\s+(\w+)',
                    r'(\d{1,2})/(\d{1,2})/(\d{4})\s+.*(?:cumpleaños|nacimiento)'
                ],
                'advance_days': [7, 1],
                'category': 'familiar'
            },
            'trabajo_importante': {
                'keywords': ['deadline', 'entrega', 'presentación importante', 'reunión crucial'],
                'patterns': [
                    r'(?:deadline|entrega)\s+(?:el\s+)?(\d{1,2})\s+de\s+(\w+)',
                    r'presentación\s+(?:importante\s+)?(?:el\s+)?(\d{1,2})\s+de\s+(\w+)',
                    r'reunión\s+(?:crucial\s+)?(?:el\s+)?(\d{1,2})\s+de\s+(\w+)'
                ],
                'advance_days': [3, 1],
                'category': 'laboral'
            },
            'examenes': {
                'keywords': ['examen', 'prueba', 'test', 'evaluación'],
                'patterns': [
                    r'examen\s+(?:de\s+\w+\s+)?(?:el\s+)?(\d{1,2})\s+de\s+(\w+)',
                    r'prueba\s+(?:de\s+\w+\s+)?(?:el\s+)?(\d{1,2})\s+de\s+(\w+)'
                ],
                'advance_days': [7, 3, 1],
                'category': 'escolar'
            },
            'citas_medicas': {
                'keywords': ['cita médica', 'doctor', 'consulta médica'],
                'patterns': [
                    r'cita\s+(?:médica\s+)?(?:con\s+)?(?:el\s+)?doctor\s+.*?(\d{1,2})\s+de\s+(\w+)',
                    r'consulta\s+(?:médica\s+)?(?:el\s+)?(\d{1,2})\s+de\s+(\w+)'
                ],
                'advance_days': [1],
                'category': 'personal'
            }
        }

    def _load_user_state(self) -> Dict[str, Any]:
        """Carga el estado actual del usuario"""
        try:
            state_file = self.data_path / "user_state.json"
            if state_file.exists():
                with open(state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando estado del usuario: {e}")
        
        return {
            'energy_level': 'normal',  # low, normal, high
            'mood': 'neutral',  # positive, neutral, negative
            'busy_level': 'normal',  # low, normal, high
            'last_exercise': None,
            'last_work_session': None,
            'context_hints': []
        }

    def _save_user_state(self) -> None:
        """Guarda el estado del usuario"""
        try:
            state_file = self.data_path / "user_state.json"
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando estado del usuario: {e}")

    def analyze_new_content(self, content: str, category: str, content_type: str) -> List[ProactiveAlert]:
        """
        Analiza contenido nuevo para detectar oportunidades proactivas
        
        Args:
            content: Contenido a analizar
            category: Categoría del contenido
            content_type: Tipo ('conversation', 'document')
            
        Returns:
            Lista de alertas generadas
        """
        new_alerts = []
        
        try:
            # Detectar eventos importantes
            event_alerts = self._detect_important_events(content, category)
            new_alerts.extend(event_alerts)
            
            # Detectar patrones de estado del usuario
            state_updates = self._detect_user_state_changes(content, category)
            if state_updates:
                self._update_user_state(state_updates)
            
            # Generar sugerencias contextuales
            contextual_alerts = self._generate_contextual_suggestions(content, category)
            new_alerts.extend(contextual_alerts)
            
            # Añadir alertas a la lista activa
            for alert in new_alerts:
                self.active_alerts.append(alert)
            
            # Guardar estado
            if new_alerts or state_updates:
                self._save_alerts()
                self._save_user_state()
            
            logger.info(f"Análisis proactivo generó {len(new_alerts)} alertas para contenido en categoría {category}")
            
        except Exception as e:
            logger.error(f"Error en análisis proactivo: {e}")
        
        return new_alerts

    def _detect_important_events(self, content: str, category: str) -> List[ProactiveAlert]:
        """Detecta eventos importantes en el contenido"""
        alerts = []
        content_lower = content.lower()
        
        for event_type, config in self.event_patterns.items():
            # Verificar si la categoría coincide
            if config['category'] != category:
                continue
            
            # Buscar palabras clave
            has_keywords = any(keyword in content_lower for keyword in config['keywords'])
            if not has_keywords:
                continue
            
            # Buscar patrones de fecha
            for pattern in config['patterns']:
                matches = re.finditer(pattern, content_lower)
                for match in matches:
                    try:
                        # Extraer fecha del patrón
                        event_date = self._parse_date_from_match(match)
                        if not event_date:
                            continue
                        
                        # Crear alertas para cada día de anticipación
                        for advance_days in config['advance_days']:
                            alert_date = event_date - timedelta(days=advance_days)
                            
                            # Solo crear alertas futuras
                            if alert_date > datetime.now():
                                alert = self._create_event_alert(
                                    event_type, event_date, advance_days, category, content
                                )
                                alerts.append(alert)
                        
                    except Exception as e:
                        logger.error(f"Error procesando evento {event_type}: {e}")
        
        return alerts

    def _parse_date_from_match(self, match) -> Optional[datetime]:
        """Parsea fecha desde una coincidencia regex"""
        try:
            groups = match.groups()
            
            if len(groups) >= 2:
                day = int(groups[0])
                month_str = groups[1].lower()
                
                # Mapeo de meses en español
                months = {
                    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                    'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
                    'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
                }
                
                month = months.get(month_str)
                if not month:
                    return None
                
                # Determinar año (usar año actual o siguiente)
                current_year = datetime.now().year
                event_date = datetime(current_year, month, day)
                
                # Si la fecha ya pasó este año, usar el siguiente
                if event_date < datetime.now():
                    event_date = datetime(current_year + 1, month, day)
                
                return event_date
            
            elif len(groups) >= 3:
                # Formato DD/MM/YYYY
                day = int(groups[0])
                month = int(groups[1])
                year = int(groups[2]) if len(groups) > 2 else datetime.now().year
                
                return datetime(year, month, day)
        
        except Exception as e:
            logger.error(f"Error parseando fecha: {e}")
        
        return None

    def _create_event_alert(self, event_type: str, event_date: datetime, 
                           advance_days: int, category: str, content: str) -> ProactiveAlert:
        """Crea una alerta para un evento importante"""
        
        # Determinar tipo de alerta y mensaje
        if advance_days == 1:
            title = f"¡Mañana es importante!"
            message_prefix = "Mañana"
            priority = 1
        elif advance_days <= 7:
            title = f"Evento próximo en {advance_days} días"
            message_prefix = f"En {advance_days} días"
            priority = 2
        else:
            title = f"Recordatorio: evento en {advance_days} días"
            message_prefix = f"En {advance_days} días"
            priority = 3
        
        # Mensajes específicos por tipo de evento
        event_messages = {
            'aniversarios': f"{message_prefix} es tu aniversario. ¿Has pensado en algo especial?",
            'cumpleanos': f"{message_prefix} es el cumpleaños de alguien importante. ¿Necesitas ayuda con ideas de regalo?",
            'trabajo_importante': f"{message_prefix} tienes una fecha límite importante. ¿Todo va según el plan?",
            'examenes': f"{message_prefix} tienes un examen. ¿Has repasado todo lo necesario?",
            'citas_medicas': f"{message_prefix} tienes una cita médica. Recuerda llevar toda la documentación."
        }
        
        message = event_messages.get(event_type, f"{message_prefix} tienes un evento importante.")
        
        return ProactiveAlert(
            id=f"{event_type}_{int(datetime.now().timestamp() * 1000)}",
            type='reminder',
            category=category,
            priority=priority,
            title=title,
            message=message,
            context={
                'event_type': event_type,
                'event_date': event_date.isoformat(),
                'advance_days': advance_days,
                'source_content': content[:200]  # Primeros 200 caracteres como contexto
            },
            created_at=datetime.now(),
            expires_at=event_date + timedelta(days=1)  # Expira un día después del evento
        )

    def _detect_user_state_changes(self, content: str, category: str) -> Dict[str, Any]:
        """Detecta cambios en el estado del usuario"""
        state_updates = {}
        content_lower = content.lower()
        
        # Detectar nivel de energía
        energy_indicators = {
            'low': ['cansado', 'agotado', 'sin energía', 'exhausto', 'fatigado'],
            'high': ['energético', 'motivado', 'activo', 'enérgico', 'vigoroso']
        }
        
        for level, indicators in energy_indicators.items():
            if any(indicator in content_lower for indicator in indicators):
                state_updates['energy_level'] = level
                break
        
        # Detectar actividad de ejercicio
        if category == 'deportiva' or any(word in content_lower for word in ['ejercicio', 'gym', 'entrenamiento']):
            state_updates['last_exercise'] = datetime.now().isoformat()
        
        # Detectar sesión de trabajo
        if category == 'laboral' or any(word in content_lower for word in ['trabajo', 'proyecto', 'reunión']):
            state_updates['last_work_session'] = datetime.now().isoformat()
        
        # Detectar nivel de ocupación
        busy_indicators = ['muy ocupado', 'sin tiempo', 'apurado', 'urgente', 'deadline']
        if any(indicator in content_lower for indicator in busy_indicators):
            state_updates['busy_level'] = 'high'
        
        return state_updates

    def _update_user_state(self, updates: Dict[str, Any]) -> None:
        """Actualiza el estado del usuario"""
        for key, value in updates.items():
            self.user_state[key] = value
        
        # Añadir marca de tiempo de actualización
        self.user_state['last_updated'] = datetime.now().isoformat()

    def _generate_contextual_suggestions(self, content: str, category: str) -> List[ProactiveAlert]:
        """Genera sugerencias contextuales basadas en el estado del usuario"""
        suggestions = []
        content_lower = content.lower()
        
        # Ejemplo 1: Usuario cansado + necesita trabajar
        if (self.user_state.get('energy_level') == 'low' and 
            (category == 'laboral' or any(word in content_lower for word in ['trabajo', 'email', 'jefe']))):
            
            suggestion = ProactiveAlert(
                id=f"contextual_{int(datetime.now().timestamp() * 1000)}",
                type='suggestion',
                category='personal',
                priority=2,
                title="💡 Sugerencia contextual",
                message="Noto que estás cansado pero necesitas trabajar. ¿Te ayudo a redactar algo más conciso y directo?",
                context={
                    'user_state': 'tired_but_working',
                    'energy_level': self.user_state.get('energy_level'),
                    'content_category': category
                },
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=2)
            )
            suggestions.append(suggestion)
        
        # Ejemplo 2: Detectar necesidad de información de otra categoría
        if self._needs_cross_category_help(content, category):
            suggestion = ProactiveAlert(
                id=f"cross_help_{int(datetime.now().timestamp() * 1000)}",
                type='opportunity',
                category=category,
                priority=2,
                title="🔗 Información relacionada disponible",
                message="Tengo información relacionada en otras categorías que podría ayudarte con esto.",
                context={
                    'type': 'cross_category_help',
                    'current_category': category,
                    'content_preview': content[:100]
                },
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=1)
            )
            suggestions.append(suggestion)
        
        return suggestions

    def _needs_cross_category_help(self, content: str, category: str) -> bool:
        """Determina si el usuario podría necesitar información de otras categorías"""
        content_lower = content.lower()
        
        # Palabras que sugieren necesidad de información cruzada
        cross_indicators = {
            'personal': ['familia', 'trabajo', 'horario'],
            'laboral': ['personal', 'familia', 'tiempo libre'],
            'familiar': ['trabajo', 'agenda', 'disponibilidad']
        }
        
        indicators = cross_indicators.get(category, [])
        return any(indicator in content_lower for indicator in indicators)

    def get_active_alerts(self, priority_filter: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Obtiene alertas activas
        
        Args:
            priority_filter: Filtrar por prioridad (1=alta, 2=media, 3=baja)
            
        Returns:
            Lista de alertas activas
        """
        now = datetime.now()
        active = []
        
        for alert in self.active_alerts:
            # Filtrar alertas expiradas
            if alert.expires_at and alert.expires_at < now:
                continue
            
            # Filtrar alertas descartadas
            if alert.dismissed:
                continue
            
            # Filtrar por prioridad si se especifica
            if priority_filter and alert.priority != priority_filter:
                continue
            
            active.append(alert.to_dict())
        
        # Ordenar por prioridad y fecha
        active.sort(key=lambda x: (x['priority'], x['created_at']))
        
        return active

    def mark_alert_shown(self, alert_id: str) -> bool:
        """Marca una alerta como mostrada"""
        for alert in self.active_alerts:
            if alert.id == alert_id:
                alert.shown = True
                self._save_alerts()
                return True
        return False

    def dismiss_alert(self, alert_id: str) -> bool:
        """Descarta una alerta"""
        for alert in self.active_alerts:
            if alert.id == alert_id:
                alert.dismissed = True
                self._save_alerts()
                return True
        return False

    def check_proactive_opportunities(self) -> List[ProactiveAlert]:
        """
        Verifica oportunidades proactivas basadas en el estado actual
        Debe llamarse periódicamente (ej: cada hora)
        """
        opportunities = []
        now = datetime.now()
        
        try:
            # Verificar aniversarios próximos en categoría familiar
            anniversary_alerts = self._check_upcoming_anniversaries()
            opportunities.extend(anniversary_alerts)
            
            # Verificar patrones de trabajo y descanso
            work_rest_alerts = self._check_work_rest_patterns()
            opportunities.extend(work_rest_alerts)
            
            # Verificar necesidades de seguimiento
            followup_alerts = self._check_followup_needs()
            opportunities.extend(followup_alerts)
            
            # Añadir nuevas oportunidades a alertas activas
            for opportunity in opportunities:
                self.active_alerts.append(opportunity)
            
            if opportunities:
                self._save_alerts()
            
            logger.info(f"Verificación proactiva encontró {len(opportunities)} oportunidades")
            
        except Exception as e:
            logger.error(f"Error en verificación proactiva: {e}")
        
        return opportunities

    def _check_upcoming_anniversaries(self) -> List[ProactiveAlert]:
        """Verifica aniversarios próximos en la categoría familiar"""
        alerts = []
        
        try:
            # Obtener contenido de categoría familiar
            familiar_items = self.category_manager.get_category_contents('familiar')
            
            for item in familiar_items:
                # Buscar fechas importantes en el contenido
                item_details = self.category_manager.get_item_details('familiar', item['id'])
                if item_details:
                    content = item_details.get('data', {}).get('content', '')
                    event_alerts = self._detect_important_events(content, 'familiar')
                    alerts.extend(event_alerts)
            
        except Exception as e:
            logger.error(f"Error verificando aniversarios: {e}")
        
        return alerts

    def _check_work_rest_patterns(self) -> List[ProactiveAlert]:
        """Verifica patrones de trabajo y descanso"""
        alerts = []
        
        try:
            last_exercise = self.user_state.get('last_exercise')
            if last_exercise:
                exercise_date = datetime.fromisoformat(last_exercise)
                days_since_exercise = (datetime.now() - exercise_date).days
                
                # Sugerir ejercicio si han pasado más de 3 días
                if days_since_exercise > 3:
                    alert = ProactiveAlert(
                        id=f"exercise_reminder_{int(datetime.now().timestamp())}",
                        type='suggestion',
                        category='deportiva',
                        priority=3,
                        title="🏃‍♂️ Recordatorio de ejercicio",
                        message=f"Han pasado {days_since_exercise} días desde tu último ejercicio. ¿Qué tal una sesión hoy?",
                        context={
                            'type': 'exercise_reminder',
                            'days_since': days_since_exercise
                        },
                        created_at=datetime.now(),
                        expires_at=datetime.now() + timedelta(days=1)
                    )
                    alerts.append(alert)
            
        except Exception as e:
            logger.error(f"Error verificando patrones trabajo-descanso: {e}")
        
        return alerts

    def _check_followup_needs(self) -> List[ProactiveAlert]:
        """Verifica si hay items que necesitan seguimiento"""
        alerts = []
        
        try:
            # Verificar items en pensamiento crítico que necesitan revisión manual
            pending_items = self.critical_thinking.get_pending_review_items()
            
            if len(pending_items) > 5:  # Si hay muchos items pendientes
                alert = ProactiveAlert(
                    id=f"review_needed_{int(datetime.now().timestamp())}",
                    type='warning',
                    category='personal',
                    priority=2,
                    title="⚠️ Revisión necesaria",
                    message=f"Tienes {len(pending_items)} items esperando revisión manual. ¿Los revisamos?",
                    context={
                        'type': 'pending_review',
                        'count': len(pending_items)
                    },
                    created_at=datetime.now(),
                    expires_at=datetime.now() + timedelta(days=7)
                )
                alerts.append(alert)
        
        except Exception as e:
            logger.error(f"Error verificando necesidades de seguimiento: {e}")
        
        return alerts

    def _load_alerts(self) -> None:
        """Carga alertas existentes desde disco"""
        try:
            alerts_file = self.data_path / "active_alerts.json"
            if alerts_file.exists():
                with open(alerts_file, 'r', encoding='utf-8') as f:
                    alerts_data = json.load(f)
                
                self.active_alerts = [
                    ProactiveAlert.from_dict(alert_data) 
                    for alert_data in alerts_data
                ]
                
                logger.info(f"Cargadas {len(self.active_alerts)} alertas activas")
        
        except Exception as e:
            logger.error(f"Error cargando alertas: {e}")
            self.active_alerts = []

    def _save_alerts(self) -> None:
        """Guarda alertas activas a disco"""
        try:
            alerts_file = self.data_path / "active_alerts.json"
            alerts_data = [alert.to_dict() for alert in self.active_alerts]
            
            with open(alerts_file, 'w', encoding='utf-8') as f:
                json.dump(alerts_data, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            logger.error(f"Error guardando alertas: {e}")

    def cleanup_expired_alerts(self) -> int:
        """Limpia alertas expiradas y retorna el número de alertas eliminadas"""
        now = datetime.now()
        original_count = len(self.active_alerts)
        
        self.active_alerts = [
            alert for alert in self.active_alerts
            if not alert.expires_at or alert.expires_at > now
        ]
        
        cleaned_count = original_count - len(self.active_alerts)
        
        if cleaned_count > 0:
            self._save_alerts()
            logger.info(f"Limpiadas {cleaned_count} alertas expiradas")
        
        return cleaned_count

    def get_user_context_summary(self) -> Dict[str, Any]:
        """Obtiene un resumen del contexto actual del usuario"""
        return {
            'state': self.user_state,
            'active_alerts_count': len([a for a in self.active_alerts if not a.dismissed and not a.expires_at or a.expires_at > datetime.now()]),
            'high_priority_alerts': len([a for a in self.active_alerts if a.priority == 1 and not a.dismissed]),
            'categories_with_recent_activity': self._get_recent_activity_categories(),
            'last_updated': self.user_state.get('last_updated', 'nunca')
        }

    def _get_recent_activity_categories(self) -> List[str]:
        """Obtiene categorías con actividad reciente"""
        recent_categories = []
        cutoff_time = datetime.now() - timedelta(days=1)
        
        for category_config in self.category_manager.get_active_categories():
            category_items = self.category_manager.get_category_contents(category_config.name)
            
            for item in category_items:
                item_time = datetime.fromisoformat(item['timestamp'])
                if item_time > cutoff_time:
                    if category_config.name not in recent_categories:
                        recent_categories.append(category_config.name)
                    break
        
        return recent_categories