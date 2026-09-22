"""LangGraph workflow:
ingest -> extract -> (is tender?) -> eligibility -> score -> human_review [pause] -> report
"""
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from .agents import eligibility, extraction, ingest, report, review, scoring
from .state import TenderState


def build_graph(checkpointer=None):
    g = StateGraph(TenderState)
    g.add_node("ingest", ingest.ingest_node)
    g.add_node("extract", extraction.extraction_node)
    g.add_node("eligibility", eligibility.eligibility_node)
    g.add_node("score", scoring.scoring_node)
    g.add_node("human_review", review.human_review_node)
    g.add_node("report", report.report_node)

    g.add_edge(START, "ingest")
    g.add_conditional_edges("ingest", lambda s: "extract" if s.get("num_chunks") else END)
    g.add_conditional_edges("extract", lambda s: "eligibility" if extraction.is_tender(s) else END)
    g.add_edge("eligibility", "score")
    g.add_edge("score", "human_review")
    g.add_edge("human_review", "report")
    g.add_edge("report", END)
    # A checkpointer is required for interrupt(): it saves state while waiting for the human.
    return g.compile(checkpointer=checkpointer or MemorySaver())
