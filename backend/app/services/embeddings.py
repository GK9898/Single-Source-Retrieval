import logging
from typing import List
import numpy as np
from app.config import settings
from app.utils.retry import llm_retry_decorator

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, model_name: str = settings.EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        if self._model is None:
            if SentenceTransformer is not None:
                try:
                    logger.info(f"Loading embedding model: {self.model_name}")
                    self._model = SentenceTransformer(self.model_name)
                except Exception as e:
                    logger.warning(f"Could not load SentenceTransformer ({e}). Using mock embeddings.")
                    self._model = "mock"
            else:
                logger.warning("SentenceTransformer not installed. Using mock embeddings.")
                self._model = "mock"
        return self._model

    @llm_retry_decorator(max_attempts=3)
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generate vector embeddings for a list of texts with retry decorator."""
        if not texts:
            return np.empty((0, 384), dtype=np.float32)

        if self.model == "mock":
            # Return deterministic normalized dummy embeddings per text for mock mode
            dimension = 384
            vecs = []
            for t in texts:
                seed = abs(hash(t)) % (2**32 - 1)
                rng = np.random.RandomState(seed)
                vec = rng.randn(dimension).astype(np.float32)
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec = vec / norm
                vecs.append(vec)
            return np.array(vecs, dtype=np.float32)


        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.astype(np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        """Embed a single query string."""
        return self.embed_texts([query])[0]


embedding_service = EmbeddingService()
