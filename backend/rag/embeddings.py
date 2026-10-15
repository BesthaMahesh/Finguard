import os
import logging
from typing import List
import numpy as np

logger = logging.getLogger(__name__)

from chromadb import EmbeddingFunction

# Module-level singleton model cache to prevent reloading 100MB+ PyTorch weights per query
_CACHED_ST_MODELS = {}

def get_cached_sentence_transformer(model_name: str = "all-MiniLM-L6-v2"):
    global _CACHED_ST_MODELS
    if os.environ.get("USE_LIGHTWEIGHT_EMBEDDINGS", "false").lower() in ("true", "1", "yes"):
        _CACHED_ST_MODELS[model_name] = None
        return None

    if model_name not in _CACHED_ST_MODELS:
        try:
            from sentence_transformers import SentenceTransformer
            _CACHED_ST_MODELS[model_name] = SentenceTransformer(model_name)
            logger.info(f"Loaded and cached global SentenceTransformer in memory: {model_name}")
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer ({e}). Using deterministic token-hash embedding.")
            _CACHED_ST_MODELS[model_name] = None
    return _CACHED_ST_MODELS[model_name]

class FinGuardEmbeddingFunction(EmbeddingFunction):
    """
    High-performance Embedding provider for ChromaDB with in-memory singleton caching.
    Uses sentence-transformers if available, or fast deterministic term-frequency normalized projection.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._st_model = get_cached_sentence_transformer(self.model_name)

    def name(self) -> str:
        return "finguard_minilm_embeddings"

    def __call__(self, input=None, **kwargs) -> List[List[float]]:
        texts = input if input is not None else kwargs.get("input", [])
        if isinstance(texts, str):
            texts = [texts]
        return self.embed_documents(list(texts))

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if self._st_model is not None:
            try:
                embeddings = self._st_model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
                return embeddings.tolist()
            except Exception as e:
                logger.warning(f"Embedding generation with model failed: {e}. Fallback to token hash.")
        
        # Deterministic 384-dimensional token hashing embedding
        return [self._hash_embed(t, dim=384) for t in texts]

    def embed_query(self, *args, **kwargs) -> List[float]:
        text = kwargs.get("input")
        if text is None:
            text = args[0] if args else ""
        if isinstance(text, list):
            return self.embed_documents(text)[0] if text else [0.0] * 384
        return self.embed_documents([str(text)])[0]

    def _hash_embed(self, text: str, dim: int = 384) -> List[float]:
        vec = np.zeros(dim, dtype=np.float32)
        words = text.lower().split()
        if not words:
            return vec.tolist()
        for w in words:
            h = hash(w) % dim
            vec[h] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()
