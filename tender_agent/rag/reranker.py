"""Cross-encoder reranker: scores (query, chunk) pairs jointly — more accurate than vector similarity."""
from fastembed.rerank.cross_encoder import TextCrossEncoder

from ..config import settings


class Reranker:
    def __init__(self):
        self.model = TextCrossEncoder(settings.rerank_model)

    def rerank(self, query: str, hits: list[dict], top_k: int) -> list[dict]:
        if not hits:
            return []
        scores = list(self.model.rerank(query, [h["text"] for h in hits]))
        ranked = sorted(zip(hits, scores), key=lambda x: x[1], reverse=True)
        return [{**h, "rerank_score": float(s)} for h, s in ranked[:top_k]]
