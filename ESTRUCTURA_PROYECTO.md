# ChatIng 2.0 - Estructura del Proyecto

## 📋 Estructura Jerárquica del Proyecto

```
chating2.0/
├── backend/                              # 🐍 Servidor Python FastAPI
│   ├── api/                              # 📡 Endpoints REST
│   │   ├── main.py                       # Endpoint principal /chat con multi-LLM
│   │   └── voice_synthesis.py           # API de síntesis de voz con ElevenLabs
│   ├── ai/                               # 🧠 Módulos de IA
│   │   ├── content_analyzer.py           # Análisis inteligente de contenido
│   │   └── __init__.py
│   ├── document_processing/              # 📄 Sistema RAG de documentos
│   │   ├── extractors/                   # 🔧 Extractores de contenido
│   │   │   ├── base_extractor.py         # Clase base para extractores
│   │   │   ├── pdf_extractor.py          # Extractor PDF con PyPDF2
│   │   │   ├── docx_extractor.py         # Extractor Word
│   │   │   ├── xlsx_extractor.py         # 🔥 Extractor Excel "Una Fila = Un Documento"
│   │   │   ├── txt_extractor.py          # Extractor texto plano
│   │   │   └── __init__.py
│   │   ├── chunkers/                     # ✂️ Fragmentación de contenido
│   │   │   ├── text_chunker.py           # Chunking inteligente de texto
│   │   │   ├── table_chunker.py          # Chunking para datos tabulares
│   │   │   └── __init__.py
│   │   ├── analyzers/                    # 🔍 Análisis de contenido
│   │   │   └── __init__.py
│   │   ├── document_manager.py           # Gestor principal de documentos
│   │   ├── document_vector_manager.py    # 🔥 Gestión de vectores con sanitización
│   │   ├── semantic_reranker.py          # Re-ranking semántico
│   │   └── __init__.py
│   ├── memory/                           # 🧠 Sistema de memoria avanzada
│   │   ├── episodic.py                   # Memoria episódica con LangChain
│   │   ├── semantic.py                   # Memoria semántica
│   │   ├── category_manager.py           # Categorización automática
│   │   ├── critical_thinking.py          # Pensamiento crítico
│   │   ├── proactive_assistant.py        # Asistente proactivo
│   │   ├── document_contextual_memory.py # Memoria contextual
│   │   └── __init__.py
│   ├── storage/                          # 💾 Gestión de almacenamiento
│   │   ├── vector_manager.py             # 🔥 Vectores híbridos (local + Gemini)
│   │   ├── file_manager.py               # Gestión de archivos
│   │   ├── onnx_embeddings.py            # Embeddings ONNX fallback
│   │   └── __init__.py
│   ├── utils/                            # 🛠️ Utilidades
│   │   ├── config.py                     # Configuración centralizada
│   │   └── logger.py                     # Sistema de logging
│   ├── data/                             # 📁 Datos persistentes
│   │   ├── documents/                    # 📄 Documentos procesados
│   │   │   ├── uploads/                  # Archivos subidos
│   │   │   ├── processed/                # Documentos procesados
│   │   │   └── temp/                     # Archivos temporales
│   │   ├── chromadb/                     # 🗄️ Base de datos vectorial
│   │   ├── categories/                   # 🏷️ Sistema de categorización
│   │   │   ├── personal/                 # Categoría personal
│   │   │   ├── familiar/                 # Categoría familiar
│   │   │   └── social/                   # Categoría social
│   │   ├── contextual_memory/            # 🔗 Memoria contextual
│   │   └── critical_thinking/            # 🤔 Pensamiento crítico
│   ├── models/                           # 🤖 Modelos ML locales
│   │   └── embeddings/                   # 📊 Modelos de embeddings
│   │       └── models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2/
│   ├── run.py                            # 🚀 Script principal del servidor
│   ├── requirements-final.txt            # 📦 Dependencias Python
│   ├── .env                              # 🔐 Variables de entorno
│   ├── .env.example                      # 📝 Plantilla de variables
│   ├── activate.sh                       # 🔧 Script de activación venv
│   └── README.md                         # 📖 Documentación backend
├── frontend/                             # ⚛️ Cliente React TypeScript
│   ├── src/                              # 📁 Código fuente
│   │   ├── components/                   # 🧩 Componentes React
│   │   │   ├── chat/                     # 💬 Interfaz de chat
│   │   │   ├── file-upload/              # 📤 Subida de archivos
│   │   │   ├── file-manager/             # 📂 Gestión de documentos
│   │   │   ├── memory/                   # 🧠 Interfaz de memoria
│   │   │   ├── voice/                    # 🎙️ Sistema de voz
│   │   │   └── ui/                       # 🎨 Componentes UI base
│   │   ├── hooks/                        # 🎣 Custom hooks
│   │   ├── services/                     # 🌐 Servicios API
│   │   ├── stores/                       # 🏪 Gestión de estado
│   │   ├── types/                        # 📝 Tipos TypeScript
│   │   ├── utils/                        # 🛠️ Utilidades frontend
│   │   └── styles/                       # 🎨 Estilos
│   ├── public/                           # 🌍 Archivos estáticos
│   │   └── manifest.json                 # 📱 Configuración PWA
│   ├── dist/                             # 📦 Build de producción
│   ├── package.json                      # 📦 Dependencias Node.js
│   ├── vite.config.ts                    # ⚡ Configuración Vite
│   ├── tsconfig.json                     # 🔧 Configuración TypeScript
│   └── index.html                        # 🏠 Punto de entrada
├── models/                               # 🤖 Modelos de ML compartidos
│   ├── embeddings/                       # 📊 Modelos de embeddings
│   │   └── models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2/
│   ├── stt/                              # 🎙️ Speech-to-Text (futuro)
│   └── tts/                              # 🔊 Text-to-Speech (futuro)
├── tests_sistema/                        # 🧪 Tests de integración
│   ├── test_completo.py                  # Test integral del sistema
│   ├── test_documents_system.py          # Tests del sistema RAG
│   └── test_anthropic.py                 # Tests de integración Anthropic
├── Historial_Procesos.md                 # 📚 Historial de desarrollo
└── ESTRUCTURA_PROYECTO.md                # 📋 Este archivo
```

---

## 🔧 Backend (Python/FastAPI)

### **`/backend/`** - Servidor Principal
Servidor FastAPI que maneja toda la lógica de negocio, IA, procesamiento de documentos y memoria.

#### **`/api/`** - Endpoints REST
- **`main.py`** - Endpoint principal `/chat` con soporte multi-LLM (Anthropic, OpenAI, DeepSeek, Gemini), sistema RAG y memoria episódica
- **`voice_synthesis.py`** - Endpoints para síntesis de voz con ElevenLabs, soporte streaming y caché de audio

#### **`/ai/`** - Inteligencia Artificial
- **`content_analyzer.py`** - Análisis inteligente de contenido con categorización automática y extracción de metadatos
- **`__init__.py`** - Inicialización del módulo AI

#### **`/document_processing/`** - Procesamiento de Documentos RAG
Sistema completo de procesamiento de documentos para RAG (Retrieval-Augmented Generation).

##### **`/extractors/`** - Extractores de Contenido
- **`base_extractor.py`** - Clase base abstracta para todos los extractores con validación y metadatos
- **`pdf_extractor.py`** - Extractor para archivos PDF usando PyPDF2 con detección de metadatos
- **`docx_extractor.py`** - Extractor para documentos Word con análisis de estructura
- **`xlsx_extractor.py`** - 🔥 **NUEVO**: Extractor Excel con estrategia "Una Fila = Un Documento" optimizado para RAG
- **`txt_extractor.py`** - Extractor para archivos de texto plano con detección de encoding
- **`__init__.py`** - Registro automático de extractores

##### **`/chunkers/`** - Fragmentación de Contenido
- **`text_chunker.py`** - Chunking inteligente de texto con overlap y preservación de contexto
- **`table_chunker.py`** - Chunking especializado para datos tabulares y tablas
- **`__init__.py`** - Inicialización de chunkers

##### **`/analyzers/`** - Análisis de Contenido
- **`__init__.py`** - Analizadores de contenido semántico (futuras extensiones)

##### **Archivos principales**
- **`document_manager.py`** - Gestor principal que coordina extracción, chunking y vectorización
- **`document_vector_manager.py`** - 🔥 **ACTUALIZADO**: Gestión de vectores con sanitización de metadatos para ChromaDB
- **`semantic_reranker.py`** - Re-ranking semántico de resultados de búsqueda para mayor precisión
- **`__init__.py`** - Inicialización del sistema de procesamiento

#### **`/memory/`** - Sistema de Memoria Avanzada
Sistema de memoria episódica y contextual integrado con AgenteIng.

- **`episodic.py`** - Memoria episódica principal con LangChain, buffer circular y persistencia
- **`semantic.py`** - Memoria semántica para conceptos y relaciones entre ideas
- **`category_manager.py`** - Gestor de categorías automáticas (personal, familiar, social) con aprendizaje
- **`critical_thinking.py`** - Sistema de pensamiento crítico para análisis de conversaciones
- **`proactive_assistant.py`** - Asistente proactivo que sugiere acciones basadas en patrones
- **`document_contextual_memory.py`** - Memoria contextual que vincula conversaciones con documentos
- **`__init__.py`** - Inicialización del sistema de memoria

#### **`/storage/`** - Gestión de Almacenamiento
- **`vector_manager.py`** - 🔥 **ACTUALIZADO**: Gestor de vectores híbrido (local + Gemini) con configuración forzada para compatibilidad
- **`file_manager.py`** - Gestión de archivos subidos con validación y organización
- **`onnx_embeddings.py`** - Embeddings ONNX como fallback para sistemas sin GPU
- **`__init__.py`** - Inicialización del sistema de almacenamiento

#### **`/utils/`** - Utilidades
- **`config.py`** - Configuración centralizada del sistema con variables de entorno
- **`logger.py`** - Sistema de logging configurado para desarrollo y producción

#### **`/data/`** - Datos Persistentes
##### **`/documents/`** - Documentos Procesados
- **`/uploads/`** - Archivos subidos por usuarios
- **`/processed/`** - Documentos procesados con metadatos y chunks
- **`/temp/`** - Archivos temporales durante procesamiento

##### **`/chromadb/`** - Base de Datos Vectorial
- Base de datos ChromaDB con embeddings y metadatos para búsqueda semántica

##### **`/categories/`** - Sistema de Categorización
- **`/personal/`** - Categoría personal con conversaciones y documentos
- **`/familiar/`** - Categoría familiar con conversaciones y documentos  
- **`/social/`** - Categoría social con conversaciones y documentos
- **`user_categories.json`** - Configuración de categorías personalizadas

##### **`/contextual_memory/`** - Memoria Contextual
- **`conversation_documents.json`** - Vínculos entre conversaciones y documentos
- **`document_topics.json`** - Temas extraídos de documentos
- **`user_preferences.json`** - Preferencias del usuario aprendidas

##### **`/critical_thinking/`** - Pensamiento Crítico
- **`temporal_buffer.json`** - Buffer temporal para análisis de conversaciones
- **`pending_review.json`** - Elementos pendientes de revisión manual

#### **Archivos de configuración**
- **`run.py`** - Script principal para ejecutar el servidor con configuración optimizada
- **`requirements-final.txt`** - Dependencias Python verificadas y compatibles con Python 3.12
- **`.env`** - Variables de entorno (API keys, configuración)
- **`.env.example`** - Plantilla de variables de entorno
- **`activate.sh`** - Script de activación del entorno virtual
- **`README.md`** - Documentación específica del backend

---

## 🎨 Frontend (React/TypeScript)

### **`/frontend/`** - Cliente Web
Aplicación React con TypeScript, Vite y PWA capabilities.

#### **`/src/`** - Código Fuente

##### **`/components/`** - Componentes React
###### **`/chat/`** - Interfaz de Chat
- Componentes para la interfaz principal de conversación con el chatbot

###### **`/file-upload/`** - Subida de Archivos
- Componentes para drag & drop y gestión de archivos con preview

###### **`/file-manager/`** - Gestión de Documentos
- Interfaz para visualizar y gestionar documentos procesados

###### **`/memory/`** - Interfaz de Memoria
- Visualización del sistema de memoria episódica y categorías

###### **`/voice/`** - Sistema de Voz
- Componentes para entrada de voz (Web Speech API) y síntesis (ElevenLabs)

###### **`/ui/`** - Componentes UI Base
- Componentes reutilizables de interfaz de usuario

##### **`/hooks/`** - Custom Hooks
- Hooks personalizados para lógica de estado y efectos reutilizables

##### **`/services/`** - Servicios API
- Servicios para comunicación con el backend (chat, documentos, voz)

##### **`/stores/`** - Gestión de Estado
- Estado global de la aplicación (Zustand/Context)

##### **`/types/`** - Definiciones TypeScript
- Tipos e interfaces TypeScript para type safety

##### **`/utils/`** - Utilidades Frontend
- Funciones auxiliares y helpers del frontend

##### **`/styles/`** - Estilos
- Estilos globales y configuración de tema

#### **Archivos de configuración**
- **`package.json`** - Dependencias y scripts de Node.js
- **`vite.config.ts`** - Configuración de Vite con PWA y optimizaciones
- **`tsconfig.json`** - Configuración de TypeScript
- **`index.html`** - Punto de entrada HTML

#### **`/public/`** - Archivos Estáticos
- **`manifest.json`** - Configuración PWA para instalación como app

#### **`/dist/`** - Build de Producción
- Archivos compilados para producción (generados automáticamente)

---

## 🤖 Models (Modelos de ML)

### **`/models/`** - Modelos de Machine Learning
Almacenamiento local de modelos para reducir dependencias externas.

#### **`/embeddings/`** - Modelos de Embeddings
- **`models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2/`** - Modelo local multilingüe para embeddings de texto

#### **`/stt/`** - Speech-to-Text
- Modelos locales para reconocimiento de voz (futuro)

#### **`/tts/`** - Text-to-Speech  
- Modelos locales para síntesis de voz (futuro)

---

## 🧪 Tests Sistema

### **`/tests_sistema/`** - Tests de Integración
Tests end-to-end del sistema completo.

- **`test_completo.py`** - Test integral de todo el flujo (chat + documentos + memoria)
- **`test_documents_system.py`** - Tests específicos del sistema de documentos RAG
- **`test_anthropic.py`** - Tests de integración con Anthropic Claude

---

## 📚 Documentación

### **Archivos de documentación**
- **`Historial_Procesos.md`** - 📖 Historial completo de desarrollo, problemas resueltos y mejoras implementadas
- **`ESTRUCTURA_PROYECTO.md`** - 📋 Este archivo con la estructura completa del proyecto

---

## 🔥 Características Principales Implementadas

### **Sistema RAG Avanzado**
- ✅ Estrategia "Una Fila = Un Documento" para archivos XLSX
- ✅ Extractores especializados para PDF, DOCX, XLSX, TXT
- ✅ Vectorización con sentence-transformers local + Gemini fallback
- ✅ ChromaDB con metadatos sanitizados para máxima compatibilidad
- ✅ Re-ranking semántico para resultados precisos

### **Memoria Episódica Inteligente**
- ✅ Memoria episódica con LangChain integrada
- ✅ Categorización automática (personal, familiar, social)
- ✅ Sistema de pensamiento crítico para análisis
- ✅ Memoria contextual que vincula conversaciones con documentos

### **Multi-LLM Support**
- ✅ Anthropic Claude (formato system prompt nativo)
- ✅ OpenAI GPT (compatible con DeepSeek)
- ✅ Google Gemini (prompt unificado)
- ✅ Personalidad configurable por usuario

### **Sistema de Voz Completo**
- ✅ Entrada: Web Speech API nativa del navegador
- ✅ Salida: ElevenLabs con streaming para baja latencia
- ✅ Visualizaciones de audio y estados de UI
- ✅ Caché inteligente de audio generado

### **Arquitectura Moderna**
- ✅ Backend: FastAPI + Python 3.12 + ChromaDB
- ✅ Frontend: React + TypeScript + Vite + PWA
- ✅ Procesamiento: pandas + sentence-transformers + LangChain
- ✅ Despliegue: Entornos virtuales independientes

---

## 🚀 Estado Actual

**✅ Sistema completamente funcional y probado:**
- RAG con archivos XLSX funciona perfectamente con respuestas precisas
- Memoria episódica integrada con categorización automática  
- Multi-LLM con personalidad configurable
- Sistema de voz completo con streaming
- Frontend React moderno con PWA capabilities

**🎯 Ready for production use!**