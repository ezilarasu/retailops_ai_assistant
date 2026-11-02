# RetailOps Project Architecture
> How every concept in this learning series fits together in one real application.

## 📌 What Is It?

**RetailOps AI Assistant** is a production-baseline RAG application that serves as the running example throughout this learning series. It answers questions for retail store operators using three workflow paths: static knowledge retrieval (RAG), live operational data (tools), and general conversation.

Understanding its architecture gives you a map of how LangChain's core concepts — LLMs, prompts, chains, memory, parsers, embeddings, retrieval, agents — connect in a real system. Think of it as the floor plan of a house you have been visiting room by room: each earlier doc explained one room, this doc shows the hallways between them.

```
RetailOps Request Lifecycle:

  HTTP POST /chat
       ↓
  FastAPI endpoint         ← doc 25: API layer, x-api-key check (doc 30)
       ↓
  RetailOpsAssistantService.ask()   ← app/services.py
       ↓
  Cache check              ← doc 29: first question of a session only; hit = skip everything
       ↓
  run_router()             ← doc 23: LLM classifies the question (app/router.py)
  ┌────────────────────────────────────────┐
  │ general   │  rag         │  tools      │
  ↓           ↓              ↓
General     Rewrite        Tool-calling agent
chain       question       (create_agent)   ← docs 20-22: tools + agents
↓           ↓              ↓
Answer      Multi-query    Tool calls
            ↓              ↓
            Hybrid search  Answer
            (vector+BM25)
            ↓
            Cross-encoder rerank
            ↓
            RAG chain      ← doc 18: structured output
            ↓
            RAGResponse
  └────────────────────────────────────────┘
       ↓
  Memory update            ← doc 24: done inside run_router()
  Cache write              ← doc 29: done by the service (first-turn general/rag answers only)
       ↓
  JSON response (route, reason, answer, sources, confidence, latency_ms, cache_hit)
  (on failure: route "error", an error code, a user-safe message, and a matching HTTP status)
```

## ❓ Why Does It Exist?

RetailOps exists to answer a practical question: "How do all these LangChain concepts actually fit together?"

Reading individual concept docs teaches you what each piece does. RetailOps shows you the decisions:
- **Why routing?** Because a single LLM prompt can't efficiently answer both "what's the vacation policy?" (static knowledge) and "which items are low on stock in store 102?" (live data)
- **Why hybrid search?** Because operational data has product codes and incident IDs (like `DENIM-4421`) that semantic search handles poorly
- **Why structured output?** Because downstream code, caching, and evaluation all need predictable response shapes
- **Why a service layer?** Because caching, routing and error handling need one place to live, separate from the HTTP layer

## ⏰ When Should You Use It?

✅ When learning how concepts connect — trace a request through the architecture  
✅ When designing your own AI assistant — use RetailOps as a reference pattern  
✅ When debugging — the architecture tells you which layer to investigate  
✅ When planning upgrades — the gaps are documented  

❌ This is a learning reference and production baseline — don't use it as-is for sensitive enterprise data without adding RBAC and metadata filtering  
❌ Don't deploy the in-memory cache and chat histories for multi-server use — both live in one process's memory (histories are per `session_id`, but lost on restart and not shared between workers); upgrade to a shared store (for example Redis) first  

## 🗂️ Types / Variants

| Component Layer | What It Does | Key Files |
|---|---|---|
| **Document Store** | Source files that answer questions: four `.txt` documents (HR, returns/refunds, IT support, store SOP) plus `inventory.csv`, `vendors.csv`, `incidents.json` used by the tools | `data/` |
| **Index Layer** | Chroma vector index of chunked documents, with a manifest recording a fingerprint (document version, chunking settings, embedding model); rebuilt automatically when it changes | `app/indexing.py`, `vectorstore/chroma/`, `vectorstore/manifest.json` |
| **Retrieval Layer** | Vector (MMR) + BM25 candidates merged and de-duplicated, multi-query expansion, cross-encoder reranking | `app/vectorstore.py`, `app/hybrid_retriever.py`, `app/bm25_retriever.py`, `app/multi_query.py`, `app/reranker.py` |
| **Chain Layer** | RAG chain, question-rewriter chain, router chain, general chat chain | `app/chains.py`, `app/prompts.py`, `app/rag.py` |
| **Agent Layer** | Tools plus a tool-calling agent for live operational data (it runs on its own model, `TOOLS_LLM_MODEL`); a LangGraph demo of the workflow | `app/tools.py`, `build_tool_agent()` in `app/chains.py`, `app/graph/` |
| **Router Layer** | Classifies questions into `general` / `rag` / `tools` and runs the chosen path | `app/router.py` |
| **Service Layer** | Single entry point: cache check (first turn only), routing, cache write (`general`/`rag` only) | `app/services.py`, `app/container.py` |
| **Memory Layer** | In-memory conversation history per `session_id` (lost on restart; not tied to a user) | `app/memory.py` |
| **Cache Layer** | In-memory TTL cache of first-turn responses, cleared on index rebuild | `app/cache.py` |
| **API Layer** | FastAPI endpoints, request/response schemas | `app/api.py`, `app/schemas.py`, `app/health.py`, `app/debug.py` |
| **Security Layer** | API-key check (constant-time) and a startup guard against the default key; nothing else | `app/security.py` |
| **Observability Layer** | Plain-text logs carrying a per-request ID, plus LangSmith tags/metadata | `app/logging_config.py`, `app/tracing.py` |
| **Evaluation Layer** | Demo question set + LLM judge + saved reports | `evals/` |
| **Test Suite** | 46 tests: retrieval and splitting, routing, tools, errors and retries, cache and sessions, API key and index rules, reranker and multi-query, graph | `tests/` (`test_rag`, `test_router`, `test_tools`, `test_errors`, `test_services`, `test_security`, `test_retrieval_components`, `test_graph`) |

## 🔀 When to Use Which Type

This architecture separates concerns so each layer can be tested, debugged, and upgraded independently:

**Improving answer quality?** → Change the retrieval layer (chunking, retrieval strategy, reranking) and run `evals/run_rag_eval.py` to measure the impact.

**Debugging a wrong answer?** → Check the router output (was it routed correctly?), then the retriever output (was the right source found? — the `/debug/retrieval` endpoint shows this), then the LLM output (was the context used correctly?).

**Scaling to more users?** → Move the per-session chat histories and the cache to a shared store such as Redis (both live in one process today), and move the vector store from local Chroma to a hosted one (Pinecone/Qdrant).

**Adding enterprise features?** → Security layer (API key → OAuth/RBAC), retrieval layer (add metadata filtering), workflow layer (wire in the LangGraph version for approval flows — see doc 33).

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Clear separation of concerns — each layer testable independently | More files and components than a minimal tutorial |
| Router pattern makes retrieval vs tools vs general explicit | In-memory chat history and cache live in one process, so they are lost on restart and don't scale to multiple servers |
| Service layer is the one place for caching and cross-cutting concerns | Chroma local storage doesn't scale to millions of documents |
| Structured output enables reliable evaluation and caching | API key auth is not enterprise-grade (one shared key, no per-user identity) |
| Hybrid search, reranking, and an evaluation harness are all present | The LangGraph version in `app/graph/` is a parallel demo, not used by the CLI or API |

## 💻 Basic Example

```python
# The request lifecycle in RetailOps — one call does everything.
# Run from the repository root (data paths are relative). Needs GROQ_API_KEY in .env.

from app.services import assistant_service

# ask() does the whole job:
#   1. looks the question up in the response cache (first question of a session only)
#   2. on a miss, calls run_router(), which classifies the question, runs the
#      general / rag / tools path, and records the turn in the session's memory
#   3. stores the result in the cache (only general/rag answers to first questions)
# So you do NOT add memory or cache calls around it — that would record turns twice.
# Calls with the same session_id share chat history (the default is "default").
result = assistant_service.ask("What is the return policy?", session_id="demo-user-1")

print(result["route"])        # "rag"
print(result["answer"])       # the generated answer
print(result["sources"])      # which documents were used (rag route only)
print(result["cache_hit"])    # False the first time; True if ANOTHER session asks it first within 5 minutes

# Example questions and the route you should expect (the router is an LLM, so
# borderline questions can go either way):
#   "What is the return policy?"                  -> rag     (static knowledge)
#   "Which items are low on stock in store 102?"  -> tools   (live data)
#   "Hello!"                                      -> general (small talk)
```

> **Lesson from this project:** count your model calls, because every one costs time and free-tier tokens. A first RAG question makes 3 (router, multi-query generation, answer); a follow-up makes 4 (it also rewrites the question); a tools question is the router plus the agent's own calls; a general question is 2. On the free tier those tokens are limited per minute *and* per day (about 8,000 and 200,000 for the default model on the key this was built with), which is why the first-question rewrite is skipped and why the router only gets the last 6 messages.

## 🔧 Real-World Example

A map from each part of the app to the concept doc that explains it. Everything below describes what the code actually does today; where RetailOps hand-writes something that LangChain also offers as a ready-made class, that is noted.

```python
# ══════════════════════════════════════════════════════════════════════════
# RetailOps Component Map
# ══════════════════════════════════════════════════════════════════════════
#
# FOUNDATION
# ─────────────────────────────────────────────────────────────────────────
# LLM: ChatGroq, model set by LLM_MODEL in .env (default gpt-oss-20b), → doc 01
#   temperature from TEMPERATURE (0). Built by get_llm() in app/llm.py.
#   Used for: RAG generation, routing, query rewriting, multi-query, evaluation judge
#   The tool agent uses its own model, TOOLS_LLM_MODEL (default gpt-oss-120b):
#   the smaller model failed multi-tool questions in most runs (measured 2 of 8 OK
#   vs 8 of 8). get_llm(model) takes an optional model name.
#
# Prompts: ChatPromptTemplate in app/prompts.py                        → docs 03-04
#   - RAG prompt, general chat prompt, question-rewrite prompt,
#     history-aware router prompt
#
# LCEL chains: prompt | llm | parser                                   → doc 05
#   - General chain: general_chat_prompt | llm | StrOutputParser
#   - Router chain:  history_aware_router_prompt | llm.with_structured_output(RouteDecision)
#   - RAG chain:     retrieve_context | rag_prompt | llm.with_structured_output(RAGResponse)
#
# Structured output: Pydantic models in app/schemas.py                 → docs 07-08
#   - RAGResponse(answer, sources, confidence)
#   - RouteDecision(route, reason)
#   - ChatResponse (the API response shape)
#
# ─────────────────────────────────────────────────────────────────────────
# RETRIEVAL
# ─────────────────────────────────────────────────────────────────────────
# Documents: the four data/*.txt files, loaded with TextLoader         → doc 09
#   (hr_policy.txt, returns_refunds_policy.txt, it_support_kb.txt,
#    store_operations_sop.txt) — app/rag.py load_documents()
#
# Chunking: semantic chunking by default (SemanticChunker, ENABLE_SEMANTIC_CHUNKING=true) → doc 10
#   - chunk_documents() in app/rag.py picks the strategy; index building and the
#     retriever both call it, so they always see the same chunks
#   - The semantic splitter uses a sentence pattern that does not cut after a list
#     number ("6.") and ignores splits that would leave a fragment under 300
#     characters (it once split the store-opening checklist in half)
#   - Fallback: RecursiveCharacterTextSplitter with CHUNK_SIZE=300 /
#     CHUNK_OVERLAP=50 from .env.example (app/rag.py)
#
# Embeddings: HuggingFaceEmbeddings(all-MiniLM-L6-v2)                  → doc 11
#   - Free, local, no API key required (app/vectorstore.py get_embeddings,
#     cached so the model loads once)
#
# Vector store: Chroma, persisted in vectorstore/chroma/               → doc 12
#   - vectorstore/manifest.json records a fingerprint: DOCUMENT_VERSION, the
#     chunking settings and the embedding model (app/indexing.py)
#   - chunks get stable IDs, so re-indexing never duplicates them
#   - Upgrade path: Pinecone or Qdrant
#
# Retrieval:
#   Vector search: vectorstore.as_retriever(search_type="mmr", k=RETRIEVAL_K) → doc 13
#   BM25: BM25Retriever class in app/bm25_retriever.py (rank_bm25)       → doc 14
#   Hybrid: HybridRetriever in app/hybrid_retriever.py                   → doc 14
#     — hand-written: vector results + BM25 top 10, merged and de-duplicated.
#       (LangChain's built-in equivalent is EnsembleRetriever, which uses
#        weights; RetailOps does not use weights.)
#   Cross-encoder rerank: CrossEncoderReranker in app/reranker.py        → doc 15
#     — hand-written with sentence-transformers CrossEncoder; keeps up to
#       RETRIEVAL_K chunks and drops any scoring below RERANK_MIN_SCORE
#       (default -9.0; the best chunk is always kept).
#       (Built-in equivalent: ContextualCompressionRetriever.)
#   Multi-query: retrieve_with_multi_query() in app/multi_query.py       → doc 16
#     — hand-written: the LLM writes up to 3 extra queries, candidates for all
#       queries are pooled, de-duplicated, then reranked with the retriever's
#       single reranker (loaded once at startup).
#       (Built-in equivalent: MultiQueryRetriever.)
#   Parent-child: app/parent_child.py exists but is not part of the default pipeline
#
# Final retrieval pipeline: rewrite question → multi-query → hybrid candidates → rerank
#
# ─────────────────────────────────────────────────────────────────────────
# CHAINS & AGENTS
# ─────────────────────────────────────────────────────────────────────────
# Question rewriter: history + question → standalone question          → doc 17
#   — build_question_rewriter_chain() and rewrite_question() in app/chains.py
#     (hand-written; built-in equivalent: create_history_aware_retriever).
#     Skipped when there is no history, so a first question saves one LLM call.
# RAG chain: context + question → RAGResponse                          → doc 18
#   — build_rag_chain(retriever, rewriter_chain, generator); AppContainer builds
#     the retriever, rewriter and generator once and shares them with the chain,
#     /debug/retrieval and the LangGraph demo
# Evaluation: LLM judge + demo question set in evals/                  → doc 19
# Tools: @tool functions in app/tools.py (get_low_stock_items,         → doc 20
#   get_vendor_for_sku, get_open_incidents)
# Agent: build_tool_agent() in app/chains.py uses                      → docs 21-22
#   langchain.agents.create_agent (LangChain 1.x; runs on LangGraph).
#   LangGraph demo (not used by the CLI/API): app/graph/ — see below
# Router: RouteDecision(route, reason); run_router() in app/router.py  → doc 23
#   branches into general / rag / tools
#
# ─────────────────────────────────────────────────────────────────────────
# PRODUCTION LAYERS
# ─────────────────────────────────────────────────────────────────────────
# Memory: one InMemoryChatMessageHistory per session_id                → doc 24
#   (add_user_message, add_ai_message, get_messages, clear_memory in app/memory.py;
#   session_id defaults to "default"; POST /chat accepts an optional session_id)
#   — in this process's memory only, unbounded, lost on restart
# API: FastAPI app in app/api.py: /health, /chat, /memory/clear,       → doc 25
#   /index/rebuild (rebuilds, then reloads the app: no restart), /debug/retrieval
#   (reuses the running retriever); all but /health need x-api-key
#   Chains are built lazily on first use via get_container() (app/container.py);
#   the CLI warms it up at start-up, the API builds it on the first request
# Observability: logging.basicConfig text logs (noisy libraries quieted);   → doc 26
#   request_id = uuid4()
#   generated in run_router() and included in log lines
# LangSmith: trace_config() in app/tracing.py adds tags + metadata     → doc 27
#   (request_id, route, environment, app_version) to every chain call
# Errors: app/exceptions.py (RetailOpsError -> LLMError -> ModelRefusalError,   → doc 26
#   RateLimitError, ModelUnavailableError, each with a code, a user-safe message
#   and an HTTP status); invoke_with_retry() in app/llm.py retries once on
#   transient model failures; run_router() returns route "error" + the code and
#   /chat maps the code to 422 / 429 / 503 / 502 / 500
# Testing: 46 tests across 8 files in tests/                           → doc 28
# Caching: SimpleTTLCache (response_cache) in app/cache.py; the service → doc 29
#   caches only first-turn general/rag answers (never tools or follow-ups)
# Security: verify_api_key (constant-time compare of the x-api-key header)   → doc 30
#   and check_api_key_configured() (refuses the default key unless APP_ENV=local)
# Indexing: ensure_index_current() rebuilds when the manifest fingerprint   → doc 31
#   changes; rebuild_index() clears the collection in place
#
# ─────────────────────────────────────────────────────────────────────────
# NOT IN THIS REPO YET (upgrade paths)
# ─────────────────────────────────────────────────────────────────────────
# Security: OAuth/JWT, RBAC, metadata-filtered retrieval, injection detection, PII scrubbing
# Memory: persistence and sharing across workers (for example Redis)
# Cache: shared cache (for example Redis), with the document version in the key
# Vector DB: Chroma local → Pinecone/Qdrant
# Workflow: the LangGraph demo in app/graph/ (approval step with interrupt(); its
#   RAG step is a real subgraph: rewrite -> retrieve -> generate, using the
#   container's shared retriever, rewriter and generator) is not wired in: the
#   API and CLI call run_router(). Importing app.graph needs no API key.  → doc 33
# Integrations: Confluence, SharePoint, ServiceNow connectors
# Compliance: audit trails, GDPR, SOC2

# ─────────────────────────────────────────────────────────────────────────
# KEY DESIGN DECISIONS (and why)
# ─────────────────────────────────────────────────────────────────────────
#
# Decision: Router before RAG, not a single prompt
# Why: A single "answer everything" prompt is fragile; routing lets each
#      workflow be optimized independently (RAG gets retrieval, tools get
#      the agent loop, general gets a direct LLM call)
#
# Decision: Build chains once, not per request
# Why: Building the RAG chain loads documents, embeds them into Chroma and
#      loads the reranker. Doing this per request adds seconds of latency.
#      get_container() is wrapped in lru_cache, so it runs once, on first use.
#
# Decision: Structured output for RAG responses
# Why: RAGResponse(answer, sources, confidence) enables evaluation,
#      source attribution, and reliable API contracts
#
# Decision: the service caches only first-turn general/rag answers
# Why: tools answers come from live data (a cached one could be 5 minutes
#      stale) and a follow-up like "What about part-timers?" means different
#      things in different conversations, so neither is cached or served from
#      the cache. Doc 29 explains the rules and the trade-off.
#
# Decision: typed errors and one retry around every model call
# Why: models fail in different ways (refuse, rate-limit, emit unparseable
#      output, get retired). Each needs a different response: retry once,
#      or tell the user clearly. A generic "something went wrong" hides which.
#
# Decision: Recall-first retrieval (multi-query + hybrid, then rerank)
# Why: Better to pull in many candidates and let the reranker pick the best
#      than to miss a relevant document in the first pass.
```

## 🏭 Production Best Practices

1. **Use the layered architecture as your debugging guide** — When an answer is wrong, check layers in order: router (was it classified correctly?), retriever (was the right source returned?), LLM (was the context used correctly?). **How:** Router → `tests/test_router.py`; retriever → `tests/test_rag.py` and the `/debug/retrieval` endpoint; LLM output quality → `python -m evals.run_rag_eval`.

2. **Keep chains in the service layer, not the API layer** — The API layer handles HTTP concerns (request/response, auth, validation). Chain logic belongs behind the service. This keeps your chains testable without HTTP overhead. **How:** `app/api.py` calls `assistant_service.ask(request.question, request.session_id)`, never `rag_chain.invoke(...)` directly.

3. **Design the upgrade path from day one** — Each component has a planned upgrade: Chroma → Pinecone, in-memory cache → Redis, API key → OAuth. Keep the storage-specific code in one module so an upgrade touches one place. **How:** `app/vectorstore.py` (`build_vectorstore`, `get_retriever`) is the module that knows about Chroma. Be honest about leaks, though: `app/indexing.py` clears the index with `Chroma(...).delete_collection()` and `app/api.py` rebuilds the container after `/index/rebuild`, and both would change in a hosted-DB migration.

4. **Match test types to architecture layers** — Tests for the router, retrieval and tools each pinpoint which layer caused a regression. **How:** see `tests/test_router.py`, `tests/test_rag.py`, `tests/test_tools.py`. `tests/test_errors.py`, `test_services.py`, `test_security.py`, `test_retrieval_components.py` and `test_graph.py` cover the error mapping, cache and session rules, key checks, index fingerprint and reranker cut-off, and the graph; they use fakes, so they run without an API key.

5. **Treat the baseline as a starting point** — RetailOps demonstrates the production baseline. The remaining gaps (RBAC, persistent and shared memory, workflow orchestration wired into the app, a much larger evaluation set) are architecture concerns rather than RAG engineering. **How:** use the readiness scorecard in doc 37 to prioritize your next investments.

## ⚠️ Common Mistakes to Avoid

⚠️ **Building a monolithic `main.py`** — When all logic lives in one file, debugging is hard, testing is harder, and upgrades require rewriting instead of swapping. Separate concerns: indexing, retrieval, chains, agents, routing, memory, caching, API.

⚠️ **Creating chains per request** — Building a Chroma index, loading embeddings, and constructing chains on every `/chat` request adds seconds of latency. Build once and reuse (`get_container()` does this). RetailOps had two places that slipped, both fixed: `retrieve_with_multi_query()` in `app/multi_query.py` created a new `CrossEncoderReranker()` (a model load of about 2 seconds) on every call, and `generate_queries()` built a new LLM client and chain every time. The reranker is now the retriever's single instance, and the query-generation chain is cached with `lru_cache`.

⚠️ **Skipping the service layer** — If route handlers call chains directly, you can't add caching, retries, or observability without touching the API layer. The service layer is the seam for all of these.

⚠️ **Wrapping `ask()` with your own memory and cache calls** — `run_router()` already records each turn and the service already uses the cache. Adding `add_user_message()` / `response_cache.set()` around it records turns twice.

⚠️ **Using the same retriever for all routes** — Retrieval only runs for questions the router sends to `rag`. Questions about live data ("what's in stock?") belong to the tools route.

⚠️ **Not planning the upgrade path** — Local Chroma and in-memory state are fine for development. Not planning for Redis, a hosted vector DB, and RBAC creates painful rewrites later.

## 🔗 How It Connects to Other Concepts

Every concept in the series connects through this architecture:

- **Docs 01–08** (LLMs, prompts, LCEL, runnables, parsers, structured output) → Foundation used by every chain and agent
- **Docs 09–17** (loaders, chunking, embeddings, vector stores, retrievers, hybrid search, reranking, multi-query, history-aware retrieval) → Retrieval layer
- **Docs 18–22** (RAG chains, evaluation, tools, agents, ReAct) → Chain and agent layer
- **Docs 23–25** (router, memory, FastAPI) → Service and orchestration layer
- **Docs 26–30** (observability, LangSmith, testing, caching, security) → Production operations layer
- **Doc 31** (indexing) → Offline pipeline that builds the retrieval layer
- **Doc 33** (LangGraph) → The workflow layer that extends this architecture; a version already exists in `app/graph/`

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Production-baseline AI assistant with router, RAG, tools, memory, caching, API-key auth, logging, and evaluation |
| **Why** | Shows how all LangChain concepts connect in a real system; serves as a reference architecture |
| **When** | Use as a reference pattern for any AI assistant; upgrade individual layers as requirements grow |
| **Types** | 14 component layers: documents, index, retrieval, chains, agents, router, service, memory, cache, API, security, observability, evaluation, tests |
| **Production gotcha** | Build chains once, not per request; the service layer owns caching and memory (don't duplicate them); chat history and cache live in one process's memory until you replace them |

## ➡️ Next Steps

- **All source files:** `app/` directory — each file corresponds to one or more architecture layers
- **Try it:** `python -m app.main` for the CLI, or `uvicorn app.api:app --reload` for the API (see the root `README.md` quickstart)
- **Previous doc:** `../33_langchain_limitations_and_langgraph/README.md`
- **Next doc:** `../35_interview_questions/README.md` — consolidated Q&A covering every concept for interview preparation
- **Official docs:** https://python.langchain.com/docs/ | https://langchain-ai.github.io/langgraph/
