from abc import ABC, abstractmethod
from typing import List, Union
import logging

logger = logging.getLogger(__name__)

class Embedder(ABC):
    """Abstract Base Class for text embedding models."""
    
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Embed a single text string into a float vector."""
        pass

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of text strings into float vectors."""
        pass


class BGEEmbedder(Embedder):
    """
    SentenceTransformers Embedder using BAAI/bge-m3 or specified HuggingFace model.
    Falls back gracefully to all-MiniLM-L6-v2 if bge-m3 fails to load.
    """
    
    def __init__(self, model_name: str = "BAAI/bge-m3"):
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        if self._model is None:
            # pyrefly: ignore [missing-import]
            from sentence_transformers import SentenceTransformer
            try:
                logger.info(f"Loading SentenceTransformer model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
            except Exception as e:
                logger.warning(f"Failed to load {self.model_name} ({e}). Falling back to 'all-MiniLM-L6-v2'.")
                self.model_name = "all-MiniLM-L6-v2"
                self._model = SentenceTransformer("all-MiniLM-L6-v2")
        return self._model

    def embed_text(self, text: str) -> List[float]:
        embedding = self.model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        return embedding.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.tolist()


class DummyEmbedder(Embedder):
    """Deterministic dummy embedder for unit tests and fast local debugging."""
    
    def __init__(self, dim: int = 384):
        self.dim = dim

    def embed_text(self, text: str) -> List[float]:
        import hashlib
        h = hashlib.md5(text.encode('utf-8')).hexdigest()
        val = int(h, 16) / float(1 << 128)
        vec = [(val + i * 0.01) % 1.0 for i in range(self.dim)]
        return vec

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]
