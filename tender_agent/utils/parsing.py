"""Deterministic parsers for Indian tender language (amounts, years, dates)."""
import re
from datetime import date

from dateutil import parser as dateparser

_UNITS = {"crore": 1e7, "crores": 1e7, "cr": 1e7, "lakh": 1e5, "lakhs": 1e5,
          "lac": 1e5, "lacs": 1e5, "million": 1e6, "mn": 1e6, "thousand": 1e3}
_AMOUNT = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(crores?|cr|lakhs?|lacs?|lac|million|mn|thousand)?\b", re.I)
_YEARS = re.compile(r"(\d+)\s*\+?\s*(?:years?|yrs?)", re.I)


def parse_inr(text: str | None) -> float | None:
    """'Rs. 5 Crore' -> 50000000.0 ; 'INR 2,50,000/-' -> 250000.0"""
    if not text:
        return None
    m = _AMOUNT.search(text)
    if not m:
        return None
    number = float(m.group(1).replace(",", ""))
    return number * _UNITS.get((m.group(2) or "").lower(), 1)


def parse_years(text: str | None) -> int | None:
    if not text:
        return None
    m = _YEARS.search(text) or re.search(r"(\d+)", text)
    return int(m.group(1)) if m else None


def parse_deadline(text: str | None) -> date | None:
    if not text:
        return None
    try:
        return dateparser.parse(text, dayfirst=True, fuzzy=True).date()
    except (ValueError, OverflowError):
        return None


def fmt_inr(amount: float | None) -> str:
    if amount is None:
        return "n/a"
    return f"₹{amount / 1e7:.2f} Cr" if amount >= 1e7 else f"₹{amount / 1e5:.2f} Lakh"
