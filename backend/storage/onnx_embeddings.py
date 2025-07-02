"""
Embeddings locales usando ONNX Runtime (compatible con Alpine Linux).
Alternativa a sentence-transformers que no requiere PyTorch.
"""

import os
import numpy as np
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class ONNXLocalEmbeddings:
    """
    Embeddings locales usando ONNX Runtime para Alpine Linux.
    """
    
    def __init__(self, model_path: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        self.model_path = model_path
        self.session = None
        self.tokenizer = None
        self._initialize()
    
    def _initialize(self):
        """Inicializa ONNX Runtime y tokenizer."""
        try:
            # Método 1: Usar modelo pre-convertido si existe
            onnx_path = "./models/embeddings/model.onnx"
            if os.path.exists(onnx_path):
                self._load_onnx_model(onnx_path)
            else:
                # Método 2: Usar optimum para convertir
                self._convert_and_load()
                
        except Exception as e:
            logger.error(f"Error inicializando ONNX embeddings: {e}")
            self.session = None
    
    def _load_onnx_model(self, onnx_path: str):
        """Carga modelo ONNX existente."""
        try:
            import onnxruntime as ort
            from transformers import AutoTokenizer
            
            self.session = ort.InferenceSession(onnx_path)
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            logger.info(f"✅ Modelo ONNX cargado: {onnx_path}")
            
        except ImportError:
            logger.error("❌ onnxruntime no instalado")
        except Exception as e:
            logger.error(f"❌ Error cargando ONNX: {e}")
    
    def _convert_and_load(self):
        """Convierte modelo a ONNX y lo carga."""
        try:
            from optimum.onnxruntime import ORTModelForFeatureExtraction
            from transformers import AutoTokenizer
            
            # Crear directorio
            os.makedirs("./models/embeddings/", exist_ok=True)
            
            logger.info("🔄 Convirtiendo modelo a ONNX...")
            
            # Convertir a ONNX
            model = ORTModelForFeatureExtraction.from_pretrained(
                self.model_path, 
                export=True,
                cache_dir="./models/embeddings/"
            )
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.session = model.model
            
            logger.info("✅ Modelo convertido y cargado exitosamente")
            
        except ImportError as e:
            logger.error(f"❌ Dependencias faltantes: {e}")
        except Exception as e:
            logger.error(f"❌ Error en conversión: {e}")
    
    def encode(self, texts: List[str]) -> Optional[np.ndarray]:
        """
        Codifica textos a embeddings.
        
        Args:
            texts: Lista de textos
            
        Returns:
            np.ndarray: Embeddings o None si falla
        """
        if not self.session or not self.tokenizer:
            logger.error("❌ Modelo no inicializado")
            return None
        
        try:
            # Tokenizar
            inputs = self.tokenizer(
                texts, 
                padding=True, 
                truncation=True, 
                return_tensors="np",
                max_length=512
            )
            
            # Inferencia ONNX
            onnx_inputs = {
                "input_ids": inputs["input_ids"].astype(np.int64),
                "attention_mask": inputs["attention_mask"].astype(np.int64)
            }
            
            outputs = self.session.run(None, onnx_inputs)
            embeddings = outputs[0]
            
            # Mean pooling
            attention_mask = inputs["attention_mask"]
            embeddings = self._mean_pooling(embeddings, attention_mask)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"❌ Error en encode: {e}")
            return None
    
    def _mean_pooling(self, embeddings: np.ndarray, attention_mask: np.ndarray) -> np.ndarray:
        """Mean pooling para sentence embeddings."""
        # Expandir attention mask
        attention_mask_expanded = np.expand_dims(attention_mask, -1)
        attention_mask_expanded = np.broadcast_to(attention_mask_expanded, embeddings.shape)
        
        # Mean pooling
        sum_embeddings = np.sum(embeddings * attention_mask_expanded, axis=1)
        sum_mask = np.sum(attention_mask_expanded, axis=1)
        
        return sum_embeddings / np.maximum(sum_mask, 1e-9)
    
    def is_available(self) -> bool:
        """Verifica si el modelo está disponible."""
        return self.session is not None and self.tokenizer is not None