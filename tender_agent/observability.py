"""LangSmith tracing. Enabled via .env; a no-op when LANGSMITH_TRACING is off."""
import os

from .config import settings

try:
    from langsmith import traceable
except ImportError:                                    # tracing is optional
    def traceable(*args, **kwargs):
        if args and callable(args[0]):
            return args[0]
        return lambda fn: fn


def setup_tracing() -> bool:
    """Export LangSmith env vars so LangChain/LangGraph auto-trace every run."""
    if not settings.langsmith_tracing or not settings.langsmith_api_key:
        return False
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    return True


def run_config(doc_name: str, thread_id: str) -> dict:
    """Config that names the trace in LangSmith and carries the thread for checkpointing."""
    return {
        "configurable": {"thread_id": thread_id},
        "run_name": f"tender:{doc_name}",
        "tags": ["tender-agent"],
        "metadata": {"document": doc_name, "llm": settings.groq_model},
    }
