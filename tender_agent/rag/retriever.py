"""Retrieval pipeline: hybrid search (top 40) -> cross-encoder rerank (top 6)."""
from functools import lru_cache

from ..config import settings
from ..observability import traceable
from .reranker import Reranker
from .store import HybridStore


@lru_cache
def get_store() -> HybridStore:
    return HybridStore()


@lru_cache
def get_reranker() -> Reranker:
    return Reranker()


@traceable(name="hybrid_retrieve", run_type="retriever")
def retrieve(query: str, doc_id: str, top_k: int | None = None) -> list[dict]:
    hits = get_store().search(query, doc_id, settings.top_k_retrieve)
    return get_reranker().rerank(query, hits, top_k or settings.top_k_rerank)