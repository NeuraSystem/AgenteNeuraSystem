"""
Módulo de memoria semántica para el chatbot.
- Integra ChromaDB como base vectorial para almacenamiento y recuperación de embeddings.
- Proporciona funciones para inicializar la base y realizar búsquedas semánticas.
"""

from langchain_chroma import Chroma
from typing import List, Optional
from langchain_core.documents import Document
from .episodic import crear_memoria_episodica

# Función: inicializar_chromadb
def inicializar_chromadb(collection_name: str, embeddings, persist_directory: str = "data/chroma_langchain_db") -> Chroma:
    """
    Inicializa la base vectorial ChromaDB para almacenamiento semántico.
    Parámetros:
        collection_name (str): Nombre de la colección.
        embeddings: Objeto de embeddings compatible con LangChain.
        persist_directory (str): Ruta de persistencia local.
    Retorna:
        Chroma: Objeto de base vectorial listo para usar.
    """
    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_directory
    )

# Función: busqueda_semantica
def busqueda_semantica(vector_store: Chroma, consulta: str, k: int = 5, filtro: Optional[dict] = None) -> List[Document]:
    """
    Realiza una búsqueda semántica en la base vectorial.
    Parámetros:
        vector_store (Chroma): Base vectorial inicializada.
        consulta (str): Texto de consulta.
        k (int): Número de resultados a devolver.
        filtro (dict, opcional): Filtro adicional para la búsqueda.
    Retorna:
        List[Document]: Lista de documentos relevantes.
    """
    return vector_store.similarity_search(consulta, k=k, filter=filtro) 