"""Node 4 — Bid/No-Bid agent: transparent weighted score + LLM-written rationale."""
from ..llm import get_llm
from ..state import TenderState

WEIGHTS = {"turnover": 25, "similar_work": 25, "experience": 20, "certifications": 10,
           "capability": 10, "emd": 5, "deadline": 5}
CREDIT = {"PASS": 1.0, "UNKNOWN": 0.5, "FAIL": 0.0}


def score_checks(checks: list[dict]) -> tuple[int, str]:
    score = round(sum(WEIGHTS.get(c["name"], 0) * CREDIT[c["status"]] for c in checks))
    hard_fail = any(c["hard"] and c["status"] == "FAIL" for c in checks)
    unknowns = sum(c["status"] == "UNKNOWN" for c in checks)
    if hard_fail:
        return score, "NO-BID"
    if score >= 70 and unknowns <= 1:
        return score, "BID"
    return score, "REVIEW" if score >= 50 else "NO-BID"


def _fallback_rationale(checks, decision) -> str:
    fails = [c["name"] for c in checks if c["status"] == "FAIL"]
    unknown = [c["name"] for c in checks if c["status"] == "UNKNOWN"]
    return f"Decision {decision}. Failed: {fails or 'none'}. Needs manual verification: {unknown or 'none'}."


def scoring_node(state: TenderState) -> dict:
    checks = state["checks"]
    score, decision = score_checks(checks)
    lines = "\n".join(f"- {c['name']}: {c['status']} — {c['detail']}" for c in checks)
    prompt = (f"You advise a bid team. Decision: {decision} (score {score}/100).\nChecks:\n{lines}\n\n"
            "Write a 3-sentence rationale a sales head can act on. Use ONLY the checks above; "
            "do not invent risks. If all checks pass, name the check with the smallest margin as the main risk.")
    try:
        rationale = get_llm().invoke(prompt).content
    except Exception:
        rationale = _fallback_rationale(checks, decision)
    return {"score": score, "decision": decision, "rationale": rationale}
