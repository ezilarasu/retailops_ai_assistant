# RetailOps AI Assistant — Learn LangChain & RAG by Reading a Real App

A hands-on LangChain learning project. You get **37 short concept docs**, **runnable examples**, and **one working application** (a retail-operations assistant) that ties them together. Each doc explains a concept in plain language, then shows exactly where it lives in the app.

**Who it's for:** developers who know Python and are new to LangChain, RAG (retrieval-augmented generation), or agents.

**What you'll learn:** calling LLMs, prompts, LCEL (the `prompt | llm | parser` pipe syntax), document loading and chunking, embeddings and vector stores, hybrid search (vector + BM25), reranking, multi-query retrieval, RAG chains, evaluation, tools and agents, routing, memory, FastAPI serving, logging/LangSmith tracing, testing, caching, security basics, and an introduction to LangGraph.

> **Honest scope:** this is a learning baseline, not a hardened enterprise system. Chat memory and the response cache live in one process's memory (history is kept per `session_id`, but lost on restart and not shared between workers), authentication is a single shared API key with no per-user identity, and the evaluation set is a 5-question demo. The docs say so wherever it matters and describe the upgrade paths. [KNOWN_ISSUES.md](KNOWN_ISSUES.md) is the honest list of limits and of what was found and fixed along the way.

---

## How the app works

```text
Question  (+ optional session_id, so each conversation keeps its own history)
   ↓
Router  (an LLM picks one path, using the last few messages of the session)
   ├── general → plain chat chain
   ├── rag     → rewrite follow-ups → multi-query → hybrid search (Chroma + BM25)
   │             → cross-encoder rerank → structured answer + sources + confidence
   └── tools   → tool-calling agent (low stock, vendor lookup, open incidents)
   ↓
Answer  (served by FastAPI at /chat, or the CLI)
```

Two details worth knowing before you read the docs:
- **Two models.** `LLM_MODEL` (default `openai/gpt-oss-20b`) does routing, chat, query rewriting and RAG answers. The tool-calling agent uses its own `TOOLS_LLM_MODEL` (default `openai/gpt-oss-120b`), because in testing the smaller model often failed to produce valid tool calls when a question needed several of them. Doc 21 has the measurements.
- **A LangGraph version** of the same flow (validation, router, RAG subgraph, tools, human approval) lives in `app/graph/`. It is a parallel demo for learning, not what the CLI or API run; see doc 33 and examples 23–28.

---

## Quickstart

**Prerequisites**
- Python 3.10 or newer (the code uses `str | None` type syntax)
- A Groq API key — Groq offers a free tier at <https://console.groq.com> (limits change; see "Free-tier limits" below)
- Internet access on the first run: two small HuggingFace models are downloaded once — the embedding model (`sentence-transformers/all-MiniLM-L6-v2`) and, if reranking is enabled, a cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`)

**1. Install**

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**2. Configure**

```bash
cp .env.example .env
```

Open `.env` and set `GROQ_API_KEY`. Every other variable has a working default and a comment in `.env.example`. Never commit `.env` (it is already in `.gitignore`).

**3. Run something**

Run everything from the **repository root** — the code reads `data/` and writes `vectorstore/` using relative paths.

```bash
# Chat with the assistant in your terminal (needs GROQ_API_KEY)
python -m app.main

# Or start the API
uvicorn app.api:app --reload
# then, in another terminal:
curl -s localhost:8000/health
curl -s -X POST localhost:8000/chat \
  -H "x-api-key: change_this_local_dev_key" \
  -H "Content-Type: application/json" \
  -d '{"question": "How many vacation days do full-time store employees get?"}'
```

**What to expect.** The first start builds the vector index into `vectorstore/` and loads the models. The CLI prints `Loading models and index...` and then `Ready.` before it asks for your first question (a few seconds; the API does the same work on its first request instead). Later starts reuse the index; it is rebuilt automatically when `DOCUMENT_VERSION`, the chunking settings or the embedding model change. When an answer comes from the response cache the CLI adds `(served from cache)`.

**Conversations.** Add an optional `session_id` to keep separate conversations apart. Follow-up questions like "What about part-time employees?" only make sense inside the same session:

```bash
curl -s -X POST localhost:8000/chat -H "x-api-key: change_this_local_dev_key" -H "Content-Type: application/json" \
  -d '{"question": "How many vacation days do full-time store employees get?", "session_id": "alice"}'
curl -s -X POST localhost:8000/chat -H "x-api-key: change_this_local_dev_key" -H "Content-Type: application/json" \
  -d '{"question": "What about part-time employees?", "session_id": "alice"}'

# forget one conversation
curl -s -X POST "localhost:8000/memory/clear?session_id=alice" -H "x-api-key: change_this_local_dev_key"
```

**When something goes wrong, `/chat` tells you what kind of failure it was:**

| HTTP status | Meaning |
|---|---|
| 422 | The model refused the request (for example an attempt to override its instructions) |
| 429 | The AI service is busy or you hit your Groq rate limit; wait and retry |
| 502 | The model provider failed, even after one automatic retry |
| 503 | The configured model is not available (see "model not found" below) |
| 500 | Anything unexpected |

**4. Verify your setup**

```bash
python -m examples.03_text_splitting   # no key needed: proves data loading and the install work
python -m examples.01_basic_chat_chain # needs GROQ_API_KEY: proves the LLM call works
pytest -v                              # 46 tests; only the 3 in tests/test_router.py call the LLM
```

### Free-tier limits and changing models

Hosted model catalogs and free-tier limits change, so treat the names in `.env.example` as a starting point. Groq limits tokens **per minute and per day, per model**. On the key this project was developed with, `gpt-oss-20b` allowed 8,000 tokens per minute and 200,000 per day; running the whole test suite, every example and the evals repeatedly in one day can use that up. When a limit is hit the app answers "The AI service is busy right now" (HTTP 429), and the daily allowance frees up gradually.

**If you see a "model not found / decommissioned" error** (HTTP 503 from the API), list the models your key can use and pick a chat model that supports structured output and tool calling:

```bash
python - <<'EOF'
import os
from dotenv import load_dotenv
load_dotenv(".env")
from groq import Groq
for m in Groq(api_key=os.getenv("GROQ_API_KEY")).models.list().data:
    print(m.id)
EOF
```

Then set `LLM_MODEL=<one of those ids>` in `.env` (and `TOOLS_LLM_MODEL=` the same way, or leave it empty to reuse `LLM_MODEL`). Only the LLM is a hosted service: the embedding model and the reranker run locally on your machine.

---

## Learning path

Start at **[docs/README.md](docs/README.md)** and follow the docs in order. Every doc uses the same 13 sections (What → Why → When → Types → Decision guide → Pros/Cons → Basic example → Real-world example → Best practices → Mistakes → Connections → Summary → Next steps), so you always know where to look.

| Phase | Docs | You'll learn |
|---|---|---|
| Foundation | 01–08 | LLMs, prompts, LCEL, runnables, parsers, structured output |
| Retrieval & RAG | 09–19 | loaders, chunking, embeddings, vector DBs, hybrid search, reranking, RAG chains, evaluation |
| Agents & orchestration | 20–25 | tools, agents, ReAct, routing, memory, FastAPI |
| Production operations | 26–31 | logging, LangSmith, testing, caching, security, indexing |
| Architecture & mastery | 32–37 | production patterns, LangGraph, project map, interview Q&A, mistakes, readiness checklist |

Docs that have a runnable demo include a `RUN.md` next to them with the exact command. All 24 example scripts were run end to end while preparing this project, and each doc says where the real code lives (`app/...`) and where it differs from the generic LangChain building block it teaches.

### Examples that need no API key

These never call the LLM, so you can try them right after `pip install` (examples 04, 15 and 19 download the HuggingFace models on first run):

| Example | Shows |
|---|---|
| `examples/02_document_loading.py` | loading the `data/` files |
| `examples/03_text_splitting.py` | chunking |
| `examples/04_vectorstore_retriever.py` | embeddings + Chroma retrieval |
| `examples/08_tools_structured_data.py` | the retail tools on CSV/JSON data |
| `examples/12_runnable_lambda.py` | a minimal LCEL runnable |
| `examples/13_runnable_parallel.py` | running branches in parallel |
| `examples/14_runnable_branch.py` | conditional routing between chains |
| `examples/15_hybrid_retrieval.py` | vector + BM25 search with reranking |
| `examples/17_bm25_retrieval.py` | keyword search |
| `examples/19_semantic_chunking.py` | recursive vs. semantic chunking |

```bash
python -m examples.03_text_splitting
```

All other examples call the LLM and need `GROQ_API_KEY`.

---

## Repository map

```text
docs/           37 concept docs (docs/NN_name/README.md) + RUN.md for runnable ones
app/            the application: chains, retrievers, router, tools, memory, cache, API
app/graph/      LangGraph version of the workflow (a parallel demo)
examples/       small runnable scripts, one concept each
evals/          RAG evaluation (LLM-as-judge) and saved reports
tests/          46 pytest tests: RAG, router, tools, errors and retries, cache and sessions,
                security, retrieval components, graph
data/           synthetic retail documents and CSV/JSON used as the knowledge base
KNOWN_ISSUES.md the honest list of limits and of what was found and fixed
CHANGELOG.md    release notes for each version
```

`docs/drafts/` holds archived early notes; you don't need to read it.

---

## Tests and evaluation

```bash
pytest -v                        # 46 tests; only tests/test_router.py needs GROQ_API_KEY
python -m evals.run_rag_eval     # runs the demo eval set; needs GROQ_API_KEY
```

Most tests use fakes, so they run in seconds without a key or a model. The first run of `tests/test_rag.py` downloads the embedding model.

The repo ships a 5-question demo evaluation set (`evals/rag_questions.jsonl`) to show how the harness works: a perfect score on five questions proves little. For a real project you would build a much larger set — see doc 19.

---

## Tech stack

Python · LangChain / LangGraph · Groq (LLM) · HuggingFace embeddings · Chroma · BM25 · FastAPI · Pydantic · pytest · LangSmith (optional tracing)

The data in `data/` is fictional and created for teaching.
