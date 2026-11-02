# Changelog

All notable changes to this project are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [semantic versioning](https://semver.org/).

## [0.1.0] - 2026-11-01

First version: a LangChain and RAG learning project built around one working application, the RetailOps AI Assistant.

### Added

**Learning material**
- 37 concept docs in `docs/`, in learning order: foundation (LLMs, prompts, LCEL, parsers, structured output), retrieval and RAG (loaders, chunking, embeddings, vector stores, hybrid search, reranking, multi-query, history-aware retrieval, RAG chains, evaluation), agents and orchestration (tools, agents, ReAct, routing, memory, FastAPI), production operations (logging, LangSmith, testing, caching, security, indexing) and architecture (production patterns, LangGraph, project map, interview questions, common mistakes, enterprise readiness checklist).
- Every doc follows the same 13-section structure, says where the real code lives in `app/`, and notes where the app writes its own version of something LangChain also provides as a built-in.
- "Lesson from this project" callouts that record real measurements and bugs found while building it.
- 24 runnable examples in `examples/`, with a `RUN.md` next to the docs that have a demo. Ten of them need no API key.
- `KNOWN_ISSUES.md`: the honest list of remaining limits and of what was found and fixed.

**The application (`app/`)**
- A router that sends each question to one of three paths: general chat, RAG over the documents, or a tool-calling agent for stock, vendor and incident lookups.
- RAG pipeline: semantic or recursive chunking, Chroma vector store with stable chunk IDs, hybrid search (vector + BM25), cross-encoder reranking with a relevance cut-off (`RERANK_MIN_SCORE`), multi-query expansion, follow-up question rewriting, structured answers with sources and confidence.
- FastAPI service and a command-line chat. The API takes an optional `session_id` for separate conversations.
- Per-session chat memory that all four routes can read; a response cache for the first question of a conversation; an index manifest that rebuilds the index when documents, chunking settings or the embedding model change.
- Typed errors with one automatic retry for transient model failures, mapped to HTTP 422, 429, 502, 503 and 500.
- API-key authentication (constant-time compare, and a start-up check that refuses the placeholder key outside `APP_ENV=local`), health check, debug-retrieval and index-rebuild endpoints.
- A LangGraph version of the workflow in `app/graph/` (a parallel demo with a human-approval step; the CLI and API do not use it).
- Two configurable models: `LLM_MODEL` (default `openai/gpt-oss-20b`) and `TOOLS_LLM_MODEL` for the tool agent (default `openai/gpt-oss-120b`).

**Quality tooling**
- 46 tests in `tests/`. Only the 3 router tests call the LLM; the rest use fakes and need no key or model.
- An evaluation harness in `evals/` (LLM-as-judge) with a 5-question demo set and saved reports.

### Fixed while preparing this version

The full list, with how each fix was checked, is in `KNOWN_ISSUES.md` (section 2). The main ones:
- The vector index grew a duplicate copy of every chunk on each start; chunks now have stable IDs.
- The semantic chunker split numbered lists in half, so a checklist answer lost its last step.
- `/index/rebuild` removed the index under a running app; it now rebuilds in place and reloads without a restart.
- The tool agent failed most multi-tool questions on the smaller model; it now has its own model setting.
- A model refusal or a rate limit became an unhelpful generic error; errors are now typed, retried once where it makes sense, and reported with a matching status code.
- The cache could serve one conversation's answer to another's follow-up, and tool answers were cached; both fixed.
- The reranker was reloaded on every question (about 2 seconds each); it now loads once.
- Several examples crashed or taught the wrong lesson, and the docs described code that did not exist; all examples were fixed and every doc was audited against the code.

### Verified

On the final code, with `openai/gpt-oss-20b` and `openai/gpt-oss-120b` on Groq and local embeddings:
- 46 of 46 tests pass.
- All 24 examples run cleanly and print correct output.
- The evaluation set scores 5/5.
- `requirements.txt` installs into a brand-new virtual environment on Python 3.12.1 and passes the same tests there. Development used Python 3.10.13.

### Known limitations

See `KNOWN_ISSUES.md` for the complete list. In short: no prompt-injection detection, PII scrubbing or per-user identity (taught as exercises); chat history and the cache live in one process's memory; the router picks one route per question; the evaluation set is a 5-question demo; the free Groq tier has per-minute and per-day token limits; and only macOS with Python 3.10 and 3.12 was tested.
