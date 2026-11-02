# LangChain Learning Path — Master Index
> Complete guide to building production RAG systems with LangChain — from LLM fundamentals to enterprise architecture.

## 📌 What Is It?

This is a 37-document learning series that teaches LangChain through a single running example: **RetailOps AI Assistant**, a production-baseline RAG application that answers questions for retail store operators. Every concept is explained in context — not in isolation.

By the end of the series, you will have built mental models for:
- **RAG systems** — retrieval-augmented generation from document loading to answer evaluation
- **Agents** — tool-calling, ReAct loops, routing, and orchestration
- **Production operations** — observability, testing, caching, security, and indexing
- **Enterprise architecture** — the gap between a demo and a production system, and how to close it

All docs follow the same 13-section structure so you can always find what you need:
`What → Why → When → Types → Decision Guide → Pros/Cons → Basic Example → Real-World Example → Best Practices → Mistakes → Connections → Summary → Next Steps`

Each concept lives in its own folder: `docs/<NN>_<concept>/README.md` is the doc itself, and `docs/<NN>_<concept>/RUN.md` (where a matching demo exists) tells you exactly how to run its `examples/` script.

### Before you start

- **Python 3.10+**, and the setup steps in the root [README.md](../README.md#quickstart) (virtual environment, `pip install -r requirements.txt`, copy `.env.example` to `.env`).
- **A free Groq API key** in `.env` as `GROQ_API_KEY` for anything that calls the LLM. These examples need no key: `02_document_loading`, `03_text_splitting`, `04_vectorstore_retriever`, `08_tools_structured_data`, `12_runnable_lambda`, `13_runnable_parallel`, `14_runnable_branch`, `15_hybrid_retrieval`, `17_bm25_retrieval`, `19_semantic_chunking`.
- **Run every command from the repository root**, because the code reads `data/` and writes `vectorstore/` using relative paths.
- **First run is slower**: two small HuggingFace models (embeddings and the reranker) are downloaded once, and the vector index is built.
- **Two models.** `LLM_MODEL` does routing, chat and RAG answers; the tool-calling agent uses `TOOLS_LLM_MODEL`. Doc 21 explains why (with measurements).
- **Free-tier limits are real.** Groq limits tokens per minute and per day for each model. If an example answers "The AI service is busy right now" (HTTP 429 from the API), you have hit one; wait and retry. Model names also change over time, so keep them in `.env` (see the root README for how to list the models your key can use).
- **Reading tip:** where a doc shows a LangChain built-in (for example `EnsembleRetriever`) and RetailOps does the same job with a small hand-written class, the doc says which is which. The code under `app/` is always the source of truth.

### How to study each doc

1. Read **What Is It?** and **Why Does It Exist?** to get the idea and the problem it solves.
2. Run the demo if there is one. These docs have a `RUN.md` with the exact command: 01, 06, 08, 09, 10, 13, 14, 16, 18, 20, 21, 22, 23, 24 and 33. All 24 example scripts in `examples/` were run end to end while preparing this series.
3. Open the `app/` file named in **Real-World Example** and compare it with the doc's simplified version.
4. Finish with **Common Mistakes to Avoid**. Several are things that really went wrong in this project and were fixed; [KNOWN_ISSUES.md](../KNOWN_ISSUES.md) lists them and the limits that remain.

## ❓ Why Does It Exist?

Most LangChain tutorials teach individual APIs in isolation. This series teaches **judgment**: when to use RAG vs tools, hybrid vs vector-only search, chains vs agents, LangChain vs LangGraph. Every concept is explained with a real system context (RetailOps), production code, and the tradeoffs that matter in practice.

## ⏰ When Should You Use It?

✅ Learning LangChain for the first time — follow the learning path in order
✅ Preparing for AI engineer interviews — see doc 35 (Interview Questions)
✅ Debugging a specific component — jump directly to that concept's doc
✅ Planning an enterprise upgrade — see doc 32 (Production RAG Patterns), doc 30 (Security), and doc 37 (Enterprise Readiness Checklist)
✅ Deciding between LangChain and LangGraph — see doc 33

## 🗂️ Learning Path — All 37 Docs

### Phase 1 — Foundation (Docs 01–08)
Core LangChain building blocks. Start here.

| # | Doc | What You'll Learn |
|---|---|---|
| 01 | [LLMs & Chat Models](01_llms_and_chat_models/README.md) | How to call language models; chat vs completion models; temperature |
| 02 | [LangChain Overview](02_langchain_overview/README.md) | What LangChain is and why it exists; the component ecosystem |
| 03 | [Prompt Templates](03_prompt_templates/README.md) | ChatPromptTemplate; system + human messages; variable substitution |
| 04 | [Prompt Engineering Patterns](04_prompt_engineering_patterns/README.md) | Few-shot, role prompting, chain-of-thought; when each pattern helps |
| 05 | [LCEL — LangChain Expression Language](05_lcel/README.md) | Pipe syntax `prompt \| llm \| parser`; composing runnables |
| 06 | [Runnables](06_runnables/README.md) | The Runnable interface; invoke/batch/stream; parallelism with RunnableParallel |
| 07 | [Output Parsers](07_output_parsers/README.md) | StrOutputParser, JsonOutputParser, PydanticOutputParser |
| 08 | [Structured Output](08_structured_output/README.md) | `llm.with_structured_output(MyModel)`; why it's better than parsing |

### Phase 2 — Retrieval & RAG (Docs 09–19)
How to build the knowledge retrieval layer. The core of most AI assistants.

| # | Doc | What You'll Learn |
|---|---|---|
| 09 | [Document Loaders](09_document_loaders/README.md) | TextLoader, DirectoryLoader, PDFLoader; loading from files and APIs |
| 10 | [Text Splitters & Chunking](10_text_splitters_and_chunking/README.md) | `RecursiveCharacterTextSplitter` vs `SemanticChunker`; chunk_size and chunk_overlap tradeoffs; how a numbered list got split in half and how it was fixed |
| 11 | [Embeddings](11_embeddings/README.md) | What embeddings are (not knowledge); semantic similarity; model choice |
| 12 | [Vector Databases](12_vector_databases/README.md) | Chroma, Pinecone, Qdrant; ANN search; when to use each |
| 13 | [Retrievers, Similarity Search & Contextual Compression](13_retrievers_and_similarity_search/README.md) | as_retriever(); k, MMR, score_threshold; contextual compression tradeoffs |
| 14 | [Hybrid Search & BM25](14_hybrid_search_and_bm25/README.md) | BM25 keyword search plus vector search; merging and de-duplicating results; why exact match matters (`EnsembleRetriever` is the built-in equivalent) |
| 15 | [Cross-Encoder Reranking](15_cross_encoder_reranking/README.md) | Cross-encoder reranking: retrieve many candidates, re-score them, keep the best and drop clearly irrelevant ones (`RERANK_MIN_SCORE`); loaded once, not per question (`ContextualCompressionRetriever` is the built-in wrapper) |
| 16 | [Multi-Query Retrieval](16_multi_query_retrieval/README.md) | Query expansion: the LLM rewrites a question several ways to improve recall (`MultiQueryRetriever` is the built-in version) |
| 17 | [History-Aware Retrieval](17_history_aware_retrieval/README.md) | Question rewriting; making follow-up questions retrieval-friendly; skipped on a conversation's first question to save an LLM call |
| 18 | [RAG Chains](18_rag_chains/README.md) | Full RAG chain; RAGResponse structured output; sources and confidence |
| 19 | [RAG Evaluation](19_rag_evaluation/README.md) | Golden dataset; LLM-as-judge; correctness, groundedness, completeness |

### Phase 3 — Agents & Orchestration (Docs 20–25)
Dynamic workflows, tool calling, routing, and serving the application.

| # | Doc | What You'll Learn |
|---|---|---|
| 20 | [Tools & Function Calling](20_tools_and_function_calling/README.md) | @tool decorator; docstrings for tool selection; tools vs RAG |
| 21 | [Agents](21_agents/README.md) | The tool-calling agent loop with `create_agent` (LangChain 1.x); when to use an agent vs a chain; why the tool agent gets its own, more reliable model |
| 22 | [ReAct Pattern](22_react_pattern/README.md) | Thought → Action → Observation loop; reading the agent's message trace; debugging agents |
| 23 | [Router Pattern](23_router_pattern/README.md) | RouteDecision; classifying questions into workflows; structured routing |
| 24 | [Memory](24_memory/README.md) | Chat history per `session_id` (`app/memory.py`); every route sees the last 6 messages; in-process only, so a Redis upgrade path |
| 25 | [FastAPI Integration](25_fastapi_integration/README.md) | FastAPI endpoints (`/chat`, `/health`, `/debug/retrieval`, `/index/rebuild`, …); `RetailOpsAssistantService`; `session_id`; typed errors mapped to HTTP 422/429/502/503/500; building chains once |

### Phase 4 — Production Operations (Docs 26–31)
Everything needed before deploying to real users.

| # | Doc | What You'll Learn |
|---|---|---|
| 26 | [Observability & Structured Logging](26_observability/README.md) | `configure_logging()` (plain-text logs, noisy libraries quieted); a request ID (uuid4) per request in `run_router()`; structured JSON logging is an upgrade path |
| 27 | [LangSmith](27_langsmith/README.md) | Automatic tracing; tags and metadata passed through `RunnableConfig` (`app/tracing.py`) |
| 28 | [Testing AI Systems](28_testing/README.md) | What 46 tests cover and how fakes keep most of them fast and key-free; router tests that call the LLM; the 5-question eval set |
| 29 | [Caching](29_caching/README.md) | `SimpleTTLCache`; what to cache and what not: only a conversation's first question, only `general`/`rag` answers, never live tool data; in-memory and per process |
| 30 | [Security](30_security/README.md) | API key auth with a constant-time compare and a guard against the default key outside local use (implemented); prompt-injection defense, PII scrubbing and RBAC (taught as exercises, not in the repo) |
| 31 | [Indexing Strategy](31_indexing_strategy/README.md) | Full rebuild vs incremental; a manifest fingerprint (document version, chunking, embedding model) that triggers rebuilds; stable chunk IDs; `/index/rebuild` without a restart |

### Phase 5 — Architecture & Mastery (Docs 32–37)
The big picture: production patterns, enterprise readiness, and how everything connects.

| # | Doc | What You'll Learn |
|---|---|---|
| 32 | [Production RAG Patterns & Enterprise Readiness](32_production_rag_patterns/README.md) | Complete production architecture; enterprise readiness scorecard (~85% for a production baseline) |
| 33 | [LangChain Limitations & LangGraph](33_langchain_limitations_and_langgraph/README.md) | Where chains break down; LangGraph nodes, edges, state, a real RAG subgraph and human approval (a parallel demo in `app/graph/`); migration strategy |
| 34 | [RetailOps Project Architecture](34_project_architecture/README.md) | Full component map; how all concepts connect; design decisions |
| 35 | [Interview Questions](35_interview_questions/README.md) | 41 Q&As organized by topic; model answers with Definition→Why→How→Tradeoff |
| 36 | [Common Mistakes](36_common_mistakes/README.md) | 43 mistakes across all layers; debugging checklist; retrieval > prompt |
| 37 | [Enterprise Readiness Checklist](37_enterprise_readiness_checklist/README.md) | Scannable RAG Foundation → Production Baseline → Enterprise Grade scorecard |

## 🔀 When to Use Which Type

**Learning from scratch?** Follow the phases in order (01 → 37). Each doc references the previous one and previews the next.

**Learning RAG specifically?** Start with Phase 1 for foundation concepts, then jump to Phase 2 (docs 09–19). Phase 4 (docs 26–31) covers the operational layer you need before deploying.

**Already know LangChain basics?** Start at doc 14 (Hybrid Search) — that's where most tutorials end and where production patterns begin.

**Debugging a production issue?** Read doc 36 (Common Mistakes) for the debugging checklist, then jump to the relevant concept doc.

**Preparing for an interview?** Read doc 35 (Interview Questions) as a self-test, then read any concept docs where your answers were weak.

**Planning an enterprise upgrade?** Read doc 32 (Production RAG Patterns) for the readiness narrative, doc 37 (Enterprise Readiness Checklist) for the scannable scorecard, doc 30 (Security) for the RBAC path, and doc 33 (LangGraph) for workflow orchestration.

## ⚖️ Pros & Cons

| ✅ What this series does well | ❌ What it doesn't cover |
|---|---|
| Real production code, not toy examples | Deep NLP theory (attention, transformers internals) |
| Every concept explained with motivation, not just API | Distributed training or fine-tuning |
| Complete running example (RetailOps) throughout | Provider-specific features (OpenAI Assistants, Bedrock) |
| Production + enterprise perspective from doc 01 | Multi-modal (vision, audio) RAG |
| Interview preparation integrated throughout | Real-time streaming architectures at scale |

## 💻 Basic Example

```python
# The RetailOps request lifecycle — one call, many concepts.
# This is the mental model the entire series builds toward.
# Run from the repository root; needs GROQ_API_KEY in .env.

from app.services import assistant_service

# assistant_service.ask() does everything. You do NOT wrap it with your own
# memory or cache calls — it already handles both (adding them would record turns twice).
#
#   1. cache lookup, only for the first question of a conversation   (doc 29)
#   2. run_router() in app/router.py generates a request_id (doc 26) and asks the
#      LLM to classify the question using the last few messages: general | rag | tools   (doc 23)
#        rag     -> rewrite follow-ups using chat history; skipped on a first question (doc 17)
#                -> multi-query expansion (doc 16)
#                -> hybrid vector + BM25 search (doc 14)
#                -> cross-encoder reranking (doc 15)
#                -> structured answer with sources (doc 18)
#        tools   -> @tool functions (doc 20) run by a tool-calling agent (docs 21-22)
#        general -> direct LLM call (doc 01)
#      every model call goes through invoke_with_retry(), so failures become typed errors (doc 25)
#   3. the turn is saved to that session's conversation memory   (doc 24)
#   4. general/rag answers to a first question are stored in the cache   (doc 29)

# Same session_id = same conversation, so the follow-up below can use the first answer.
first = assistant_service.ask(
    "How many vacation days do full-time store employees get?", session_id="alice"
)
follow_up = assistant_service.ask("What about part-time employees?", session_id="alice")

print(first["route"])        # which path the router chose
print(first["answer"])       # the generated answer
print(first["sources"])      # documents used (rag route only)
print(follow_up["answer"])   # answered in the context of the first question
```

## 🔧 Real-World Example

What the app actually uses, and which doc explains it. Where RetailOps writes a
small piece by hand instead of using LangChain's ready-made class, the built-in
equivalent is shown in brackets — the docs teach both.

```
RetailOps Component (app/ file)                          → Concept Docs
────────────────────────────────────────────────────────────────────────
ChatGroq via get_llm(model=None)  (llm.py)               → doc 01
  LLM_MODEL for chat/routing/RAG; TOOLS_LLM_MODEL for the tool agent
ChatPromptTemplate.from_messages([...])  (prompts.py)    → doc 03
  (the general prompt has an optional MessagesPlaceholder for chat history)
prompt | llm | StrOutputParser  (general chain)          → doc 05, 07
llm.with_structured_output(RAGResponse / RouteDecision)  → doc 08
TextLoader, RecursiveCharacterTextSplitter, SemanticChunker, chunk_documents() (rag.py) → doc 09, 10
HuggingFaceEmbeddings (cached), Chroma  (vectorstore.py) → doc 11, 12
vectorstore.as_retriever(search_type="mmr")              → doc 13
HybridRetriever: vector + BM25 merged, de-duplicated  (hybrid_retriever.py, bm25_retriever.py)
                                          [built-in: EnsembleRetriever]  → doc 14
CrossEncoderReranker + RERANK_MIN_SCORE cut-off  (reranker.py)
                              [built-in: ContextualCompressionRetriever] → doc 13, 15
retrieve_with_multi_query()  (multi_query.py)
                                      [built-in: MultiQueryRetriever]    → doc 16
rewrite_question() + question rewriter chain  (chains.py)
                            [built-in: create_history_aware_retriever]   → doc 17
build_rag_chain(): retrieve -> structured answer  (chains.py) → doc 18
RAGResponse(answer, sources, confidence)  (schemas.py)   → doc 18
LLM judge + evals/rag_questions.jsonl + JSON reports     → doc 19
@tool get_low_stock_items, get_vendor_for_sku,
get_open_incidents  (tools.py)                           → doc 20
create_agent(...)  in build_tool_agent()  (chains.py)    → doc 21, 22
RouteDecision + run_router()  (router.py, schemas.py)    → doc 23
per-session add_user_message / add_ai_message / get_messages (memory.py) → doc 24
FastAPI + RetailOpsAssistantService  (api.py, services.py)  → doc 25
typed errors + invoke_with_retry()  (exceptions.py, llm.py) → doc 25
configure_logging() + request_id (uuid4 in run_router)   → doc 26
LangSmith tags + metadata via trace_config()  (tracing.py)  → doc 27
pytest: 46 tests in 8 files (tests/)                     → doc 28
SimpleTTLCache (response_cache): first-turn general/rag only  (cache.py) → doc 29
verify_api_key (constant-time) + default-key guard  (security.py) → doc 30
ensure_index_current() + manifest fingerprint  (indexing.py) → doc 31
LangGraph demo: nodes, RAG subgraph, approval  (app/graph/)  → doc 33
```

## 🏭 Production Best Practices

The series distills to five principles for production RAG:

1. **Retrieval quality determines answer quality** — More than prompt engineering, model choice, or chunking strategy, getting the right document into the LLM's context determines answer quality. Invest in hybrid search and reranking before anything else.

2. **Measure before you optimize** — A golden dataset with 20+ examples is the most valuable thing you can build. Without it, every change is a guess. With it, every change is a measurement.

3. **Observe from day one** — LangSmith tracing and structured logging take 30 minutes to set up and save days of debugging. Enable them before your first deployment.

4. **Build for upgrades** — Local Chroma → Pinecone. In-memory cache → Redis. API key → OAuth. In-memory sessions → Redis. Every component should have a clear upgrade path that doesn't require rewriting the components that call it.

5. **Enterprise problems are architecture problems** — The gap between production baseline (~85%) and enterprise grade (90%+) is security (RBAC), workflow (LangGraph), and governance (audit trails) — not RAG engineering. Great retrieval doesn't make a system enterprise-ready. See doc 37 for the exact checklist.

## ⚠️ Common Mistakes to Avoid

⚠️ **Reading without building** — Every doc has runnable code. Where a `RUN.md` exists in a concept's folder, run the actual `examples/` script as you go — the concepts click faster when you've run the code.

⚠️ **Skipping evaluation (doc 19)** — Many developers read docs 01–18, build a working RAG system, and ship it without evaluation. Evaluation is not optional for production systems.

⚠️ **Treating this series as exhaustive** — This covers production RAG patterns well. It doesn't cover fine-tuning, multi-modal, real-time streaming at scale, or provider-specific features. Know what it is and what it isn't.

## 🔗 How It Connects to Other Concepts

The five phases build on each other:
- **Phase 1** (Foundation) is required for everything that follows
- **Phase 2** (Retrieval) is the core of every RAG system; docs 14–16 are where most tutorials end and production begins
- **Phase 3** (Agents) extends RAG into dynamic workflows; doc 23 (Router) is the bridge
- **Phase 4** (Production) wraps everything built in phases 1–3 in the operational layer required for real deployments
- **Phase 5** (Architecture) provides the map — how it all fits together, the enterprise checklist, and where to go next

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | 37-doc LangChain learning series from fundamentals to enterprise architecture, built around the RetailOps AI assistant |
| **Why** | Teaches judgment (when to use what) not just API knowledge; every concept grounded in production context |
| **When** | Learning LangChain; preparing for interviews; debugging production systems; planning enterprise upgrades |
| **Phases** | Foundation (01–08) → Retrieval/RAG (09–19) → Agents (20–25) → Production (26–31) → Architecture (32–37) |
| **Production gotcha** | Retrieval quality > prompt quality; measure before optimizing; observe from day one; build for upgrades |

## ➡️ Next Steps

- **Start here:** [01_llms_and_chat_models/README.md](01_llms_and_chat_models/README.md) — or jump to any doc above based on your current level
- **Quick reference:** doc 35 (Interview Questions) covers all topics in Q&A format — useful for self-assessment
- **Production diagnosis:** doc 36 (Common Mistakes) contains the debugging checklist for production issues; doc 37 has the scannable enterprise-readiness scorecard
- **Official docs:** https://python.langchain.com/docs/ | https://langchain-ai.github.io/langgraph/

---

Earlier draft notes (the raw first-pass write-ups and the more granular per-concept notes that preceded this polished series) are archived in `docs/drafts/` for reference — they're not required reading, everything of substance was folded into the docs above.
