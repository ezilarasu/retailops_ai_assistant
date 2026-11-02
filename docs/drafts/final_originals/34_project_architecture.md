# RetailOps Project Architecture
> How every concept in this learning series fits together in one real application.

## 📌 What Is It?

**RetailOps AI Assistant** is a production-baseline RAG application that serves as the running example throughout this learning series. It answers questions for retail store operators using three workflow paths: static knowledge retrieval (RAG), live operational data (tools), and general conversation.

Understanding its architecture gives you a map of how LangChain's core concepts — LLMs, prompts, chains, memory, parsers, embeddings, retrieval, agents — connect in a real system.

```
RetailOps Request Lifecycle:

  HTTP POST /chat
       ↓
  FastAPI endpoint         ← doc 25: API layer, auth dependency
       ↓
  AssistantService         ← service layer, chain startup
       ↓
  Cache check              ← doc 29: skip if seen before
       ↓
  Router                   ← doc 23: classify question
  ┌────────────────────────────────────────┐
  │ general   │  rag         │  tools      │
  ↓           ↓              ↓
General     Rewriter       AgentExecutor
chain       ↓              (ReAct loop)   ← doc 21-22: agent
↓           Multi-Query    ↓
Answer      ↓              Tool calls     ← doc 20: tools
            Hybrid Search  ↓
            (Vector+BM25)  Answer
            ↓
            Cross-Encoder
            ↓
            RAG Chain      ← doc 18: structured output
            ↓
            RAGResponse
  └────────────────────────────────────────┘
       ↓
  Memory update            ← doc 24: add turn to session history
  Cache write
       ↓
  Structured JSON response
```

## ❓ Why Does It Exist?

RetailOps exists to answer a practical question: "How do all these LangChain concepts actually fit together?"

Reading individual concept docs teaches you what each piece does. RetailOps shows you the decisions:
- **Why routing?** Because a single LLM can't efficiently answer both "what's the vacation policy?" (static knowledge) and "show me today's sales" (live data)
- **Why hybrid search?** Because operational data has product codes and incident IDs that semantic search handles poorly
- **Why structured output?** Because downstream code, caching, and evaluation all need predictable response shapes
- **Why a service layer?** Because chains are expensive to build — you want to build them once at startup, not per request

## ⏰ When Should You Use It?

✅ When learning how concepts connect — trace a request through the architecture  
✅ When designing your own AI assistant — use RetailOps as a reference pattern  
✅ When debugging — the architecture tells you which layer to investigate  
✅ When planning enterprise upgrades — the gaps are documented  

❌ This is a learning reference and production baseline — don't use it as-is for sensitive enterprise data without adding RBAC and metadata filtering  
❌ Don't deploy the in-memory cache and session store for multi-server deployments — upgrade to Redis first  

## 🗂️ Types / Variants

| Component Layer | What It Does | Key Files |
|---|---|---|
| **Document Store** | Source TXT files that answer questions | `data/*.txt` |
| **Index Layer** | Vector store + BM25 index of chunked documents | `app/indexing.py`, `chroma_db/` |
| **Retrieval Layer** | Hybrid search + cross-encoder reranking | `app/vector_store.py` |
| **Chain Layer** | RAG chain, rewriter chain, general chain | `app/rag.py`, `app/chains.py` |
| **Agent Layer** | Tool-calling agent for live operational data | `app/agents.py`, `app/tools.py` |
| **Router Layer** | Classifies questions into workflow paths | `app/router.py` |
| **Service Layer** | Orchestrates all workflows per request | `app/services.py` |
| **Memory Layer** | Per-session conversation history | `app/memory.py` |
| **Cache Layer** | Response deduplication | `app/cache.py` |
| **API Layer** | FastAPI endpoints, auth, validation | `app/api.py` |
| **Security Layer** | Auth, injection detection, PII scrubbing | `app/security.py` |
| **Observability Layer** | Structured logs + LangSmith traces | `app/logging_config.py` |
| **Evaluation Layer** | Golden dataset + LLM judge | `evals/` |
| **Test Suite** | Unit, integration, retrieval tests | `tests/` |

## 🔀 When to Use Which Type

This architecture separates concerns so each layer can be tested, debugged, and upgraded independently:

**Improving answer quality?** → Change the retrieval layer (chunking, retrieval strategy, reranking) and run `evals/` to measure the impact.

**Debugging a wrong answer?** → Check the router output (was it routed correctly?), then the retriever output (was the right source found?), then the LLM output (was the context used correctly?). The three-layer test suite mirrors this diagnostic path.

**Scaling to more users?** → Upgrade memory layer (in-memory → Redis), cache layer (in-memory dict → Redis), and vector store (Chroma local → Pinecone/Qdrant).

**Adding enterprise features?** → Security layer (API key → OAuth/RBAC), retrieval layer (add metadata filtering), workflow layer (add LangGraph for approval flows).

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Clear separation of concerns — each layer testable independently | More files and components than a minimal tutorial |
| Router pattern makes retrieval vs tools vs general explicit | In-memory state (cache, sessions) doesn't scale to multiple servers |
| Service layer builds chains once at startup | Chroma local storage doesn't scale to millions of documents |
| Structured output enables reliable evaluation and caching | API key auth is not enterprise-grade |
| All production patterns present: hybrid search, reranking, evaluation | Workflow layer (LangGraph) not implemented yet |

## 💻 Basic Example

```python
# The request lifecycle in RetailOps — simplified to show the core flow.
# Each function call represents one layer of the architecture.

from app.router import route_question          # Layer: Router
from app.memory import get_history, add_turn   # Layer: Memory
from app.cache import RetailOpsCache           # Layer: Cache
from app.services import ask_rag, ask_tools, ask_general  # Layer: Chains/Agent

cache = RetailOpsCache()

def handle(question: str, session_id: str) -> dict:
    # 1. Check cache — skip everything for repeated questions
    decision = route_question(question)
    cached = cache.get(question, decision.route)
    if cached:
        return cached

    # 2. Get conversation history for context
    history = get_history(session_id)

    # 3. Route to the right workflow
    if decision.route == "rag":
        result = ask_rag(question, history)      # retrieve → generate
    elif decision.route == "tools":
        result = ask_tools(question)              # agent → tools → answer
    else:
        result = ask_general(question)            # direct LLM

    # 4. Update memory and cache
    add_turn(session_id, question, result["answer"])
    cache.set(question, decision.route, result)

    return result

# Example requests and their routes:
handle("What is the return policy?", "s1")          # → rag
handle("Show me today's sales for store 101", "s1") # → tools
handle("Hello!", "s1")                               # → general
```

## 🔧 Real-World Example

The complete component map with each concept doc cross-referenced, showing exactly which code implements which concept:

```python
# ══════════════════════════════════════════════════════════════════════════
# RetailOps Component Map
# ══════════════════════════════════════════════════════════════════════════
#
# FOUNDATION
# ─────────────────────────────────────────────────────────────────────────
# LLM: ChatGroq (llama-3.3-70b-versatile, temperature=0)        → doc 01
#   - Used for: RAG generation, routing, rewriting, evaluation
#   - Config: GROQ_API_KEY in .env, model name in .env
#
# Prompts: ChatPromptTemplate (system + human messages)          → doc 02-03
#   - RAG prompt: system with context + security rules, human question
#   - Router prompt: classify into general/rag/tools
#   - Rewriter prompt: expand follow-up questions using history
#
# LCEL chains: prompt | llm | parser                             → doc 04
#   - All chains use pipe syntax (not legacy LLMChain)
#   - RAG chain: prompt | llm | PydanticOutputParser(RAGResponse)
#   - Router chain: prompt | llm.with_structured_output(RouteDecision)
#
# Structured Output: Pydantic models                             → doc 05
#   - RAGResponse(answer, sources, confidence)
#   - RouteDecision(route, reason)
#   - Tool response strings (tools return formatted strings)
#
# ─────────────────────────────────────────────────────────────────────────
# RETRIEVAL
# ─────────────────────────────────────────────────────────────────────────
# Documents: 4 TXT files in data/                                → doc 06
#   - hr_policy.txt, returns_policy.txt, it_support_kb.txt, store_sop.txt
#
# Chunking: RecursiveCharacterTextSplitter(500, 50)              → doc 07
#   - Enterprise upgrade: SemanticChunker
#
# Embeddings: HuggingFaceEmbeddings(all-MiniLM-L6-v2)           → doc 08-10
#   - Free, local, no API key required
#
# Vector Store: Chroma (local persistence)                       → doc 11-12
#   - chroma_db/ directory with manifest.json
#   - Enterprise upgrade: Pinecone or Qdrant
#
# Retrieval:
#   Semantic: vectorstore.as_retriever(k=10)                     → doc 09
#   BM25: BM25Retriever(all_docs, k=10)                         → doc 11
#   MMR: available as search_type="mmr"                          → doc 10
#   Hybrid: EnsembleRetriever([semantic, bm25], [0.6, 0.4])     → doc 11
#   Multi-Query: MultiQueryRetriever wrapping hybrid             → doc 13
#   Parent-Child: available pattern (not current default)        → doc 14
#   Cross-Encoder: ContextualCompressionRetriever + reranker     → doc 15
#
# Final retriever pipeline: multi-query → hybrid → cross-encoder
#
# ─────────────────────────────────────────────────────────────────────────
# CHAINS & AGENTS
# ─────────────────────────────────────────────────────────────────────────
# Question Rewriter: history + question → standalone question    → doc 16-18
# RAG Chain: context + question → RAGResponse                    → doc 18
# Evaluation: LLM judge scores against golden dataset            → doc 19
# Tools: @tool functions for inventory, sales, incidents         → doc 20
# Agent: create_tool_calling_agent + AgentExecutor               → doc 21
# ReAct: intermediate_steps show Thought/Action/Observation      → doc 22
# Router: RouteDecision with route + reason fields               → doc 23
#
# ─────────────────────────────────────────────────────────────────────────
# PRODUCTION LAYERS
# ─────────────────────────────────────────────────────────────────────────
# Memory: _sessions dict[str, list[dict]], MAX_HISTORY_MESSAGES  → doc 24
# API: FastAPI + lifespan + AssistantService + streaming         → doc 25
# Observability: RetailOpsFormatter, Timer, ContextVar request_id → doc 26
# LangSmith: LANGCHAIN_TRACING_V2=true, @traceable, RunnableConfig → doc 27
# Testing: pytest pyramid — unit, router, retrieval, API tests   → doc 28
# Caching: RetailOpsCache with DOCUMENT_VERSION in key           → doc 29
# Security: verify_api_key, detect_injection_attempt, scrub_pii  → doc 30
# Indexing: versioned rebuild, manifest.json, DOCUMENT_VERSION   → doc 31
#
# ─────────────────────────────────────────────────────────────────────────
# ENTERPRISE PATH (planned, not yet implemented)
# ─────────────────────────────────────────────────────────────────────────
# Security upgrade: OAuth/JWT → RBAC → metadata-filtered retrieval
# Memory upgrade: in-memory dict → Redis (session persistence)
# Cache upgrade: in-memory dict → Redis (shared across workers)
# Vector DB upgrade: Chroma local → Pinecone/Qdrant (distributed)
# Workflow: LangGraph approval workflows (refund escalation etc) → doc 33
# Integrations: Confluence, SharePoint, ServiceNow document connectors
# Compliance: audit trails, GDPR, SOC2

# ─────────────────────────────────────────────────────────────────────────
# KEY DESIGN DECISIONS (and why)
# ─────────────────────────────────────────────────────────────────────────
#
# Decision: Router before RAG, not unified prompt
# Why: A single "answer everything" prompt is fragile; routing lets each
#      workflow be optimized independently (RAG gets retrieval, tools get
#      agent loop, general gets direct LLM)
#
# Decision: Service layer builds chains at startup (lifespan)
# Why: Building chains involves loading Chroma, building retrievers, and
#      initializing models. Doing this per-request adds 2-10s latency.
#
# Decision: Structured output for RAG responses
# Why: RAGResponse(answer, sources, confidence) enables evaluation,
#      caching by content, source attribution, and reliable API contracts
#
# Decision: Cache never caches tools route
# Why: Tools answer live data (current inventory, today's sales). Caching
#      tool responses would serve stale operational data.
#
# Decision: Recall-first retrieval (multi-query + hybrid)
# Why: Better to retrieve too many relevant candidates and rerank than
#      to miss relevant documents entirely in the initial retrieval pass.
```

## 🏭 Production Best Practices

1. **Use the layered architecture as your debugging guide** — When an answer is wrong, check layers in order: router (was it classified correctly?), retriever (was the right source returned?), LLM (was the context used correctly?). Each layer has a dedicated test type to isolate it. **How:** Router → `test_router.py`, Retriever → `test_retrieval.py`, LLM → `evals/run_rag_eval.py`.

2. **Keep chains in the service layer, not the API layer** — The API layer handles HTTP concerns (request/response, auth, validation). Chain logic belongs in the service layer. This separation keeps your chains testable without HTTP overhead. **How:** `api.py` calls `_service.ask(question)`, not `rag_chain.invoke(question)` directly.

3. **Design the upgrade path from day one** — Every component has a planned upgrade: Chroma → Pinecone, in-memory cache → Redis, API key auth → OAuth. Design component interfaces so upgrades require changing one module, not every file that touches it. **How:** `get_vectorstore()` in `vector_store.py` returns a retriever interface — callers don't care whether it's Chroma or Pinecone.

4. **Match test types to architecture layers** — Unit tests for tools, router tests for routing layer, retrieval tests for retrieval layer, API tests for API layer. This lets you pinpoint which layer introduced a regression. **How:** See `tests/test_tools.py`, `test_router.py`, `test_retrieval.py`, `test_api.py`.

5. **The ~80% production score is a starting point, not a ceiling** — RetailOps demonstrates the production baseline. The remaining 20% (RBAC, persistent memory, workflow orchestration) are enterprise architecture concerns, not RAG engineering. Plan your upgrade path based on actual use case requirements. **How:** Use the enterprise readiness scorecard (doc 32) to prioritize your next investments.

## ⚠️ Common Mistakes to Avoid

⚠️ **Building a monolithic `main.py`** — When all logic lives in one file, debugging is hard, testing is harder, and upgrades require rewriting instead of swapping. Separate concerns: indexing, retrieval, chains, agents, routing, memory, caching, API.

⚠️ **Creating chains per request** — Building a Chroma retriever, loading embeddings, and constructing chains on every `/chat` request adds seconds of latency. Build chains once at startup (via `lifespan`), hold them in a service object, call them per request.

⚠️ **Skipping the service layer** — FastAPI route handlers that call chains directly make it impossible to add caching, retry logic, or observability without modifying the API layer. A service layer is the seam for all of these.

⚠️ **Using the same retriever for all routes** — Routing questions to "rag" but using the same retriever for "what's in stock?" (better answered by tools) produces poor results. The router's job is to send questions to the right workflow; the retriever only runs for questions that belong in the knowledge base.

⚠️ **Not planning the enterprise upgrade path** — Starting with local Chroma and in-memory state is fine for development. Not planning the Redis/distributed DB/RBAC upgrade creates painful rewrites later. Design interfaces that abstract storage backends from day one.

## 🔗 How It Connects to Other Concepts

Every concept in the series connects through this architecture:

- **Docs 01–05** (LLMs, prompts, chains, parsers) → Foundation used by every chain and agent
- **Docs 06–15** (embeddings, retrieval, hybrid, reranking) → Retrieval layer
- **Docs 16–22** (RAG chains, evaluation, tools, agents, ReAct) → Chain and agent layer
- **Docs 23–25** (router, memory, FastAPI) → Service and orchestration layer
- **Docs 26–30** (observability, LangSmith, testing, caching, security) → Production operations layer
- **Doc 31** (indexing) → Offline pipeline that builds the retrieval layer
- **Doc 33** (LangGraph) → The enterprise workflow layer that extends this architecture

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Production-baseline AI assistant with router, RAG, tools, memory, caching, auth, observability, and evaluation |
| **Why** | Shows how all LangChain concepts connect in a real system; serves as reference architecture |
| **When** | Use as a reference pattern for any AI assistant; upgrade individual layers as requirements grow |
| **Types** | 14 component layers: foundation, retrieval, chains/agents, service, memory, cache, API, security, observability, indexing, evaluation, testing |
| **Production gotcha** | Build chains at startup, not per request; use service layer as seam for cross-cutting concerns; plan the enterprise upgrade path |

## ➡️ Next Steps

- **All source files:** `app/` directory — each file corresponds to one or more architecture layers
- **Next doc:** `35_interview_questions.md` — consolidated Q&A covering every concept for interview preparation
- **Architecture diagram:** trace any request through the request lifecycle diagram at the top of this doc
