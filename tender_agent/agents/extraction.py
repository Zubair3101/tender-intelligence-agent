"""Node 2 — Extraction agent: targeted RAG queries per field group -> structured output -> grounding check."""
import re
from rapidfuzz import fuzz

from ..config import settings
from ..llm import structured
from ..rag.retriever import retrieve
from ..schemas import BasicInfo, Financials, TechEligibility
from ..state import TenderState

# (output schema, retrieval queries). Multiple focused queries beat one vague query.
FIELD_GROUPS = [
    (BasicInfo, ["name of work full description of work to be executed",
                 "tender reference NIT NIB number dated", "issuing authority employer organisation department",
                 "last date and time of online bid submission", "scope of work description of plant"]),
    (Financials, ["earnest money deposit EMD bid security amount to be deposited",
                  "estimated cost of work tender value probable amount of contract Rs lakh",
                  "minimum average annual turnover of last three financial years",
                  "financial eligibility criteria annual turnover requirement"]),
    (TechEligibility, ["similar work experience completed works eligibility criteria",
                       "minimum years of experience of bidder", "ISO certification registration requirement"]),
]

PROMPT = """You extract facts from an Indian government / PSU tender document.
Use ONLY the context below. For tender_title use the FULL text that follows "Name of Work", never a section heading.
If a field is not in the context, set value, page and quote to null.
Criteria stated as a percentage (e.g. "turnover not less than 50% of estimated cost") ARE valid values — capture them verbatim.
For every value give the page number and a short EXACT quote copied from the context.

CONTEXT:
{context}"""


def _gather_context(queries: list[str], doc_id: str) -> list[dict]:
    seen, hits = set(), []
    for q in queries:
        for h in retrieve(q, doc_id):
            if h["chunk_id"] not in seen:
                seen.add(h["chunk_id"])
                hits.append(h)
    return hits


def _extract_group(schema, hits: list[dict]) -> dict:
    context = "\n\n".join(f"[{h['source']} | page {h['page']}]\n{h['text']}" for h in hits)
    return structured(schema, PROMPT.format(context=context)).model_dump()


def _norm(text: str) -> str:
    """PDFs break lines mid-sentence and pad with spaces — compare on collapsed whitespace."""
    return re.sub(r"\s+", " ", text).strip().lower()


def verify_grounding(field: dict, hits: list[dict]) -> dict:
    """Hallucination guard: the quote must really exist on the cited page."""
    if not field.get("value") or not field.get("quote"):
        return {**field, "grounded": False}
    page_texts = [h["text"] for h in hits if h["page"] == field.get("page")] or [h["text"] for h in hits]
    quote = _norm(field["quote"])
    best = max((fuzz.partial_ratio(quote, _norm(t)) for t in page_texts), default=0)
    return {**field, "grounded": best >= settings.grounding_threshold}


def extraction_node(state: TenderState) -> dict:
    requirements, errors = {}, []
    for schema, queries in FIELD_GROUPS:
        hits = _gather_context(queries, state["doc_id"])
        try:
            group = _extract_group(schema, hits)
        except Exception as e:  # rate limit / malformed output -> degrade gracefully
            errors.append(f"{schema.__name__} extraction failed: {e}")
            continue
        for name, field in group.items():
            requirements[name] = verify_grounding(field, hits)
    _repair_title(requirements)
    return {"requirements": requirements, "errors": errors}


def _repair_title(req: dict) -> None:
    """Headings like 'WORKS' get picked up as the title — fall back to the scope text."""
    title, scope = req.get("tender_title") or {}, req.get("scope_of_work") or {}
    if scope.get("value") and (not title.get("value") or len(title["value"].split()) < 4):
        req["tender_title"] = {**scope}


def is_tender(state: TenderState) -> bool:
    """Router: stop early if nothing tender-like was found."""
    req = state.get("requirements", {})
    return any((req.get(k) or {}).get("value") for k in ("tender_title", "scope_of_work", "tender_id"))
