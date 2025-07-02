#!/bin/bash
# Script de activación del entorno virtual ChatIng
# Uso: source activate.sh

echo "🚀 Activando entorno virtual ChatIng..."
source chatbot_venv/bin/activate

echo "✅ Entorno virtual activado"
echo "📁 Directorio: $(pwd)"
echo "🐍 Python: $(python --version)"
echo "📦 Pip: $(pip --version)"

echo ""
echo "🎯 COMANDOS DISPONIBLES:"
echo "  python test_anthropic.py     - Prueba rápida"
echo "  python test_completo.py      - Prueba completa"
echo "  python run.py                - Iniciar servidor"
echo "  uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "🌐 Servidor API: http://localhost:8000"
echo "📚 Docs API: http://localhost:8000/docs"