from datetime import date

from tender_agent.agents.eligibility import (check_capability, check_deadline, check_emd,
                                             check_experience, check_turnover)
from tender_agent.agents.scoring import score_checks

PROFILE = {
    "name": "Test Co", "avg_annual_turnover_inr": 750_000_000, "years_in_business": 15,
    "certifications": ["ISO 9001:2015", "ISO 14001:2015"],
    "capabilities": ["ETP", "WTP", "STP", "ZLD"], "max_emd_inr": 5_000_000,
    "completed_projects": [{"title": "2 MLD ZLD system", "value_inr": 180_000_000, "year": 2023}],
}
f = lambda v: {"value": v}


def test_turnover_pass_and_fail():
    assert check_turnover({"min_annual_turnover": f("Rs. 25 Crore")}, PROFILE).status == "PASS"
    assert check_turnover({"min_annual_turnover": f("Rs. 100 Crore")}, PROFILE).status == "FAIL"
    assert check_turnover({}, PROFILE).status == "UNKNOWN"


def test_other_checks():
    assert check_experience({"min_experience_years": f("10 years")}, PROFILE).status == "PASS"
    assert check_capability({"scope_of_work": f("10 MLD WTP on EPC basis")}, PROFILE).status == "PASS"
    assert check_emd({"emd_amount": f("Rs. 1 Crore")}, PROFILE).status == "FAIL"
    closed = check_deadline({"submission_deadline": f("01-01-2026")}, today=date(2026, 9, 1))
    assert closed.status == "FAIL" and closed.hard


def test_hard_fail_forces_no_bid():
    checks = [{"name": "turnover", "status": "FAIL", "hard": True},
              {"name": "similar_work", "status": "PASS", "hard": True}]
    assert score_checks(checks)[1] == "NO-BID"
