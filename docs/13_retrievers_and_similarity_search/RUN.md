# How to Run This Example

```bash
# from the repository root (data paths in the code are relative)
source .venv/bin/activate
python -m examples.04_vectorstore_retriever
```

What it does: splits the documents, builds a Chroma vector store, and runs a retriever query against it (also demonstrates doc 12's vector database setup). The retriever is the MMR retriever from `get_retriever()` in `app/vectorstore.py`.

No API key required — it only uses embeddings. The first run downloads the small HuggingFace embedding model (`all-MiniLM-L6-v2`).
