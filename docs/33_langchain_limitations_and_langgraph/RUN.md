# How to Run These Examples

```bash
# from the repository root (data paths are relative)
source .venv/bin/activate

python -m examples.example_23_langgraph_router    # LangGraph state machine: one question per route
python -m examples.example_24_langgraph_memory    # checkpointed memory across turns (thread_id)
python -m examples.example_25_langgraph_streaming # streaming events from a LangGraph run
python -m examples.example_26_prebuilt_toolnode   # tool loop built by hand with ToolNode
python -m examples.example_27_create_react_agent  # langgraph.prebuilt create_react_agent
python -m examples.example_28_approval            # human-in-the-loop approval via interrupt()
```

Requires `GROQ_API_KEY` set in `.env` (see project `README.md`). Every example above calls the LLM. The graph builds without a key, but the first question builds the app container (vector index, embedding model, reranker), so the first run is slower and downloads small HuggingFace models.

Notes:
- `app/graph/` is a parallel demo: the CLI and API use `run_router()`, not this graph.
- Example 23 asks three questions (general, RAG, tools). The tools question reaches the approval step, so the graph pauses there; the printed answer is the agent's result before approval. Timings and debug info are reset every turn, so each question shows only its own stages.
- Example 24 asks two related questions on the same `thread_id`, so the second can use the first as context, then shows an empty question being rejected by the validation node.
- Example 25 prints one event per node (`validation`, `router`, `rag`); the final `rag` event carries the answer. The `rag` node is a subgraph (rewrite, retrieve, generate), shown as a single event.
- Example 28 shows the full pause-and-resume cycle with `Command(resume=...)`.
- The tool agent in examples 23, 26, 27 and 28 uses `TOOLS_LLM_MODEL` (default `openai/gpt-oss-120b`), not `LLM_MODEL`.
