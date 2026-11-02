# Common Mistakes (Consolidated)
> 43 mistakes engineers make when building LangChain, RAG, and production AI systems — and exactly what to do instead.

## 📌 What Is It?

This doc catalogs the most common implementation mistakes across every layer of an AI system: prompts, chunking, retrieval, agents, evaluation, observability, security, and architecture. Each mistake has a pattern (what the bad version looks like), the problem it causes, and the fix.

The core insight from building RetailOps:

```
Most AI system failures are not caused by the model.
They are caused by:

  Architecture  → wrong tool for the job (tools vs RAG, chain vs agent)
  Retrieval     → vector-only, no reranking, wrong chunk size
  Evaluation    → no golden dataset, no metrics, "looks good" testing
  Operations    → no observability, no versioning, no security
```

If your system gives wrong answers, check retrieval before blaming the LLM. If it gives inconsistent answers, check your evaluation setup. If it's slow or expensive, check your architecture. The model is rarely the root cause.

## ❓ Why Does It Exist?

Every mistake here has been made repeatedly across real production systems. Documenting them serves two purposes:
1. **Prevention** — knowing the pattern before you build lets you skip the debugging cycle
2. **Diagnosis** — when something goes wrong, this catalog tells you where to look first

The same 10 mistakes cause 80% of RAG failures in production. Learning them once saves weeks of debugging.

## ⏰ When Should You Use It?

✅ Before starting a new feature — check if its category appears here  
✅ When debugging a wrong answer — work through the debugging checklist at the end  
✅ During code review — use as a checklist for the layers being changed  
✅ When designing a new system — the architecture mistakes section prevents the most expensive decisions  

❌ Don't read this as a list of things to fear — most mistakes are easily fixed once identified  

## 🗂️ Types / Variants

| Category | Mistakes | Most Common |
|---|---|---|
| **Prompts** | #1–3 | Unstructured output, monolithic prompts |
| **Chunking** | #4–7 | Chunks too large or too small, no evaluation |
| **Embeddings** | #8–9 | Model/index mismatch |
| **Retrieval** | #10–13 | Vector-only, no reranking, blaming the LLM |
| **RAG** | #14–16 | No sources, out-of-context answers |
| **Multi-Query** | #17–18 | Too many queries, missing reranker |
| **Tools** | #19–21 | RAG for live data, huge tool functions |
| **Agents** | #22–24 | Agents for simple tasks, no iteration limit |
| **Routing** | #25–27 | No router, no routing evaluation |
| **Evaluation** | #28–31 | Manual testing only, no golden dataset |
| **Observability** | #32–35 | Print statements, no request IDs |
| **Security** | #36–38 | Auth without authz, post-retrieval filtering |
| **Memory** | #39–40 | Confusing memory and RAG, unlimited history |
| **Architecture** | #41–43 | Premature LangGraph, calling demo "enterprise" |

## 🔀 When to Use Which Type

If you're debugging a **wrong answer**: start with retrieval mistakes (#10–13), then RAG mistakes (#14–16), then evaluation mistakes (#28–31) to understand whether the system can even measure the problem.

If you're debugging **slow or expensive requests**: check architecture mistakes (#41–43) and agent mistakes (#22–24) first.

If you're doing **security review**: focus on #36–38 and the security best practices in doc 30.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Prevents the most common debugging cycles | Reading a mistake catalog doesn't substitute for experience |
| Debugging checklist focuses investigation on root cause | Some mistakes are context-dependent — "too large" depends on your documents |
| Architecture mistakes section prevents the most expensive errors | |

## 💻 Basic Example

```python
# The 5-question debugging checklist
# Before blaming the LLM, work through these in order.

def debug_wrong_answer(question: str, answer: str) -> None:
    """Systematic approach to diagnosing a wrong RAG answer."""

    # 1. Was the right route selected?
    from app.router import route_question
    decision = route_question(question)
    print(f"Route: {decision.route} (reason: {decision.reason})")
    # If route is wrong → fix the router prompt or test cases

    # 2. Was the right document retrieved?
    from app.vector_store import build_reranking_retriever
    from app.document_loader import load_all_documents
    retriever = build_reranking_retriever(...)
    docs = retriever.invoke(question)
    sources = [d.metadata.get("source") for d in docs]
    print(f"Retrieved sources: {sources}")
    # If wrong source → fix chunking, retrieval weights, or add hybrid search

    # 3. What context did the LLM receive?
    # Check LangSmith trace → open LLM node → read full prompt
    # If context is correct but answer is wrong → fix the RAG prompt

    # 4. Is the answer grounded?
    # Run the LLM judge from evals/ on this specific question
    # If ungrounded → tighten the system prompt ("use only provided context")

    # 5. Is the golden dataset up to date?
    # If this is a new document type, add an example to golden_dataset.json
    # Then re-run evals to establish a baseline


# Most RAG failures are caught at step 2 — wrong document retrieved.
# Most "model hallucination" complaints turn out to be retrieval failures.
```

## 🔧 Real-World Example

All 43 mistakes organized by category with fix patterns:

```python
# ══════════════════════════════════════════════════════════════════════════
# SECTION 1: PROMPT MISTAKES
# ══════════════════════════════════════════════════════════════════════════

# Mistake 1: Treating prompts as text, not code
# ─────────────────────────────────────────────
# Bad: prompt strings scattered across files, duplicated, inconsistent
# f"Answer this question: {question}"  # in api.py
# f"Using context, answer: {question}" # in services.py (different!)
#
# Good: centralized prompt management
# app/prompts.py contains all prompts as ChatPromptTemplate objects
# Every module imports from app/prompts.py — one source of truth

# Mistake 2: No output format specified
# ─────────────────────────────────────
# Bad: prompt says "answer the question" — LLM format varies per request
# Good: use structured output
#
# from pydantic import BaseModel
# class RAGResponse(BaseModel):
#     answer: str
#     sources: list[str]
#     confidence: str  # "high" | "medium" | "low"
#
# chain = prompt | llm.with_structured_output(RAGResponse)

# Mistake 3: One giant prompt for everything
# ──────────────────────────────────────────
# Bad: one system prompt handles RAG, tools, routing, security rules — 500 lines
# Good: separate focused prompts for each workflow
# RAG prompt: context + answer format
# Router prompt: classification only
# Rewriter prompt: expand question using history
# Smaller prompts are easier to test, version, and debug


# ══════════════════════════════════════════════════════════════════════════
# SECTION 2: CHUNKING MISTAKES
# ══════════════════════════════════════════════════════════════════════════

# Mistake 4: Chunks too large (2000+ tokens)
# ──────────────────────────────────────────
# Problem: retrieval returns an entire document section — most of it irrelevant
# Fix: start with chunk_size=500, chunk_overlap=50
# Evaluate source accuracy → tune from measured results, not intuition

# Mistake 5: Chunks too small (20–50 tokens)
# ──────────────────────────────────────────
# Problem: chunks contain no context — a sentence fragment like "The policy states"
# is meaningless alone
# Fix: minimum meaningful chunk is a complete sentence or paragraph (~100 tokens)

# Mistake 6: No overlap between chunks
# ─────────────────────────────────────
# Problem: sentences that cross chunk boundaries are split — meaning is lost
# Example: "Employees receive 15 vacation days. | Part-time employees receive..."
# The second chunk misses "Employees receive 15 vacation days."
# Fix: chunk_overlap=50 (10% of chunk_size) ensures boundary content appears in both chunks

# Mistake 7: Never evaluating chunk quality
# ─────────────────────────────────────────
# Problem: changing chunk_size from 500 to 1000 "feels better" but source accuracy drops
# Reality: chunk quality = retrieval quality = answer quality
# Fix: run test_retrieval_source_accuracy() after any chunking change
# If source accuracy drops, revert or investigate


# ══════════════════════════════════════════════════════════════════════════
# SECTION 3: EMBEDDING MISTAKES
# ══════════════════════════════════════════════════════════════════════════

# Mistake 8: Thinking embeddings store knowledge
# ───────────────────────────────────────────────
# Wrong: "I embedded my documents so the model knows the content"
# Correct: embeddings represent semantic relationships, not facts
# The model doesn't know anything until the chunk text is injected into the prompt
# Embeddings help FIND the right chunks; the chunk TEXT provides the knowledge

# Mistake 9: Changing embedding models without rebuilding the index
# ────────────────────────────────────────────────────────────────
# Problem: switching from all-MiniLM-L6-v2 to text-embedding-3-small with
# an existing index produces garbage retrieval results
# The stored vectors were computed with one model; queries use a different model
# They don't live in the same vector space
# Fix: any embedding model change requires a full index rebuild


# ══════════════════════════════════════════════════════════════════════════
# SECTION 4: RETRIEVAL MISTAKES
# ══════════════════════════════════════════════════════════════════════════

# Mistake 10: Using vector search only
# ─────────────────────────────────────
# Problem: "What does P1 mean?" retrieves well; "Show me P1 incidents" retrieves poorly
# because the exact string "P1" is a low-information token for embeddings
# Fix: EnsembleRetriever([semantic, bm25], weights=[0.6, 0.4])
# BM25 catches exact matches that semantic search misses

# Mistake 11: No reranking
# ────────────────────────
# Problem: retrieval returns 10 candidates ranked by embedding similarity
# The 3rd or 4th most similar may be the most relevant to the actual question
# Fix: wrap retriever in ContextualCompressionRetriever + CrossEncoderReranker
# Retrieve 20 → rerank → keep top 4. Typically +15–25% source accuracy.

# Mistake 12: Retrieving too many chunks (k=20+ in final context)
# ────────────────────────────────────────────────────────────────
# Problem: including 20 chunks in the LLM context fills the context window with noise
# The model struggles to identify the most relevant information
# Fix: retrieve 20 candidates for reranking, then pass top 4 to the LLM
# More candidates is fine for the reranker; fewer is better for the LLM

# Mistake 13: Blaming the LLM for retrieval failures
# ───────────────────────────────────────────────────
# Reality: most RAG wrong answers are retrieval failures, not generation failures
# "The LLM hallucinated" often means: the right document wasn't retrieved,
# so the LLM answered from model weights (which may be outdated/incorrect)
# Fix: always check retrieved sources before investigating the LLM
# In LangSmith: open trace → check retriever node sources


# ══════════════════════════════════════════════════════════════════════════
# SECTION 5: RAG CHAIN MISTAKES
# ══════════════════════════════════════════════════════════════════════════

# Mistake 14: No source attribution
# ──────────────────────────────────
# Problem: answers with no sources can't be verified, trusted, or debugged
# Fix: always return sources[] in RAGResponse
# class RAGResponse(BaseModel):
#     answer: str
#     sources: list[str]  # always include — even if empty
#     confidence: str

# Mistake 15: Allowing answers outside the provided context
# ──────────────────────────────────────────────────────────
# Bad system prompt: "Answer using the context, but use your knowledge if needed"
# Problem: "if needed" is interpreted as license to hallucinate
# Good system prompt: "Answer ONLY using the provided Context.
#                      If the answer is not in the Context, say you don't know."
# This forces grounded answers and catches retrieval failures as "I don't know"
# rather than confident wrong answers

# Mistake 16: No confidence score
# ────────────────────────────────
# Problem: users can't distinguish a well-supported answer from a guess
# Fix: include confidence: "high" | "medium" | "low" in structured output
# "high": multiple relevant sources agree
# "medium": one relevant source or partial match
# "low": no direct source, answer is inferred


# ══════════════════════════════════════════════════════════════════════════
# SECTION 6: MULTI-QUERY MISTAKES
# ══════════════════════════════════════════════════════════════════════════

# Mistake 17: Generating too many queries (5+)
# ─────────────────────────────────────────────
# Problem: 5 queries × 10 docs each = 50 candidates before reranking
# Latency and token cost multiply with each additional query
# Fix: 3 queries is usually sufficient for recall improvement
# MultiQueryRetriever default is 3 — don't increase without measuring the benefit

# Mistake 18: Using Multi-Query without reranking
# ───────────────────────────────────────────────
# Problem: multi-query produces many candidates; without reranking, you
# send all of them to the LLM — noisy context = worse answers
# Fix: multi-query improves recall; cross-encoder reranking improves precision
# Always pair them: MultiQueryRetriever → EnsembleRetriever → CrossEncoderReranker


# ══════════════════════════════════════════════════════════════════════════
# SECTION 7: TOOL MISTAKES
# ══════════════════════════════════════════════════════════════════════════

# Mistake 19: Using RAG for dynamic data (inventory, sales, incidents)
# ────────────────────────────────────────────────────────────────────
# Problem: "What's in stock?" indexed in Chroma answers based on yesterday's data
# Fix: live operational data belongs in tools, not the knowledge base
# @tool def get_low_stock_items(store_id: str) -> str:
#     return current_inventory_from_csv(store_id)

# Mistake 20: Using tools for static documentation
# ─────────────────────────────────────────────────
# Problem: return_policy_tool() that reads a static file on every call
# is slower, harder to maintain, and misses semantic search benefits
# Fix: static documents belong in the RAG knowledge base, not as tools
# RAG handles "what's the return policy?" better than a tool ever will

# Mistake 21: Tools with too many responsibilities
# ──────────────────────────────────────────────────
# Bad: get_store_data(store_id, type: "inventory"|"sales"|"incidents")
# Problem: ambiguous type → wrong tool behavior, hard to test, hard to debug
# Fix: single responsibility per tool
# get_low_stock_items(store_id) ← inventory only
# get_store_sales(store_id, period) ← sales only
# get_open_incidents(priority) ← incidents only


# ══════════════════════════════════════════════════════════════════════════
# SECTION 8: AGENT MISTAKES
# ══════════════════════════════════════════════════════════════════════════

# Mistake 22: Using agents for simple questions
# ─────────────────────────────────────────────
# Bad: AgentExecutor for "What is the return policy?" — adds 500ms+
# for ReAct reasoning when a simple RAG chain handles it in 200ms
# Fix: use the router. RAG questions → RAG chain. Tool questions → agent.
# Agents add value only when multiple tool calls are needed adaptively.

# Mistake 23: No tool docstrings
# ───────────────────────────────
# Problem: the LLM selects tools based on their name and docstring
# @tool def get_low_stock_items(store_id): pass  # no description
# The LLM can't know when to call it or what arguments to pass
# Fix: always include clear docstrings
# @tool
# def get_low_stock_items(store_id: str) -> str:
#     """Get items with low inventory for a specific store or 'all' stores.
#     Returns formatted list of items below reorder threshold."""

# Mistake 24: No iteration limit
# ───────────────────────────────
# Problem: a confused agent can loop: call tool A → inconclusive result →
# call tool A again → still inconclusive → call tool A again...
# Fix: AgentExecutor(max_iterations=3, handle_parsing_errors=True)
# Always set both — max_iterations prevents loops, handle_parsing_errors
# recovers from malformed tool call syntax


# ══════════════════════════════════════════════════════════════════════════
# SECTION 9: ROUTING MISTAKES
# ══════════════════════════════════════════════════════════════════════════

# Mistake 25: No router — everything goes to RAG
# ───────────────────────────────────────────────
# Problem: "Show me today's sales" → RAG → no relevant docs → "I don't know"
# Or worse: the LLM makes up sales figures from model knowledge
# Fix: router classifies questions before they reach any workflow
# general (chat) | rag (knowledge) | tools (live data)

# Mistake 26: Too many routes
# ────────────────────────────
# Problem: 8+ routes create ambiguity — too many boundaries, too many edge cases
# "Is this HR or policy or documentation or general?" — model confusion
# Fix: 3 routes is the production sweet spot: general / rag / tools
# Add more only if you have strong evaluation evidence for the distinction

# Mistake 27: No routing evaluation
# ───────────────────────────────────
# Problem: a prompt change accidentally misclassifies "P1 incidents" as rag → wrong workflow
# Fix: parametrized router tests (20+ cases) run on every code change
# pytest tests/test_router.py catches routing regressions in 30 seconds


# ══════════════════════════════════════════════════════════════════════════
# SECTION 10: EVALUATION MISTAKES
# ══════════════════════════════════════════════════════════════════════════

# Mistake 28: Manual testing only
# ────────────────────────────────
# Problem: "I tested 5 questions and they looked good"
# The 5 chosen questions cover the happy path; edge cases and regressions are invisible
# Fix: golden dataset with 20+ examples covering all routes and edge cases
# Run automatically after every significant change

# Mistake 29: No golden dataset
# ──────────────────────────────
# Problem: changing chunk size from 500 → 1000 "feels better"
# but source accuracy actually dropped from 85% to 70% — you don't know
# Fix: evals/golden_dataset.json — (question, expected_source, expected_answer)
# This is the single most valuable artifact in a production RAG system

# Mistake 30: Only measuring answer correctness
# ─────────────────────────────────────────────
# Problem: "answer correct: 80%" misses two important failure modes:
# - Retrieved wrong document but LLM produced plausible answer (source failure)
# - Retrieved right document but answer is incomplete (completeness failure)
# Fix: measure all three: source_accuracy, groundedness, completeness
# Each metric diagnoses a different layer of the pipeline

# Mistake 31: No evaluation reports or history
# ─────────────────────────────────────────────
# Problem: you ran an eval last month; you can't compare to today's results
# Fix: save timestamped JSON reports after every eval run
# evals/results/2026-06-08_eval.json
# Compare before/after for every system change


# ══════════════════════════════════════════════════════════════════════════
# SECTION 11: OBSERVABILITY MISTAKES
# ══════════════════════════════════════════════════════════════════════════

# Mistake 32: Using print() in production
# ────────────────────────────────────────
# print("Got answer:", answer)  # unstructured, unfilterable, no severity
# Fix: logger.info("answer_generated", extra={"extra_fields": {
#     "route": route, "sources": sources, "confidence": confidence
# }})
# Structured JSON logs are filterable, searchable, and aggregatable

# Mistake 33: No request IDs
# ──────────────────────────
# Problem: user reports "the assistant gave wrong answer at 2pm"
# Finding it in 10,000 log lines by timestamp is painful
# Fix: assign a UUID to each request; propagate it through all logs
# _request_id: ContextVar[str] = ContextVar("request_id", default="")
# Then grep logs for "req_abc123" to see the complete request lifecycle

# Mistake 34: Not logging retrieval results
# ──────────────────────────────────────────
# Problem: wrong answer reported → logs show "request_complete" but not what was retrieved
# You can't tell if it was a retrieval failure or a generation failure
# Fix: log_retrieval(question, docs, elapsed_ms) after every retriever.invoke()
# Log: sources[], scores[], num_docs, retrieval_ms
# Never log document content — only filenames and scores

# Mistake 35: Not enabling LangSmith
# ───────────────────────────────────
# Problem: when an answer is wrong, you don't know what prompt the LLM received,
# what documents were retrieved, or how long each stage took
# Fix: add 3 lines to .env:
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY=ls__...
# LANGCHAIN_PROJECT=RetailOps
# Cost: ~$0 for small scale. Benefit: full trace for every request from day one.


# ══════════════════════════════════════════════════════════════════════════
# SECTION 12: SECURITY MISTAKES
# ══════════════════════════════════════════════════════════════════════════

# Mistake 36: Authentication without authorization
# ─────────────────────────────────────────────────
# Problem: valid API key → access to everything including executive compensation data
# Authentication answers "who are you?" — it doesn't control what you can see
# Fix: add RBAC + metadata filtering at the retrieval layer
# filter={"access_level": {"$in": allowed_levels_for_this_user}}
# Pre-retrieval filtering prevents unauthorized content from reaching the LLM

# Mistake 37: Filtering after retrieval
# ──────────────────────────────────────
# Problem: retrieve all docs → instruct LLM "don't mention HR docs to this user"
# The LLM has already seen the content. It may still reference it indirectly.
# Fix: ALWAYS filter before retrieval, not after
# vectorstore.as_retriever(search_kwargs={"filter": {"access_level": {"$in": allowed}}})

# Mistake 38: Logging sensitive data
# ────────────────────────────────────
# Never log: passwords, API tokens, session tokens, full document content (may contain PII)
# Problem: document content often includes salary bands, SSNs, personal employee data
# These have weaker security controls in log aggregators than in the document store
# Fix: log source filenames and scores, never document text
# Scrub PII from question logs: scrub_pii(question[:80]) before logging


# ══════════════════════════════════════════════════════════════════════════
# SECTION 13: MEMORY MISTAKES
# ══════════════════════════════════════════════════════════════════════════

# Mistake 39: Confusing Memory and RAG
# ─────────────────────────────────────
# Memory = conversation context (what was said in this session)
# RAG = domain knowledge (what's in the knowledge base)
# Common error: "I'll add memory so the assistant remembers the return policy"
# That's wrong — policies belong in the RAG knowledge base, not memory
# Memory answers: "you asked about returns earlier, now asking about refunds"
# RAG answers: "the return policy states..."

# Mistake 40: Unlimited history
# ──────────────────────────────
# Problem: 50-turn conversation → context window fills with early irrelevant turns
# LLM costs increase; early context dilutes recent relevant context
# Fix: MAX_HISTORY_MESSAGES = 20 (10 turns)
# messages[-MAX_HISTORY_MESSAGES:] keeps the most recent context
# Alternative for long sessions: summarize old turns before windowing


# ══════════════════════════════════════════════════════════════════════════
# SECTION 14: ARCHITECTURE MISTAKES
# ══════════════════════════════════════════════════════════════════════════

# Mistake 41: Using LangGraph prematurely
# ────────────────────────────────────────
# Problem: adding LangGraph for a RAG system that's fine with chains
# LangGraph adds: state TypedDicts, graph compilation, checkpoint backends,
# conditional edge logic — all for zero benefit if you don't need HITL or persistence
# Fix: start with LangChain chains. Add LangGraph only when you need:
# human approval, persistent cross-session state, or multi-agent coordination

# Mistake 42: Building manual state management instead of using LangGraph
# ──────────────────────────────────────────────────────────────────────
# Problem: complex dict passed between chain steps, manually tracked progress flags,
# custom retry loops — all reinventing what LangGraph already provides
# Fix: if your workflow needs state, use LangGraph. It's designed for exactly this.

# Mistake 43: Calling a production baseline "enterprise-grade"
# ─────────────────────────────────────────────────────────────
# Production baseline (RetailOps, ~80%): hybrid search, evaluation, observability, API key auth
# Enterprise grade (90%+): per-user identity, RBAC, metadata filtering,
# persistent state, workflow orchestration, audit trails, compliance controls
# This distinction matters for stakeholder trust, security reviews, and compliance audits
# Fix: be precise — "production baseline with enterprise upgrade path planned"
```

## 🏭 Production Best Practices

1. **Check retrieval before blaming the LLM** — The single most impactful debugging habit. Open the LangSmith trace, click the retriever node, and read the source files. If the right source isn't there, the problem is retrieval — not the model. Most "hallucination" reports are retrieval failures in disguise. **How:** Log sources after every retriever call: `logger.info("retrieval", extra={"extra_fields": {"sources": [d.metadata["source"] for d in docs]}})`.

2. **Build a golden dataset before you build anything else** — The golden dataset (question, expected_source, expected_answer) is the single most valuable artifact in a production system. Without it, you can't measure quality, detect regressions, or prove that changes helped. Build it early — 20 examples is enough to start. **How:** `evals/golden_dataset.json` — add one example per document in your knowledge base, plus edge cases.

3. **Use hybrid search by default** — Vector-only search is never the right production choice for enterprise data. Product codes, incident IDs, abbreviations, and exact phrases all require BM25. The implementation cost is low (EnsembleRetriever, two lines) and the recall improvement is consistently significant. **How:** `EnsembleRetriever([semantic_retriever, bm25_retriever], weights=[0.6, 0.4])`.

4. **Enable LangSmith from day one** — It's three environment variables and zero code changes. By the time you have a production problem, you want months of trace history. If you enable it after the problem, you have nothing to look at. **How:** Add `LANGCHAIN_TRACING_V2=true`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT` to your `.env` file today.

5. **Run routing tests on every code change** — Routing errors cascade: a question routed to the wrong workflow gives a wrong answer regardless of how good your retrieval and generation are. 20 parametrized test cases catch routing regressions in 30 seconds. **How:** `pytest tests/test_router.py -v` as a pre-commit or CI step.

6. **Understand the three key realizations from RetailOps** — These change how you approach AI system debugging: (1) **Retrieval quality > prompt quality** — for RAG, better retrieval outperforms better prompts almost every time; (2) **Evaluation > opinion** — "I think it's better" without data is guessing; (3) **Enterprise problems ≠ RAG problems** — the gap between production and enterprise is security, workflow, and governance, not retrieval engineering.

## ⚠️ Common Mistakes to Avoid

⚠️ **Starting with architecture, not data** — Many teams spend weeks on agent frameworks, LangGraph, and multi-modal pipelines before establishing basic retrieval quality. Fix retrieval first; architecture is secondary.

⚠️ **"It looks good" as a quality bar** — This is the most dangerous phrase in AI development. Confident wrong answers look good until they cause a real problem. The only valid quality bar is a measured score against a golden dataset.

⚠️ **Fixing the wrong layer** — When the answer is wrong: most engineers first try to fix the prompt. But if retrieval returned the wrong document, no prompt change will fix the answer. Always diagnose the layer before applying a fix.

⚠️ **Skipping the upgrade path** — In-memory cache, in-memory sessions, and local Chroma are fine for development. Not planning the Redis/distributed DB/RBAC upgrade creates painful rewrites when you hit scale or a security review. Build the interface now; swap the implementation later.

## 🔗 How It Connects to Other Concepts

This doc is the negative-space complement to the entire series:
- Each mistake here points to a concept doc that explains the correct approach
- Prompt mistakes → docs 02–05 (prompts, LCEL, structured output)
- Retrieval mistakes → docs 07–15 (chunking through reranking)
- Evaluation mistakes → doc 19 (RAG evaluation)
- Observability mistakes → docs 26–27 (structured logging, LangSmith)
- Security mistakes → doc 30 (security)
- Architecture mistakes → docs 32–33 (production patterns, LangGraph)

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Catalog of 43 common mistakes across all AI system layers with patterns, problems, and fixes |
| **Why** | Most failures come from architecture, retrieval, and evaluation decisions — not the model |
| **When** | Before building (prevention); when debugging (diagnosis); during code review (checklist) |
| **Types** | Prompts, chunking, retrieval, RAG, agents, routing, evaluation, observability, security, architecture |
| **Production gotcha** | Check retrieval first; measure everything; retrieval quality > prompt quality for RAG |

## ➡️ Next Steps

- **Debugging checklist:** Route → Retrieve → Context → Generate → Evaluate — work through this order before any other investigation
- **Next doc:** `37_enterprise_readiness_checklist.md` — a scannable scorecard covering the same production-vs-enterprise distinction as a checklist you can run before any stakeholder review
- **Official docs:** https://python.langchain.com/docs/ | https://langchain-ai.github.io/langgraph/ | https://owasp.org/www-project-top-10-for-large-language-model-applications/
