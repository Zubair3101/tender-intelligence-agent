"""Generate a synthetic 3-page tender PDF for demos and tests (no real tender data needed)."""
import sys

import pymupdf as fitz

PAGES = [
    """NOTICE INVITING TENDER (NIT)
Tender Reference No: MJP/WTP/2026/0457
Issuing Authority: Maharashtra Jeevan Pradhikaran, Public Works Division, Pune
Name of Work: Design, supply, erection and commissioning of 10 MLD Water Treatment Plant (WTP)
on EPC basis including 5 years O&M at Shirur, District Pune.
Last date and time of online bid submission: 30-11-2026 at 15:00 hrs.""",
    """FINANCIAL CONDITIONS
Estimated cost of work: Rs. 42.50 Crore.
Earnest Money Deposit (EMD): Rs. 42.50 Lakh to be paid online.
The bidder shall have a minimum average annual financial turnover of Rs. 25 Crore
during the last three financial years ending 31-03-2026.""",
    """TECHNICAL ELIGIBILITY CRITERIA
The bidder should have minimum 10 years of experience in water / wastewater treatment works.
Similar work: The bidder must have successfully completed at least one water or wastewater
treatment plant of capacity not less than 2 MLD with value not less than Rs. 15 Crore in the last 7 years.
The bidder must hold valid ISO 9001 and ISO 14001 certification.""",
]

out = sys.argv[1] if len(sys.argv) > 1 else "data/tenders/sample_tender.pdf"
doc = fitz.open()
for text in PAGES:
    doc.new_page().insert_textbox(fitz.Rect(50, 50, 550, 800), text, fontsize=11)
doc.save(out)
print(f"Saved {out}")
