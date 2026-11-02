# How to Run This Example

```bash
# from the repository root
source .venv/bin/activate
python -m examples.08_tools_structured_data
```

What it does: calls RetailOps' `@tool`-decorated functions directly (inventory, vendor, incidents) without going through an agent.

Requires: no API key — it only reads the files in `data/`. Run it from the repository root because the data paths are relative.

To see the same tools used by an LLM agent, run `python -m examples.09_agent_with_tools` (needs `GROQ_API_KEY` set in `.env`; see the project `README.md`).
