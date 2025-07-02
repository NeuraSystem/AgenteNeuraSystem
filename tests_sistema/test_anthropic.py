"""
Script de prueba enfocado en Anthropic Claude Haiku 3.
- Verifica la configuración de Anthropic
- Prueba la API de Anthropic
- Verifica el funcionamiento básico del chatbot
"""

import os
import sys
import asyncio
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
    print(f"\n{'='*40}")
    print(f"🤖 {title}")
    print('='*40)

def print_test(test_name, success, message=""):
    """Imprime resultado de una prueba."""
    status = "✅" if success else "❌"
    print(f"{status} {test_name}")
    if message:
        print(f"   {message}")

async def test_anthropic_config():
    """Verifica la configuración de Anthropic."""
    print_section("CONFIGURACIÓN DE ANTHROPIC")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    model = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
    provider = os.getenv("DEFAULT_PROVIDER", "anthropic")
    
    print_test("API Key configurada", bool(api_key), f"Key: {api_key[:15]}..." if api_key else "No configurada")
    print_test("Modelo configurado", bool(model), f"Modelo: {model}")
    print_test("Proveedor por defecto", provider == "anthropic", f"Proveedor: {provider}")
    
    return bool(api_key) and bool(model)

async def test_anthropic_api():
    """Prueba la API de Anthropic."""
    print_section("PRUEBA DE API ANTHROPIC")
    
    try:
        from api.main import chat_anthropic
        
        # Mensaje de prueba
        test_message = "Hola, responde brevemente: ¿Cuál es tu nombre y modelo?"
        
        print(f"📤 Enviando mensaje: {test_message}")
        response = await chat_anthropic(test_message)
        
        if "Error" not in response and len(response) > 0:
            print_test("Conexión con Anthropic", True)
            print(f"📥 Respuesta recibida:")
            print(f"   {response}")
            return True
        else:
            print_test("Conexión con Anthropic", False, response)
            return False
            
    except Exception as e:
        print_test("API de Anthropic", False, f"Error: {str(e)}")
        return False

async def test_dependencies():
    """Verifica dependencias críticas."""
    print_section("DEPENDENCIAS CRÍTICAS")
    
    critical_deps = [
        ("anthropic", "Cliente Anthropic"),
        ("fastapi", "Framework API"),
        ("uvicorn", "Servidor web"),
        ("python-dotenv", "Configuración")
    ]
    
    success_count = 0
    for package, description in critical_deps:
        try:
            __import__(package.replace("-", "_"))
            print_test(f"{package}", True, description)
            success_count += 1
        except ImportError:
            print_test(f"{package}", False, f"{description} - NO INSTALADO")
    
    return success_count == len(critical_deps)

async def test_api_server():
    """Verifica que el servidor puede iniciarse."""
    print_section("SERVIDOR API")
    
    try:
        from api.main import app
        
        print_test("FastAPI app", True, "Aplicación cargada correctamente")
        
        # Verificar endpoints
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        has_chat = "/chat" in routes
        
        print_test("Endpoint /chat", has_chat, "Endpoint de chat disponible")
        
        return has_chat
        
    except Exception as e:
        print_test("Servidor API", False, f"Error: {str(e)}")
        return False

async def main():
    """Función principal de pruebas."""
    print("🤖 PRUEBA RÁPIDA: ANTHROPIC CLAUDE HAIKU 3")
    print(f"📁 Directorio: {os.getcwd()}")
    
    # Ejecutar pruebas en orden de importancia
    tests = [
        ("Dependencias críticas", test_dependencies),
        ("Configuración Anthropic", test_anthropic_config),
        ("API Anthropic", test_anthropic_api),
        ("Servidor API", test_api_server)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print_test(f"ERROR en {test_name}", False, str(e))
            results.append((test_name, False))
    
    # Resumen
    print_section("RESUMEN")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        print_test(test_name, result)
    
    print(f"\n📊 Resultado: {passed}/{total} pruebas exitosas")
    
    if passed == total:
        print(f"\n🎉 ¡LISTO PARA USAR!")
        print(f"\n🚀 Para iniciar el chatbot:")
        print(f"   python -m uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000")
        print(f"\n🧪 Para probar:")
        print(f"   curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' -d '{{\"mensaje\": \"Hola Claude\"}}'")
    else:
        print(f"\n⚠️  Faltan {total - passed} configuraciones.")
        if not results[0][1]:  # Dependencias
            print(f"   Ejecuta: python install.py")
        if not results[1][1]:  # Configuración
            print(f"   Verifica tu archivo .env")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())