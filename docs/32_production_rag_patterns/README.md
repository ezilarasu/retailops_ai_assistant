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
  Score: ~85% enterprise readiness

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
| **Observability Stack** | Request-ID logs + LangSmith traces for debugging (structured JSON logs are an upgrade) | Low-Medium |
| **Caching Layer** | Deduplicates LLM calls for repeated questions | Medium |
| **Security Layer** | Auth, input sanitization, PII protection (RetailOps implements API-key auth only; see doc 30) | Medium-High |
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
| Caching can cut repeat LLM costs substantially (how much depends on how often users repeat questions) | Pattern interactions can be hard to debug in isolation |

## 💻 Basic Example

```python
# The recall-first, precision-second retrieval pattern
# This is the core pattern that separates production RAG from tutorial RAG.
#
# This snippet uses LangChain's ready-made classes (the "built-in" version).
# RetailOps does the same job with small hand-written classes in
# app/hybrid_retriever.py and app/reranker.py — see the Real-World Example.
# Run from the repository root. In LangChain 1.x these classes live in the
# `langchain_classic` package (installed alongside langchain-community).

from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from app.rag import load_documents, split_documents   # RetailOps loaders (docs 09-10)

# ── Step 1: Build recall layer (hybrid search) ───────────────────────────
# Semantic search finds conceptually similar chunks.
# BM25 finds exact keyword matches (P1, SKU-789, INC-1001).
# Combining them maximizes recall.

all_docs = split_documents(load_documents())          # the data/*.txt chunks
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
# In-memory index built right here, so the snippet runs without the app's saved index
vectorstore = Chroma.from_documents(all_docs, embeddings)

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

from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

cross_encoder = HuggingFaceCrossEncoder(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
reranker = CrossEncoderReranker(model=cross_encoder, top_n=4)

# Wrap: hybrid_retriever returns up to ~20 candidates (10 semantic + 10 keyword), reranker keeps top 4
production_retriever = ContextualCompressionRetriever(
    base_compressor=reranker,
    base_retriever=hybrid_retriever,
)

# Result: high recall (hybrid) + high precision (reranker) = production quality
docs = production_retriever.invoke("How many vacation days do employees get?")
print([d.metadata["source"] for d in docs])  # should include hr_policy.txt
```

## 🔧 Real-World Example

RetailOps' production architecture — each layer shown with its role and where it lives in the code, the full request lifecycle, and the enterprise readiness scorecard. Where RetailOps hand-writes a layer that LangChain also ships as a class, the built-in equivalent is noted.

```python
# ══════════════════════════════════════════════════════════════════════════
# RetailOps Production RAG Architecture — full request lifecycle
#
# Layer 1: Router          → classify question (general/rag/tools)      app/router.py
# Layer 2: Rewriter        → expand follow-up questions using history   app/chains.py
#                            (skipped on the first question: no history yet;
#                             built-in equivalent: create_history_aware_retriever)
# Layer 3: Multi-Query     → generate alternative phrasings for recall  app/multi_query.py
#                            (built-in equivalent: MultiQueryRetriever)
# Layer 4: Hybrid Retrieval → vector (MMR) + BM25 candidates, merged     app/hybrid_retriever.py
#                            and de-duplicated (built-in: EnsembleRetriever)
# Layer 5: Cross-Encoder   → rerank to the top RETRIEVAL_K chunks        app/reranker.py
#                            (2 with .env.example; chunks scoring below RERANK_MIN_SCORE
#                             are dropped; built-in: ContextualCompressionRetriever)
# Layer 6: RAG Chain       → structured output with sources + confidence app/chains.py
# Layer 7: Cache           → skip layers 1-6 for repeated first questions app/services.py, app/cache.py
#                            (general/rag only; never tools or follow-ups)
# Layer 8: Observability   → request_id log lines + LangSmith metadata   app/router.py, app/tracing.py
# Layer 9: Reliability     → typed errors, one retry, HTTP status mapping app/exceptions.py, app/llm.py
#
# Models: LLM_MODEL (default openai/gpt-oss-20b) runs the router, general chat and
# RAG answer; TOOLS_LLM_MODEL (default openai/gpt-oss-120b) runs the tool agent,
# because the smaller model often failed multi-tool questions (2 of 8 runs worked,
# against 8 of 8 for the larger one). Use a stronger model where the task needs it.
# ══════════════════════════════════════════════════════════════════════════

from app.services import assistant_service

# One call runs every layer. Do NOT add your own memory, cache or logging
# calls around it: the service already checks the cache (Layer 7), and
# run_router() already generates a request_id, logs it, saves the turn to
# the session's conversation memory, retries transient model failures, and
# turns errors into a safe response with a code. Calls with the same
# session_id share chat history; the default session is "default".
result = assistant_service.ask(
    "How many vacation days do full-time store employees get?",
    session_id="demo-user-1",
)

print(result["route"])        # general | rag | tools | error
print(result["sources"])      # rag route only
print(result["confidence"])   # rag route only: high | medium | low
print(result["latency_ms"])   # measured inside run_router() (or the cache lookup)
print(result["cache_hit"])    # True if a first question was served from the 5-minute cache
print(result.get("error"))    # on route "error": model_refused | rate_limited | ...


# ── Enterprise Readiness Scorecard (a rough self-assessment) ─────────────
#
# Layer                      RetailOps Status   Gap
# ──────────────────────────────────────────────────────────────────────────
# Foundation (LLM, LCEL)     PASS               —
# RAG (hybrid, reranker)     PASS               —
# Evaluation (LLM judge)     PARTIAL            Harness exists; demo set is only 5 questions;
#                                               the same model writes and grades the answers
# Observability (logs+LS)    PARTIAL            Plain-text logs with request IDs, LangSmith tags;
#                                               no JSON logs, metrics, or dashboards
# API (FastAPI, schemas)     PASS               —
# Security                   PARTIAL            API key only (constant-time compare; default key
#                                               refused outside local): no OAuth, RBAC, metadata
#                                               filter, injection defense, or PII scrubbing
# Indexing                   PARTIAL            Fingerprinted, versioned rebuild; no incremental updates
# Memory                     PARTIAL            Per-session in-memory history; lost on restart,
#                                               not shared between workers, not tied to a user
# Caching                    PARTIAL            First-turn general/rag answers only, in-memory
# Workflow / HITL            PARTIAL            Working LangGraph demo in app/graph/ (examples 23-28),
#                                               not wired into the CLI or API
# Multi-Agent                NOT IMPLEMENTED    LangGraph needed
# Enterprise Integrations    NOT IMPLEMENTED    Confluence, SharePoint
# Reliability                PARTIAL            Typed errors, one retry, friendly messages and HTTP
#                                               statuses; no circuit breaker or fallback model
# Cost / rate limits         PARTIAL            Free-tier token limits (per minute AND per day) surface
#                                               as a friendly 429; no budgets or per-user quotas
# Scalability                PARTIAL            Redis cache, distributed DB
# Compliance / Governance    NOT IMPLEMENTED    Audit trails, GDPR
#
# Overall score: ~85% as a rough judgment of a production *baseline* (doc 37's checklist
# gives 24 of 28 items; not a measured number, and not enterprise-grade). The gap is
# enterprise architecture, not RAG engineering.

# ── Key insight ──────────────────────────────────────────────────────────
# Most teams spend their effort on chunking, embeddings, and prompts.
# Enterprise readiness is determined by:
#   Security (authorization + metadata filtering)
#   Workflow orchestration (approvals, persistent state)
#   Governance (audit trails, compliance)
# — not retrieval quality alone.
```

> **Lesson from this project:** the biggest speed-ups were not clever tuning, they were "do the expensive thing once". Reloading the cross-encoder on every question cost about 2 seconds and about 36 Hugging Face requests each time (retrieval went from about 6.4 s to under 1 s once it was loaded at start-up). The embedding model was loaded twice at start-up until `get_embeddings()` was cached. Re-adding every chunk to Chroma on every start grew the index to 460 entries for 22 distinct texts until chunks got stable IDs. Reliability followed the same pattern: pick the model per task (the tool agent needs a stronger model than the router) and turn provider failures into typed errors with one retry, instead of letting a raw 400 reach the user. Measure before you tune, and look for work that is repeated for no reason.

## 🏭 Production Best Practices

1. **Use hybrid search as your default retrieval strategy** — Pure vector search misses exact-match queries for product codes, incident IDs, and abbreviations. Adding BM25 captures these at near-zero implementation cost. **How:** with the built-in class, `EnsembleRetriever(retrievers=[semantic, bm25], weights=[0.6, 0.4])` (tune the weights on your eval set). RetailOps takes a simpler route in `app/hybrid_retriever.py`: it merges the vector results with the BM25 top 10, removes duplicates, and lets the reranker decide the order, so it has no weights to tune.

2. **Add cross-encoder reranking before launch** — This is often the highest-ROI retrieval improvement available: retrieve a broad set of candidates, then keep only the few the cross-encoder scores highest. It adds a few hundred milliseconds of latency, so measure the gain on your own eval set before and after. **How:** with the built-in classes, wrap your hybrid retriever in `ContextualCompressionRetriever(base_compressor=CrossEncoderReranker(...), base_retriever=hybrid_retriever)`. RetailOps does the same thing by hand: `CrossEncoderReranker` in `app/reranker.py` scores each (question, chunk) pair with `cross-encoder/ms-marco-MiniLM-L-6-v2` and keeps the top `RETRIEVAL_K`.

3. **Build a golden dataset before optimizing anything** — Without ground truth (question, expected_source, expected_answer) pairs, you're guessing whether changes help or hurt. Build 20 or more representative examples covering all routes and run evaluation after every significant change. **How:** RetailOps keeps its questions in `evals/rag_questions.jsonl` (one JSON object per line with `question`, `expected_answer`, `expected_source`) and runs them with `python -m evals.run_rag_eval`. The repo ships only 5 demo questions to show the harness; treat that as a template and grow it.

4. **Return sources in every RAG response** — Sources let users verify answers, let developers debug retrieval failures, and let evaluation pipelines check source accuracy. They also reduce hallucination trust: if the source doesn't support the answer, the user can see it. **How:** `RAGResponse(answer=..., sources=[d.metadata["source"] for d in docs], confidence=...)`.

5. **Treat "it looks good" as a red flag** — The most dangerous production bugs are confident wrong answers. An LLM citing an outdated policy with high confidence is worse than "I don't know." Measure correctness, groundedness, and completeness against your golden dataset. **How:** Use LLM-as-judge evaluation (doc 19) on a schedule and after every change.

6. **Distinguish production baseline from enterprise grade** — A system with hybrid search, evaluation, and observability is a strong production baseline (~85%). Enterprise grade requires authorization (RBAC + metadata filtering), persistent memory, workflow orchestration, and compliance controls. Don't confuse one for the other when setting stakeholder expectations. **How:** Use the enterprise readiness scorecard as a planning tool — it tells you exactly what's missing.

## ⚠️ Common Mistakes to Avoid

⚠️ **Calling a demo "production-ready"** — `PDF → Chroma → Chat` is a tutorial. Production means evaluated, observable, and maintainable. The distinction matters because demos fail at the first edge case; production systems handle them gracefully.

⚠️ **Skipping evaluation** — Without a golden dataset and measurable metrics, you have no way to know if a prompt change improved or degraded quality. "I tested 5 questions and they looked good" is not evaluation.

⚠️ **Vector-only search in enterprise contexts** — Enterprise data is full of exact-match requirements: incident IDs (P1, INC-1001), product codes (SKU-789), dates, and abbreviations. Pure vector search scores these poorly. Add BM25.

⚠️ **Post-retrieval access filtering** — Retrieving all documents and then telling the LLM "don't mention HR docs to this user" is not secure. The LLM has already seen the content. Filter before retrieval using metadata filters on the vector store.

⚠️ **Calling production-baseline "enterprise-grade"** — A system with API key auth is not enterprise-grade. Enterprise requires per-user authorization, RBAC, metadata filtering, audit trails, and compliance controls. Promising enterprise-grade without these creates security and compliance risk.

## 🔗 How It Connects to Other Concepts

- **Hybrid Search** (doc 14) — The recall layer of the production retrieval pattern; combines semantic + BM25 results (`EnsembleRetriever` is the built-in; RetailOps merges them by hand)
- **Cross-Encoder Reranking** (doc 15) — The precision layer; re-scores the merged candidates (`ContextualCompressionRetriever` is the built-in wrapper; RetailOps calls a cross-encoder directly)
- **Multi-Query Retrieval** (doc 16) — Generates alternative query phrasings to improve recall
- **History-Aware Retrieval** (doc 17) — Rewrites follow-up questions into standalone ones before retrieval
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
| **Production gotcha** | Hybrid + reranking first; evaluate before optimizing; distinguish production baseline (~85%) from enterprise grade (90%+) |

## ➡️ Next Steps

- **Example files:** `app/services.py`, `app/router.py`, `app/hybrid_retriever.py`, `app/reranker.py`, `app/multi_query.py` — the complete RetailOps production pipeline (`python -m app.main` to try it; needs `GROQ_API_KEY`)
- **Previous doc:** `../31_indexing_strategy/README.md`
- **Next doc:** `../33_langchain_limitations_and_langgraph/README.md` — where LangChain reaches its limits and when LangGraph becomes necessary
- **Official docs:** https://python.langchain.com/docs/tutorials/rag/
