import logging
from typing import List, Dict, Any
from app.config import settings

try:
    from sentence_transformers import CrossEncoder
except ImportError:
    CrossEncoder = None

logger = logging.getLogger(__name__)


class ReRankerService:
    def __init__(self, model_name: str = settings.RERANKER_MODEL_NAME):
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        if self._model is None:
            if CrossEncoder is not None:
                try:
                    logger.info(f"Loading CrossEncoder model: {self.model_name}")
                    self._model = CrossEncoder(self.model_name)
                except Exception as e:
                    logger.warning(f"Could not load CrossEncoder ({e}). Using length & keyword heuristic re-ranking.")
                    self._model = "heuristic"
            else:
                logger.warning("CrossEncoder not installed. Using length & keyword heuristic re-ranking.")
                self._model = "heuristic"
        return self._model

    def rerank(self, query: str, chunks: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """Re-rank candidate retrieved chunks using CrossEncoder or heuristic fallback."""
        if not chunks:
            return []

        if self.model == "heuristic":
            query_words = set(query.lower().split())
            scored_chunks = []
            for chunk in chunks:
                chunk_words = set(chunk["text"].lower().split())
                overlap = len(query_words.intersection(chunk_words))
                base_score = chunk.get("score", 0.5)
                # Combine embedding score with keyword match heuristic
                combined_score = (base_score * 0.6) + (min(overlap / max(1, len(query_words)), 1.0) * 0.4)
                item = chunk.copy()
                item["score"] = float(combined_score)
                scored_chunks.append(item)

            scored_chunks.sort(key=lambda x: x["score"], reverse=True)
            return scored_chunks[:top_k]

        pairs = [[query, c["text"]] for c in chunks]
        scores = self.model.predict(pairs)

        reranked = []
        for idx, score in enumerate(scores):
            item = chunks[idx].copy()
            item["score"] = float(score)
            reranked.append(item)

        reranked.sort(key=lambda x: x["score"], reverse=True)
        return reranked[:top_k]


reranker_service = ReRankerService()
