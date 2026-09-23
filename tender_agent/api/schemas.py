"""Request/response models for the API."""
from pydantic import BaseModel, Field


class JobCreated(BaseModel):
    job_id: str
    document: str
    status: str = "processing"


class JobStatus(BaseModel):
    job_id: str
    document: str
    status: str                      # processing | awaiting_review | completed | failed
    doc_id: str | None = None
    num_pages: int | None = None
    score: int | None = None
    decision: str | None = None
    rationale: str | None = None
    requirements: dict = Field(default_factory=dict)
    checks: list[dict] = Field(default_factory=list)
    final_decision: str | None = None
    notes: str | None = None
    report_ready: bool = False
    errors: list[str] = Field(default_factory=list)


class Decision(BaseModel):
    final_decision: str = Field(description="BID | REVIEW | NO-BID")
    notes: str = ""
