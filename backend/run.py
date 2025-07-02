"""
Script simple para iniciar el chatbot sin instalación compleja.
Funciona con la configuración básica existente.
"""

import sys
import os
from pathlib import Path

# Cambiar al directorio del proyecto
project_dir = Path(__file__).parent
os.chdir(project_dir)

# Agregar el directorio backend al path de Python
sys.path.insert(0, str(project_dir / "backend"))

print("🚀 Iniciando Chatbot Modular")
print("=" * 40)

# Verificar configuración básica
if not os.path.exists(".env"):
    print("❌ Archivo .env no encontrado")
    sys.exit(1)

print("✅ Configuración encontrada")

# Crear directorios básicos si no existen
directories = ["data", "data/logs"]
for directory in directories:
    Path(directory).mkdir(parents=True, exist_ok=True)
    print(f"📁 Directorio: {directory}")

print("\n🔧 Para instalar dependencias, ejecuta:")
print("   pip install fastapi uvicorn anthropic python-dotenv")

print("\n🚀 Para iniciar el servidor, ejecuta:")
print("   uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000")

print("\n🧪 Para probar la API:")
print("   curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' -d '{\"mensaje\": \"Hola\"}'")

print("\n✅ Configuración completada")