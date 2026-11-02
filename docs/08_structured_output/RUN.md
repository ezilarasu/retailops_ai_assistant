# How to Run This Example

```bash
# from the repository root (data paths in the code are relative to it)
source .venv/bin/activate
python -m examples.07_structured_rag_output
```

What it does: runs a RAG query and returns a structured `RAGResponse` (answer, sources, confidence) instead of a plain string.

Requires `GROQ_API_KEY` set in `.env` (see the project `README.md` quickstart). Run it from the repository root. The first run is slower: it builds the vector index in `vectorstore/` and downloads two small HuggingFace models (embeddings and the reranker).
