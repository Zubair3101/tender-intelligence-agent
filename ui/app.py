"""Streamlit review UI — upload a tender, read the evidence, approve or override."""
import os
import time

import pandas as pd
import requests
import streamlit as st

API = os.getenv("API_URL", "http://localhost:8000")
ICON = {"PASS": "✅", "FAIL": "❌", "UNKNOWN": "❔"}

st.set_page_config(page_title="Tender Intelligence Agent", page_icon="📄", layout="wide")
st.title("📄 Tender Intelligence Agent")
st.caption("Upload a tender PDF → eligibility checks with page-level citations → your decision → Excel report")

if "job_id" not in st.session_state:
    st.session_state.job_id = None

uploaded = st.file_uploader("Tender document (PDF)", type="pdf")
if uploaded and st.button("Analyse tender", type="primary"):
    r = requests.post(f"{API}/tenders", files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")}, timeout=60)
    r.raise_for_status()
    st.session_state.job_id = r.json()["job_id"]

if not st.session_state.job_id:
    st.stop()

job_id = st.session_state.job_id
placeholder = st.empty()
job = requests.get(f"{API}/tenders/{job_id}", timeout=30).json()
while job["status"] == "processing":
    placeholder.info("Reading the document, retrieving criteria and checking eligibility…")
    time.sleep(3)
    job = requests.get(f"{API}/tenders/{job_id}", timeout=30).json()
placeholder.empty()

if job["status"] == "failed":
    st.error("Analysis failed")
    for e in job.get("errors", []):
        st.write(f"- {e}")
    st.stop()

req = job.get("requirements", {})
value = lambda k: (req.get(k) or {}).get("value") or "—"

st.subheader(value("tender_title"))
c1, c2, c3, c4 = st.columns(4)
c1.metric("AI decision", job.get("decision") or "—")
c2.metric("Score", f"{job.get('score', 0)}/100")
c3.metric("Pages", job.get("num_pages") or 0)
c4.metric("Deadline", value("submission_deadline"))

st.markdown("### Eligibility checks")
for c in job.get("checks", []):
    st.write(f"{ICON.get(c['status'], '•')} **{c['name']}** — {c['detail']}")
st.info(job.get("rationale") or "")

with st.expander("Extracted criteria and citations", expanded=False):
    rows = [{"field": k, "value": v.get("value"), "page": v.get("page"),
             "grounded": "✅" if v.get("grounded") else "⚠️", "quote": v.get("quote")}
            for k, v in req.items()]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.caption("⚠️ = the quote could not be verified against the cited page — check it manually.")

st.markdown("### Your decision")
if job["status"] == "awaiting_review":
    options = ["BID", "REVIEW", "NO-BID"]
    choice = st.radio("Final decision", options, horizontal=True,
                      index=options.index(job["decision"]) if job.get("decision") in options else 1)
    notes = st.text_input("Notes (optional)")
    if st.button("Confirm and generate report", type="primary"):
        requests.post(f"{API}/tenders/{job_id}/decision",
                      json={"final_decision": choice, "notes": notes}, timeout=120).raise_for_status()
        st.rerun()
else:
    st.success(f"Final decision: {job.get('final_decision')} — {job.get('notes') or 'no notes'}")
    if job.get("report_ready"):
        report = requests.get(f"{API}/tenders/{job_id}/report", timeout=60)
        st.download_button("⬇️ Download Excel report", report.content, file_name=f"tender_{job_id[:8]}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
