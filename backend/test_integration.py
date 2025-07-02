#!/usr/bin/env python3
"""
Script de validación para verificar la integración entre DocumentVectorManager y HybridRetrievalSystem.
CRITICAL TEST: Verificar que los documentos se guarden y encuentren correctamente.
"""

import asyncio
import logging
from storage.vector_manager import VectorManager
from memory.hybrid_retrieval import HybridRetrievalSystem

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

async def test_integration():
    """Test de integración crítico"""
    logger.info("🔍 INICIANDO TEST DE INTEGRACIÓN CRÍTICO")
    
    try:
        # 1. Inicializar componentes
        logger.info("1️⃣ Inicializando VectorManager...")
        vector_manager = VectorManager()
        
        logger.info("2️⃣ Inicializando HybridRetrievalSystem...")
        hybrid_system = HybridRetrievalSystem(vector_manager)
        
        # 2. Verificar colecciones disponibles
        logger.info("3️⃣ Verificando colecciones disponibles...")
        stats = vector_manager.get_collection_stats()
        logger.info(f"📊 Estadísticas ChromaDB: {stats}")
        
        # 3. Test: Agregar documentos de prueba
        logger.info("4️⃣ Agregando documentos de prueba...")
        test_documents = [
            "Marco Aurelio escribió las Meditaciones como reflexiones personales sobre filosofía estoica.",
            "Las Meditaciones contienen pensamientos sobre la virtud, la muerte y el deber.",
            "El emperador romano Marco Aurelio fue también un filósofo estoico."
        ]
        
        test_metadatas = [
            {"file_name": "test_marco_aurelio.pdf", "file_type": "pdf", "chunk_id": "1"},
            {"file_name": "test_marco_aurelio.pdf", "file_type": "pdf", "chunk_id": "2"}, 
            {"file_name": "test_marco_aurelio.pdf", "file_type": "pdf", "chunk_id": "3"}
        ]
        
        test_ids = ["test_doc_1", "test_doc_2", "test_doc_3"]
        
        result = await vector_manager.add_documents(
            collection_name="documents",
            documents=test_documents,
            metadatas=test_metadatas,
            ids=test_ids
        )
        
        if result:
            logger.info(f"✅ Documentos de prueba agregados exitosamente: {result}")
        else:
            logger.error("❌ FALLO: No se pudieron agregar documentos de prueba")
            return False
        
        # 4. Test: Búsqueda con HybridRetrievalSystem
        logger.info("5️⃣ Probando búsqueda con HybridRetrievalSystem...")
        
        test_queries = [
            "Marco Aurelio filosofía estoica",
            "Meditaciones emperador romano",
            "reflexiones sobre la muerte"
        ]
        
        for query in test_queries:
            logger.info(f"🔍 Probando query: '{query}'")
            context = await hybrid_system.search(query)
            
            if "Marco Aurelio" in context or "Meditaciones" in context:
                logger.info(f"✅ Query exitosa: encontró contenido relevante")
                logger.info(f"📄 Contexto (preview): {context[:200]}...")
            else:
                logger.error(f"❌ FALLO: Query no encontró contenido relevante")
                logger.error(f"📄 Contexto recibido: {context}")
                return False
        
        # 5. Test: Verificar scores de similitud positivos
        logger.info("6️⃣ Verificando scores de similitud...")
        search_results = await vector_manager.search("documents", "Marco Aurelio", n_results=3)
        
        for result in search_results:
            similarity = result.get('similarity', 0)
            distance = result.get('distance', 999)
            logger.info(f"📊 Resultado: similarity={similarity:.3f}, distance={distance:.3f}")
            
            if similarity < 0:
                logger.error(f"❌ FALLO: Similarity negativa detectada: {similarity}")
                return False
            
            if similarity > 1:
                logger.warning(f"⚠️ Similarity mayor que 1: {similarity}")
        
        logger.info("🎉 TODOS LOS TESTS PASARON EXITOSAMENTE")
        logger.info("✅ La integración DocumentVectorManager <-> HybridRetrievalSystem funciona correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ ERROR EN TEST DE INTEGRACIÓN: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_integration())