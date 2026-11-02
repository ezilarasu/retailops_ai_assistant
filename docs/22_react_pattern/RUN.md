# How to Run These Examples

```bash
# from the repository root
source .venv/bin/activate

python -m examples.example_26_prebuilt_toolnode   # hand-wired LangGraph loop with the prebuilt ToolNode
python -m examples.example_27_create_react_agent  # LangGraph's prebuilt create_react_agent helper
```

What they do: ask "Show low stock items for store 102." and print every message of the run (human, AI tool call, tool result, final AI answer), so you can watch the ReAct loop.

Requires `GROQ_API_KEY` set in `.env` (see project `README.md`). Run from the repository root because the tools read `data/` through relative paths. Both examples use the tool agent's own model, `TOOLS_LLM_MODEL` (default `openai/gpt-oss-120b`).
