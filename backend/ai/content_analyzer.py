"""
Analizador de Contenido Inteligente para AgenteIng
Analiza documentos y conversaciones para sugerir categorización automática.
"""

import re
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

from utils.logger import get_logger
from document_processing.extractors.pdf_extractor import PDFExtractor
from document_processing.extractors.docx_extractor import DOCXExtractor
from document_processing.extractors.xlsx_extractor import XLSXExtractor
from document_processing.extractors.txt_extractor import TXTExtractor

logger = get_logger(__name__)

class ContentAnalyzer:
    """
    Analizador de Contenido Inteligente
    
    Analiza documentos y conversaciones para sugerir categorías apropiadas
    usando análisis de palabras clave, contexto y patrones.
    """
    
    def __init__(self):
        # Extractores de documentos
        self.extractors = {
            '.pdf': PDFExtractor(),
            '.docx': DOCXExtractor(),
            '.doc': DOCXExtractor(),
            '.xlsx': XLSXExtractor(),
            '.xls': XLSXExtractor(),
            '.txt': TXTExtractor()
        }
        
        # Patrones de categorización mejorados
        self.category_patterns = self._load_category_patterns()
        
        # Palabras de stop (ignorar en análisis)
        self.stop_words = {
            'el', 'la', 'de', 'que', 'y', 'es', 'en', 'un', 'una', 'por', 'para', 
            'con', 'se', 'del', 'al', 'lo', 'le', 'da', 'su', 'sus', 'me', 'mi',
            'te', 'tu', 'nos', 'os', 'les', 'pero', 'o', 'u', 'si', 'no'
        }
        
        logger.info("Analizador de Contenido Inteligente inicializado")

    def _load_category_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Carga los patrones de categorización mejorados"""
        return {
            'personal': {
                'keywords': {
                    # Información personal básica
                    'identidad': ['yo', 'mi nombre', 'me llamo', 'soy', 'tengo', 'nací'],
                    'gustos': ['me gusta', 'prefiero', 'disfruto', 'amo', 'odio', 'detesto'],
                    'rutina': ['rutina', 'costumbre', 'siempre', 'todos los días', 'habitualmente'],
                    'hobbies': ['hobby', 'pasatiempo', 'afición', 'tiempo libre', 'diversión'],
                    'emociones': ['siento', 'me siento', 'estoy', 'emocionado', 'triste', 'feliz'],
                    'salud': ['salud', 'médico', 'enfermo', 'dolor', 'medicamento', 'síntoma']
                },
                'patterns': [
                    r'\bmi\s+\w+\s+(favorit[oa]|preferid[oa])\b',
                    r'\bme\s+(gusta|encanta|fascina)\b',
                    r'\bsiempre\s+\w+\b',
                    r'\btodos\s+los\s+días\b'
                ],
                'weight': 1.0
            },
            
            'familiar': {
                'keywords': {
                    'relaciones': ['familia', 'esposa', 'esposo', 'marido', 'mujer', 'pareja'],
                    'hijos': ['hijo', 'hija', 'niño', 'niña', 'bebé', 'adolescente'],
                    'padres': ['madre', 'padre', 'mamá', 'papá', 'progenitor'],
                    'hermanos': ['hermano', 'hermana', 'primo', 'prima', 'sobrino', 'sobrina'],
                    'abuelos': ['abuelo', 'abuela', 'bisabuelo', 'bisabuela'],
                    'eventos': ['aniversario', 'boda', 'cumpleaños', 'reunión familiar', 'navidad'],
                    'actividades': ['cena familiar', 'visita', 'llamada familiar']
                },
                'patterns': [
                    r'\bmi\s+(esposa|esposo|marido|mujer|pareja)\b',
                    r'\baniversario\s+de\b',
                    r'\bcumpleaños\s+de\b',
                    r'\breunión\s+familiar\b'
                ],
                'weight': 1.2
            },
            
            'social': {
                'keywords': {
                    'amigos': ['amigo', 'amiga', 'conocido', 'compañero', 'vecino'],
                    'eventos': ['fiesta', 'reunión', 'evento', 'celebración', 'encuentro'],
                    'actividades': ['salir', 'quedar', 'verse', 'visitarse', 'charlar'],
                    'lugares': ['bar', 'restaurante', 'cine', 'parque', 'centro comercial'],
                    'grupos': ['grupo', 'pandilla', 'círculo', 'comunidad', 'red social']
                },
                'patterns': [
                    r'\bquedé\s+con\b',
                    r'\bfuimos\s+a\b',
                    r'\bfiesta\s+de\b',
                    r'\breunión\s+social\b'
                ],
                'weight': 1.0
            },
            
            'laboral': {
                'keywords': {
                    'trabajo': ['trabajo', 'empleo', 'oficina', 'empresa', 'negocio'],
                    'personas': ['jefe', 'colega', 'compañero de trabajo', 'cliente', 'proveedor'],
                    'actividades': ['reunión', 'proyecto', 'tarea', 'informe', 'presentación'],
                    'lugares': ['oficina', 'despacho', 'sala de juntas', 'fábrica', 'almacén'],
                    'tiempo': ['horario', 'turno', 'jornada', 'horas extra', 'vacaciones'],
                    'objetivos': ['meta', 'objetivo', 'resultado', 'venta', 'ganancia']
                },
                'patterns': [
                    r'\breunión\s+de\s+trabajo\b',
                    r'\bproyecto\s+de\b',
                    r'\binforme\s+de\b',
                    r'\bcliente\s+\w+\b'
                ],
                'weight': 1.1
            },
            
            'escolar': {
                'keywords': {
                    'instituciones': ['universidad', 'colegio', 'instituto', 'academia', 'escuela'],
                    'personas': ['profesor', 'maestro', 'compañero', 'estudiante', 'alumno'],
                    'actividades': ['clase', 'examen', 'tarea', 'práctica', 'laboratorio'],
                    'materias': ['matemáticas', 'historia', 'ciencias', 'idiomas', 'literatura'],
                    'evaluación': ['nota', 'calificación', 'examen', 'prueba', 'test'],
                    'tiempo': ['semestre', 'curso', 'año académico', 'vacaciones']
                },
                'patterns': [
                    r'\bexamen\s+de\b',
                    r'\bclase\s+de\b',
                    r'\btarea\s+de\b',
                    r'\bproyecto\s+universitario\b'
                ],
                'weight': 1.0
            },
            
            'deportiva': {
                'keywords': {
                    'actividades': ['ejercicio', 'deporte', 'entrenar', 'correr', 'nadar'],
                    'lugares': ['gym', 'gimnasio', 'piscina', 'cancha', 'estadio', 'pista'],
                    'equipos': ['equipo', 'club', 'selección', 'liga', 'torneo'],
                    'fitness': ['fitness', 'cardio', 'pesas', 'yoga', 'pilates'],
                    'resultados': ['marca', 'tiempo', 'récord', 'victoria', 'derrota'],
                    'rutina': ['rutina', 'entrenamiento', 'plan', 'programa', 'sesión']
                },
                'patterns': [
                    r'\bentrenamiento\s+de\b',
                    r'\brutina\s+de\s+ejercicio\b',
                    r'\bfui\s+al\s+gym\b',
                    r'\bpartido\s+de\b'
                ],
                'weight': 1.0
            },
            
            'religion': {
                'keywords': {
                    'creencias': ['dios', 'fe', 'religión', 'espiritual', 'alma', 'cielo'],
                    'lugares': ['iglesia', 'templo', 'mezquita', 'sinagoga', 'catedral'],
                    'actividades': ['oración', 'misa', 'servicio', 'culto', 'meditación'],
                    'personas': ['pastor', 'sacerdote', 'imam', 'rabino', 'monje'],
                    'eventos': ['bautismo', 'comunión', 'confirmación', 'boda religiosa'],
                    'textos': ['biblia', 'corán', 'torá', 'evangelio', 'salmo']
                },
                'patterns': [
                    r'\bfui\s+a\s+misa\b',
                    r'\boración\s+de\b',
                    r'\bservicio\s+religioso\b',
                    r'\bfe\s+en\b'
                ],
                'weight': 1.0
            }
        }

    def analyze_document(self, file_path: str, file_name: str = None) -> Dict[str, Any]:
        """
        Analiza un documento completo para sugerir categorización
        
        Args:
            file_path: Ruta al archivo
            file_name: Nombre del archivo (opcional)
            
        Returns:
            Diccionario con análisis y sugerencias
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
            
            # Determinar tipo de archivo
            file_extension = file_path.suffix.lower()
            
            if file_extension not in self.extractors:
                return {
                    'success': False,
                    'error': f'Tipo de archivo no soportado: {file_extension}',
                    'suggested_category': 'personal',
                    'confidence': 0.1
                }
            
            # Extraer contenido
            extractor = self.extractors[file_extension]
            extraction_result = extractor.extract(str(file_path))
            
            if not extraction_result['success']:
                return {
                    'success': False,
                    'error': f'Error extrayendo contenido: {extraction_result.get("error")}',
                    'suggested_category': 'personal',
                    'confidence': 0.1
                }
            
            content = extraction_result['content']
            
            # Generar preview (primeras 500 palabras o 2000 caracteres)
            preview = self._generate_preview(content)
            
            # Analizar contenido
            analysis = self._analyze_text_content(content)
            
            # Análisis adicional del nombre del archivo
            filename_analysis = self._analyze_filename(file_name or file_path.name)
            
            # Combinar análisis
            combined_analysis = self._combine_analyses([analysis, filename_analysis])
            
            return {
                'success': True,
                'file_info': {
                    'name': file_name or file_path.name,
                    'size': file_path.stat().st_size,
                    'type': file_extension,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                },
                'content_preview': preview,
                'suggested_category': combined_analysis['category'],
                'confidence': combined_analysis['confidence'],
                'reasoning': combined_analysis['reasoning'],
                'alternative_categories': combined_analysis['alternatives']
            }
            
        except Exception as e:
            logger.error(f"Error analizando documento {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_info': None,
                'suggested_category': 'personal',
                'confidence': 0.1,
                'reasoning': f'Error al procesar archivo: {str(e)}',
                'alternative_categories': []
            }

    def analyze_conversation(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Analiza una conversación para sugerir categorización
        
        Args:
            messages: Lista de mensajes [{'role': 'user/assistant', 'content': '...'}]
            
        Returns:
            Diccionario con análisis y sugerencias
        """
        try:
            # Combinar todos los mensajes del usuario
            user_content = ' '.join([
                msg['content'] for msg in messages 
                if msg.get('role') == 'user'
            ])
            
            if not user_content.strip():
                return {
                    'success': False,
                    'error': 'No hay contenido de usuario para analizar',
                    'suggested_category': 'personal',
                    'confidence': 0.1
                }
            
            # Analizar contenido
            analysis = self._analyze_text_content(user_content)
            
            # Análisis contextual de conversación
            context_analysis = self._analyze_conversation_context(messages)
            
            # Combinar análisis
            combined_analysis = self._combine_analyses([analysis, context_analysis])
            
            return {
                'success': True,
                'conversation_info': {
                    'message_count': len(messages),
                    'user_messages': len([m for m in messages if m.get('role') == 'user']),
                    'length': len(user_content)
                },
                'content_summary': self._generate_conversation_summary(messages),
                'suggested_category': combined_analysis['category'],
                'confidence': combined_analysis['confidence'],
                'reasoning': combined_analysis['reasoning'],
                'alternative_categories': combined_analysis['alternatives']
            }
            
        except Exception as e:
            logger.error(f"Error analizando conversación: {e}")
            return {
                'success': False,
                'error': str(e),
                'conversation_info': None,
                'content_summary': f'Error al procesar conversación: {str(e)}',
                'suggested_category': 'personal',
                'confidence': 0.1,
                'reasoning': f'Error al procesar conversación: {str(e)}',
                'alternative_categories': []
            }

    def _analyze_text_content(self, content: str) -> Dict[str, Any]:
        """Analiza contenido de texto usando patrones y palabras clave"""
        content_lower = content.lower()
        category_scores = {}
        reasoning_details = {}
        
        for category, config in self.category_patterns.items():
            score = 0
            found_keywords = []
            found_patterns = []
            
            # Análisis de palabras clave por subcategoría
            for subcategory, keywords in config['keywords'].items():
                subcategory_score = 0
                subcategory_keywords = []
                
                for keyword in keywords:
                    if keyword in content_lower:
                        subcategory_score += 1
                        subcategory_keywords.append(keyword)
                
                if subcategory_keywords:
                    found_keywords.extend(subcategory_keywords)
                    score += subcategory_score * 1.5  # Peso por subcategoría
            
            # Análisis de patrones regex
            for pattern in config.get('patterns', []):
                matches = re.findall(pattern, content_lower)
                if matches:
                    found_patterns.extend(matches)
                    score += len(matches) * 2  # Mayor peso para patrones específicos
            
            # Aplicar peso de categoría
            weighted_score = score * config.get('weight', 1.0)
            
            if weighted_score > 0:
                category_scores[category] = weighted_score
                reasoning_details[category] = {
                    'keywords_found': found_keywords,
                    'patterns_found': found_patterns,
                    'raw_score': score,
                    'weighted_score': weighted_score
                }
        
        if not category_scores:
            return {
                'category': 'personal',
                'confidence': 0.1,
                'reasoning': 'No se encontraron patrones específicos, categoría por defecto',
                'alternatives': []
            }
        
        # Ordenar por puntuación
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        best_category = sorted_categories[0][0]
        best_score = sorted_categories[0][1]
        
        # Calcular confianza (normalizada)
        total_words = len([w for w in content_lower.split() if w not in self.stop_words])
        confidence = min(0.95, (best_score / max(total_words, 10)) * 2)
        
        # Generar explicación
        reasoning = self._generate_reasoning(best_category, reasoning_details.get(best_category, {}))
        
        # Categorías alternativas
        alternatives = [
            {
                'category': cat,
                'confidence': min(0.9, (score / best_score) * confidence),
                'reasoning': self._generate_reasoning(cat, reasoning_details.get(cat, {}))
            }
            for cat, score in sorted_categories[1:3]  # Top 2 alternativas
        ]
        
        return {
            'category': best_category,
            'confidence': confidence,
            'reasoning': reasoning,
            'alternatives': alternatives
        }

    def _analyze_filename(self, filename: str) -> Dict[str, Any]:
        """Analiza el nombre del archivo para obtener pistas de categorización"""
        filename_lower = filename.lower()
        
        # Patrones comunes en nombres de archivo
        filename_patterns = {
            'laboral': ['trabajo', 'proyecto', 'informe', 'empresa', 'cv', 'curriculum'],
            'escolar': ['tarea', 'examen', 'universidad', 'curso', 'materia'],
            'personal': ['personal', 'foto', 'documento'],
            'familiar': ['familia', 'boda', 'aniversario'],
            'deportiva': ['entrenamiento', 'gym', 'deporte'],
            'religion': ['iglesia', 'sermon', 'biblia']
        }
        
        for category, patterns in filename_patterns.items():
            for pattern in patterns:
                if pattern in filename_lower:
                    return {
                        'category': category,
                        'confidence': 0.3,  # Confianza moderada basada solo en nombre
                        'reasoning': f'Nombre del archivo contiene "{pattern}"',
                        'alternatives': []
                    }
        
        return {
            'category': 'personal',
            'confidence': 0.05,
            'reasoning': 'Sin pistas en el nombre del archivo',
            'alternatives': []
        }

    def _analyze_conversation_context(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Analiza el contexto de una conversación"""
        # Análisis simple por ahora - puede expandirse
        user_messages = [m['content'] for m in messages if m.get('role') == 'user']
        
        if not user_messages:
            return {
                'category': 'personal',
                'confidence': 0.1,
                'reasoning': 'Sin mensajes de usuario',
                'alternatives': []
            }
        
        # Contar preguntas vs afirmaciones
        questions = sum(1 for msg in user_messages if '?' in msg)
        statements = len(user_messages) - questions
        
        # Si hay muchas preguntas, podría ser consulta personal o de ayuda
        if questions > statements:
            return {
                'category': 'personal',
                'confidence': 0.2,
                'reasoning': 'Conversación con muchas preguntas, probablemente consulta personal',
                'alternatives': []
            }
        
        # Análisis temporal (si es posible)
        # Por ahora, retornar análisis neutro
        return {
            'category': 'personal',
            'confidence': 0.1,
            'reasoning': 'Análisis contextual básico',
            'alternatives': []
        }

    def _combine_analyses(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combina múltiples análisis en uno final"""
        # Ponderación por confianza
        total_weight = sum(analysis['confidence'] for analysis in analyses)
        
        if total_weight == 0:
            return {
                'category': 'personal',
                'confidence': 0.1,
                'reasoning': 'No se pudo determinar categoría',
                'alternatives': []
            }
        
        # Calcular puntuación ponderada por categoría
        category_weighted_scores = {}
        
        for analysis in analyses:
            weight = analysis['confidence']
            category = analysis['category']
            
            if category not in category_weighted_scores:
                category_weighted_scores[category] = 0
            category_weighted_scores[category] += weight
        
        # Encontrar mejor categoría
        best_category = max(category_weighted_scores, key=category_weighted_scores.get)
        best_score = category_weighted_scores[best_category]
        
        # Confianza final (promedio ponderado)
        final_confidence = best_score / total_weight
        
        # Combinar razonamientos
        reasoning_parts = [
            f"{analysis['reasoning']} (confianza: {analysis['confidence']:.2f})"
            for analysis in analyses if analysis['confidence'] > 0.1
        ]
        combined_reasoning = '; '.join(reasoning_parts)
        
        # Alternativas combinadas
        all_alternatives = []
        for analysis in analyses:
            all_alternatives.extend(analysis.get('alternatives', []))
        
        # Filtrar y ordenar alternativas únicas
        unique_alternatives = {}
        for alt in all_alternatives:
            cat = alt['category']
            if cat != best_category:
                if cat not in unique_alternatives or alt['confidence'] > unique_alternatives[cat]['confidence']:
                    unique_alternatives[cat] = alt
        
        alternatives = sorted(unique_alternatives.values(), key=lambda x: x['confidence'], reverse=True)[:2]
        
        return {
            'category': best_category,
            'confidence': final_confidence,
            'reasoning': combined_reasoning,
            'alternatives': alternatives
        }

    def _generate_preview(self, content: str) -> str:
        """Genera un preview del contenido"""
        # Limpiar contenido
        cleaned = re.sub(r'\s+', ' ', content.strip())
        
        # Límite de caracteres para preview
        max_chars = 500
        
        if len(cleaned) <= max_chars:
            return cleaned
        
        # Cortar en una palabra completa
        preview = cleaned[:max_chars]
        last_space = preview.rfind(' ')
        
        if last_space > max_chars * 0.8:  # Si el último espacio está cerca del final
            preview = preview[:last_space]
        
        return preview + "..."

    def _generate_conversation_summary(self, messages: List[Dict[str, str]]) -> str:
        """Genera un resumen de la conversación"""
        user_messages = [m['content'] for m in messages if m.get('role') == 'user']
        
        if not user_messages:
            return "Sin mensajes de usuario"
        
        # Tomar el primer y último mensaje para crear un resumen básico
        first_msg = user_messages[0][:100] + ("..." if len(user_messages[0]) > 100 else "")
        
        if len(user_messages) == 1:
            return f"Usuario preguntó: {first_msg}"
        
        last_msg = user_messages[-1][:100] + ("..." if len(user_messages[-1]) > 100 else "")
        
        return f"Conversación de {len(user_messages)} mensajes. Inició: {first_msg}. Último: {last_msg}"

    def _generate_reasoning(self, category: str, details: Dict[str, Any]) -> str:
        """Genera explicación del razonamiento para una categoría"""
        reasoning_parts = []
        
        keywords = details.get('keywords_found', [])
        patterns = details.get('patterns_found', [])
        
        if keywords:
            reasoning_parts.append(f"Palabras clave encontradas: {', '.join(keywords[:3])}")
        
        if patterns:
            reasoning_parts.append(f"Patrones detectados: {len(patterns)}")
        
        if not reasoning_parts:
            reasoning_parts.append("Análisis general del contenido")
        
        return f"Categoría '{category}': {'; '.join(reasoning_parts)}"

    def bulk_analyze_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """Analiza múltiples archivos en lote"""
        results = []
        
        for file_path in file_paths:
            try:
                result = self.analyze_document(file_path)
                result['file_path'] = file_path
                results.append(result)
            except Exception as e:
                logger.error(f"Error en análisis en lote para {file_path}: {e}")
                results.append({
                    'file_path': file_path,
                    'success': False,
                    'error': str(e),
                    'suggested_category': 'personal',
                    'confidence': 0.1
                })
        
        logger.info(f"Análisis en lote completado: {len(results)} archivos procesados")
        return results