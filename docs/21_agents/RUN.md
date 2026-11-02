# How to Run This Example

```bash
# from the repository root
source .venv/bin/activate
python -m examples.09_agent_with_tools
```

What it does: lets the LLM decide which of RetailOps' tools to call (a tool-calling agent loop built with `create_agent`) instead of calling a tool directly. It asks three questions and prints each final answer.

Requires `GROQ_API_KEY` set in `.env` (see project `README.md`). Run it from the repository root because the tools read `data/` through relative paths. The agent uses its own model, `TOOLS_LLM_MODEL` (default `openai/gpt-oss-120b`), not `LLM_MODEL`; doc 21 explains why.
