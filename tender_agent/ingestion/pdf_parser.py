"""PDF -> page-level text, keeping page numbers for citations."""
from dataclasses import dataclass

import pymupdf as fitz


@dataclass
class Page:
    source: str
    page: int
    text: str


def parse_pdf(path: str) -> list[Page]:
    pages = []
    with fitz.open(path) as doc:
        name = path.replace("\\", "/").split("/")[-1]
        for i, p in enumerate(doc, start=1):
            text = p.get_text("text").strip()
            if text:  # scanned pages return "" -> OCR support is a Phase 3 item
                pages.append(Page(source=name, page=i, text=text))
    return pages
