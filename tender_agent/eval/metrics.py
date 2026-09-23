"""Scoring an agent run against human-written ground truth."""
import re

from rapidfuzz import fuzz

from ..utils.parsing import parse_inr, parse_years

AMOUNT_FIELDS = {"emd_amount", "estimated_value", "min_annual_turnover"}
FUZZY_THRESHOLD = 85


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9% ]+", " ", re.sub(r"\s+", " ", str(text).lower())).strip()


def values_match(field: str, predicted: str | None, expected: str | None) -> bool:
    """Amounts compare numerically (±1%), years exactly, free text fuzzily."""
    if expected is None:
        return predicted is None
    if predicted is None:
        return False
    if field in AMOUNT_FIELDS and "%" not in str(expected):
        p, e = parse_inr(predicted), parse_inr(expected)
        if p is not None and e:
            return abs(p - e) <= 0.01 * e
    if field == "min_experience_years":
        return parse_years(predicted) == parse_years(expected)
    return fuzz.token_set_ratio(_norm(predicted), _norm(expected)) >= FUZZY_THRESHOLD


def evaluate_fields(requirements: dict, expected: dict) -> list[dict]:
    rows = []
    for field, exp in expected.items():
        got = requirements.get(field) or {}
        exp_value = exp.get("value") if isinstance(exp, dict) else exp
        exp_page = exp.get("page") if isinstance(exp, dict) else None
        rows.append({
            "field": field,
            "expected": exp_value,
            "predicted": got.get("value"),
            "correct": values_match(field, got.get("value"), exp_value),
            "grounded": bool(got.get("grounded")),
            "page_correct": exp_page is None or got.get("page") == exp_page,
        })
    return rows


def aggregate(rows: list[dict]) -> dict:
    present = [r for r in rows if r["expected"] is not None]
    extracted = [r for r in rows if r["predicted"] is not None]
    pct = lambda n, d: round(100 * n / d, 1) if d else 0.0
    return {
        "fields_expected": len(present),
        "fields_extracted": len(extracted),
        "coverage_pct": pct(len([r for r in present if r["predicted"] is not None]), len(present)),
        "accuracy_pct": pct(sum(r["correct"] for r in present), len(present)),
        "grounding_pct": pct(sum(r["grounded"] for r in extracted), len(extracted)),
        # extracted but unverifiable against the source = potential hallucination
        "ungrounded_pct": pct(sum(not r["grounded"] for r in extracted), len(extracted)),
        "page_accuracy_pct": pct(sum(r["page_correct"] for r in extracted), len(extracted)),
        "false_positive_pct": pct(len([r for r in rows if r["expected"] is None and r["predicted"] is not None]), len(rows)),
    }


def combine(per_doc: list[dict]) -> dict:
    """Micro-average across documents, plus decision accuracy."""
    keys = ["coverage_pct", "accuracy_pct", "grounding_pct", "ungrounded_pct", "page_accuracy_pct"]
    n = len(per_doc) or 1
    out = {k: round(sum(d["metrics"][k] for d in per_doc) / n, 1) for k in keys}
    judged = [d for d in per_doc if d.get("expected_decision")]
    out["decision_accuracy_pct"] = round(
        100 * sum(d["decision"] == d["expected_decision"] for d in judged) / len(judged), 1) if judged else None
    out["documents"] = len(per_doc)
    return out
