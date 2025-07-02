#!/usr/bin/env python3
"""
Script de prueba para el sistema de procesamiento de documentos.
Verifica que todos los componentes funcionen correctamente.
"""

import asyncio
import sys
from pathlib import Path
import tempfile
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_document_system():
    """
    Prueba el sistema completo de procesamiento de documentos.
    """
    try:
        print("🧪 PRUEBA DEL SISTEMA DE DOCUMENTOS")
        print("=" * 50)
        
        # Importar componentes
        from backend.document_processing import DocumentManager
        
        # Inicializar gestor
        print("📋 Inicializando DocumentManager...")
        doc_manager = DocumentManager()
        
        # Verificar formatos soportados
        formats = doc_manager.get_supported_formats()
        print(f"✅ Formatos soportados: {', '.join(formats)}")
        
        # Crear archivo de prueba TXT
        print("\n📝 Creando archivo de prueba...")
        test_content = """
# Documento de Prueba

Este es un documento de prueba para el sistema ChatIng.

## Características del Sistema

- Procesamiento de múltiples formatos
- Extracción inteligente de contenido
- Chunking semántico optimizado
- Vectorización automática con embeddings
- Búsqueda semántica avanzada

## Tecnologías Utilizadas

El sistema utiliza:
1. FastAPI para la API REST
2. ChromaDB para almacenamiento vectorial
3. sentence-transformers para embeddings locales
4. PyPDF2, python-docx, openpyxl para extracción

## Casos de Uso

- Análisis de documentos empresariales
- Búsqueda de información en archivos
- Asistente inteligente con contexto documental
"""
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(test_content)
            test_file_path = Path(f.name)
        
        print(f"📄 Archivo creado: {test_file_path}")
        
        # Procesar documento
        print("\n🔄 Procesando documento...")
        result = await doc_manager.process_document(test_file_path, "test_doc_001")
        
        print(f"✅ Documento procesado:")
        print(f"   - ID: {result['document_id']}")
        print(f"   - Archivo: {result['file_name']}")
        print(f"   - Tipo: {result['file_type']}")
        print(f"   - Chunks: {result['chunk_count']}")
        print(f"   - Tokens: {result['total_tokens']}")
        print(f"   - Vectorizado: {result.get('vectorized', 'N/A')}")
        
        # Listar documentos
        print("\n📋 Listando documentos...")
        docs = await doc_manager.list_documents()
        for doc in docs:
            print(f"   - {doc['file_name']} ({doc['file_type']}) - {doc['chunk_count']} chunks")
        
        # Probar búsqueda
        print("\n🔍 Probando búsqueda semántica...")
        search_queries = [
            "sistema de embeddings",
            "tecnologías utilizadas",
            "FastAPI",
            "casos de uso empresariales"
        ]
        
        for query in search_queries:
            results = await doc_manager.search_documents(query, limit=2)
            print(f"\n🔎 Búsqueda: '{query}'")
            
            if results:
                for i, result in enumerate(results, 1):
                    print(f"   {i}. Similitud: {result['similarity']:.3f}")
                    print(f"      Archivo: {result['file_name']}")
                    print(f"      Contenido: {result['content'][:100]}...")
            else:
                print("   ⚠️ Sin resultados")
        
        # Obtener chunks específicos
        print("\n📄 Obteniendo chunks del documento...")
        chunks = await doc_manager.get_document_chunks("test_doc_001")
        for chunk in chunks[:2]:  # Solo primeros 2 chunks
            print(f"   - Chunk {chunk['chunk_id']}: {len(chunk['content'])} caracteres")
        
        # Limpiar
        print(f"\n🧹 Limpiando archivo temporal...")
        test_file_path.unlink()
        
        print("\n✅ ¡PRUEBA COMPLETADA EXITOSAMENTE!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("💡 Asegúrate de que todas las dependencias estén instaladas")
        return False
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        logger.exception("Detalles del error:")
        return False

async def test_extractors():
    """
    Prueba individual de extractores.
    """
    print("\n🔧 PRUEBA DE EXTRACTORES INDIVIDUALES")
    print("=" * 40)
    
    try:
        from backend.document_processing.extractors import TXTExtractor, PDFExtractor, DOCXExtractor, XLSXExtractor
        
        # Probar TXT extractor
        print("📝 Probando TXTExtractor...")
        txt_extractor = TXTExtractor()
        print(f"   Formatos: {txt_extractor.supported_formats}")
        
        # Probar PDF extractor
        print("📄 Probando PDFExtractor...")
        pdf_extractor = PDFExtractor()
        print(f"   Formatos: {pdf_extractor.supported_formats}")
        
        # Probar DOCX extractor
        print("📋 Probando DOCXExtractor...")
        docx_extractor = DOCXExtractor()
        print(f"   Formatos: {docx_extractor.supported_formats}")
        
        # Probar XLSX extractor
        print("📊 Probando XLSXExtractor...")
        xlsx_extractor = XLSXExtractor()
        print(f"   Formatos: {xlsx_extractor.supported_formats}")
        
        print("✅ Todos los extractores inicializados correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error probando extractores: {e}")
        return False

async def main():
    """
    Función principal de pruebas.
    """
    print("🚀 INICIO DE PRUEBAS DEL SISTEMA DE DOCUMENTOS")
    print()
    
    # Probar extractores individuales
    extractors_ok = await test_extractors()
    
    if extractors_ok:
        # Probar sistema completo
        system_ok = await test_document_system()
        
        if system_ok:
            print("\n🎉 TODAS LAS PRUEBAS EXITOSAS")
            print("\n💡 El sistema está listo para:")
            print("   - Subir documentos vía API")
            print("   - Procesar PDF, DOCX, XLSX, TXT")
            print("   - Búsqueda semántica en contenido")
            print("   - Integración con chat ChatIng")
            sys.exit(0)
        else:
            print("\n❌ FALLO EN PRUEBAS DEL SISTEMA")
            sys.exit(1)
    else:
        print("\n❌ FALLO EN PRUEBAS DE EXTRACTORES")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())