# How to Run This Example

```bash
# from the repository root (data paths in the code are relative to it)
source .venv/bin/activate
python -m examples.01_basic_chat_chain
```

What it does: sends a question through RetailOps' basic chat chain (no retrieval) and prints the LLM's answer.

Requires `GROQ_API_KEY` set in `.env` (see the project `README.md` quickstart). Run it from the repository root.
