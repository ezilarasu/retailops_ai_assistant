# Production RAG Patterns & Enterprise Readiness
> The complete picture of what separates a working demo from a production RAG system — and what separates production from enterprise.

## 📌 What Is It?

**Production RAG** is not a single feature — it's a collection of patterns working together to make a RAG system reliable, observable, evaluated, and maintainable. A demo that loads a PDF into Chroma and answers questions is not production RAG, even if it produces good answers on the happy path.

```
Tutorial RAG (demo):
  PDF → Chroma → Chat
  Score: ~20–30% enterprise readiness

Production Baseline (RetailOps):
  Router → Rewriter → Multi-Query → Hybrid Search
  → Cross-Encoder → Structured Output → Evaluation
  → Observability → Caching → Versioning
  Score: ~80% enterprise readiness

Enterprise Grade (not yet):
  + OAuth/RBAC + Metadata Filtering + Persistent State
  + Workflow Orchestration + Governance + Compliance
  Score: 90%+
```

Each layer in a production system addresses a different failure class. Skipping retrieval quality means wrong answers. Skipping evaluation means you don't know you have wrong answers. Skipping observability means you can't diagnose why.

## ❓ Why Does It Exist?

Demo RAG fails in production for predictable reasons:
- Vector-only search misses exact match queries like "P1", "INC-1001", "SKU-7823"
- Single questions don't recall all relevant chunks — rephrasing helps
- Retrieved chunks are ranked by embedding similarity, not actual relevance
- "Looks good to me" is not a quality metric — you need ground truth evaluation
- When wrong answers appear in production, you need traces to diagnose them

Production patterns evolved specifically to address these failure modes. Each pattern has a clear job: multi-query improves recall, hybrid search adds exact match, cross-encoding improves precision, evaluation makes quality measurable.

## ⏰ When Should You Use It?

✅ Before launching to real users — establish evaluation baselines  
✅ When deploying hybrid search — the most impactful single retrieval improvement  
✅ When deploying to multiple user roles — add metadata filtering at the same time as RBAC  
✅ When query volume grows — add caching before the LLM bill grows  
✅ After any prompt or retrieval change — re-run evaluation to check for regression  

❌ Don't add all patterns at once to a tutorial — build incrementally  
❌ Don't call a system "enterprise-grade" without authorization and metadata filtering  
❌ Don't skip source attribution — answers without sources can't be verified or trusted  
❌ Don't optimize retrieval quality without a golden dataset to measure against  

## 🗂️ Types / Variants

| Pattern | What It Solves | Complexity |
|---|---|---|
| **Recall-First Retrieval** | Multi-query + hybrid search finds more relevant chunks | Medium |
| **Precision Layer** | Cross-encoder reranking keeps only the best chunks | Medium |
| **History-Aware Retrieval** | Question rewriter makes follow-up questions retrievable | Low |
| **Structured Output** | Predictable API responses with sources and confidence | Low |
| **Evaluation Pipeline** | Measurable quality with golden dataset + LLM judge | Medium |
| **Observability Stack** | Structured logs + LangSmith traces for debugging | Low-Medium |
| **Caching Layer** | Deduplicates LLM calls for repeated questions | Medium |
| **Security Layer** | Auth, input sanitization, PII protection | Medium-High |
| **Indexing Strategy** | Version-tracked, maintainable document index | Low |
| **Enterprise Additions** | RBAC, persistent memory, workflow orchestration | High |

## 🔀 When to Use Which Type

**Start with hybrid search + cross-encoder** — the two highest-ROI retrieval improvements. Hybrid search catches exact-match queries that pure vector search misses. Cross-encoder reranking filters the retrieved candidates to only the most relevant.

**Add multi-query + question rewriting** for conversational systems. Multi-query improves recall for ambiguous questions. Question rewriting (using conversation history) makes follow-up questions like "what about part-time employees?" retrieval-friendly.

**Build evaluation before optimizing** — without a golden dataset, you don't know if your changes help or hurt. Evaluation is the foundation for all further tuning.

**Add observability and caching** in parallel — they're low-risk, low-complexity, and solve expensive production problems (debugging and cost).

**Defer enterprise additions** (RBAC, persistent memory, workflow orchestration) until the use case requires them. These are high-complexity and add significant operational overhead.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Each pattern addresses a specific, real failure mode | More patterns = more complexity and latency |
| Hybrid search + reranking dramatically improve retrieval | Cross-encoder adds 200–800ms latency |
| Evaluation makes quality measurable and regression-detectable | Building a good golden dataset requires effort |
| Structured output enables reliable APIs and automation | Enterprise additions (RBAC, workflow) are high-cost |
| Caching cuts repeat LLM costs by 40–70% | Pattern interactions can be hard to debug in isolation |

## 💻 Basic Example

```python
# The recall-first, precision-second retrieval pattern
# This is the core pattern that separates production RAG from tutorial RAG.

from langchain_core.runnables import RunnablePassthrough
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# ── Step 1: Build recall layer (hybrid search) ───────────────────────────
# Semantic search finds conceptually similar chunks.
# BM25 finds exact keyword matches (P1, SKU-789, INC-1001).
# Combining them maximizes recall.

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)

semantic_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
bm25_retriever = BM25Retriever.from_documents(all_docs, k=10)

# EnsembleRetriever merges results with configurable weights
hybrid_retriever = EnsembleRetriever(
    retrievers=[semantic_retriever, bm25_retriever],
    weights=[0.6, 0.4],  # tune based on eval results
)

# ── Step 2: Add precision layer (cross-encoder reranking) ────────────────
# Cross-encoder scores each (query, doc) pair — much more accurate than
# embedding similarity, but too slow to use as the initial retriever.
# Pattern: broad retrieval (top 20) → precise reranking (top 4).

from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

cross_encoder = HuggingFaceCrossEncoder(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
reranker = CrossEncoderReranker(model=cross_encoder, top_n=4)

# Wrap: hybrid_retriever retrieves top 20, reranker keeps top 4
production_retriever = ContextualCompressionRetriever(
    base_compressor=reranker,
    base_retriever=hybrid_retriever,
)

# Result: high recall (hybrid) + high precision (reranker) = production quality
docs = production_retriever.invoke("How many vacation days do employees get?")
print([d.metadata["source"] for d in docs])  # should include hr_policy.txt
```

## 🔧 Real-World Example

RetailOps' complete production architecture — each layer shown with its role, the full request lifecycle, and the enterprise readiness scorecard.

```python
# ══════════════════════════════════════════════════════════════════════════
# RetailOps Production RAG Architecture — full request lifecycle
#
# Layer 1: Router          → classify question (general/rag/tools)
# Layer 2: Rewriter        → expand follow-up questions using history
# Layer 3: Multi-Query     → generate alternative phrasings for recall
# Layer 4: Hybrid Retrieval → semantic + BM25 for broad recall
# Layer 5: Cross-Encoder   → rerank to top 4 for precision
# Layer 6: RAG Chain       → structured output with sources + confidence
# Layer 7: Cache           → skip layers 2-6 for repeated questions
# Layer 8: Observability   → logs + LangSmith trace for every request
# ══════════════════════════════════════════════════════════════════════════

from app.router import route_question
from app.services import ask_rag, ask_tools, ask_general
from app.memory import get_history, add_turn
from app.cache import RetailOpsCache
from app.logging_config import log_request, log_error, new_request_id
import time

cache = RetailOpsCache()


def handle_request(question: str, session_id: str) -> dict:
    """Complete production request handler — all layers."""
    new_request_id()  # assign request_id to all logs for this request
    t_start = time.perf_counter()

    # ── Layer 1: Route ───────────────────────────────────────────────────
    decision = route_question(question)
    route = decision.route

    # ── Layer 7: Cache check ─────────────────────────────────────────────
    cached = cache.get(question, route)
    if cached:
        return cached  # skip retrieval + LLM entirely

    # ── Layer 2-6: RAG, Tools, or General ───────────────────────────────
    history = get_history(session_id)
    try:
        if route == "rag":
            result = ask_rag(question, history)
        elif route == "tools":
            result = ask_tools(question)
        else:
            result = ask_general(question)
    except Exception as e:
        log_error("pipeline", e, question)
        return {"answer": "I'm unable to answer right now. Please try again.", "route": route}

    # ── Memory + Cache ───────────────────────────────────────────────────
    add_turn(session_id, question, result["answer"])
    cache.set(question, route, result)

    # ── Layer 8: Log ─────────────────────────────────────────────────────
    total_ms = round((time.perf_counter() - t_start) * 1000, 1)
    log_request(question, route, result.get("sources", []), result.get("confidence", ""), {"total_ms": total_ms})

    return result


# ── Enterprise Readiness Scorecard ───────────────────────────────────────
#
# Layer                      RetailOps Status   Gap
# ──────────────────────────────────────────────────────────────────────────
# Foundation (LLM, LCEL)     PASS               —
# RAG (hybrid, reranker)     PASS               —
# Evaluation (LLM judge)     PASS               —
# Observability (logs+LS)    PASS               —
# API (FastAPI, schemas)     PASS               —
# Security                   PARTIAL            OAuth, RBAC, metadata filter
# Indexing                   PARTIAL            Incremental updates
# Memory                     PARTIAL            Persistent (Redis)
# Workflow / HITL            NOT IMPLEMENTED    LangGraph needed
# Multi-Agent                NOT IMPLEMENTED    LangGraph needed
# Enterprise Integrations    NOT IMPLEMENTED    Confluence, SharePoint
# Reliability                PARTIAL            Circuit breakers, retries
# Scalability                PARTIAL            Redis cache, distributed DB
# Compliance / Governance    NOT IMPLEMENTED    Audit trails, GDPR
#
# Overall score: ~80% (production baseline, not yet enterprise-grade)
# The gap is enterprise architecture, not RAG engineering.

# ── Key insight ──────────────────────────────────────────────────────────
# Most teams spend their effort on chunking, embeddings, and prompts.
# Enterprise readiness is determined by:
#   Security (authorization + metadata filtering)
#   Workflow orchestration (approvals, persistent state)
#   Governance (audit trails, compliance)
# — not retrieval quality alone.
```

## 🏭 Production Best Practices

1. **Use hybrid search as your default retrieval strategy** — Pure vector search misses exact-match queries for product codes, incident IDs, and abbreviations. Adding BM25 with 40% weight captures these at near-zero implementation cost. **How:** `EnsembleRetriever(retrievers=[semantic, bm25], weights=[0.6, 0.4])`.

2. **Add cross-encoder reranking before launch** — This is the highest-ROI retrieval improvement available. Retrieving 20 candidates and reranking to 4 typically improves source accuracy by 15–25 percentage points. The 300ms latency cost is worth it. **How:** Wrap your hybrid retriever in `ContextualCompressionRetriever(base_compressor=CrossEncoderReranker(...), base_retriever=hybrid_retriever)`.

3. **Build a golden dataset before optimizing anything** — Without ground truth (question, expected_source, expected_answer) pairs, you're guessing whether changes help or hurt. Build 20 representative examples covering all routes and run evaluation after every significant change. **How:** Save `evals/golden_dataset.json` and run `python -m evals.run_rag_eval` after each change.

4. **Return sources in every RAG response** — Sources let users verify answers, let developers debug retrieval failures, and let evaluation pipelines check source accuracy. They also reduce hallucination trust: if the source doesn't support the answer, the user can see it. **How:** `RAGResponse(answer=..., sources=[d.metadata["source"] for d in docs], confidence=...)`.

5. **Treat "it looks good" as a red flag** — The most dangerous production bugs are confident wrong answers. An LLM citing an outdated policy with high confidence is worse than "I don't know." Measure correctness, groundedness, and completeness against your golden dataset. **How:** Use LLM-as-judge evaluation (doc 19) on a schedule and after every change.

6. **Distinguish production baseline from enterprise grade** — A system with hybrid search, evaluation, and observability is a strong production baseline (~80%). Enterprise grade requires authorization (RBAC + metadata filtering), persistent memory, workflow orchestration, and compliance controls. Don't confuse one for the other when setting stakeholder expectations. **How:** Use the enterprise readiness scorecard as a planning tool — it tells you exactly what's missing.

## ⚠️ Common Mistakes to Avoid

⚠️ **Calling a demo "production-ready"** — `PDF → Chroma → Chat` is a tutorial. Production means evaluated, observable, and maintainable. The distinction matters because demos fail at the first edge case; production systems handle them gracefully.

⚠️ **Skipping evaluation** — Without a golden dataset and measurable metrics, you have no way to know if a prompt change improved or degraded quality. "I tested 5 questions and they looked good" is not evaluation.

⚠️ **Vector-only search in enterprise contexts** — Enterprise data is full of exact-match requirements: incident IDs (P1, INC-1001), product codes (SKU-789), dates, and abbreviations. Pure vector search scores these poorly. Add BM25.

⚠️ **Post-retrieval access filtering** — Retrieving all documents and then telling the LLM "don't mention HR docs to this user" is not secure. The LLM has already seen the content. Filter before retrieval using metadata filters on the vector store.

⚠️ **Calling production-baseline "enterprise-grade"** — A system with API key auth is not enterprise-grade. Enterprise requires per-user authorization, RBAC, metadata filtering, audit trails, and compliance controls. Promising enterprise-grade without these creates security and compliance risk.

## 🔗 How It Connects to Other Concepts

- **Hybrid Search** (doc 11) — The recall layer of the production retrieval pattern; EnsembleRetriever combines semantic + BM25
- **Cross-Encoder Reranking** (doc 15) — The precision layer; wraps the retriever in ContextualCompressionRetriever
- **Multi-Query Retrieval** (doc 13) — Generates alternative query phrasings to improve recall
- **RAG Evaluation** (doc 19) — The measurement tool for production quality; without it you can't validate patterns are working
- **Security** (doc 30) — RBAC + metadata filtering is the key gap between production baseline and enterprise grade
- **LangChain Limitations & LangGraph** (doc 33) — Workflow orchestration and persistent state are the remaining enterprise architecture gaps

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Collection of retrieval, evaluation, observability, and security patterns that define production-quality RAG |
| **Why** | Demo RAG fails on exact match, multi-step queries, and edge cases; each production pattern addresses a specific failure mode |
| **When** | Before launch (evaluation, hybrid search); at scale (caching, observability); for enterprise (RBAC, workflow) |
| **Types** | Recall (multi-query, hybrid), precision (reranking), quality (evaluation), operations (observability, caching), enterprise (RBAC, workflow) |
| **Production gotcha** | Hybrid + reranking first; evaluate before optimizing; distinguish production baseline (~80%) from enterprise grade (90%+) |

## ➡️ Next Steps

- **Example files:** `app/services.py`, `app/router.py`, `app/vector_store.py` — complete RetailOps production pipeline
- **Next doc:** `33_langchain_limitations_and_langgraph.md` — where LangChain reaches its limits and when LangGraph becomes necessary
- **Official docs:** https://python.langchain.com/docs/tutorials/rag/
