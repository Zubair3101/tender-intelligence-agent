"""Typed contracts passed between agents."""
from enum import Enum

from pydantic import BaseModel, Field


class Extracted(BaseModel):
    """One extracted tender field, with the evidence behind it."""
    value: str | None = Field(None, description="The answer exactly as stated in the tender, or null if not present in the context")
    page: int | None = Field(None, description="Page number where the answer was found")
    quote: str | None = Field(None, description="Short EXACT quote (under 25 words) from the context supporting the value")
    grounded: bool = Field(False, description="Leave false; set by the system after verification")


class BasicInfo(BaseModel):
    tender_title: Extracted
    issuing_org: Extracted
    tender_id: Extracted
    submission_deadline: Extracted
    scope_of_work: Extracted


class Financials(BaseModel):
    emd_amount: Extracted
    estimated_value: Extracted
    min_annual_turnover: Extracted


class TechEligibility(BaseModel):
    min_experience_years: Extracted
    similar_work_criteria: Extracted
    required_certifications: Extracted


class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class CheckResult(BaseModel):
    name: str
    status: Status
    hard: bool          # a hard FAIL means we are not eligible to bid
    detail: str


class SimilarWorkVerdict(BaseModel):
    status: Status
    matched_project: str | None = Field(None, description="Title of the company project that satisfies the criterion, if any")
    reason: str = Field(description="One sentence explanation")
