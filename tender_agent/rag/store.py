"""Qdrant hybrid store: dense (semantic) + sparse BM25 (keyword) vectors in one collection."""
from fastembed import SparseTextEmbedding, TextEmbedding
from qdrant_client import QdrantClient, models

from ..config import settings
from ..ingestion.chunker import Chunk


class HybridStore:
    def __init__(self, client: QdrantClient | None = None):
        if client is None:
            client = (QdrantClient(location=":memory:") if settings.qdrant_url == ":memory:"
                      else QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key))
        self.client = client
        self.name = settings.collection
        self.dense = TextEmbedding(settings.dense_model)
        self.sparse = SparseTextEmbedding(settings.sparse_model)
        self._ensure_collection()

    def _ensure_collection(self):
        if self.client.collection_exists(self.name):
            return
        dim = len(next(iter(self.dense.embed(["dimension probe"]))))
        self.client.create_collection(
            self.name,
            vectors_config={"dense": models.VectorParams(size=dim, distance=models.Distance.COSINE)},
            sparse_vectors_config={"sparse": models.SparseVectorParams(modifier=models.Modifier.IDF)},
        )
        self.client.create_payload_index(self.name, "doc_id", models.PayloadSchemaType.KEYWORD)

    def add(self, chunks: list[Chunk]) -> int:
        texts = [c.text for c in chunks]
        dense = list(self.dense.embed(texts))
        sparse = list(self.sparse.embed(texts))
        points = [
            models.PointStruct(
                id=c.id,
                vector={"dense": d.tolist(),
                        "sparse": models.SparseVector(indices=s.indices.tolist(), values=s.values.tolist())},
                payload={"chunk_id": c.id, "doc_id": c.doc_id, "source": c.source, "page": c.page, "text": c.text},
            )
            for c, d, s in zip(chunks, dense, sparse)
        ]
        self.client.upsert(self.name, points)
        return len(points)

    def search(self, query: str, doc_id: str, limit: int) -> list[dict]:
        q_dense = next(iter(self.dense.query_embed(query))).tolist()
        q_sparse = next(iter(self.sparse.query_embed(query)))
        only_this_doc = models.Filter(must=[models.FieldCondition(key="doc_id", match=models.MatchValue(value=doc_id))])
        res = self.client.query_points(
            self.name,
            prefetch=[
                models.Prefetch(query=q_dense, using="dense", limit=limit, filter=only_this_doc),
                models.Prefetch(query=models.SparseVector(indices=q_sparse.indices.tolist(), values=q_sparse.values.tolist()),
                                using="sparse", limit=limit, filter=only_this_doc),
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),  # Reciprocal Rank Fusion
            limit=limit,
            with_payload=True,
        )
        return [{**p.payload, "score": p.score} for p in res.points]
