"""Node 6 — Report agent: bid-decision Excel with full citation trail."""
import os

import pandas as pd

from ..config import settings
from ..state import TenderState


def report_node(state: TenderState) -> dict:
    req, human = state.get("requirements", {}), state.get("human_decision", {})
    v = lambda k: (req.get(k) or {}).get("value")
    summary = pd.DataFrame([
        ("Tender title", v("tender_title")), ("Issuing org", v("issuing_org")), ("Tender ID", v("tender_id")),
        ("Deadline", v("submission_deadline")), ("AI score", state.get("score")), ("AI decision", state.get("decision")),
        ("Final decision (human)", human.get("final_decision")), ("Reviewer notes", human.get("notes")),
        ("Rationale", state.get("rationale")),
    ], columns=["Item", "Value"])
    fields = pd.DataFrame([{"field": k, **f} for k, f in req.items()])
    checks = pd.DataFrame(state.get("checks", []))

    os.makedirs(settings.output_dir, exist_ok=True)
    path = os.path.join(settings.output_dir, f"tender_{state['doc_id']}.xlsx")
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        summary.to_excel(xw, sheet_name="Summary", index=False)
        fields.to_excel(xw, sheet_name="Extracted Fields", index=False)
        checks.to_excel(xw, sheet_name="Eligibility Checks", index=False)
    return {"report_path": path}
