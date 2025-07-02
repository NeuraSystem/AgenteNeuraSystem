# backend/

Esta carpeta contiene la lógica principal del chatbot, incluyendo:
- API (por ejemplo, FastAPI o Flask)
- Integración con modelos LLM y embeddings locales
- Gestión de memoria (episódica, semántica, procedimental)
- Integración con ChromaDB
- Hooks para futuras integraciones de voz (TTS/STT)

## Estructura sugerida
- `api/` : Endpoints y lógica de la API
- `embeddings/` : Adaptadores y carga de modelos de embeddings
- `memory/` : Módulos de memoria conversacional y semántica
- `tools/` : Integración de herramientas y automatizaciones
- `utils/` : Utilidades y funciones auxiliares

## Documentación de funciones y módulos
Cada archivo y función debe tener un encabezado y docstring explicativo. Ejemplo:

```python
# Función: cargar_embeddings_locales
"""
Carga el modelo de embeddings local (MiniLM) usando sentence-transformers y lo adapta para LangChain.
Parámetros:
    model_path (str): Ruta al modelo local.
Retorna:
    embeddings (obj): Objeto de embeddings compatible con LangChain.
"""
```

## Pendientes
- Crear subcarpetas y archivos base.
- Implementar módulos y funciones siguiendo la documentación y comentarios.
- Definir parámetros configurables por el usuario. 