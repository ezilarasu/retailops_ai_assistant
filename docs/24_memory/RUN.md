# How to Run This Example

```bash
# from the repository root
source .venv/bin/activate
python -m examples.11_memory_followup
```

What it does: clears the default session's memory, then asks four questions through `run_router()` — a policy question, its follow-up ("What about part-time employees?"), an inventory question, and its follow-up ("What about store 310?"). It prints the route, reason and answer for each, so you can see how conversation history carries across turns (the follow-ups work on both the RAG and the tools route, because both receive the recent history).

Requires `GROQ_API_KEY` set in `.env` (see project `README.md`). The first run builds the vector index (and downloads small HuggingFace models), so it takes longer. Run from the repository root because data paths are relative.
