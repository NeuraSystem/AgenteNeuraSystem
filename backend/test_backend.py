#!/usr/bin/env python3
"""
Script de prueba simple para verificar que el backend puede iniciarse
"""

import sys
import os

# Añadir el directorio backend al path
sys.path.append('backend')

try:
    from fastapi import FastAPI, UploadFile, File, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
    import asyncio
    import uuid
    import time
    
    print("✅ FastAPI importado correctamente")
    
    # Crear app básica
    app = FastAPI(title="ChatIng Backend Test", version="1.0")
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    class TestResponse(BaseModel):
        message: str
        status: str
    
    @app.get("/")
    async def root():
        return {"message": "ChatIng Backend funcionando!", "status": "OK"}
    
    @app.get("/test")
    async def test():
        return TestResponse(message="Backend conectado exitosamente", status="success")
    
    @app.get("/agente/categories")
    async def get_categories():
        """Endpoint de prueba para categorías"""
        return {
            "categories": [
                {
                    "id": "personal",
                    "name": "personal", 
                    "displayName": "Personal",
                    "description": "Información personal, gustos, rutinas",
                    "enabled": True,
                    "subcategories": ["documentos", "conversaciones"]
                },
                {
                    "id": "familiar",
                    "name": "familiar",
                    "displayName": "Familiar", 
                    "description": "Familia, eventos familiares",
                    "enabled": True,
                    "subcategories": ["documentos", "conversaciones"]
                },
                {
                    "id": "laboral",
                    "name": "laboral",
                    "displayName": "Laboral",
                    "description": "Trabajo, proyectos",
                    "enabled": False,
                    "subcategories": ["documentos", "conversaciones"]
                }
            ]
        }
    
    @app.get("/documents/list")
    async def list_documents():
        """Endpoint de prueba para documentos"""
        return []
    
    @app.get("/agente/status")
    async def get_status():
        """Endpoint de prueba para el estado de AgenteIng"""
        return {
            "critical_thinking_enabled": True,
            "buffer_status": {"items": 0},
            "category_stats": {"personal": {"total_items": 0}, "familiar": {"total_items": 0}, "social": {"total_items": 0}},
            "active_alerts_count": 0,
            "pending_review_count": 0
        }
    
    @app.get("/agente/stats")
    async def get_stats():
        """Endpoint alternativo de estadísticas"""
        return {
            "critical_thinking_enabled": True,
            "buffer_status": {"items": 0},
            "category_stats": {"personal": {"total_items": 0}, "familiar": {"total_items": 0}, "social": {"total_items": 0}},
            "active_alerts_count": 0,
            "pending_review_count": 0
        }
    
    # Simulación de almacenamiento de documentos
    uploaded_documents = {}
    
    @app.post("/documents/upload")
    async def upload_document(file: UploadFile = File(...)):
        """Endpoint para subir archivos con procesamiento simulado"""
        try:
            # Generar ID único para el documento
            document_id = str(uuid.uuid4())
            file_name = file.filename or "archivo_sin_nombre"
            
            # Simular lectura del archivo
            content = await file.read()
            
            # Guardar información del documento
            uploaded_documents[document_id] = {
                "document_id": document_id,
                "file_name": file_name,
                "file_type": file_name.split('.')[-1] if '.' in file_name else "unknown",
                "status": "uploaded",
                "processed_at": time.time(),
                "size": len(content)
            }
            
            return {
                "document_id": document_id,
                "file_name": file_name,
                "file_type": file_name.split('.')[-1] if '.' in file_name else "unknown",
                "status": "uploaded",
                "message": f"Archivo '{file_name}' subido exitosamente"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al subir archivo: {str(e)}")
    
    @app.post("/agente/analyze/file") 
    async def analyze_file(request: dict):
        """Endpoint para analizar archivos y sugerir categorización"""
        try:
            file_path = request.get("file_path", "")
            file_name = request.get("file_name", "")
            
            # Simular procesamiento con delay realista
            await asyncio.sleep(2)  # Simular tiempo de procesamiento
            
            # Lógica simple de categorización basada en nombre del archivo
            file_lower = file_name.lower()
            
            if any(word in file_lower for word in ["cv", "curriculum", "trabajo", "empresa", "laboral"]):
                suggested_category = "laboral"
                confidence = 0.85
                reasoning = "El archivo parece contener información laboral o profesional"
            elif any(word in file_lower for word in ["familia", "familiar", "papa", "mama", "hermano"]):
                suggested_category = "familiar"
                confidence = 0.80
                reasoning = "El archivo parece contener información familiar"
            elif any(word in file_lower for word in ["social", "amigos", "evento", "fiesta"]):
                suggested_category = "social" 
                confidence = 0.75
                reasoning = "El archivo parece contener información social"
            else:
                suggested_category = "personal"
                confidence = 0.60
                reasoning = "Categoría personal asignada por defecto"
            
            return {
                "success": True,
                "suggested_category": suggested_category,
                "confidence": confidence,
                "reasoning": reasoning,
                "alternative_categories": ["personal", "familiar", "social"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error al analizar archivo: {str(e)}"
            }
    
    @app.post("/agente/approve/categorization")
    async def approve_categorization(request: dict):
        """Endpoint para aprobar categorización de archivos"""
        try:
            file_id = request.get("file_id")
            approved_category = request.get("approved_category")
            
            if file_id in uploaded_documents:
                uploaded_documents[file_id]["category"] = approved_category
                uploaded_documents[file_id]["status"] = "categorized"
                
                return {
                    "success": True,
                    "message": f"Archivo categorizado en '{approved_category}' exitosamente"
                }
            else:
                return {
                    "success": False,
                    "error": "Archivo no encontrado"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error al aprobar categorización: {str(e)}"
            }
    
    @app.get("/agente/alerts")
    async def get_alerts():
        """Endpoint para obtener alertas proactivas"""
        return {"alerts": []}
    
    @app.post("/agente/alerts/action")
    async def handle_alert_action(request: dict):
        """Endpoint para manejar acciones de alertas"""
        return {"success": True}
    
    # Sistema de memoria conversacional simple (en memoria del servidor)
    conversation_memory = {}
    
    @app.post("/chat")
    async def chat_endpoint(request: dict):
        """Endpoint de chat conversacional y cálido"""
        mensaje = request.get("mensaje", "")
        session_id = request.get("session_id", "default")
        
        # Inicializar memoria de sesión si no existe
        if session_id not in conversation_memory:
            conversation_memory[session_id] = {
                "messages": [],
                "user_info": {},
                "conversation_count": 0
            }
        
        # Agregar mensaje a la memoria
        conversation_memory[session_id]["messages"].append({"role": "user", "content": mensaje})
        conversation_memory[session_id]["conversation_count"] += 1
        
        # Generar respuesta natural y cálida
        respuesta = generate_natural_response(mensaje, conversation_memory[session_id])
        
        # Guardar respuesta en memoria
        conversation_memory[session_id]["messages"].append({"role": "assistant", "content": respuesta})
        
        return {"respuesta": respuesta, "proveedor": "agenteIng", "metadatos": {"lenguaje": "es"}}
    
    def generate_natural_response(mensaje, session_memory):
        """Genera respuestas naturales y conversacionales"""
        mensaje_lower = mensaje.lower()
        conversation_count = session_memory["conversation_count"]
        
        # Respuestas de saludo más naturales
        if any(word in mensaje_lower for word in ["hola", "buenas", "hey", "hi"]):
            if conversation_count == 1:
                return "¡Hola! Me da mucho gusto conocerte. Soy tu asistente personal y estoy aquí para acompañarte. ¿Cómo te gusta que te llamen?"
            else:
                return "¡Hola de nuevo! ¿Cómo estás hoy? ¿En qué puedo ayudarte?"
        
        # Respuestas sobre capacidades - más conversacionales
        elif any(word in mensaje_lower for word in ["qué puedes", "que haces", "ayuda", "funciones"]):
            return "¡Me encanta que preguntes! Soy como tu asistente personal digital. Puedo platicar contigo, recordar las cosas importantes que me cuentes, organizar tus documentos cuando quieras, y en general estar aquí para lo que necesites. ¿Hay algo específico en lo que te gustaría que te ayude?"
        
        # Conversación sobre el usuario
        elif any(word in mensaje_lower for word in ["me llamo", "soy", "mi nombre"]):
            # Extraer nombre si es posible
            palabras = mensaje.split()
            if "llamo" in mensaje_lower:
                try:
                    idx = palabras.index(next(p for p in palabras if "llamo" in p.lower()))
                    if idx + 1 < len(palabras):
                        nombre = palabras[idx + 1].replace(",", "").replace(".", "")
                        session_memory["user_info"]["nombre"] = nombre
                        return f"¡Qué bonito nombre, {nombre}! Me da mucho gusto conocerte. Cuéntame, ¿a qué te dedicas o qué te gusta hacer en tu tiempo libre?"
                except:
                    pass
            return "¡Qué genial conocerte! Me encanta cuando las personas se presentan. Cuéntame más sobre ti, ¿qué te gusta hacer?"
        
        # Respuestas sobre trabajo/estudios
        elif any(word in mensaje_lower for word in ["trabajo", "estudio", "universidad", "colegio", "empresa"]):
            return "¡Qué interesante! Me encanta conocer sobre lo que haces. ¿Te gusta tu trabajo/estudio? ¿Hay algo en particular que te emocione o algún reto que estés enfrentando?"
        
        # Respuestas sobre familia
        elif any(word in mensaje_lower for word in ["familia", "papá", "mamá", "hermano", "hermana", "hijo", "hija", "esposo", "esposa"]):
            return "La familia es muy importante. Me parece genial que me cuentes sobre ellos. ¿Son muy unidos? ¿Hay alguna tradición familiar que les guste?"
        
        # Respuestas sobre gustos y hobbies
        elif any(word in mensaje_lower for word in ["gusta", "hobby", "tiempo libre", "deporte", "música", "películas", "leer"]):
            return "¡Me fascina conocer los gustos de las personas! Eso dice mucho de quién eres. ¿Tienes algún hobby favorito o algo que hagas para relajarte?"
        
        # Respuestas sobre sentimientos
        elif any(word in mensaje_lower for word in ["feliz", "triste", "cansado", "estresado", "contento", "bien", "mal"]):
            if any(word in mensaje_lower for word in ["bien", "feliz", "contento", "genial", "excelente"]):
                return "¡Qué bueno escuchar eso! Me alegra saber que te sientes bien. ¿Hay algo en particular que haya hecho tu día mejor?"
            else:
                return "Te escucho. A veces tenemos días difíciles y está bien sentirse así. ¿Quieres contarme qué está pasando? A veces hablar ayuda."
        
        # Preguntas sobre el tiempo o el día
        elif any(word in mensaje_lower for word in ["día", "mañana", "tarde", "noche", "tiempo", "clima"]):
            return "¡Sí! ¿Cómo ha estado tu día? ¿Has hecho algo interesante o tienes planes para más tarde?"
        
        # Respuestas sobre solo platicar
        elif any(word in mensaje_lower for word in ["platicar", "conversar", "hablar", "solo", "aburrido"]):
            return "¡Por supuesto! Me encanta platicar. A veces es bonito tener una conversación relajada. ¿De qué te gustaría que hablemos? ¿Cómo ha estado tu día?"
        
        # Respuestas por defecto - naturales y abiertas
        else:
            respuestas_naturales = [
                f"Interesante lo que me dices. Cuéntame más sobre eso, me parece fascinante.",
                f"Me gusta mucho que compartirlo conmigo. ¿Qué más me puedes contar sobre eso?",
                f"Eso suena muy interesante. ¿Podrías contarme un poco más?",
                f"Me parece muy cool eso que me cuentas. ¿Y tú qué opinas al respecto?",
                f"¡Qué genial! Me encanta conocer cosas nuevas. ¿Hay algo más que te gustaría contarme sobre eso?"
            ]
            
            # Usar el contador de conversación para variar respuestas
            respuesta_idx = conversation_count % len(respuestas_naturales)
            return respuestas_naturales[respuesta_idx]
    
    if __name__ == "__main__":
        print("🚀 Iniciando servidor de prueba en puerto 8000...")
        uvicorn.run(app, host="127.0.0.1", port=8000)
        
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("Instala las dependencias básicas: pip install fastapi uvicorn")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error inesperado: {e}")
    sys.exit(1)