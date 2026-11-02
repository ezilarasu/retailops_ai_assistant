# How to Run These Examples

```bash
# from the repository root (data paths in the code are relative)
source .venv/bin/activate

python -m examples.03_text_splitting      # RecursiveCharacterTextSplitter baseline
python -m examples.19_semantic_chunking   # compares recursive vs semantic chunking
```

Neither example calls the LLM, so **no `GROQ_API_KEY` is needed**.

`19_semantic_chunking.py` computes embeddings to find topic boundaries, so the first run downloads the small HuggingFace embedding model (`all-MiniLM-L6-v2`) and takes longer.
