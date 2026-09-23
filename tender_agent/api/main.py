"""FastAPI service. The graph pauses at human_review; the decision endpoint resumes it.

State lives in an in-process checkpointer + job dict — fine for a single worker.
For multiple workers, swap MemorySaver for a Postgres checkpointer and JOBS for Redis.
"""
import os
import shutil
import uuid
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from langgraph.types import Command

from ..config import settings
from ..graph import build_graph
from ..observability import run_config, setup_tracing
from .schemas import Decision, JobCreated, JobStatus

UPLOAD_DIR = "data/tenders"
JOBS: dict[str, dict] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    app.state.tracing = setup_tracing()
    yield


app = FastAPI(title="Tender Intelligence Agent", version="1.0", lifespan=lifespan,
              description="Upload a tender PDF, get a citation-backed bid/no-bid recommendation.")
graph = build_graph()


def _analyse(job_id: str) -> None:
    """Runs in the background: ingest -> extract -> eligibility -> score -> pause."""
    job = JOBS[job_id]
    try:
        result = graph.invoke({"pdf_path": job["pdf_path"]}, run_config(job["document"], job_id))
        job["errors"] = result.get("errors", [])
        if "__interrupt__" not in result:
            job.update(status="failed",
                       errors=job["errors"] or ["Document did not look like a tender"])
            return
        job.update(status="awaiting_review", doc_id=result.get("doc_id"),
                   num_pages=result.get("num_pages"), score=result.get("score"),
                   decision=result.get("decision"), rationale=result.get("rationale"),
                   requirements=result.get("requirements", {}), checks=result.get("checks", []))
    except Exception as e:                       # noqa: BLE001 — surface any failure to the caller
        job.update(status="failed", errors=[str(e)])


@app.get("/health")
def health():
    return {"status": "ok", "llm": settings.groq_model, "tracing": app.state.tracing}


@app.post("/tenders", response_model=JobCreated, status_code=202)
async def upload_tender(background: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")
    job_id = str(uuid.uuid4())
    path = os.path.join(UPLOAD_DIR, f"{job_id[:8]}_{file.filename}")
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    JOBS[job_id] = {"job_id": job_id, "document": file.filename, "pdf_path": path, "status": "processing"}
    background.add_task(_analyse, job_id)
    return JobCreated(job_id=job_id, document=file.filename)


@app.get("/tenders", response_model=list[JobStatus])
def list_tenders():
    return [JobStatus(**j) for j in JOBS.values()]


@app.get("/tenders/{job_id}", response_model=JobStatus)
def get_tender(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(404, "Unknown job")
    return JobStatus(**JOBS[job_id])


@app.post("/tenders/{job_id}/decision", response_model=JobStatus)
def submit_decision(job_id: str, decision: Decision):
    """Human-in-the-loop: resumes the paused graph and writes the Excel report."""
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Unknown job")
    if job["status"] != "awaiting_review":
        raise HTTPException(409, f"Job is '{job['status']}', not awaiting review")
    result = graph.invoke(
        Command(resume={"final_decision": decision.final_decision, "notes": decision.notes}),
        run_config(job["document"], job_id))
    job.update(status="completed", final_decision=decision.final_decision, notes=decision.notes,
               report_path=result.get("report_path"), report_ready=bool(result.get("report_path")))
    return JobStatus(**job)


@app.get("/tenders/{job_id}/report")
def download_report(job_id: str):
    job = JOBS.get(job_id)
    if not job or not job.get("report_path"):
        raise HTTPException(404, "Report not ready")
    return FileResponse(job["report_path"], filename=os.path.basename(job["report_path"]),
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
