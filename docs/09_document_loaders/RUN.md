# How to Run This Example

```bash
# from the repository root (data paths in the code are relative)
source .venv/bin/activate
python -m examples.02_document_loading
```

What it does: loads the RetailOps knowledge base files (`data/*.txt`) into LangChain `Document` objects and prints the source and the first 300 characters of each.

No API key required — it is pure document loading.
