# How to Run This Example

```bash
# from the repository root (data paths in the code are relative)
source .venv/bin/activate
python -m examples.21_multi_query_retrieval
```

What it does: asks the LLM to rephrase each sample question and prints the generated retrieval queries (the original question plus up to three variants). It stops there — it does not run retrieval. The full pipeline (pooling results from every query and reranking them) lives in `retrieve_with_multi_query()` in `app/multi_query.py` and runs inside the RAG chain.

Requires `GROQ_API_KEY` set in `.env` (see the project `README.md`), because it calls the LLM.
