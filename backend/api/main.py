"""
Archivo principal de la API del chatbot.
- Framework: FastAPI
- Endpoints: /chat (POST)
- Selección de proveedor LLM por parámetro o por defecto
- Soporte para Anthropic, DeepSeek, Gemini, OpenAI (API Key)
- Soporte para modelo local Ollama (función comentada)
- Logs en consola y archivo
- Carga de configuración desde .env
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List, Union
import os
import logging
import json
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
import uuid
import io

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("../data/api.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# Inicializar FastAPI
app = FastAPI(title="Chatbot Modular API", version="1.0")

# Importar y registrar routers
from .voice_synthesis import router as voice_router
app.include_router(voice_router)

# Configurar CORS para permitir frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"],  # Frontend URLs + Chat Simple
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# ================================
# INICIALIZACIÓN DE SISTEMAS
# ================================

# --- Nuevo Sistema de Recuperación Híbrido ---
from storage.vector_manager import VectorManager
from memory.hybrid_retrieval import HybridRetrievalSystem

vector_manager = VectorManager()
hybrid_retriever = HybridRetrievalSystem(vector_manager)
logger.info("✅ Sistema de Recuperación Híbrido inicializado.")
# -----------------------------------------

# Sistema de memoria (compatible con versión actual y avanzada) - CARGA LAZY
ADVANCED_MEMORY_ENABLED = os.getenv("ENABLE_ADVANCED_MEMORY", "false").lower() == "true"
MEMORIA_DISPONIBLE = False
memoria_conversacional = None
memoria_avanzada = None

def initialize_memory_lazy():
    """Inicializa memoria de forma lazy solo cuando sea necesaria"""
    global memoria_conversacional, memoria_avanzada, MEMORIA_DISPONIBLE
    
    if MEMORIA_DISPONIBLE:
        return  # Ya inicializada
    
    try:
        if ADVANCED_MEMORY_ENABLED:
            # Memoria avanzada (nueva funcionalidad)
            from memory.episodic import EpisodicMemoryManager
            memoria_avanzada = EpisodicMemoryManager(buffer_size=5)
            logger.info("Sistema de memoria avanzada inicializado")
        
        # Memoria básica (mantener compatibilidad)
        from memory.episodic import crear_memoria_episodica
        memoria_conversacional = crear_memoria_episodica(buffer_size=5)
        MEMORIA_DISPONIBLE = True
        logger.info("Memoria episódica básica inicializada correctamente")
        
    except ImportError as e:
        logger.warning(f"Memoria episódica no disponible: {e}")
        memoria_conversacional = None
        memoria_avanzada = None
        MEMORIA_DISPONIBLE = False

# Sistema de procesamiento de documentos - CARGA LAZY
DOCUMENT_PROCESSING_ENABLED = False
document_manager = None
CONTEXTUAL_MEMORY_ENABLED = False
contextual_memory = None

def initialize_documents_lazy():
    """Inicializa sistema de documentos de forma lazy"""
    global document_manager, DOCUMENT_PROCESSING_ENABLED, contextual_memory, CONTEXTUAL_MEMORY_ENABLED
    
    if DOCUMENT_PROCESSING_ENABLED:
        return  # Ya inicializado
    
    try:
        from document_processing import DocumentManager
        document_manager = DocumentManager()
        DOCUMENT_PROCESSING_ENABLED = True
        logger.info("Sistema de procesamiento de documentos inicializado")
        
        # Memoria contextual con documentos
        try:
            from memory.document_contextual_memory import DocumentContextualMemory
            contextual_memory = DocumentContextualMemory()
            CONTEXTUAL_MEMORY_ENABLED = True
            logger.info("Sistema de memoria contextual inicializado")
        except ImportError as e:
            logger.warning(f"Memoria contextual no disponible: {e}")
            contextual_memory = None
            CONTEXTUAL_MEMORY_ENABLED = False
            
    except ImportError as e:
        logger.warning(f"Sistema de documentos no disponible: {e}")
        document_manager = None
        DOCUMENT_PROCESSING_ENABLED = False

# Sistema AgenteIng - CARGA LAZY
AGENTE_ING_ENABLED = False
critical_thinking = None
category_manager = None
proactive_assistant = None
content_analyzer = None

def initialize_agente_ing_lazy():
    """Inicializa AgenteIng de forma lazy solo cuando sea necesario"""
    global critical_thinking, category_manager, proactive_assistant, content_analyzer, AGENTE_ING_ENABLED
    
    if AGENTE_ING_ENABLED:
        return  # Ya inicializado
    
    try:
        from memory.critical_thinking import CriticalThinking
        from memory.category_manager import CategoryManager
        from memory.proactive_assistant import ProactiveAssistant
        from ai.content_analyzer import ContentAnalyzer
        
        critical_thinking = CriticalThinking()
        category_manager = CategoryManager()
        proactive_assistant = ProactiveAssistant()
        content_analyzer = ContentAnalyzer()
        
        AGENTE_ING_ENABLED = True
        logger.info("🤖 Sistema AgenteIng inicializado - Memoria Inteligente activa")
    except ImportError as e:
        logger.warning(f"Sistema AgenteIng no disponible: {e}")
        critical_thinking = None
        category_manager = None
        proactive_assistant = None
        content_analyzer = None
        AGENTE_ING_ENABLED = False


# Modelos de entrada y salida
class ChatRequest(BaseModel):
    mensaje: str
    proveedor: Optional[str] = None  # anthropic, deepseek, gemini, openai, ollama
    parametros: Optional[Dict[str, Any]] = None  # Parámetros extra para el LLM

class ChatResponse(BaseModel):
    respuesta: str
    proveedor: str
    metadatos: Dict[str, Any]

# Modelos para documentos
class DocumentUploadResponse(BaseModel):
    document_id: str
    file_name: str
    file_type: str
    status: str
    message: str

class DocumentInfo(BaseModel):
    document_id: str
    file_name: str
    file_type: str
    processed_at: str
    chunk_count: int
    status: str

class DocumentSearchRequest(BaseModel):
    query: str
    document_id: Optional[str] = None
    limit: Optional[int] = 5


# Modelos para AgenteIng
class CategoryConfigRequest(BaseModel):
    category_name: str
    enabled: bool

class CategoryResponse(BaseModel):
    categories: List[Dict[str, Any]]
    stats: Dict[str, Any]

class FileAnalysisRequest(BaseModel):
    file_path: str
    file_name: Optional[str] = None

class FileAnalysisResponse(BaseModel):
    success: bool
    file_info: Optional[Dict[str, Any]]
    suggested_category: str
    confidence: float
    reasoning: str
    alternative_categories: List[Dict[str, Any]]
    error: Optional[str] = None

class CategoryApprovalRequest(BaseModel):
    file_id: str
    approved_category: str

class ProactiveAlertsResponse(BaseModel):
    alerts: List[Dict[str, Any]]
    user_context: Dict[str, Any]

class AlertActionRequest(BaseModel):
    alert_id: str
    action: str  # 'dismiss', 'mark_shown'

class ConversationAnalysisRequest(BaseModel):
    messages: List[Dict[str, str]]

class MemoryStatusResponse(BaseModel):
    critical_thinking_enabled: bool
    buffer_status: Dict[str, Any]
    category_stats: Dict[str, Any]
    active_alerts_count: int
    pending_review_count: int

# Modelos para sistema de personalidad configurable
class PersonalityConfig(BaseModel):
    user_id: Optional[str] = "default"
    personality_text: str
    tone: Optional[str] = "neutral"  # neutral, warm, professional, casual
    response_style: Optional[str] = "balanced"  # concise, detailed, balanced
    enabled: bool = True

class PersonalityUpdateRequest(BaseModel):
    personality_text: str
    tone: Optional[str] = "neutral"
    response_style: Optional[str] = "balanced"

class PersonalityResponse(BaseModel):
    success: bool
    personality: PersonalityConfig
    message: str

# ================================
# SISTEMA DE PERSONALIDAD CONFIGURABLE
# ================================

# Storage simple en memoria para configuraciones de personalidad
# En un entorno de producción, esto debería ser una base de datos
personality_configs: Dict[str, PersonalityConfig] = {}

def get_personality_config(user_id: str = "default") -> PersonalityConfig:
    """Obtiene la configuración de personalidad para un usuario."""
    if user_id not in personality_configs:
        # Configuración por defecto
        personality_configs[user_id] = PersonalityConfig(
            user_id=user_id,
            personality_text="Neutral, eficiente y solidaria. Responde de manera profesional pero amigable.",
            tone="neutral",
            response_style="balanced",
            enabled=True
        )
    return personality_configs[user_id]

def save_personality_config(user_id: str, config: PersonalityConfig) -> bool:
    """Guarda la configuración de personalidad para un usuario."""
    try:
        config.user_id = user_id
        personality_configs[user_id] = config
        return True
    except Exception as e:
        logger.error(f"Error guardando configuración de personalidad: {e}")
        return False

def build_personality_prompt(user_id: str = "default") -> str:
    """Construye el prompt de personalidad basado en la configuración del usuario."""
    config = get_personality_config(user_id)
    
    if not config.enabled:
        return ""
    
    tone_instructions = {
        "neutral": "Mantén un tono neutral y profesional.",
        "warm": "Usa un tono cálido y empático, como un amigo cercano.",
        "professional": "Mantén un tono formal y profesional en todo momento.",
        "casual": "Usa un tono casual y relajado, como en una conversación informal."
    }
    
    style_instructions = {
        "concise": "Sé conciso y directo en tus respuestas.",
        "detailed": "Proporciona respuestas detalladas y exhaustivas.",
        "balanced": "Equilibra la concisión con el detalle necesario."
    }
    
    personality_prompt = f"\nPERSONALIDAD PERSONALIZADA: {config.personality_text}\n"
    personality_prompt += f"TONO: {tone_instructions.get(config.tone, tone_instructions['neutral'])}\n"
    personality_prompt += f"ESTILO: {style_instructions.get(config.response_style, style_instructions['balanced'])}\n"
    
    return personality_prompt

# Función: obtener proveedor por defecto desde .env
def get_default_provider() -> str:
    """Obtiene el proveedor LLM por defecto desde las variables de entorno."""
    return os.getenv("DEFAULT_PROVIDER", "anthropic")

# Función: obtener API Key para un proveedor
def get_api_key(proveedor: str) -> Optional[str]:
    """Obtiene la API Key correspondiente al proveedor desde .env."""
    return os.getenv(f"{proveedor.upper()}_API_KEY")

# Función común para preparar contexto mejorado
async def prepare_enhanced_context(mensaje: str, user_id: str = "default") -> Dict[str, Any]:
    """
    Prepara el contexto mejorado con el nuevo sistema de recuperación híbrido.
    """
    # 🚀 USAR EL NUEVO SISTEMA DE RECUPERACIÓN HÍBRIDO
    try:
        document_context = await hybrid_retriever.search(mensaje)
        logger.info("Contexto recuperado exitosamente por el sistema híbrido.")
    except Exception as e:
        logger.error(f"Error en el sistema de recuperación híbrido: {e}")
        document_context = "Error al recuperar el contexto de la memoria."

    # 🧠 MEMORIA CONVERSACIONAL (Historial de la sesión actual)
    initialize_memory_lazy()
    messages = []
    if MEMORIA_DISPONIBLE and memoria_conversacional:
        historial = memoria_conversacional.chat_memory.messages
        for msg in historial:
            if hasattr(msg, 'type'):
                if msg.type == 'human':
                    messages.append({"role": "user", "content": msg.content})
                elif msg.type == 'ai':
                    messages.append({"role": "assistant", "content": msg.content})
    
    # ✨ PERSONALIDAD CONFIGURABLE
    personality_prompt = build_personality_prompt(user_id)
    
    # 🔄 CONSTRUIR PROMPT DEL SISTEMA
    system_prompt = f"""Eres ChatIng, un asistente conversacional útil y preciso.\n\nREGLAS FUNDAMENTALES:\n1. Responde directamente a la pregunta sin añadir saludos innecesarios.\n2. Basa tus respuestas ESTRICTAMENTE en la información proporcionada en el contexto.\n3. Si la información solicitada no está en el contexto, responde claramente: "No encuentro esa información en los documentos disponibles".\n4. NO inventes respuestas. Es mejor admitir que no sabes algo.\n5. Mantén un tono conversacional pero profesional.\n6. Usa el historial para mantener contexto de la conversación.{personality_prompt}"""
    
    # 📄 CONSTRUIR CONTEXTO RAG
    rag_context = ""
    if document_context:
        rag_context += "\n\n" + document_context
        rag_context += "\n\nINSTRUCCIONES RAG: Usa SOLO la información del contexto anterior para responder. Si la respuesta no está en el contexto, indica claramente que no tienes esa información."
    
    return {
        "system_prompt": system_prompt,
        "rag_context": rag_context,
        "messages": messages,
        "conversation_id": str(uuid.uuid4()) # Generar un ID para la interacción
    }

# Función común para guardar en memoria
async def save_to_memory(mensaje: str, respuesta: str, proveedor: str = "anthropic") -> None:
    """
    Guarda la conversación en los sistemas de memoria disponibles.
    """
    # Memoria básica (LangChain)
    if MEMORIA_DISPONIBLE and memoria_conversacional:
        memoria_conversacional.chat_memory.add_user_message(mensaje)
        memoria_conversacional.chat_memory.add_ai_message(respuesta)
    
    # Guardar en la colección 'conversations' de ChromaDB
    try:
        conversation_id = f"conv_{datetime.now().isoformat()}"
        document_to_add = f"Usuario: {mensaje}\nAsistente: {respuesta}"
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "provider": proveedor
        }
        await vector_manager.add_documents(
            collection_name="conversations",
            documents=[document_to_add],
            metadatas=[metadata],
            ids=[conversation_id]
        )
        logger.info(f"Conversación {conversation_id} guardada en la colección de vectores.")
    except Exception as e:
        logger.error(f"Error guardando conversación en ChromaDB: {e}")


# Función: llamada a Anthropic
async def chat_anthropic(mensaje: str, parametros: Optional[Dict[str, Any]] = None) -> str:
    """
    Realiza una consulta a Anthropic usando la API Key.
    Parámetros:
        mensaje (str): Mensaje del usuario.
        parametros (dict): Parámetros adicionales para el modelo.
    Retorna:
        str: Respuesta generada por el modelo.
    """
    try:
        import anthropic
        
        # Obtener configuración desde .env
        api_key = get_api_key("anthropic")
        modelo = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
        
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY no está configurada en el archivo .env")
        
        # Crear cliente de Anthropic
        client = anthropic.Anthropic(api_key=api_key)
        
        # Configurar parámetros por defecto
        max_tokens = parametros.get("max_tokens", 1024) if parametros else 1024
        temperature = parametros.get("temperature", 0.7) if parametros else 0.7
        
        # ✨ USAR CONTEXTO MEJORADO CENTRALIZADO
        user_id = "default"  # En el futuro, esto vendrá del sistema de autenticación
        context = await prepare_enhanced_context(mensaje, user_id)
        
        # Construir mensajes finales (sin sistema, ya que Anthropic lo maneja separado)
        messages = context["messages"]
        
        # Construir mensaje final del usuario con contexto RAG
        final_message = mensaje + context["rag_context"]
        messages.append({"role": "user", "content": final_message})
        
        # Realizar la consulta (Anthropic maneja el system prompt como parámetro separado)
        response = client.messages.create(
            model=modelo,
            max_tokens=max_tokens,
            temperature=temperature,
            system=context["system_prompt"],
            messages=messages
        )
        
        respuesta = response.content[0].text
        
        # 💾 GUARDAR EN MEMORIA (sistema híbrido)
        await save_to_memory(mensaje, respuesta, "anthropic")
        
        return respuesta
        
    except ImportError:
        logger.error("La librería 'anthropic' no está instalada. Instálala con: pip install anthropic")
        return "Error: Librería Anthropic no disponible"
    except Exception as e:
        logger.error(f"Error al consultar Anthropic: {e}")
        return f"Error en la consulta: {str(e)}"

# Función: llamada a DeepSeek
async def chat_deepseek(mensaje: str, parametros: Optional[Dict[str, Any]] = None) -> str:
    """
    Realiza una consulta a DeepSeek usando la API Key.
    """
    try:
        import openai
        
        # Obtener configuración desde .env
        api_key = get_api_key("deepseek")
        modelo = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY no está configurada en el archivo .env")
        
        # Crear cliente de OpenAI compatible (DeepSeek usa protocolo compatible)
        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        
        # Configurar parámetros por defecto
        max_tokens = parametros.get("max_tokens", 1024) if parametros else 1024
        temperature = parametros.get("temperature", 0.7) if parametros else 0.7
        
        # ✨ USAR CONTEXTO MEJORADO CENTRALIZADO
        user_id = "default"
        context = await prepare_enhanced_context(mensaje, user_id)
        
        # Construir mensajes finales
        messages = context["messages"]
        
        # Agregar mensaje del sistema como primer mensaje
        if not messages or len(messages) == 0:
            messages.append({"role": "system", "content": context["system_prompt"]})
        
        # Construir mensaje final del usuario con contexto RAG
        final_message = mensaje + context["rag_context"]
        messages.append({"role": "user", "content": final_message})
        
        # Realizar la consulta
        response = client.chat.completions.create(
            model=modelo,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=messages
        )
        
        respuesta = response.choices[0].message.content
        
        # 💾 GUARDAR EN MEMORIA (sistema híbrido)
        await save_to_memory(mensaje, respuesta, "deepseek")
        
        return respuesta
        
    except ImportError:
        logger.error("La librería 'openai' no está instalada. Instálala con: pip install openai")
        return "Error: Librería OpenAI no disponible"
    except Exception as e:
        logger.error(f"Error al consultar DeepSeek: {e}")
        return f"Error en la consulta: {str(e)}"

# Función: llamada a Gemini
async def chat_gemini(mensaje: str, parametros: Optional[Dict[str, Any]] = None) -> str:
    """
    Realiza una consulta a Gemini usando la API Key.
    """
    try:
        import google.generativeai as genai
        
        # Obtener configuración desde .env
        api_key = get_api_key("gemini")
        modelo = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY no está configurada en el archivo .env")
        
        # Configurar la API de Gemini
        genai.configure(api_key=api_key)
        
        # Crear el modelo
        model = genai.GenerativeModel(modelo)
        
        # Configurar parámetros por defecto
        temperature = parametros.get("temperature", 0.7) if parametros else 0.7
        max_tokens = parametros.get("max_tokens", 1024) if parametros else 1024
        
        # �� USAR CONTEXTO MEJORADO CENTRALIZADO
        user_id = "default"
        context = await prepare_enhanced_context(mensaje, user_id)
        
        # Para Gemini, combinar todo en un solo mensaje
        # Ya que Gemini maneja mejor el contexto de manera diferente
        full_prompt = context["system_prompt"] + "\n\n"
        
        # Añadir historial si existe
        if context["messages"]:
            for msg in context["messages"]:
                role = "Usuario" if msg["role"] == "user" else "Asistente"
                full_prompt += f"{role}: {msg['content']}\n"
        
        # Añadir contexto y mensaje actual
        full_prompt += context["rag_context"] + "\n\nUsuario: " + mensaje + "\nAsistente:"
        
        # Realizar la consulta
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
        )
        
        respuesta = response.text
        
        # 💾 GUARDAR EN MEMORIA (sistema híbrido)
        await save_to_memory(mensaje, respuesta, "gemini")
        
        return respuesta
        
    except ImportError:
        logger.error("La librería 'google-generativeai' no está instalada. Instálala con: pip install google-generativeai")
        return "Error: Librería Google Generative AI no disponible"
    except Exception as e:
        logger.error(f"Error al consultar Gemini: {e}")
        return f"Error en la consulta: {str(e)}"

# Función: llamada a OpenAI
async def chat_openai(mensaje: str, parametros: Optional[Dict[str, Any]] = None) -> str:
    """
    Realiza una consulta a OpenAI usando la API Key.
    """
    try:
        import openai
        
        # Obtener configuración desde .env
        api_key = get_api_key("openai")
        modelo = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY no está configurada en el archivo .env")
        
        # Crear cliente de OpenAI
        client = openai.OpenAI(api_key=api_key)
        
        # Configurar parámetros por defecto
        max_tokens = parametros.get("max_tokens", 1024) if parametros else 1024
        temperature = parametros.get("temperature", 0.7) if parametros else 0.7
        
        # ✨ USAR CONTEXTO MEJORADO CENTRALIZADO
        user_id = "default"
        context = await prepare_enhanced_context(mensaje, user_id)
        
        # Construir mensajes finales
        messages = context["messages"]
        
        # Agregar mensaje del sistema como primer mensaje
        if not messages or len(messages) == 0:
            messages.append({"role": "system", "content": context["system_prompt"]})
        
        # Construir mensaje final del usuario con contexto RAG
        final_message = mensaje + context["rag_context"]
        messages.append({"role": "user", "content": final_message})
        
        # Realizar la consulta
        response = client.chat.completions.create(
            model=modelo,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=messages
        )
        
        respuesta = response.choices[0].message.content
        
        # 💾 GUARDAR EN MEMORIA (sistema híbrido)
        await save_to_memory(mensaje, respuesta, "openai")
        
        return respuesta
        
    except ImportError:
        logger.error("La librería 'openai' no está instalada. Instálala con: pip install openai")
        return "Error: Librería OpenAI no disponible"
    except Exception as e:
        logger.error(f"Error al consultar OpenAI: {e}")
        return f"Error en la consulta: {str(e)}"

# Función: llamada a Ollama (modelo local)
# async def chat_ollama(mensaje: str, parametros: Optional[Dict[str, Any]] = None) -> str:
#     """
#     Realiza una consulta a un modelo local usando Ollama.
#     """
#     # Aquí iría la integración real con Ollama (por ejemplo, vía REST API local)
#     return "[Respuesta simulada de Ollama]"

# Función: seleccionar y llamar al proveedor adecuado
async def obtener_respuesta_llm(mensaje: str, proveedor: str, parametros: Optional[Dict[str, Any]] = None) -> (str, str):
    """
    Selecciona el proveedor LLM y obtiene la respuesta.
    Parámetros:
        mensaje (str): Mensaje del usuario.
        proveedor (str): Nombre del proveedor.
        parametros (dict): Parámetros adicionales.
    Retorna:
        (respuesta, proveedor)
    """
    if proveedor == "anthropic":
        return await chat_anthropic(mensaje, parametros), "anthropic"
    elif proveedor == "deepseek":
        return await chat_deepseek(mensaje, parametros), "deepseek"
    elif proveedor == "gemini":
        return await chat_gemini(mensaje, parametros), "gemini"
    # elif proveedor == "ollama":
    #     return await chat_ollama(mensaje, parametros), "ollama"
    else:
        raise HTTPException(status_code=400, detail=f"Proveedor '{proveedor}' no soportado.")

# Endpoint principal de chat
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint principal para interactuar con el chatbot.
    Permite seleccionar el proveedor LLM y pasar parámetros adicionales.
    """
    proveedor = request.proveedor or get_default_provider()
    logger.info(f"Mensaje recibido: {request.mensaje} | Proveedor: {proveedor}")
    try:
        respuesta, proveedor_usado = await obtener_respuesta_llm(request.mensaje, proveedor, request.parametros)
        return ChatResponse(
            respuesta=respuesta,
            proveedor=proveedor_usado,
            metadatos={"lenguaje": os.getenv("LANGUAGE", "es")}
        )
    except Exception as e:
        logger.error(f"Error en el endpoint /chat: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor.")

# Nuevo endpoint de diagnóstico
@app.get("/memory/status")
async def memory_status():
    """
    Endpoint para diagnosticar el estado del sistema de memoria.
    """
    status = {
        "memoria_basica_disponible": MEMORIA_DISPONIBLE,
        "memoria_avanzada_habilitada": ADVANCED_MEMORY_ENABLED,
        "timestamp": datetime.now().isoformat()
    }
    
    # Estadísticas de memoria básica
    if memoria_conversacional:
        status["memoria_basica"] = {
            "mensajes_en_buffer": len(memoria_conversacional.chat_memory.messages),
            "tipo": "ConversationBufferWindowMemory"
        }
    
    # Estadísticas de memoria avanzada
    if ADVANCED_MEMORY_ENABLED and memoria_avanzada:
        try:
            stats = memoria_avanzada.get_memory_stats()
            status["memoria_avanzada"] = stats
            
            # Contar mensajes del día
            daily_count = await memoria_avanzada.file_manager.count_messages_today()
            status["memoria_avanzada"]["mensajes_hoy"] = daily_count
            
        except Exception as e:
            status["memoria_avanzada"] = {"error": str(e)}
    
    return status

@app.get("/debug/system-status")
async def debug_system_status():
    """
    Endpoint para diagnosticar todos los sistemas del backend.
    """
    status = {
        "timestamp": datetime.now().isoformat(),
        "document_processing": {
            "enabled": DOCUMENT_PROCESSING_ENABLED,
            "manager_initialized": document_manager is not None,
            "error": None
        },
        "agente_ing": {
            "enabled": AGENTE_ING_ENABLED,
            "critical_thinking_initialized": critical_thinking is not None,
            "category_manager_initialized": category_manager is not None,
            "error": None
        },
        "contextual_memory": {
            "enabled": CONTEXTUAL_MEMORY_ENABLED,
            "initialized": contextual_memory is not None,
            "error": None
        }
    }
    
    # Intentar inicializar DocumentManager para ver qué falla
    if not DOCUMENT_PROCESSING_ENABLED:
        try:
            from document_processing import DocumentManager
            test_manager = DocumentManager()
            status["document_processing"]["test_initialization"] = "SUCCESS"
        except Exception as e:
            status["document_processing"]["error"] = str(e)
            status["document_processing"]["test_initialization"] = "FAILED"
    
    # Intentar inicializar AgenteIng para ver qué falla
    if not AGENTE_ING_ENABLED:
        try:
            from memory.critical_thinking import CriticalThinking
            test_critical = CriticalThinking()
            status["agente_ing"]["test_initialization"] = "SUCCESS"
        except Exception as e:
            status["agente_ing"]["error"] = str(e)
            status["agente_ing"]["test_initialization"] = "FAILED"
    
    return status

@app.get("/memory/recent")
async def get_recent_messages(days: int = 7, limit: int = 20):
    """
    Obtiene mensajes recientes del sistema de memoria avanzada.
    """
    if not (ADVANCED_MEMORY_ENABLED and memoria_avanzada):
        raise HTTPException(
            status_code=404, 
            detail="Memoria avanzada no disponible"
        )
    
    try:
        messages = await memoria_avanzada.get_recent_history(days, limit)
        return {
            "total_messages": len(messages),
            "days_searched": days,
            "messages": messages
        }
    except Exception as e:
        logger.error(f"Error obteniendo mensajes recientes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/search")
async def search_semantic_memory(query: str, limit: int = 5):
    """
    Búsqueda semántica en memoria vectorizada.
    """
    if not (ADVANCED_MEMORY_ENABLED and memoria_avanzada):
        raise HTTPException(
            status_code=404,
            detail="Memoria avanzada no disponible"
        )
    
    if not query.strip():
        raise HTTPException(
            status_code=400,
            detail="Query no puede estar vacío"
        )
    
    try:
        results = await memoria_avanzada.search_semantic_memory(query, limit)
        
        return {
            "query": query,
            "total_results": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error en búsqueda semántica: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory/vectorize")
async def force_vectorization():
    """
    Fuerza vectorización manual de mensajes pendientes.
    """
    if not (ADVANCED_MEMORY_ENABLED and memoria_avanzada):
        raise HTTPException(
            status_code=404,
            detail="Memoria avanzada no disponible"
        )
    
    try:
        await memoria_avanzada._trigger_vectorization()
        
        stats = memoria_avanzada.get_memory_stats()
        return {
            "status": "vectorization_triggered",
            "pending_messages": stats.get("pending_messages", 0),
            "message": "Vectorización forzada ejecutada"
        }
    except Exception as e:
        logger.error(f"Error en vectorización forzada: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory/close")
async def close_conversation():
    """
    Cierra la conversación actual y vectoriza mensajes pendientes.
    Útil para asegurar que todos los mensajes se procesen al finalizar una sesión.
    """
    if not (ADVANCED_MEMORY_ENABLED and memoria_avanzada):
        raise HTTPException(
            status_code=404,
            detail="Memoria avanzada no disponible"
        )
    
    try:
        await memoria_avanzada.close_conversation()
        
        stats = memoria_avanzada.get_memory_stats()
        return {
            "status": "conversation_closed",
            "pending_messages": stats.get("pending_messages", 0),
            "message": "Conversación cerrada y mensajes vectorizados"
        }
    except Exception as e:
        logger.error(f"Error cerrando conversación: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# ENDPOINTS DE MEMORIA CONTEXTUAL
# ================================

@app.get("/memory/contextual/status")
async def contextual_memory_status():
    """
    Estado de la memoria contextual con estadísticas.
    """
    if not CONTEXTUAL_MEMORY_ENABLED:
        raise HTTPException(
            status_code=404,
            detail="Memoria contextual no disponible"
        )
    
    try:
        stats = contextual_memory.get_memory_stats()
        return {
            "enabled": True,
            "timestamp": datetime.now().isoformat(),
            **stats
        }
    except Exception as e:
        logger.error(f"Error obteniendo estado de memoria contextual: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/contextual/suggestions")
async def get_document_suggestions(query: str, limit: int = 3):
    """
    Obtiene sugerencias de documentos basadas en contexto.
    """
    if not CONTEXTUAL_MEMORY_ENABLED:
        raise HTTPException(
            status_code=404,
            detail="Memoria contextual no disponible"
        )
    
    try:
        suggestions = await contextual_memory.suggest_relevant_documents(query, limit)
        return {
            "query": query,
            "suggestions": suggestions,
            "total": len(suggestions)
        }
    except Exception as e:
        logger.error(f"Error obteniendo sugerencias: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/contextual/conversations")
async def get_recent_contextual_conversations(days: int = 7, limit: int = 10):
    """
    Obtiene conversaciones recientes con contexto de documentos.
    """
    if not CONTEXTUAL_MEMORY_ENABLED:
        raise HTTPException(
            status_code=404,
            detail="Memoria contextual no disponible"
        )
    
    try:
        conversations = await contextual_memory.get_recent_conversations(days, limit)
        return {
            "conversations": conversations,
            "total": len(conversations),
            "days_searched": days
        }
    except Exception as e:
        logger.error(f"Error obteniendo conversaciones contextuales: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# ENDPOINTS DE PROCESAMIENTO DE DOCUMENTOS
# ================================

@app.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Sube y procesa un documento.
    Formatos soportados: PDF, DOCX, XLSX, TXT, MD
    """
    # Intentar inicializar sistema de documentos si no está habilitado
    if not DOCUMENT_PROCESSING_ENABLED:
        initialize_documents_lazy()
    
    if not DOCUMENT_PROCESSING_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Sistema de procesamiento de documentos no disponible"
        )
    
    try:
        # Validar formato
        file_extension = Path(file.filename).suffix.lower()
        supported_formats = document_manager.get_supported_formats()
        
        if file_extension not in supported_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Formato no soportado. Formatos válidos: {', '.join(supported_formats)}"
            )
        
        # Validar tamaño (50MB máximo)
        max_size = 50 * 1024 * 1024
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > max_size:
            raise HTTPException(
                status_code=413,
                detail="Archivo muy grande. Máximo 50MB permitido."
            )
        
        # Generar ID único
        document_id = str(uuid.uuid4())
        
        # Guardar archivo temporalmente
        upload_path = document_manager.uploads_path / f"{document_id}_{file.filename}"
        
        with open(upload_path, "wb") as f:
            f.write(file_content)
        
        # Procesar documento
        result = await document_manager.process_document(upload_path, document_id)
        
        # Limpiar archivo temporal
        upload_path.unlink()
        
        return DocumentUploadResponse(
            document_id=document_id,
            file_name=file.filename,
            file_type=file_extension.replace(".", ""),
            status="processed",
            message=f"Documento procesado exitosamente. {result['chunk_count']} chunks generados."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error procesando documento: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando documento: {str(e)}")

@app.get("/documents/list", response_model=List[DocumentInfo])
async def list_documents():
    """
    Lista todos los documentos procesados.
    """
    # Intentar inicializar sistema de documentos si no está habilitado
    if not DOCUMENT_PROCESSING_ENABLED:
        initialize_documents_lazy()
    
    if not DOCUMENT_PROCESSING_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Sistema de procesamiento de documentos no disponible"
        )
    
    try:
        documents = await document_manager.list_documents()
        return [DocumentInfo(**doc) for doc in documents]
        
    except Exception as e:
        logger.error(f"Error listando documentos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{document_id}")
async def get_document(document_id: str):
    """
    Obtiene información detallada de un documento específico.
    """
    if not DOCUMENT_PROCESSING_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Sistema de procesamiento de documentos no disponible"
        )
    
    try:
        document = await document_manager.get_document(document_id)
        
        if not document:
            raise HTTPException(
                status_code=404,
                detail="Documento no encontrado"
            )
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo documento {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """
    Elimina un documento procesado.
    """
    if not DOCUMENT_PROCESSING_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Sistema de procesamiento de documentos no disponible"
        )
    
    try:
        success = await document_manager.delete_document(document_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Documento no encontrado"
            )
        
        return {"message": f"Documento {document_id} eliminado exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando documento {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{document_id}/chunks")
async def get_document_chunks(document_id: str, chunk_type: Optional[str] = None):
    """
    Obtiene los chunks de un documento específico.
    """
    if not DOCUMENT_PROCESSING_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Sistema de procesamiento de documentos no disponible"
        )
    
    try:
        chunks = await document_manager.get_document_chunks(document_id, chunk_type)
        
        return {
            "document_id": document_id,
            "chunk_count": len(chunks),
            "chunks": chunks
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo chunks del documento {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/documents/search")
async def search_documents(request: DocumentSearchRequest):
    """
    Busca contenido en documentos vectorizados.
    """
    initialize_documents_lazy()
    if not DOCUMENT_PROCESSING_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Sistema de procesamiento de documentos no disponible"
        )
    
    try:
        results = await document_manager.search_documents(
            query=request.query,
            document_id=request.document_id,
            limit=request.limit or 5
        )
        
        return {"results": results}
        
    except Exception as e:
        logger.error(f"Error en búsqueda de documentos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test/motorola/{modelo}")
async def test_motorola_search(modelo: str):
    """
    🧪 ENDPOINT DE PRUEBA: Buscar modelo específico de Motorola
    """
    initialize_documents_lazy()
    if not DOCUMENT_PROCESSING_ENABLED:
        return {"error": "Sistema no disponible"}
    
    try:
        # Búsqueda optimizada
        search_query = f"Motorola {modelo}"
        results = await document_manager.search_documents(search_query, limit=3)
        
        # Procesar resultados
        processed_results = []
        for result in results:
            content = result.get('content', '')
            file_name = result.get('metadata', {}).get('file_name', '')
            
            if 'Motorola' in file_name and modelo.upper() in content.upper():
                processed_results.append({
                    "found": True,
                    "model": modelo,
                    "content": content,
                    "similarity": result.get('similarity', 0)
                })
        
        # Construir respuesta final
        if processed_results:
            first_result = processed_results[0]
            content = first_result['content']
            
            # Extraer precio si es formato conocido
            import re
            price_match = re.search(r"'Columna_2': '(\d+)'", content)
            precio = price_match.group(1) if price_match else "No disponible"
            
            return {
                "success": True,
                "modelo": modelo,
                "precio": f"${precio}",
                "detalles": content,
                "respuesta": f"El precio del Motorola {modelo} es ${precio} según la información disponible.",
                "raw_results": processed_results
            }
        else:
            return {
                "success": False,
                "modelo": modelo,
                "mensaje": f"No se encontró información sobre el modelo {modelo}",
                "all_results": results
            }
            
    except Exception as e:
        return {"error": str(e)}


@app.get("/test/context/{query}")
async def test_context_building(query: str):
    """
    🧪 ENDPOINT DE PRUEBA: Ver cómo se construye el contexto RAG
    """
    initialize_documents_lazy()
    if not DOCUMENT_PROCESSING_ENABLED:
        return {"error": "Sistema no disponible"}
    
    try:
        # Simular búsqueda como en el chat
        import re
        
        search_query = query
        model_patterns = [
            r'\bE\d+[A-Za-z]*\b',
            r'\bG\s*\w+\b',
            r'\bEdge\s*\w*\b',
            r'\bOne\s*\w*\b'
        ]
        
        extracted_models = []
        for pattern in model_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            extracted_models.extend(matches)
        
        if extracted_models:
            search_query = f"Motorola {' '.join(extracted_models)}"
        
        # Buscar documentos
        doc_results = await document_manager.search_documents(search_query, limit=3)
        
        # Construir contexto como en el chat
        document_context = ""
        if doc_results:
            document_context = "\n\nCONTEXTO DE DOCUMENTOS:\n"
            for i, result in enumerate(doc_results, 1):
                file_name = result.get('metadata', {}).get('file_name', 'Sin nombre')
                content = result.get('content', '')
                
                if 'Motorola' in file_name and 'Columna_1' in content:
                    document_context += f"\n{i}. Archivo: {file_name} (Catálogo de productos Motorola)\n"
                    document_context += f"   📱 PRODUCTO: {content}\n"
                    document_context += f"   💡 FORMATO: Columna_1=Modelo, Columna_2=Precio, Columna_3=Tipo, Columna_4=Stock\n"
                else:
                    document_context += f"\n{i}. Archivo: {file_name}\n"
                    document_context += f"   Contenido: {content[:200]}...\n"
        
        return {
            "original_query": query,
            "optimized_query": search_query,
            "extracted_models": extracted_models,
            "context": document_context,
            "raw_results": doc_results
        }
        
    except Exception as e:
        return {"error": str(e)}

# =============================================================================
# 🤖 ENDPOINTS AGENTE ING - Sistema de Memoria Inteligente
# =============================================================================

@app.get("/agente/stats", response_model=MemoryStatusResponse)
async def get_agente_stats():
    """
    Endpoint de estadísticas de AgenteIng (alias de /agente/status para compatibilidad frontend).
    """
    return await get_agente_status()

@app.get("/agente/status", response_model=MemoryStatusResponse)
async def get_agente_status():
    """
    Obtiene el estado del sistema AgenteIng.
    """
    # Intentar inicializar sistema AgenteIng si no está habilitado
    if not AGENTE_ING_ENABLED:
        initialize_agente_ing_lazy()
    
    if not AGENTE_ING_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Sistema AgenteIng no disponible"
        )
    
    try:
        buffer_status = critical_thinking.get_buffer_status()
        category_stats = category_manager.get_category_statistics()
        pending_review = critical_thinking.get_pending_review_items()
        active_alerts = proactive_assistant.get_active_alerts()
        
        return MemoryStatusResponse(
            critical_thinking_enabled=True,
            buffer_status=buffer_status,
            category_stats=category_stats,
            active_alerts_count=len(active_alerts),
            pending_review_count=len(pending_review)
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo estado AgenteIng: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agente/categories", response_model=CategoryResponse)
async def get_categories():
    """
    Obtiene todas las categorías disponibles y sus estadísticas.
    """
    # Intentar inicializar sistema AgenteIng si no está habilitado
    if not AGENTE_ING_ENABLED:
        initialize_agente_ing_lazy()
    
    if not AGENTE_ING_ENABLED:
        raise HTTPException(status_code=503, detail="Sistema AgenteIng no disponible")
    
    try:
        all_categories = category_manager.get_all_categories()
        stats = category_manager.get_category_statistics()
        
        categories_list = []
        for cat_name, cat_config in all_categories.items():
            categories_list.append({
                'id': cat_config.name,
                'name': cat_config.name,
                'displayName': cat_config.display_name,
                'description': cat_config.description,
                'enabled': cat_config.enabled,
                'subcategories': cat_config.subcategories
            })
        
        return CategoryResponse(
            categories=categories_list,
            stats=stats
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo categorías: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agente/categories/configure")
async def configure_category(request: CategoryConfigRequest):
    """
    Habilita o deshabilita una categoría opcional.
    """
    if not AGENTE_ING_ENABLED:
        raise HTTPException(status_code=503, detail="Sistema AgenteIng no disponible")
    
    try:
        if request.enabled:
            success = category_manager.enable_optional_category(request.category_name)
        else:
            success = category_manager.disable_optional_category(request.category_name)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"No se pudo {'habilitar' if request.enabled else 'deshabilitar'} la categoría"
            )
        
        return {
            "success": True,
            "message": f"Categoría {request.category_name} {'habilitada' if request.enabled else 'deshabilitada'} exitosamente"
        }
        
    except Exception as e:
        logger.error(f"Error configurando categoría: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agente/process-file", response_model=FileAnalysisResponse)
async def process_file(request: FileAnalysisRequest):
    """
    Procesa un archivo para análisis y categorización (alias de analyze_file para compatibilidad frontend).
    """
    return await analyze_file(request)

@app.post("/agente/analyze/file", response_model=FileAnalysisResponse)
async def analyze_file(request: FileAnalysisRequest):
    """
    Analiza un archivo para sugerir categorización automática.
    """
    if not AGENTE_ING_ENABLED:
        raise HTTPException(status_code=503, detail="Sistema AgenteIng no disponible")
    
    try:
        # Primero intentar encontrar el documento en los archivos procesados
        document_id = None
        content_to_analyze = None
        file_info = None
        
        # Extraer ID del documento desde el nombre del archivo si es posible
        file_path_str = str(request.file_path)
        if "_" in file_path_str:
            potential_id = file_path_str.split("_")[0].split("/")[-1]
            if len(potential_id) == 36:  # UUID length
                document_id = potential_id
        
        # Buscar el documento procesado
        if document_id:
            processed_file = Path("data/documents/processed") / f"{document_id}.json"
            if processed_file.exists():
                try:
                    with open(processed_file, 'r', encoding='utf-8') as f:
                        processed_data = json.load(f)
                    
                    content_to_analyze = processed_data.get('extraction_result', {}).get('content', '')
                    file_info = {
                        'name': processed_data.get('file_name', request.file_name),
                        'size': len(content_to_analyze),
                        'type': processed_data.get('file_type', 'unknown'),
                        'processed_at': processed_data.get('processed_at', datetime.now().isoformat())
                    }
                    logger.info(f"Usando contenido procesado para documento {document_id}")
                except Exception as e:
                    logger.warning(f"Error leyendo documento procesado {document_id}: {e}")
        
        # Si no encontramos el documento procesado, intentar analizar el archivo original
        if not content_to_analyze:
            logger.info(f"No se encontró documento procesado, intentando archivo original: {request.file_path}")
            analysis_result = content_analyzer.analyze_document(
                file_path=request.file_path,
                file_name=request.file_name
            )
            return FileAnalysisResponse(**analysis_result)
        
        # Analizar el contenido usando una conversación simulada
        simulated_messages = [
            {'role': 'user', 'content': content_to_analyze[:5000]}  # Limitar a primeros 5000 chars
        ]
        
        analysis_result = content_analyzer.analyze_conversation(simulated_messages)
        
        # Ajustar el resultado para incluir file_info
        if file_info:
            analysis_result['file_info'] = file_info
        
        # Asegurar que todos los campos requeridos estén presentes
        if 'reasoning' not in analysis_result:
            analysis_result['reasoning'] = f"Análisis basado en contenido procesado del documento"
        if 'alternative_categories' not in analysis_result:
            analysis_result['alternative_categories'] = []
        
        return FileAnalysisResponse(**analysis_result)
        
    except Exception as e:
        logger.error(f"Error analizando archivo: {e}")
        # Retornar respuesta válida en caso de error
        return FileAnalysisResponse(
            success=False,
            error=str(e),
            file_info=None,
            suggested_category='personal',
            confidence=0.1,
            reasoning=f'Error al procesar archivo: {str(e)}',
            alternative_categories=[]
        )

@app.post("/agente/analyze/conversation")
async def analyze_conversation(request: ConversationAnalysisRequest):
    """
    Analiza una conversación para sugerir categorización.
    """
    if not AGENTE_ING_ENABLED:
        raise HTTPException(status_code=503, detail="Sistema AgenteIng no disponible")
    
    try:
        analysis_result = content_analyzer.analyze_conversation(request.messages)
        
        return {
            "success": analysis_result['success'],
            "suggested_category": analysis_result['suggested_category'],
            "confidence": analysis_result['confidence'],
            "reasoning": analysis_result['reasoning'],
            "conversation_info": analysis_result.get('conversation_info', {}),
            "content_summary": analysis_result.get('content_summary', ''),
            "alternative_categories": analysis_result.get('alternative_categories', [])
        }
        
    except Exception as e:
        logger.error(f"Error analizando conversación: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agente/approve/categorization")
async def approve_categorization(request: CategoryApprovalRequest):
    """
    Aprueba una categorización sugerida y almacena el item.
    """
    if not AGENTE_ING_ENABLED:
        raise HTTPException(status_code=503, detail="Sistema AgenteIng no disponible")
    
    try:
        success = critical_thinking.approve_pending_item(
            item_id=request.file_id,
            category=request.approved_category
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Item no encontrado o ya procesado"
            )
        
        return {
            "success": True,
            "message": f"Item categorizado como '{request.approved_category}' exitosamente"
        }
        
    except Exception as e:
        logger.error(f"Error aprobando categorización: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agente/alerts", response_model=ProactiveAlertsResponse)
async def get_proactive_alerts():
    """
    Obtiene alertas proactivas del asistente.
    """
    if not AGENTE_ING_ENABLED:
        raise HTTPException(status_code=503, detail="Sistema AgenteIng no disponible")
    
    try:
        # Verificar nuevas oportunidades proactivas
        new_opportunities = proactive_assistant.check_proactive_opportunities()
        
        # Obtener todas las alertas activas
        active_alerts = proactive_assistant.get_active_alerts()
        
        # Obtener contexto del usuario
        user_context = proactive_assistant.get_user_context_summary()
        
        return ProactiveAlertsResponse(
            alerts=active_alerts,
            user_context=user_context
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo alertas proactivas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agente/alerts/action")
async def handle_alert_action(request: AlertActionRequest):
    """
    Maneja acciones sobre alertas (descartar, marcar como vista).
    """
    if not AGENTE_ING_ENABLED:
        raise HTTPException(status_code=503, detail="Sistema AgenteIng no disponible")
    
    try:
        if request.action == 'dismiss':
            success = proactive_assistant.dismiss_alert(request.alert_id)
        elif request.action == 'mark_shown':
            success = proactive_assistant.mark_alert_shown(request.alert_id)
        else:
            raise HTTPException(
                status_code=400,
                detail="Acción no válida. Use 'dismiss' o 'mark_shown'"
            )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Alerta no encontrada"
            )
        
        return {
            "success": True,
            "message": f"Acción '{request.action}' ejecutada exitosamente"
        }
        
    except Exception as e:
        logger.error(f"Error manejando acción de alerta: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agente/pending-review")
async def get_pending_review_items():
    """
    Obtiene items que requieren revisión manual.
    """
    if not AGENTE_ING_ENABLED:
        raise HTTPException(status_code=503, detail="Sistema AgenteIng no disponible")
    
    try:
        pending_items = critical_thinking.get_pending_review_items()
        
        return {
            "pending_items": pending_items,
            "count": len(pending_items)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo items pendientes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agente/force-process")
async def force_process_buffer():
    """
    Fuerza el procesamiento de todos los elementos en el buffer de pensamiento crítico.
    """
    if not AGENTE_ING_ENABLED:
        raise HTTPException(status_code=503, detail="Sistema AgenteIng no disponible")
    
    try:
        critical_thinking.force_process_all()
        
        return {
            "success": True,
            "message": "Procesamiento forzado completado"
        }
        
    except Exception as e:
        logger.error(f"Error en procesamiento forzado: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agente/categories/{category_name}/contents")
async def get_category_contents(category_name: str, content_type: Optional[str] = None):
    """
    Obtiene el contenido de una categoría específica.
    """
    if not AGENTE_ING_ENABLED:
        raise HTTPException(status_code=503, detail="Sistema AgenteIng no disponible")
    
    try:
        contents = category_manager.get_category_contents(category_name, content_type)
        
        return {
            "category": category_name,
            "content_type": content_type or "all",
            "items": contents,
            "count": len(contents)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo contenido de categoría: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agente/search")
async def search_across_categories(query: str, categories: Optional[str] = None):
    """
    Busca contenido a través de múltiples categorías.
    """
    if not AGENTE_ING_ENABLED:
        raise HTTPException(status_code=503, detail="Sistema AgenteIng no disponible")
    
    try:
        search_categories = categories.split(',') if categories else None
        results = category_manager.search_across_categories(query, search_categories)
        
        return {
            "query": query,
            "categories_searched": search_categories or "all",
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# ENDPOINTS DE PERSONALIDAD CONFIGURABLE
# ================================

@app.get("/personality/config", response_model=PersonalityResponse)
async def get_personality_config_endpoint(user_id: str = "default"):
    """
    Obtiene la configuración de personalidad actual para un usuario.
    """
    try:
        config = get_personality_config(user_id)
        return PersonalityResponse(
            success=True,
            personality=config,
            message="Configuración de personalidad obtenida exitosamente"
        )
    except Exception as e:
        logger.error(f"Error obteniendo configuración de personalidad: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/personality/config", response_model=PersonalityResponse)
async def update_personality_config_endpoint(
    request: PersonalityUpdateRequest, 
    user_id: str = "default"
):
    """
    Actualiza la configuración de personalidad para un usuario.
    """
    try:
        # Validar entrada
        if not request.personality_text.strip():
            raise HTTPException(
                status_code=400, 
                detail="El texto de personalidad no puede estar vacío"
            )
        
        # Crear nueva configuración
        new_config = PersonalityConfig(
            user_id=user_id,
            personality_text=request.personality_text.strip(),
            tone=request.tone or "neutral",
            response_style=request.response_style or "balanced",
            enabled=True
        )
        
        # Guardar configuración
        success = save_personality_config(user_id, new_config)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Error guardando configuración de personalidad"
            )
        
        return PersonalityResponse(
            success=True,
            personality=new_config,
            message="Configuración de personalidad actualizada exitosamente"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando configuración de personalidad: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/personality/config")
async def reset_personality_config_endpoint(user_id: str = "default"):
    """
    Restaura la configuración de personalidad por defecto para un usuario.
    """
    try:
        # Eliminar configuración personalizada (volverá al default)
        if user_id in personality_configs:
            del personality_configs[user_id]
        
        # Obtener configuración por defecto
        default_config = get_personality_config(user_id)
        
        return PersonalityResponse(
            success=True,
            personality=default_config,
            message="Configuración de personalidad restaurada al valor por defecto"
        )
        
    except Exception as e:
        logger.error(f"Error restaurando configuración de personalidad: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/personality/toggle")
async def toggle_personality_endpoint(user_id: str = "default"):
    """
    Habilita o deshabilita la personalidad personalizada para un usuario.
    """
    try:
        config = get_personality_config(user_id)
        config.enabled = not config.enabled
        
        success = save_personality_config(user_id, config)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Error actualizando estado de personalidad"
            )
        
        status = "habilitada" if config.enabled else "deshabilitada"
        
        return {
            "success": True,
            "enabled": config.enabled,
            "message": f"Personalidad personalizada {status} exitosamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cambiando estado de personalidad: {e}")
        raise HTTPException(status_code=500, detail=str(e))