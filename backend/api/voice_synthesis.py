"""
Endpoint para síntesis de voz usando ElevenLabs.
Actúa como proxy seguro para la API de ElevenLabs con caching y optimizaciones.
"""

import os
import asyncio
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Configuración
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_01cea666c20e2b4d2e4e31907af90c4d016652b8331ed2f1")
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io"
CACHE_DIR = Path("cache/audio")
CACHE_DURATION_HOURS = 24
MAX_CACHE_SIZE_MB = 100

# Crear directorio de cache
CACHE_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/voice", tags=["voice_synthesis"])


class TextToSpeechRequest(BaseModel):
    text: str
    voice_id: Optional[str] = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
    voice_settings: Optional[Dict[str, Any]] = None
    model_id: Optional[str] = "eleven_turbo_v2"
    pronunciation_dictionary: Optional[bool] = True
    emotional_context: Optional[str] = "friendly"
    stream: Optional[bool] = False


class VoiceSettings(BaseModel):
    stability: float = 0.75
    similarity_boost: float = 0.85
    style: float = 0.65
    use_speaker_boost: bool = True


def get_cache_key(text: str, voice_id: str, settings: Dict) -> str:
    """Genera una clave única para el cache basada en el contenido."""
    content = f"{text}_{voice_id}_{str(sorted(settings.items()))}"
    return hashlib.md5(content.encode()).hexdigest()


def enhance_text_for_natural_speech(text: str) -> str:
    """
    Mejora el texto con controles de habla natural y marcadores emocionales.
    """
    enhanced = text

    # Añadir pausas naturales después de puntuación
    enhanced = enhanced.replace('. ', '.<break time="0.5s"/> ')
    enhanced = enhanced.replace('! ', '!<break time="0.5s"/> ')
    enhanced = enhanced.replace('? ', '?<break time="0.5s"/> ')
    enhanced = enhanced.replace(', ', ',<break time="0.3s"/> ')
    enhanced = enhanced.replace('; ', ';<break time="0.3s"/> ')
    enhanced = enhanced.replace(': ', ':<break time="0.3s"/> ')

    # Añadir énfasis para ciertos patrones
    enhanced = enhanced.replace('**', '')  # Remover markdown bold
    enhanced = enhanced.replace('*', '')   # Remover markdown italic

    # Manejar términos técnicos que pueden necesitar ayuda de pronunciación
    technical_terms = {
        'API': '<phoneme alphabet="ipa" ph="eɪ piː aɪ">API</phoneme>',
        'HTTP': '<phoneme alphabet="ipa" ph="eɪtʃ tiː tiː piː">HTTP</phoneme>',
        'JSON': '<phoneme alphabet="ipa" ph="dʒeɪsən">JSON</phoneme>',
        'URL': '<phoneme alphabet="ipa" ph="juː ɑr ɛl">URL</phoneme>',
        'ChatIng': '<phoneme alphabet="ipa" ph="tʃæt ɪŋ">ChatIng</phoneme>',
        'SQL': '<phoneme alphabet="ipa" ph="ɛs kjuː ɛl">SQL</phoneme>'
    }

    for term, pronunciation in technical_terms.items():
        enhanced = enhanced.replace(term, pronunciation)

    return enhanced


def get_voice_settings_for_context(context: str) -> VoiceSettings:
    """
    Ajusta configuraciones de voz para diferentes contextos emocionales.
    """
    base_settings = VoiceSettings()

    context_settings = {
        'excited': VoiceSettings(
            stability=0.65,
            similarity_boost=0.85,
            style=0.85,
            use_speaker_boost=True
        ),
        'calm': VoiceSettings(
            stability=0.85,
            similarity_boost=0.85,
            style=0.45,
            use_speaker_boost=True
        ),
        'professional': VoiceSettings(
            stability=0.80,
            similarity_boost=0.85,
            style=0.55,
            use_speaker_boost=True
        ),
        'friendly': VoiceSettings(
            stability=0.70,
            similarity_boost=0.85,
            style=0.75,
            use_speaker_boost=True
        ),
        'helpful': VoiceSettings(
            stability=0.75,
            similarity_boost=0.85,
            style=0.65,
            use_speaker_boost=True
        )
    }

    return context_settings.get(context, base_settings)


def detect_emotional_context(text: str) -> str:
    """
    Detecta el contexto emocional del texto para ajustar la voz.
    """
    lower_text = text.lower()
    
    if any(word in lower_text for word in ['error', 'problema', 'sorry', 'disculpa']):
        return 'calm'
    
    if '!' in text and any(word in lower_text for word in ['genial', 'perfecto', 'excelente', 'fantástico']):
        return 'excited'
    
    if any(word in lower_text for word in ['técnico', 'configuración', 'código', 'sistema']):
        return 'professional'
    
    if any(word in lower_text for word in ['hola', 'gracias', 'bueno', 'bienvenido']):
        return 'friendly'
    
    return 'helpful'


def clean_cache():
    """
    Limpia archivos de cache antiguos para mantener el tamaño bajo control.
    """
    try:
        current_time = datetime.now()
        total_size = 0
        files_to_remove = []

        for cache_file in CACHE_DIR.glob("*.mp3"):
            file_age = current_time - datetime.fromtimestamp(cache_file.stat().st_mtime)
            file_size = cache_file.stat().st_size
            total_size += file_size

            # Marcar archivos antiguos para eliminación
            if file_age > timedelta(hours=CACHE_DURATION_HOURS):
                files_to_remove.append(cache_file)

        # Eliminar archivos antiguos
        for file_path in files_to_remove:
            file_path.unlink()
            total_size -= file_path.stat().st_size

        # Si el cache sigue siendo muy grande, eliminar archivos más antiguos
        if total_size > MAX_CACHE_SIZE_MB * 1024 * 1024:
            cache_files = sorted(CACHE_DIR.glob("*.mp3"), key=lambda x: x.stat().st_mtime)
            for cache_file in cache_files:
                if total_size <= MAX_CACHE_SIZE_MB * 1024 * 1024:
                    break
                total_size -= cache_file.stat().st_size
                cache_file.unlink()

        logger.info(f"Cache cleaned. Current size: {total_size / (1024*1024):.2f} MB")

    except Exception as e:
        logger.error(f"Error cleaning cache: {e}")


@router.post("/text-to-speech")
async def text_to_speech(request: TextToSpeechRequest):
    """
    Convierte texto a voz usando ElevenLabs con cache y optimizaciones.
    Soporta streaming de audio.
    """
    try:
        # Validar entrada
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="El texto no puede estar vacío")

        if len(request.text) > 5000:
            raise HTTPException(status_code=400, detail="El texto es demasiado largo (máximo 5000 caracteres)")

        # Detectar contexto emocional si no se especifica
        if not request.voice_settings:
            detected_context = request.emotional_context or detect_emotional_context(request.text)
            context_settings = get_voice_settings_for_context(detected_context)
            voice_settings = context_settings.dict()
        else:
            voice_settings = request.voice_settings

        # Mejorar texto para habla natural
        enhanced_text = enhance_text_for_natural_speech(request.text)

        # Generar clave de cache
        cache_key = get_cache_key(enhanced_text, request.voice_id, voice_settings)
        cache_file = CACHE_DIR / f"{cache_key}.mp3"

        # Verificar cache (solo para no-streaming)
        if not request.stream and cache_file.exists():
            logger.info(f"Cache hit for audio: {cache_key}")
            
            def iterfile():
                with open(cache_file, "rb") as file_like:
                    yield from file_like

            return StreamingResponse(
                iterfile(),
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": "inline; filename=speech.mp3",
                    "Cache-Control": "public, max-age=3600"
                }
            )

        # Limpiar cache periódicamente
        clean_cache()

        # Preparar request para ElevenLabs
        elevenlabs_payload = {
            "text": enhanced_text,
            "voice_settings": voice_settings,
            "model_id": request.model_id
        }

        # Función para streamear audio desde ElevenLabs
        async def stream_audio_from_elevenlabs():
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{ELEVENLABS_BASE_URL}/v1/text-to-speech/{request.voice_id}?output_format=mp3_44100_128",
                    headers={
                        "Accept": "audio/mpeg",
                        "Content-Type": "application/json",
                        "xi-api-key": ELEVENLABS_API_KEY
                    },
                    json=elevenlabs_payload
                ) as response:
                    if response.status_code != 200:
                        error_detail = f"ElevenLabs API error: {response.status_code}"
                        try:
                            error_data = await response.aread()
                            error_detail += f" - {error_data.decode()}"
                        except:
                            pass
                        logger.error(error_detail)
                        # No podemos lanzar HTTPException aquí porque la respuesta ya ha comenzado
                        # El cliente tendrá que manejar la interrupción del stream
                        return

                    # Stream y cache al mismo tiempo
                    audio_chunks = []
                    async for chunk in response.aiter_bytes():
                        audio_chunks.append(chunk)
                        yield chunk
                    
                    # Guardar en cache después de un stream exitoso
                    if not cache_file.exists():
                        try:
                            with open(cache_file, "wb") as f:
                                f.write(b"".join(audio_chunks))
                            logger.info(f"Audio cached after streaming: {cache_key}")
                        except Exception as e:
                            logger.warning(f"Failed to cache audio after streaming: {e}")

        # Si se solicita streaming
        if request.stream:
            return StreamingResponse(
                stream_audio_from_elevenlabs(),
                media_type="audio/mpeg",
                headers={"Content-Disposition": "inline; filename=speech.mp3"}
            )

        # Si no se solicita streaming (comportamiento original)
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{ELEVENLABS_BASE_URL}/v1/text-to-speech/{request.voice_id}",
                headers={
                    "Accept": "audio/mpeg",
                    "Content-Type": "application/json",
                    "xi-api-key": ELEVENLABS_API_KEY
                },
                json=elevenlabs_payload
            )

            if response.status_code != 200:
                error_detail = f"ElevenLabs API error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_detail += f" - {error_data.get('detail', 'Unknown error')}"
                except:
                    error_detail += f" - {response.text}"
                
                logger.error(error_detail)
                raise HTTPException(status_code=500, detail=error_detail)

            # Guardar en cache
            audio_content = response.content
            if not cache_file.exists():
                try:
                    with open(cache_file, "wb") as f:
                        f.write(audio_content)
                    logger.info(f"Audio cached: {cache_key}")
                except Exception as e:
                    logger.warning(f"Failed to cache audio: {e}")

            # Retornar audio
            def stream_audio_content():
                yield audio_content

            return StreamingResponse(
                stream_audio_content(),
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": "inline; filename=speech.mp3",
                    "Cache-Control": "public, max-age=3600"
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in text-to-speech: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")


@router.get("/voices")
async def get_voices():
    """
    Obtiene la lista de voces disponibles de ElevenLabs.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{ELEVENLABS_BASE_URL}/v1/voices",
                headers={"xi-api-key": ELEVENLABS_API_KEY}
            )

            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Error al obtener voces de ElevenLabs")

            return response.json()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.delete("/cache")
async def clear_cache():
    """
    Limpia manualmente el cache de audio.
    """
    try:
        removed_count = 0
        for cache_file in CACHE_DIR.glob("*.mp3"):
            cache_file.unlink()
            removed_count += 1

        return {
            "message": f"Cache limpiado exitosamente. {removed_count} archivos eliminados.",
            "removed_files": removed_count
        }

    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Error limpiando el cache")


@router.get("/cache/stats")
async def get_cache_stats():
    """
    Obtiene estadísticas del cache de audio.
    """
    try:
        file_count = len(list(CACHE_DIR.glob("*.mp3")))
        total_size = sum(f.stat().st_size for f in CACHE_DIR.glob("*.mp3"))
        
        return {
            "cache_directory": str(CACHE_DIR),
            "file_count": file_count,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "max_size_mb": MAX_CACHE_SIZE_MB,
            "cache_duration_hours": CACHE_DURATION_HOURS
        }

    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo estadísticas del cache")