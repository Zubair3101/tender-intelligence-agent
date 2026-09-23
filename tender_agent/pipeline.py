"""Headless pipeline (no human pause) — used by evaluation and, later, the API."""
import time

from .agents.eligibility import eligibility_node
from .agents.extraction import extraction_node
from .agents.ingest import ingest_node
from .agents.scoring import scoring_node
from .observability import setup_tracing, traceable

STAGES = [("ingest", ingest_node), ("extract", extraction_node),
          ("eligibility", eligibility_node), ("score", scoring_node)]


@traceable(name="tender_pipeline")
def run_pipeline(pdf_path: str) -> dict:
    setup_tracing()
    state: dict = {"pdf_path": pdf_path, "errors": [], "timings": {}}
    for name, node in STAGES:
        start = time.perf_counter()
        out = node(state)
        state["errors"] = state["errors"] + out.pop("errors", [])
        state.update(out)
        state["timings"][name] = round(time.perf_counter() - start, 2)
        if name == "ingest" and not state.get("num_chunks"):
            break
    return state
