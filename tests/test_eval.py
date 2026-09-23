from tender_agent.eval.metrics import aggregate, combine, evaluate_fields, values_match


def test_amount_and_text_matching():
    assert values_match("emd_amount", "Rs. 8,461/-", "Rs 8461")           # numeric, ±1%
    assert not values_match("emd_amount", "Rs. 2", "Rs 8461")
    assert values_match("min_experience_years", "minimum 10 years", "10 years")
    assert values_match("issuing_org", "INDIAN INSTITUTE OF INFORMATION TECHNOLOGY UNA",
                        "Indian Institute of Information Technology Una")
    assert values_match("min_experience_years", None, None)               # absent in tender
    assert not values_match("tender_id", None, "ABC/123")                 # missed extraction


def test_metrics():
    req = {"tender_id": {"value": "ABC/123", "page": 1, "grounded": True},
           "emd_amount": {"value": "Rs 2", "page": 4, "grounded": False}}
    expected = {"tender_id": {"value": "ABC/123", "page": 1}, "emd_amount": "Rs 8461",
                "min_experience_years": None}
    rows = evaluate_fields(req, expected)
    m = aggregate(rows)
    assert m["accuracy_pct"] == 50.0        # 1 of 2 stated fields correct
    assert m["grounding_pct"] == 50.0
    assert m["ungrounded_pct"] == 50.0
    assert m["page_accuracy_pct"] == 100.0

    overall = combine([{"metrics": m, "decision": "BID", "expected_decision": "BID"}])
    assert overall["decision_accuracy_pct"] == 100.0 and overall["documents"] == 1
