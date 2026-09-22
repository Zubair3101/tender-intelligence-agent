"""LLM factory — swap providers from .env without touching agent code."""
from functools import lru_cache

from .config import settings


@lru_cache
def get_llm():
    provider = settings.llm_provider.lower()
    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model=settings.groq_model, api_key=settings.groq_api_key, temperature=0)
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=settings.gemini_model, google_api_key=settings.google_api_key, temperature=0)
    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=settings.ollama_model, temperature=0)
    raise ValueError(f"Unknown LLM provider: {provider}")
