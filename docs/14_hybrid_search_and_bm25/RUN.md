# How to Run These Examples

```bash
# from the repository root (data paths in the code are relative)
source .venv/bin/activate

python -m examples.15_hybrid_retrieval   # vector + BM25 candidates merged, then reranked
python -m examples.17_bm25_retrieval     # BM25 keyword retrieval alone
```

Neither example calls the LLM, so **no `GROQ_API_KEY` is needed**.

`15_hybrid_retrieval.py` builds embeddings and (when `ENABLE_RERANKING=true`) loads a cross-encoder reranker, so the first run downloads two small HuggingFace models. `17_bm25_retrieval.py` is pure keyword search and runs instantly.
