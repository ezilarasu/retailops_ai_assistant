# LangChain Learning Path — Master Index
> Complete guide to building production RAG systems with LangChain — from LLM fundamentals to enterprise architecture.

## 📌 What Is It?

This is a 36-document learning series that teaches LangChain through a single running example: **RetailOps AI Assistant**, a production-baseline RAG application that answers questions for retail store operators. Every concept is explained in context — not in isolation.

By the end of the series, you will have built mental models for:
- **RAG systems** — retrieval-augmented generation from document loading to answer evaluation
- **Agents** — tool-calling, ReAct loops, routing, and orchestration
- **Production operations** — observability, testing, caching, security, and indexing
- **Enterprise architecture** — the gap between a demo and a production system, and how to close it

All docs follow the same 13-section structure so you can always find what you need:
`What → Why → When → Types → Decision Guide → Pros/Cons → Basic Example → Real-World Example → Best Practices → Mistakes → Connections → Summary → Next Steps`

## ❓ Why Does It Exist?

Most LangChain tutorials teach individual APIs in isolation. This series teaches **judgment**: when to use RAG vs tools, hybrid vs vector-only search, chains vs agents, LangChain vs LangGraph. Every concept is explained with a real system context (RetailOps), production code, and the tradeoffs that matter in practice.

## ⏰ When Should You Use It?

✅ Learning LangChain for the first time — follow the learning path in order  
✅ Preparing for AI engineer interviews — see doc 35 (Interview Questions)  
✅ Debugging a specific component — jump directly to that concept's doc  
✅ Planning an enterprise upgrade — see doc 32 (Production RAG Patterns) and doc 30 (Security)  
✅ Deciding between LangChain and LangGraph — see doc 33  

## 🗂️ Learning Path — All 36 Docs

### Phase 1 — Foundation (Docs 01–08)
Core LangChain building blocks. Start here.

| # | Doc | What You'll Learn |
|---|---|---|
| 01 | [LLMs & Chat Models](01_llms_and_chat_models.md) | How to call language models; chat vs completion models; temperature |
| 02 | [LangChain Overview](02_langchain_overview.md) | What LangChain is and why it exists; the component ecosystem |
| 03 | [Prompt Templates](03_prompt_templates.md) | ChatPromptTemplate; system + human messages; variable substitution |
| 04 | [Prompt Engineering Patterns](04_prompt_engineering_patterns.md) | Few-shot, role prompting, chain-of-thought; when each pattern helps |
| 05 | [LCEL — LangChain Expression Language](05_lcel.md) | Pipe syntax `prompt | llm | parser`; composing runnables |
| 06 | [Runnables](06_runnables.md) | The Runnable interface; invoke/batch/stream; parallelism with RunnableParallel |
| 07 | [Output Parsers](07_output_parsers.md) | StrOutputParser, JsonOutputParser, PydanticOutputParser |
| 08 | [Structured Output](08_structured_output.md) | `llm.with_structured_output(MyModel)`; why it's better than parsing |

### Phase 2 — Retrieval & RAG (Docs 09–19)
How to build the knowledge retrieval layer. The core of most AI assistants.

| # | Doc | What You'll Learn |
|---|---|---|
| 09 | [Document Loaders](09_document_loaders.md) | TextLoader, DirectoryLoader, PDFLoader; loading from files and APIs |
| 10 | [Text Splitters & Chunking](10_text_splitters_and_chunking.md) | RecursiveCharacterTextSplitter; chunk_size and chunk_overlap tradeoffs |
| 11 | [Embeddings](11_embeddings.md) | What embeddings are (not knowledge); semantic similarity; model choice |
| 12 | [Vector Databases](12_vector_databases.md) | Chroma, Pinecone, Qdrant; ANN search; when to use each |
| 13 | [Retrievers & Similarity Search](13_retrievers_and_similarity_search.md) | as_retriever(); k, MMR, score_threshold; retriever vs vector store |
| 14 | [Hybrid Search & BM25](14_hybrid_search_and_bm25.md) | EnsembleRetriever; why exact match matters; 60/40 weighting |
| 15 | [Cross-Encoder Reranking](15_cross_encoder_reranking.md) | ContextualCompressionRetriever; retrieve 20 → rerank → keep 4 |
| 16 | [Multi-Query Retrieval](16_multi_query_retrieval.md) | MultiQueryRetriever; query expansion for better recall |
| 17 | [History-Aware Retrieval](17_history_aware_retrieval.md) | Question rewriting; making follow-up questions retrieval-friendly |
| 18 | [RAG Chains](18_rag_chains.md) | Full RAG chain; RAGResponse structured output; sources and confidence |
| 19 | [RAG Evaluation](19_rag_evaluation.md) | Golden dataset; LLM-as-judge; correctness, groundedness, completeness |

### Phase 3 — Agents & Orchestration (Docs 20–25)
Dynamic workflows, tool calling, routing, and serving the application.

| # | Doc | What You'll Learn |
|---|---|---|
| 20 | [Tools & Function Calling](20_tools_and_function_calling.md) | @tool decorator; docstrings for tool selection; tools vs RAG |
| 21 | [Agents](21_agents.md) | create_tool_calling_agent; AgentExecutor; max_iterations; when to use agents |
| 22 | [ReAct Pattern](22_react_pattern.md) | Thought → Action → Observation loop; intermediate_steps; debugging agents |
| 23 | [Router Pattern](23_router_pattern.md) | RouteDecision; classifying questions into workflows; structured routing |
| 24 | [Memory](24_memory.md) | Session history; MAX_HISTORY_MESSAGES; format_for_rewriter; Redis upgrade |
| 25 | [FastAPI Integration](25_fastapi_integration.md) | lifespan startup; AssistantService; streaming; /debug/retrieval endpoint |

### Phase 4 — Production Operations (Docs 26–31)
Everything needed before deploying to real users.

| # | Doc | What You'll Learn |
|---|---|---|
| 26 | [Observability & Structured Logging](26_observability.md) | JSON logs; request IDs; Timer; log_retrieval(); per-stage latency |
| 27 | [LangSmith](27_langsmith.md) | Automatic tracing; @traceable; RunnableConfig metadata; dataset upload |
| 28 | [Testing AI Systems](28_testing.md) | Unit, router, retrieval, API test layers; parametrized tests; golden dataset |
| 29 | [Caching](29_caching.md) | RetailOpsCache; DOCUMENT_VERSION invalidation; never cache tools route |
| 30 | [Security](30_security.md) | API key auth; prompt injection defense; PII scrubbing; RBAC path |
| 31 | [Indexing Strategy](31_indexing_strategy.md) | Full rebuild vs incremental; DOCUMENT_VERSION; manifest files |

### Phase 5 — Architecture & Mastery (Docs 32–36)
The big picture: production patterns, enterprise readiness, and how everything connects.

| # | Doc | What You'll Learn |
|---|---|---|
| 32 | [Production RAG Patterns & Enterprise Readiness](32_production_rag_patterns.md) | Complete production architecture; enterprise readiness scorecard (~80%) |
| 33 | [LangChain Limitations & LangGraph](33_langchain_limitations_and_langgraph.md) | Where chains break down; LangGraph nodes/edges/state/HITL; migration strategy |
| 34 | [RetailOps Project Architecture](34_project_architecture.md) | Full component map; how all concepts connect; design decisions |
| 35 | [Interview Questions](35_interview_questions.md) | 30+ Q&As organized by topic; model answers with Definition→Why→How→Tradeoff |
| 36 | [Common Mistakes](36_common_mistakes.md) | 43 mistakes across all layers; debugging checklist; retrieval > prompt |

## 🔀 When to Use Which Type

**Learning from scratch?** Follow the phases in order (01 → 36). Each doc references the previous one and previews the next.

**Learning RAG specifically?** Start with Phase 1 for foundation concepts, then jump to Phase 2 (docs 09–19). Phase 4 (docs 26–31) covers the operational layer you need before deploying.

**Already know LangChain basics?** Start at doc 14 (Hybrid Search) — that's where most tutorials end and where production patterns begin.

**Debugging a production issue?** Read doc 36 (Common Mistakes) for the debugging checklist, then jump to the relevant concept doc.

**Preparing for an interview?** Read doc 35 (Interview Questions) as a self-test, then read any concept docs where your answers were weak.

**Planning an enterprise upgrade?** Read doc 32 (Production RAG Patterns) for the readiness scorecard, doc 30 (Security) for the RBAC path, and doc 33 (LangGraph) for workflow orchestration.

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
# The RetailOps request lifecycle — one line per concept doc.
# This is the mental model the entire series builds toward.

from app.router import route_question           # doc 23: classify the question
from app.memory import get_history, add_turn   # doc 24: conversation context
from app.cache import RetailOpsCache           # doc 29: skip repeated questions
from app.services import ask_rag, ask_tools, ask_general  # docs 18, 21: workflows
from app.logging_config import new_request_id  # doc 26: trace every request

cache = RetailOpsCache()

def handle(question: str, session_id: str) -> dict:
    new_request_id()                            # assign trace ID to all logs

    decision = route_question(question)         # general | rag | tools
    cached = cache.get(question, decision.route)
    if cached:
        return cached

    history = get_history(session_id)           # last N conversation turns

    if decision.route == "rag":
        # doc 17: rewrite → doc 16: multi-query → doc 14: hybrid search
        # → doc 15: reranking → doc 18: structured output
        result = ask_rag(question, history)
    elif decision.route == "tools":
        # doc 20: @tool functions → doc 21: AgentExecutor → doc 22: ReAct
        result = ask_tools(question)
    else:
        result = ask_general(question)          # doc 01: direct LLM call

    add_turn(session_id, question, result["answer"])
    cache.set(question, decision.route, result)
    return result
```

## 🔧 Real-World Example

```
RetailOps Component → Concept Docs
────────────────────────────────────────────────────────────────────────
ChatGroq(temperature=0)                         → doc 01
ChatPromptTemplate.from_messages([...])         → doc 03
prompt | llm | PydanticOutputParser(RAGResponse)→ doc 05, 07, 08
TextLoader, RecursiveCharacterTextSplitter      → doc 09, 10
HuggingFaceEmbeddings, Chroma                   → doc 11, 12
vectorstore.as_retriever(search_type="mmr")     → doc 13
EnsembleRetriever([semantic, bm25], [0.6, 0.4]) → doc 14
CrossEncoderReranker, ContextualCompression     → doc 15
MultiQueryRetriever.from_llm(retriever, llm)    → doc 16
create_history_aware_retriever + rewriter chain → doc 17
RAGResponse(answer, sources, confidence)        → doc 18
LLM judge + golden_dataset.json + JSON reports → doc 19
@tool get_low_stock_items, get_store_sales      → doc 20
create_tool_calling_agent + AgentExecutor       → doc 21
return_intermediate_steps, trace_agent_steps()  → doc 22
RouteDecision + llm.with_structured_output()    → doc 23
_sessions dict, MAX_HISTORY_MESSAGES            → doc 24
FastAPI + lifespan + AssistantService           → doc 25
RetailOpsFormatter + Timer + ContextVar         → doc 26
LANGCHAIN_TRACING_V2 + @traceable               → doc 27
pytest parametrize + scope="module" fixtures    → doc 28
RetailOpsCache + DOCUMENT_VERSION hash key      → doc 29
verify_api_key + detect_injection_attempt()     → doc 30
build_vectorstore() + manifest.json             → doc 31
```

## 🏭 Production Best Practices

The series distills to five principles for production RAG:

1. **Retrieval quality determines answer quality** — More than prompt engineering, model choice, or chunking strategy, getting the right document into the LLM's context determines answer quality. Invest in hybrid search and reranking before anything else.

2. **Measure before you optimize** — A golden dataset with 20+ examples is the most valuable thing you can build. Without it, every change is a guess. With it, every change is a measurement.

3. **Observe from day one** — LangSmith tracing and structured logging take 30 minutes to set up and save days of debugging. Enable them before your first deployment.

4. **Build for upgrades** — Local Chroma → Pinecone. In-memory cache → Redis. API key → OAuth. In-memory sessions → Redis. Every component should have a clear upgrade path that doesn't require rewriting the components that call it.

5. **Enterprise problems are architecture problems** — The gap between production baseline (~80%) and enterprise grade (90%+) is security (RBAC), workflow (LangGraph), and governance (audit trails) — not RAG engineering. Great retrieval doesn't make a system enterprise-ready.

## ⚠️ Common Mistakes to Avoid

⚠️ **Reading without building** — Every doc has runnable code. Build the RetailOps system as you go — the concepts click faster when you've run the code.

⚠️ **Skipping evaluation (doc 19)** — Many developers read docs 01–18, build a working RAG system, and ship it without evaluation. Evaluation is not optional for production systems.

⚠️ **Treating this series as exhaustive** — This covers production RAG patterns well. It doesn't cover fine-tuning, multi-modal, real-time streaming at scale, or provider-specific features. Know what it is and what it isn't.

## 🔗 How It Connects to Other Concepts

The five phases build on each other:
- **Phase 1** (Foundation) is required for everything that follows
- **Phase 2** (Retrieval) is the core of every RAG system; docs 14–16 are where most tutorials end and production begins
- **Phase 3** (Agents) extends RAG into dynamic workflows; doc 23 (Router) is the bridge
- **Phase 4** (Production) wraps everything built in phases 1–3 in the operational layer required for real deployments
- **Phase 5** (Architecture) provides the map — how it all fits together and where to go next

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | 36-doc LangChain learning series from fundamentals to enterprise architecture, built around the RetailOps AI assistant |
| **Why** | Teaches judgment (when to use what) not just API knowledge; every concept grounded in production context |
| **When** | Learning LangChain; preparing for interviews; debugging production systems; planning enterprise upgrades |
| **Phases** | Foundation (01–08) → Retrieval/RAG (09–19) → Agents (20–25) → Production (26–31) → Architecture (32–36) |
| **Production gotcha** | Retrieval quality > prompt quality; measure before optimizing; observe from day one; build for upgrades |

## ➡️ Next Steps

- **Start here:** [01_llms_and_chat_models.md](01_llms_and_chat_models.md) — or jump to any doc above based on your current level
- **Quick reference:** doc 35 (Interview Questions) covers all topics in Q&A format — useful for self-assessment
- **Production diagnosis:** doc 36 (Common Mistakes) contains the debugging checklist for production issues
- **Official docs:** https://python.langchain.com/docs/ | https://langchain-ai.github.io/langgraph/
