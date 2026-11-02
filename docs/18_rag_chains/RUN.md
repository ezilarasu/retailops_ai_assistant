# How to Run These Examples

```bash
# from the repository root (data paths in the code are relative)
source .venv/bin/activate

python -m examples.05_basic_rag_chain        # the full RetailOps RAG chain, structured output
python -m examples.06_basic_rag_with_parser  # a simpler hand-built chain ending in StrOutputParser (see doc 07)
```

Both examples call the LLM, so they need `GROQ_API_KEY` set in `.env` (see the project `README.md`).

The first run is slower: it builds the vector index and downloads small HuggingFace models (embeddings, plus the reranker for example 05). Example 05 loads the whole app container, so it also builds the router and tool-agent chains.
