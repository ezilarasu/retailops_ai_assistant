import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_API_KEY = "change_this_local_dev_key"


class Settings:
    llm_provider: str = os.getenv("LLM_PROVIDER", "groq")
    groq_api_key: str | None = os.getenv("GROQ_API_KEY")
    llm_model: str = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")
    # The tool-calling agent uses its own model: gpt-oss-20b often fails to produce valid
    # tool calls when a question needs several (measured: 2 of 8 runs worked, against 8 of 8
    # for gpt-oss-120b). Set TOOLS_LLM_MODEL to an empty value to use LLM_MODEL instead.
    tools_llm_model: str = os.getenv("TOOLS_LLM_MODEL", "openai/gpt-oss-120b").strip() or llm_model
    temperature: float = float(os.getenv("TEMPERATURE", "0"))

    chunk_size: int = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    retrieval_k: int = int(os.getenv("RETRIEVAL_K", "4"))
    vectorstore_dir: str = os.getenv("VECTORSTORE_DIR", "vectorstore/chroma")
    app_env: str = os.getenv("APP_ENV", "local")
    app_version: str = os.getenv("APP_VERSION", "0.2.0")
    app_api_key: str = os.getenv("APP_API_KEY", DEFAULT_API_KEY)
    document_version: str = os.getenv("DOCUMENT_VERSION", "local-v1")
    enable_multi_query: bool = os.getenv("ENABLE_MULTI_QUERY", "true").lower() == "true"
    enable_semantic_chunking: bool = (
        os.getenv("ENABLE_SEMANTIC_CHUNKING", "true").lower() == "true"
    )

    enable_reranking: bool = (
        os.getenv("ENABLE_RERANKING", "true").lower() == "true"
    )

    # Chunks the reranker scores below this are dropped (the best chunk is always kept).
    # Set RERANK_MIN_SCORE=none to keep exactly RETRIEVAL_K chunks regardless of score.
    rerank_min_score: float | None = (
        None
        if os.getenv("RERANK_MIN_SCORE", "-9.0").strip().lower() in ("", "none", "off")
        else float(os.getenv("RERANK_MIN_SCORE", "-9.0"))
    )

settings = Settings()