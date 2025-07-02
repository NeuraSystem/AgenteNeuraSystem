"""
Módulo de adaptación de embeddings locales para LangChain y ChromaDB.
- Carga el modelo paraphrase-multilingual-MiniLM-L12-v2 usando sentence-transformers.
- Proporciona una clase adaptadora para usar embeddings locales en LangChain.
"""

from sentence_transformers import SentenceTransformer
from langchain_core.embeddings import Embeddings
from typing import List

# Clase: LocalMiniLMEmbeddings
class LocalMiniLMEmbeddings(Embeddings):
    """
    Adaptador para usar el modelo local MiniLM como embeddings en LangChain.
    Parámetros:
        model_path (str): Ruta al modelo local.
    Métodos:
        embed_documents(texts: List[str]) -> List[List[float]]
        embed_query(text: str) -> List[float]
    """
    def __init__(self, model_path: str):
        self.model = SentenceTransformer(model_path)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings para una lista de textos."""
        return self.model.encode(texts).tolist()

    def embed_query(self, text: str) -> List[float]:
        """Genera un embedding para una consulta individual."""
        return self.model.encode([text])[0].tolist()

# Función: cargar_embeddings_locales
def cargar_embeddings_locales(model_path: str) -> LocalMiniLMEmbeddings:
    """
    Carga el modelo de embeddings local y retorna el adaptador para LangChain.
    Parámetros:
        model_path (str): Ruta al modelo local.
    Retorna:
        LocalMiniLMEmbeddings: Adaptador listo para usar en ChromaDB/LangChain.
    """
    return LocalMiniLMEmbeddings(model_path) 