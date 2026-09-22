"""Node 5 — Human-in-the-loop: the graph pauses here until a person approves or overrides."""
from langgraph.types import interrupt

from ..state import TenderState


def human_review_node(state: TenderState) -> dict:
    req = state.get("requirements", {})
    answer = interrupt({
        "tender_title": (req.get("tender_title") or {}).get("value"),
        "decision": state["decision"],
        "score": state["score"],
        "rationale": state["rationale"],
        "checks": state["checks"],
    })
    # answer = {"final_decision": "BID" | "REVIEW" | "NO-BID", "notes": "..."}
    return {"human_decision": answer}
