from datetime import date

from tender_agent.utils.parsing import parse_deadline, parse_inr, parse_years


def test_parse_inr_units():
    assert parse_inr("Rs. 42.50 Crore") == 425_000_000
    assert parse_inr("EMD: Rs. 42.50 Lakh") == 4_250_000
    assert parse_inr("INR 2,50,000/-") == 250_000
    assert parse_inr("Rs 5 Cr.") == 50_000_000
    assert parse_inr(None) is None


def test_parse_years_and_deadline():
    assert parse_years("minimum 10 years of experience") == 10
    assert parse_deadline("30-11-2026 at 15:00 hrs") == date(2026, 11, 30)
