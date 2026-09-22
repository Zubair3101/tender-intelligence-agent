"""End-to-end graph run with the LLM and vector store faked -> runs offline, no API keys."""
import subprocess

from langgraph.types import Command

from tender_agent.agents import eligibility, extraction, ingest, scoring
from tender_agent.config import settings
from tender_agent.graph import build_graph
from tender_agent.schemas import CheckResult, Status


class FakeStore:
    def __init__(self):
        self.chunks = []

    def add(self, chunks):
        self.chunks += chunks
        return len(chunks)


def fake_extract(schema, hits):
    all_fields = {
        "tender_title": ("10 MLD Water Treatment Plant (WTP) on EPC basis", 1),
        "issuing_org": ("Maharashtra Jeevan Pradhikaran", 1),
        "tender_id": ("MJP/WTP/2026/0457", 1),
        "submission_deadline": ("30-11-2030 at 15:00 hrs", 1),
        "scope_of_work": ("10 MLD Water Treatment Plant (WTP) on EPC basis", 1),
        "emd_amount": ("Rs. 42.50 Lakh", 2),
        "estimated_value": ("Rs. 42.50 Crore", 2),
        "min_annual_turnover": ("Rs. 25 Crore", 2),
        "min_experience_years": ("minimum 10 years", 3),
        "similar_work_criteria": ("at least one plant not less than 2 MLD, value not less than Rs. 15 Crore", 3),
        "required_certifications": ("valid ISO 9001 and ISO 14001 certification", 3),
    }
    return {k: {"value": v, "page": p, "quote": v, "grounded": False}
            for k, (v, p) in all_fields.items() if k in schema.model_fields}


def test_full_pipeline(tmp_path, monkeypatch):
    pdf = tmp_path / "t.pdf"
    subprocess.run(["python", "scripts/make_sample_tender.py", str(pdf)], check=True)
    store = FakeStore()
    monkeypatch.setattr(ingest, "get_store", lambda: store)
    monkeypatch.setattr(extraction, "retrieve",
                        lambda q, doc_id: [{"chunk_id": c.id, "page": c.page, "text": c.text, "source": c.source}
                                           for c in store.chunks])
    monkeypatch.setattr(extraction, "_extract_group", fake_extract)
    monkeypatch.setattr(eligibility, "judge_similar_work",
                        lambda r, p: CheckResult(name="similar_work", status=Status.PASS, hard=True, detail="2 MLD ZLD"))
    monkeypatch.setattr(scoring, "get_llm", lambda: (_ for _ in ()).throw(RuntimeError("offline")))
    monkeypatch.setattr(settings, "output_dir", str(tmp_path))

    graph = build_graph()
    cfg = {"configurable": {"thread_id": "test"}}
    paused = graph.invoke({"pdf_path": str(pdf)}, cfg)
    assert "__interrupt__" in paused                    # graph waits for the human
    assert paused["decision"] == "BID"
    assert paused["requirements"]["min_annual_turnover"]["grounded"]   # quote found in PDF text

    done = graph.invoke(Command(resume={"final_decision": "BID", "notes": "go"}), cfg)
    assert done["report_path"].endswith(".xlsx")
