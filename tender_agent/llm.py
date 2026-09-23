"""LLM factory + robust structured output."""
import json
import re
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

def structured(schema, prompt):
    """Structured output with a JSON fallback.

    Some models (e.g. gpt-oss on Groq) occasionally answer in prose instead of calling the
    tool, which raises 'tool_use_failed'. We then re-ask for plain JSON and parse it.
    """
    llm = get_llm()
    try:
        return llm.with_structured_output(schema).invoke(prompt)
    except Exception:
        fallback = (f"{prompt}\n\nRespond with ONLY a valid JSON object matching this schema, "
                    f"no markdown, no explanation:\n{json.dumps(schema.model_json_schema())}")
        text = str(llm.invoke(fallback).content)
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            raise
        return schema.model_validate_json(match.group(0))