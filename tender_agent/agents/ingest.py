"""Node 1 — Ingest: parse the tender PDF, chunk it, index it in Qdrant."""
import hashlib

from ..ingestion.chunker import chunk_pages
from ..ingestion.pdf_parser import parse_pdf
from ..rag.retriever import get_store
from ..state import TenderState


def ingest_node(state: TenderState) -> dict:
    path = state["pdf_path"]
    with open(path, "rb") as f:
        doc_id = hashlib.sha1(f.read()).hexdigest()[:12]   # same file -> same id
    pages = parse_pdf(path)
    if not pages:
        return {"doc_id": doc_id, "num_pages": 0, "num_chunks": 0,
                "errors": ["No extractable text (scanned PDF?). OCR is not enabled yet."]}
    chunks = chunk_pages(pages, doc_id)
    get_store().add(chunks)
    return {"doc_id": doc_id, "num_pages": len(pages), "num_chunks": len(chunks)}
