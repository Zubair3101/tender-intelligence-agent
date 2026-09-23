"""Central configuration. Every value can be overridden via .env or environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM (all free options)
    llm_provider: str = "groq"                      # groq | gemini | ollama
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    google_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    ollama_model: str = "llama3.1"

    # Vector store
    qdrant_url: str = "http://localhost:6333"       # ":memory:" for quick local runs
    qdrant_api_key: str | None = None
    collection: str = "tenders"

    # Local, free models (run on CPU via fastembed / ONNX)
    dense_model: str = "BAAI/bge-small-en-v1.5"
    sparse_model: str = "Qdrant/bm25"
    rerank_model: str = "Xenova/ms-marco-MiniLM-L-6-v2"

    # Chunking & retrieval
    chunk_size: int = 800
    chunk_overlap: int = 120
    top_k_retrieve: int = 40
    top_k_rerank: int = 6

    # Grounding: min fuzzy match (0-100) between LLM quote and source text
    grounding_threshold: int = 85

    company_profile_path: str = "data/company_profile.yaml"
    output_dir: str = "outputs"


settings = Settings()
