"""Node 3 — Eligibility agent: deterministic checks where possible, LLM judgement only where needed."""
from datetime import date

import yaml

from ..config import settings
from ..llm import get_llm
from ..schemas import CheckResult, SimilarWorkVerdict, Status
from ..state import TenderState
from ..utils.parsing import fmt_inr, parse_deadline, parse_inr, parse_years


def load_profile(path: str | None = None) -> dict:
    with open(path or settings.company_profile_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _val(req: dict, key: str) -> str | None:
    return (req.get(key) or {}).get("value")


def check_turnover(req, profile) -> CheckResult:
    need = parse_inr(_val(req, "min_annual_turnover"))
    have = profile["avg_annual_turnover_inr"]
    if need is None:
        return CheckResult(name="turnover", status=Status.UNKNOWN, hard=True, detail="Turnover criterion not found")
    ok = have >= need
    return CheckResult(name="turnover", status=Status.PASS if ok else Status.FAIL, hard=True,
                       detail=f"Required {fmt_inr(need)}, company has {fmt_inr(have)}")


def check_experience(req, profile) -> CheckResult:
    need = parse_years(_val(req, "min_experience_years"))
    have = profile["years_in_business"]
    if need is None:
        return CheckResult(name="experience", status=Status.UNKNOWN, hard=True, detail="Experience criterion not found")
    return CheckResult(name="experience", status=Status.PASS if have >= need else Status.FAIL, hard=True,
                       detail=f"Required {need} yrs, company has {have} yrs")


def check_certifications(req, profile) -> CheckResult:
    text = (_val(req, "required_certifications") or "").lower()
    if not text:
        return CheckResult(name="certifications", status=Status.UNKNOWN, hard=False, detail="No certification requirement found")
    required = [n for n in ("9001", "14001", "45001") if n in text]
    held = [n for n in required if any(n in c for c in profile["certifications"])]
    missing = [n for n in required if n not in held]
    return CheckResult(name="certifications", status=Status.FAIL if missing else Status.PASS, hard=True,
                       detail=f"Required ISO {required or 'none'}; held {held or 'none'}; missing {missing or 'none'}")


def check_capability(req, profile) -> CheckResult:
    scope = f"{_val(req, 'scope_of_work') or ''} {_val(req, 'tender_title') or ''}".lower()
    matched = [c for c in profile["capabilities"] if c.lower() in scope]
    return CheckResult(name="capability", status=Status.PASS if matched else Status.FAIL, hard=False,
                       detail=f"Scope matches: {matched or 'none of our capabilities'}")


def check_emd(req, profile) -> CheckResult:
    emd = parse_inr(_val(req, "emd_amount"))
    if emd is None:
        return CheckResult(name="emd", status=Status.UNKNOWN, hard=False, detail="EMD not found")
    ok = emd <= profile["max_emd_inr"]
    return CheckResult(name="emd", status=Status.PASS if ok else Status.FAIL, hard=False,
                       detail=f"EMD {fmt_inr(emd)} vs limit {fmt_inr(profile['max_emd_inr'])}")


def check_deadline(req, today: date | None = None) -> CheckResult:
    d = parse_deadline(_val(req, "submission_deadline"))
    if d is None:
        return CheckResult(name="deadline", status=Status.UNKNOWN, hard=False, detail="Deadline not parsed")
    days = (d - (today or date.today())).days
    if days < 0:
        return CheckResult(name="deadline", status=Status.FAIL, hard=True, detail=f"Closed on {d} ({-days} days ago)")
    return CheckResult(name="deadline", status=Status.PASS if days >= 7 else Status.FAIL, hard=False,
                       detail=f"{days} days left (closes {d})")


def judge_similar_work(req, profile) -> CheckResult:
    criterion = _val(req, "similar_work_criteria")
    if not criterion:
        return CheckResult(name="similar_work", status=Status.UNKNOWN, hard=True, detail="Similar-work criterion not found")
    projects = "\n".join(f"- {p['title']} | value {fmt_inr(p['value_inr'])} | {p['year']}" for p in profile["completed_projects"])
    prompt = (f"Tender similar-work criterion:\n{criterion}\n\nCompany's completed projects:\n{projects}\n\n"
              "Does at least one project satisfy the criterion (type of work AND value)? "
              "Answer PASS, FAIL, or UNKNOWN if the criterion is ambiguous.")
    try:
        v = get_llm().with_structured_output(SimilarWorkVerdict).invoke(prompt)
        return CheckResult(name="similar_work", status=v.status, hard=True,
                           detail=f"{v.reason} (matched: {v.matched_project or 'none'})")
    except Exception as e:
        return CheckResult(name="similar_work", status=Status.UNKNOWN, hard=True, detail=f"LLM judge failed: {e}")


def run_checks(req: dict, profile: dict) -> list[CheckResult]:
    return [check_turnover(req, profile), check_experience(req, profile), judge_similar_work(req, profile),
            check_certifications(req, profile), check_capability(req, profile), check_emd(req, profile),
            check_deadline(req)]


def eligibility_node(state: TenderState) -> dict:
    checks = run_checks(state["requirements"], load_profile())
    return {"checks": [c.model_dump(mode="json") for c in checks]}
