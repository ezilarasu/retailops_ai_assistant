# Enterprise RAG Readiness Checklist
> One consolidated scorecard for judging whether a RAG system is a tutorial, a production baseline, or enterprise-grade.

## 📌 What Is It?

A maturity checklist with three tiers — **RAG Foundation → Production Baseline → Enterprise Grade** — used to score a RAG application layer by layer (LLM, retrieval, API, observability, evaluation, security, workflow, compliance). Think of it like a building inspection checklist: individual rooms (retrieval quality, logging, auth) can each look fine, but the checklist tells you the overall grade of the building.

## ❓ Why Does It Exist?

Doc 32 (Production RAG Patterns) and doc 34 (Project Architecture) already narrate *why* each production pattern matters and *how* RetailOps implements it. This doc exists for a different purpose: a fast, scannable checkbox list to run through before a demo, a stakeholder review, or a "are we enterprise-ready?" conversation — without re-reading the full narrative docs.

## ⏰ When Should You Use It?

✅ Before telling a stakeholder a system is "production-ready" or "enterprise-grade" — verify against the checklist first
✅ When planning the next quarter of work on a RAG system — the unchecked items are your roadmap
✅ When comparing two RAG systems' maturity objectively
✅ When onboarding a new engineer — this doc shows what "done" looks like at each tier

❌ Don't use this as a substitute for the detailed reasoning in docs 32/34 — it tells you *what's* missing, not *why* or *how* to add it
❌ Don't treat 100% Enterprise Grade as a requirement for every project — most internal tools only need Production Baseline

## 🗂️ Types / Variants

| Tier | Focus | Typical Score |
|---|---|---|
| **RAG Foundation** | LLM integration, basic RAG, source attribution | 20–30% |
| **Production Baseline** | Retrieval quality, API layer, observability, evaluation, caching | 70–85% |
| **Enterprise Grade** | Identity, authorization, audit, persistent state, workflow orchestration, compliance | 90%+ |

## 🔀 When to Use Which Type

Score your own system tier by tier, top to bottom. Most teams over-invest in retrieval quality (chunking, embeddings, reranking) and under-invest in the layers that actually gate enterprise deployment: **security, authorization, workflow orchestration, and governance**. If you're deciding what to build next, the biggest maturity jump usually comes from the Enterprise Grade section, not from further retrieval tuning.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Fast way to communicate maturity to non-engineers | A checkbox says nothing about *quality* of implementation |
| Forces explicit acknowledgment of gaps instead of vague confidence | Checklists age — revisit periodically as the system evolves |
| Good roadmap-prioritization tool | Doesn't replace real evaluation (doc 19) or security review (doc 30) |

## 💻 Basic Example

Scoring is simple: go tier by tier and tick an item **only if you can point to the code, config, or test that proves it**. No evidence, no tick. A tier's score is ticked items divided by total items.

```text
Item                         Evidence you can point to       Tick?
Hybrid search                app/hybrid_retriever.py         [x]
Cross-encoder reranking      app/reranker.py                 [x]
Role-based access control    (nothing in the repo)           [ ]

Tier score = ticked / total
```

You can also let a script count the boxes in this file. Run it from the repository root; it prints the score for each of the three checklists below.

```python
import re
from pathlib import Path

# Read this doc and split it at the three "### Checklist — Level N" headings
text = Path("docs/37_enterprise_readiness_checklist/README.md").read_text(encoding="utf-8")
parts = re.split(r"^### Checklist — (Level \d)", text, flags=re.M)

# parts = [intro, "Level 1", body, "Level 2", body, "Level 3", body]
for level, body in zip(parts[1::2], parts[2::2]):
    body = body.split("\n## ")[0]                       # stop at the next top-level section
    done = len(re.findall(r"^- \[x\]", body, flags=re.M))   # ticked boxes
    todo = len(re.findall(r"^- \[ \]", body, flags=re.M))   # empty boxes
    print(f"{level}: {done}/{done + todo} = {done / (done + todo):.0%}")
```

Start with Level 1 below, which a working RAG demo should already pass.

### Checklist — Level 1: RAG Foundation

**LLM Layer**
- [x] LLM integration
- [x] Prompt templates
- [x] Structured output
- [x] Configuration management (env vars, no hardcoded values)

**Knowledge Layer**
- [x] Document loaders
- [x] Chunking
- [x] Embeddings
- [x] Vector database
- [x] Retriever

**Basic RAG**
- [x] RAG prompt (context-only, grounded)
- [x] Source attribution
- [x] Retrieval testing

## 🔧 Real-World Example

Here is the checklist applied to RetailOps, tier by tier, with the evidence (or lack of it) from the actual code:

| Area | Result | Evidence / caveat |
|---|---|---|
| Foundation (Level 1) | All ticked | `app/llm.py`, `app/prompts.py`, `app/schemas.py`, `app/rag.py`, `app/vectorstore.py`, `tests/test_rag.py` |
| Retrieval quality | Strong | `app/hybrid_retriever.py`, `app/reranker.py`, `app/multi_query.py`, `/debug/retrieval` in `app/api.py`; the reranker and the multi-query chain are each built once and reused; one cut-off (`RERANK_MIN_SCORE`) keeps clearly irrelevant chunks out of the prompt |
| API layer | Mostly | FastAPI + Pydantic schemas; typed errors in `app/exceptions.py`, one retry for transient model failures (`invoke_with_retry()` in `app/llm.py`), and `/chat` maps the error code to an HTTP status (422 refusal, 429 rate limit, 503 model gone, 502 provider failure, 500 other) |
| Observability | Partial | Plain-text logs with a `request_id`, LangSmith tags/metadata (`app/tracing.py`), per-stage timings; no JSON logs |
| Evaluation | Partial | Runner, judge, reports and comparison all exist; the question set is a 5-question demo |
| Performance | Partial | Cache and health check exist; the cache is in-memory and per process, serves only first-turn `general`/`rag` answers (never `tools`, never follow-ups) and is cleared on index rebuild |
| Conversation state and index | Mostly | Chat history per `session_id` (in-process only); the index records a fingerprint and rebuilds when it changes, and `/index/rebuild` refreshes the running app without a restart |
| Security | Minimal | API key only (`app/security.py`), compared in constant time, with the placeholder key refused outside `APP_ENV=local` |
| Enterprise (Level 3) | Not started | Workflow approval exists only as a LangGraph demo in `app/graph/` that is not wired into the API |

Level 2 below scores 24 of 28 items (86%) by this method, which is where the "roughly 85%" figure in docs 32 and 36 comes from. (It was 21 of 25, 84%, before the cache, session, index, error-handling and API-key fixes; the percentage moved little because those fixes also added items to the list.) Treat it as a rough self-assessment of a **production baseline**, not a measured quality number and not an enterprise-grade rating.

### Checklist — Level 2: Production Baseline

**Retrieval Quality**
- [x] Semantic chunking
- [x] Hybrid search (vector + BM25)
- [x] Cross-encoder reranking
- [x] Multi-query retrieval
- [x] Retrieval debug mode (`/debug/retrieval`)
- [ ] Contextual compression *(evaluated, not enabled by default — see doc 13; current corpus is small enough that hybrid + reranking already keeps context tight)*

**API Layer**
- [x] FastAPI
- [x] Request/response schemas
- [x] Error handling (typed `RetailOpsError` subclasses with a user-safe message and HTTP status; one retry on transient model failures; a generic catch-all as the last resort)
- [ ] API documentation (FastAPI serves an OpenAPI page at `/docs`, and the root README and doc 25 describe the endpoints and the error codes, but there is no published, versioned API reference)

**Observability**
- [x] Logging with a per-request ID (plain-text `key=value` lines)
- [ ] Structured (JSON) logging
- [x] LangSmith tracing
- [x] Latency tracking per stage
- [x] Retrieval debug logs

**Evaluation**
- [x] Golden dataset (`evals/rag_questions.jsonl`, a 5-question demo set)
- [x] Evaluation runner (`evals/run_rag_eval.py`)
- [x] Evaluation reports
- [x] Report comparison (`evals/compare_reports.py`)
- [x] LLM-as-judge (`evals/judge.py`)

**Performance**
- [x] Startup initialization (chains built once and reused via `get_container()`; the CLI builds them at start-up, the API on the first request)
- [x] Response caching (in-memory TTL cache; only first-turn `general`/`rag` answers, never `tools` answers or follow-ups; cleared by `/index/rebuild`)
- [x] Health check endpoint
- [ ] Distributed/shared cache (Redis) — in-memory only, doesn't scale across workers

**Conversation State and Index**
- [x] Per-session chat history (`session_id`; in-process memory only, see the persistent-memory item in Level 3)
- [x] Versioned index (manifest fingerprint, automatic rebuild when it changes, in-place rebuild via `/index/rebuild`)

**Security**
- [x] API key protection (constant-time comparison; a missing key is rejected)
- [x] Default-key guard (startup refuses the placeholder `APP_API_KEY` unless `APP_ENV=local`)

Anything beyond API-key protection (OAuth, RBAC, metadata filtering, injection defense, PII scrubbing) belongs to Level 3 below and is not in the repo.

## 🏭 Production Best Practices

1. **Score with evidence, not feelings** — "It feels production-ready" is not a checkbox. **How:** for every ticked item, be able to name the file, config value, or test that proves it, as in the table above.
2. **Re-score after every major change** — Checklists age. **How:** re-run the counting script in the Basic Example after a release and look at which items moved.
3. **Fix the biggest gap for your real deployment first** — A single-user internal tool may never need SSO; a customer-facing product needs authorization before a fancier reranker. **How:** pick items from Level 3 that match your actual requirements, not from the top of the list.
4. **Report the tier honestly to stakeholders** — Say "production baseline with a documented enterprise upgrade path," not "enterprise-grade." **How:** quote the Level 2 score and list the unticked Level 3 items next to it.
5. **Pair the checklist with real evaluation and review** — A tick says a feature exists, not that it works well. **How:** back the evaluation items with a larger question set (doc 19) and the security items with a proper review (doc 30).

### Checklist — Level 3: Enterprise Grade *(not yet implemented — the actual roadmap)*

**Identity & Authentication**
- [ ] OAuth2 / OpenID Connect / SSO (Azure AD, Okta, SAML)

**Authorization**
- [ ] Role-based access control (RBAC)
- [ ] Attribute-based access control (ABAC)
- [ ] Metadata filtering at retrieval time (`filter={"department": ..., "role": ...}`)
- [ ] Document classification (Public / Internal / Confidential / Restricted)

**Audit & Compliance**
- [ ] Immutable audit trail (user, query, retrieved docs, generated answer)
- [ ] GDPR / SOC2 / HIPAA controls as applicable
- [ ] Data retention & legal hold support

**Persistence & Workflow**
- [ ] Persistent memory (Redis / Postgres / LangGraph checkpoints) — chat history is per session but in-process only, unbounded and lost on restart
- [ ] Incremental indexing (only re-embed changed documents) — currently full rebuild
- [ ] Human-in-the-loop approval workflows (refund escalation, vendor onboarding, HR actions) — a working LangGraph `interrupt()` demo exists in `app/graph/` (examples 23-28) but is not wired into the CLI or API
- [ ] LangGraph-based state orchestration with retry/timeout/failure recovery (see doc 33)

**Scale & Reliability**
- [ ] Horizontal scaling, load balancing, distributed vector DB
- [ ] Circuit breakers, fallback models, graceful degradation — a single retry and friendly error messages exist, but no circuit breaker and no fallback model
- [ ] Metrics dashboard, alerting, cost/latency monitoring

**Integrations & Multi-Tenancy**
- [ ] Enterprise data connectors (Confluence, SharePoint, Google Drive, Jira, ServiceNow)
- [ ] Multi-agent orchestration (planner/researcher/reviewer agents)
- [ ] Tenant isolation (per-tenant indexes, permissions, evaluation)

## ⚠️ Common Mistakes to Avoid

⚠️ **Calling "Production Baseline" complete work "Enterprise Grade."** API-key auth and good retrieval are not the same as RBAC, audit trails, and workflow orchestration. Conflating the two sets the wrong expectations with stakeholders.

⚠️ **Treating this checklist as a to-do list to clear in order.** Prioritize based on actual deployment requirements — a single-user internal tool may never need multi-tenancy or SSO; a customer-facing enterprise product needs authorization before it needs a fancier reranker.

⚠️ **Skipping the checklist entirely and self-reporting maturity.** "It feels production-ready" is not a checklist. Score it explicitly, item by item.

## 🔗 How It Connects to Other Concepts

- **Production RAG Patterns** (doc 32) — the narrative version of this checklist, explaining *why* and *how* for each pattern
- **Project Architecture** (doc 34) — maps each checklist item to the actual RetailOps file that implements it
- **Security** (doc 30) — the authentication/authorization items in Level 3 are detailed here
- **LangChain Limitations & LangGraph** (doc 33) — the workflow orchestration and persistent-state gap is exactly what LangGraph closes

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Three-tier maturity checklist (Foundation → Production Baseline → Enterprise Grade) for RAG systems |
| **Why** | Fast, explicit way to score and communicate system maturity instead of relying on vague confidence |
| **When** | Before claiming "production-ready"/"enterprise-grade," or when prioritizing the next quarter of work |
| **Types** | Foundation (LLM + basic RAG), Production Baseline (retrieval quality + ops), Enterprise Grade (identity, workflow, compliance) |
| **RetailOps current score** | Production Baseline: roughly 85% complete (24 of 28 items, a self-assessed estimate; the counting script above gives the exact tick ratio). Enterprise Grade: not yet started (0 of 18). The gap is enterprise architecture (auth, workflow, compliance), not RAG engineering. |

## ➡️ Next Steps

- **Reference:** re-run this checklist after any major change to see what moved
- **Previous doc:** `../36_common_mistakes/README.md`
- **Next doc:** none — this is the final reference doc; return to `docs/README.md` for the full learning path
- **Official docs:** https://owasp.org/www-project-top-10-for-large-language-model-applications/ | https://langchain-ai.github.io/langgraph/
