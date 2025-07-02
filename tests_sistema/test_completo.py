"""
Script de prueba completo para el Chatbot Modular.
- Verifica la instalación de dependencias
- Prueba todas las APIs de LLM configuradas
- Verifica el funcionamiento de embeddings y memoria
- Prueba la API FastAPI
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Cambiar al directorio del proyecto
project_dir = Path(__file__).parent
os.chdir(project_dir)
sys.path.insert(0, str(project_dir / "backend"))

# Cargar configuración
load_dotenv()

def print_section(title):
    """Imprime una sección de prueba."""
    print(f"\n{'='*50}")
    print(f"🧪 {title}")
    print('='*50)

def print_test(test_name, success, message=""):
    """Imprime resultado de una prueba."""
    status = "✅" if success else "❌"
    print(f"{status} {test_name}")
    if message:
        print(f"   {message}")

async def test_dependencies():
    """Verifica que las dependencias estén instaladas."""
    print_section("VERIFICACIÓN DE DEPENDENCIAS")
    
    dependencies = [
        ("fastapi", "FastAPI framework"),
        ("anthropic", "Cliente Anthropic"),
        ("openai", "Cliente OpenAI"),
        ("google-generativeai", "Cliente Google Gemini"),
        ("sentence-transformers", "Embeddings locales"),
        ("langchain", "Framework LangChain"),
        ("chromadb", "Base vectorial ChromaDB"),
        ("uvicorn", "Servidor ASGI")
    ]
    
    success_count = 0
    for package, description in dependencies:
        try:
            __import__(package.replace("-", "_"))
            print_test(f"{package} ({description})", True)
            success_count += 1
        except ImportError:
            print_test(f"{package} ({description})", False, "No instalado")
    
    print(f"\n📊 Dependencias: {success_count}/{len(dependencies)} instaladas")
    return success_count == len(dependencies)

async def test_configuration():
    """Verifica la configuración del .env."""
    print_section("VERIFICACIÓN DE CONFIGURACIÓN")
    
    config_vars = {
        "DEFAULT_PROVIDER": "Proveedor por defecto",
        "ANTHROPIC_API_KEY": "API Key de Anthropic",
        "ANTHROPIC_MODEL": "Modelo de Anthropic",
        "EMBEDDINGS_MODEL_PATH": "Ruta del modelo de embeddings",
        "LANGUAGE": "Idioma configurado"
    }
    
    success_count = 0
    for var, description in config_vars.items():
        value = os.getenv(var)
        if value:
            # No mostrar API keys completas por seguridad
            display_value = value if not "API_KEY" in var else f"{value[:10]}..."
            print_test(f"{var} ({description})", True, f"= {display_value}")
            success_count += 1
        else:
            print_test(f"{var} ({description})", False, "No configurada")
    
    print(f"\n📊 Configuración: {success_count}/{len(config_vars)} variables configuradas")
    return success_count >= 3  # Al menos las básicas

async def test_llm_apis():
    """Prueba las APIs de LLM configuradas."""
    print_section("PRUEBA DE APIs LLM")
    
    # Importar las funciones del backend
    from api.main import chat_anthropic, chat_openai, chat_gemini, chat_deepseek
    
    apis = [
        ("Anthropic", chat_anthropic, "ANTHROPIC_API_KEY"),
        ("OpenAI", chat_openai, "OPENAI_API_KEY"),
        ("Gemini", chat_gemini, "GEMINI_API_KEY"),
        ("DeepSeek", chat_deepseek, "DEEPSEEK_API_KEY")
    ]
    
    test_message = "Responde brevemente: ¿Cuál es la capital de Francia?"
    success_count = 0
    
    for name, func, api_key_var in apis:
        try:
            if os.getenv(api_key_var):
                response = await func(test_message)
                if "Error" not in response and len(response) > 0:
                    print_test(f"API {name}", True, f"Respuesta: {response[:50]}...")
                    success_count += 1
                else:
                    print_test(f"API {name}", False, response[:100])
            else:
                print_test(f"API {name}", False, f"{api_key_var} no configurada")
        except Exception as e:
            print_test(f"API {name}", False, f"Error: {str(e)[:50]}")
    
    print(f"\n📊 APIs: {success_count}/{len(apis)} funcionando")
    return success_count > 0

async def test_embeddings():
    """Prueba el sistema de embeddings locales."""
    print_section("PRUEBA DE EMBEDDINGS LOCALES")
    
    try:
        from embeddings.adapter import cargar_embeddings_locales
        
        # Intentar cargar el modelo
        model_path = os.getenv("EMBEDDINGS_MODEL_PATH", "paraphrase-multilingual-MiniLM-L12-v2")
        embeddings = cargar_embeddings_locales(model_path)
        
        # Probar embedding de una consulta
        test_text = "Este es un texto de prueba para embeddings"
        embedding = embeddings.embed_query(test_text)
        
        print_test("Carga del modelo de embeddings", True, f"Dimensión: {len(embedding)}")
        
        # Probar embedding de múltiples documentos
        test_docs = ["Documento 1", "Documento 2", "Documento 3"]
        doc_embeddings = embeddings.embed_documents(test_docs)
        
        print_test("Embeddings de documentos", True, f"Procesados: {len(doc_embeddings)} documentos")
        
        return True
        
    except Exception as e:
        print_test("Sistema de embeddings", False, f"Error: {str(e)}")
        return False

async def test_memory_system():
    """Prueba el sistema de memoria."""
    print_section("PRUEBA DE SISTEMA DE MEMORIA")
    
    try:
        from memory.episodic import crear_memoria_episodica
        from memory.semantic import inicializar_chromadb
        from embeddings.adapter import cargar_embeddings_locales
        
        # Probar memoria episódica
        memoria = crear_memoria_episodica(buffer_size=5)
        print_test("Memoria episódica", True, f"Buffer size: 5")
        
        # Probar memoria semántica
        model_path = os.getenv("EMBEDDINGS_MODEL_PATH", "paraphrase-multilingual-MiniLM-L12-v2")
        embeddings = cargar_embeddings_locales(model_path)
        
        vector_store = inicializar_chromadb(
            collection_name="test_collection",
            embeddings=embeddings,
            persist_directory="./data/test_chromadb"
        )
        
        print_test("Memoria semántica (ChromaDB)", True, "Inicializada correctamente")
        
        return True
        
    except Exception as e:
        print_test("Sistema de memoria", False, f"Error: {str(e)}")
        return False

async def test_api_server():
    """Prueba si el servidor API puede iniciarse."""
    print_section("PRUEBA DE SERVIDOR API")
    
    try:
        # Importar la aplicación FastAPI
        from api.main import app
        
        print_test("Importación de FastAPI app", True, "App cargada correctamente")
        
        # Verificar que los endpoints están definidos
        routes = [route.path for route in app.routes]
        has_chat_endpoint = "/chat" in routes
        
        print_test("Endpoint /chat", has_chat_endpoint, "Endpoint disponible" if has_chat_endpoint else "Endpoint no encontrado")
        
        return has_chat_endpoint
        
    except Exception as e:
        print_test("Servidor API", False, f"Error: {str(e)}")
        return False

async def main():
    """Función principal de pruebas."""
    print("🚀 INICIANDO PRUEBAS COMPLETAS DEL CHATBOT MODULAR")
    print(f"📁 Directorio de trabajo: {os.getcwd()}")
    
    # Ejecutar todas las pruebas
    tests = [
        ("Dependencias", test_dependencies),
        ("Configuración", test_configuration),
        ("APIs LLM", test_llm_apis),
        ("Embeddings", test_embeddings),
        ("Sistema de Memoria", test_memory_system),
        ("Servidor API", test_api_server)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = await test_func()
        except Exception as e:
            print_test(f"ERROR en {test_name}", False, str(e))
            results[test_name] = False
    
    # Resumen final
    print_section("RESUMEN DE PRUEBAS")
    total_tests = len(tests)
    passed_tests = sum(results.values())
    
    for test_name, passed in results.items():
        print_test(test_name, passed)
    
    print(f"\n📊 RESULTADO FINAL: {passed_tests}/{total_tests} pruebas exitosas")
    
    if passed_tests == total_tests:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print("\nPara iniciar el chatbot:")
        print("   python -m uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000")
        print("\nPara probar la API:")
        print("   curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' -d '{\"mensaje\": \"Hola\"}'")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} pruebas fallaron. Revisa los errores anteriores.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    asyncio.run(main())