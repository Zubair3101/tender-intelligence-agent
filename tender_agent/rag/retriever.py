"""Retrieval pipeline: hybrid search (top 20) -> cross-encoder rerank (top 5)."""
from functools import lru_cache

from ..config import settings
from .reranker import Reranker
from .store import HybridStore


@lru_cache
def get_store() -> HybridStore:
    return HybridStore()


@lru_cache
def get_reranker() -> Reranker:
    return Reranker()


def retrieve(query: str, doc_id: str, top_k: int | None = None) -> list[dict]:
    hits = get_store().search(query, doc_id, settings.top_k_retrieve)
    return get_reranker().rerank(query, hits, top_k or settings.top_k_rerank)
