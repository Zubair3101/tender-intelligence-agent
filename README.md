# Tender Intelligence Agent

A multi-agent system that reads Indian government/PSU tender documents and produces a
**bid / no-bid recommendation** with citations, pausing for human approval before the final report.

**Problem:** Bid teams spend hours reading 100+ page tender PDFs just to check eligibility.
**Solution:** Upload a tender → get eligibility checks, a score, and a cited Excel report in minutes.

## Architecture

```
Tender PDF
   │
[1 Ingest]  PyMuPDF → page-aware chunks → dense (bge-small) + sparse (BM25) vectors → Qdrant
   │ (no text? stop)
[2 Extract] targeted queries → hybrid search + RRF → cross-encoder rerank → LLM structured output
   │        → grounding check: every quote must exist on the cited page
   │ (not a tender? stop)
[3 Eligibility] deterministic checks (turnover, years, EMD, deadline, ISO, capability)
   │            + LLM judge only for "similar work" (fuzzy criterion)
[4 Score]   transparent weighted score, hard-fail rules → BID / REVIEW / NO-BID + rationale
   │
[5 Human review]  LangGraph interrupt() — pauses, state checkpointed, human approves/overrides
   │
[6 Report]  Excel: summary, extracted fields with page + quote + grounded flag, all checks
```

## Tech stack (₹0 to build)
LangGraph · Qdrant · fastembed (local embeddings + reranker) · Groq / Gemini free API · PyMuPDF · pandas

## Run it

```bash
pip install -r requirements.txt
cp .env.example .env                 # add your free Groq key
docker compose up -d                 # or set QDRANT_URL=:memory:
python scripts/make_sample_tender.py # creates data/tenders/sample_tender.pdf
python -m tender_agent.cli data/tenders/sample_tender.pdf
pytest -q                            # runs offline, no API key needed
```

Edit `data/company_profile.yaml` to match the bidding company.

## Roadmap
- [x] Phase 1 — core agent pipeline, hybrid RAG, grounding check, human-in-the-loop, Excel report, tests
- [ ] Phase 2 — LangSmith tracing + evaluation set (field accuracy, grounding rate, decision accuracy)
- [ ] Phase 3 — Discovery agent (tender alert emails / portals), OCR for scanned PDFs
- [ ] Phase 4 — FastAPI + Streamlit UI, Docker, deploy on Hugging Face Spaces
