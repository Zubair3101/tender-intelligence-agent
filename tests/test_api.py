"""API contract test — the graph is faked, so this runs offline."""
import io

import pytest
from fastapi.testclient import TestClient

from tender_agent.api import main


class FakeGraph:
    """Mimics a graph that pauses for human review, then writes a report."""

    def invoke(self, payload, config):
        if isinstance(payload, dict):
            return {"__interrupt__": [object()], "doc_id": "abc123", "num_pages": 2, "score": 90,
                    "decision": "BID", "rationale": "meets all criteria",
                    "requirements": {"tender_title": {"value": "10 MLD WTP", "page": 1, "grounded": True}},
                    "checks": [{"name": "turnover", "status": "PASS", "hard": True, "detail": "ok"}],
                    "errors": []}
        return {"report_path": "outputs/tender_abc123.xlsx"}


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "graph", FakeGraph())
    monkeypatch.setattr(main, "UPLOAD_DIR", str(tmp_path))
    main.JOBS.clear()
    with TestClient(main.app) as c:
        yield c


def test_upload_review_and_report(client):
    assert client.get("/health").json()["status"] == "ok"

    r = client.post("/tenders", files={"file": ("t.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")})
    assert r.status_code == 202
    job_id = r.json()["job_id"]

    job = client.get(f"/tenders/{job_id}").json()          # background task runs on request
    assert job["status"] == "awaiting_review" and job["decision"] == "BID"

    done = client.post(f"/tenders/{job_id}/decision", json={"final_decision": "BID", "notes": "go"}).json()
    assert done["status"] == "completed" and done["report_ready"]

    assert client.post(f"/tenders/{job_id}/decision", json={"final_decision": "BID"}).status_code == 409
    assert client.get("/tenders/nope").status_code == 404


def test_rejects_non_pdf(client):
    r = client.post("/tenders", files={"file": ("x.txt", io.BytesIO(b"hi"), "text/plain")})
    assert r.status_code == 400
