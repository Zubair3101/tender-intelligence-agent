"""Shared LangGraph state. Plain dicts keep checkpoints JSON-serialisable."""
import operator
from typing import Annotated, TypedDict


class TenderState(TypedDict, total=False):
    pdf_path: str
    doc_id: str
    num_pages: int
    num_chunks: int
    requirements: dict          # field -> Extracted (as dict)
    checks: list[dict]          # CheckResult dicts
    score: int
    decision: str               # BID | REVIEW | NO-BID
    rationale: str
    human_decision: dict        # {"final_decision": ..., "notes": ...}
    report_path: str
    errors: Annotated[list[str], operator.add]
