"""Page-aware chunking: a chunk never crosses a page, so every citation is exact."""
import uuid
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

from ..config import settings
from .pdf_parser import Page


@dataclass
class Chunk:
    id: str
    doc_id: str
    source: str
    page: int
    text: str


def chunk_pages(pages: list[Page], doc_id: str) -> list[Chunk]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)
    chunks = []
    for p in pages:
        for i, text in enumerate(splitter.split_text(p.text)):
            cid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{doc_id}:{p.page}:{i}"))  # deterministic -> re-ingest is idempotent
            chunks.append(Chunk(cid, doc_id, p.source, p.page, text))
    return chunks
