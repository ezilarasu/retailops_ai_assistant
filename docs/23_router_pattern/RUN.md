# How to Run This Example

```bash
# from the repository root
source .venv/bin/activate
python -m examples.10_router_chain
```

What it does: sends four questions (a greeting, a policy question, an inventory question, a vendor question) through `run_router()`. For each one it prints the route the LLM chose (`general` / `rag` / `tools`), the reason, and the answer.

Requires `GROQ_API_KEY` set in `.env` (see project `README.md`). The first run builds the vector index (and downloads small HuggingFace models), so it takes longer. Run from the repository root because data paths are relative.
