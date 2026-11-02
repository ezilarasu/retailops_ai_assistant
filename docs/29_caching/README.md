# Caching
> Answering the same question 1,000 times for the cost of answering it once.

## 📌 What Is It?

**Caching** stores previously computed results so that identical (or near-identical) requests can be served instantly from the cache instead of re-running the full pipeline. In an AI system, the expensive steps are LLM calls, embedding generation, and cross-encoder reranking — caching these turns thousands of identical requests into a single computation.

The cache flow:

```
Without cache:
  "What does P1 mean?" → retrieval → reranking → LLM → answer (2s, $0.002)
  "What does P1 mean?" → retrieval → reranking → LLM → answer (2s, $0.002)
  "What does P1 mean?" → ... × 1000 = $2.00 and 2000 seconds

With cache:
  "What does P1 mean?" → cache miss → retrieval → LLM → store → answer (2s)
  "What does P1 mean?" → cache hit → answer instantly (1ms, $0.000)
  "What does P1 mean?" → cache hit → answer instantly × 999 = ~$0.002 total
```

Three types of caching are relevant for LangChain applications:
- **Response cache** — cache the final answer for a question
- **LLM call cache** — cache individual LLM responses for identical prompts (LangChain built-in)
- **Embedding cache** — cache computed embedding vectors for repeated text

## ❓ Why Does It Exist?

Enterprise retail assistants see the same questions repeatedly. "What does P1 mean?", "What is the return policy?", and "How many vacation days?" are asked by dozens of employees every day. Without caching, every one of those questions runs the full pipeline — retrieval, reranking, LLM generation — even though the answer hasn't changed.

Two costs compound:
1. **API cost** — every LLM call costs tokens; 1,000 identical calls cost 1,000× as much as one cached result
2. **Latency** — users wait 1–3 seconds per request; a cache hit serves in <5ms

Caching is one of the highest-ROI production optimizations available because it targets the most expensive operations with the cheapest possible solution.

**Important: don't cache live operational data.** Inventory levels, sales figures, and incident status change constantly. Caching the answer to "Which items are low in stock?" for 5 minutes means users see stale data. Tools route questions get their answers from operational data that changes (in a real deployment, live systems; in this learning repo, the CSV/JSON files in `data/`) — don't cache them.

## ⏰ When Should You Use It?

✅ Static knowledge questions routed to RAG — the answer doesn't change until documents are updated  
✅ High-volume assistants with many repeated questions  
✅ When LLM API costs are a concern  
✅ When p99 latency matters to users  

❌ Don't cache answers from the `tools` route — inventory, sales, and incidents change constantly  
❌ Don't cache without TTL — stale answers are worse than no answers  
❌ Don't cache before your system is stable — caching a bad answer amplifies the bug  
❌ Don't use in-memory caching for multi-process deployments — use Redis  

## 🗂️ Types / Variants

| Type | What Gets Cached | TTL Guidance | Best For |
|---|---|---|---|
| **Response cache** | Final answer for a question | 5–60 minutes | RAG questions; policy Q&A |
| **LLM call cache** | LLM output for identical prompt+model | Indefinite (content-addressed) | Development; reducing API costs |
| **Embedding cache** | Embedding vectors for text strings | Days to weeks | High-volume query embedding |
| **Retrieval cache** | Retrieved document list for a query | 5–30 minutes | Expensive hybrid+reranking pipelines |
| **Redis cache** | Any of the above, persisted and shared | Configurable | Production multi-instance deployments |

**What RetailOps has:** only the response cache (`SimpleTTLCache` in `app/cache.py`). It does not use LangChain's LLM cache, an embedding cache, a retrieval cache or Redis — those are the upgrade paths in this doc.

## 🔀 When to Use Which Type

**Start with response caching** — it's the simplest and highest-impact. Cache the final answer keyed by question hash. One TTL parameter controls freshness.

**Use LangChain's built-in LLM cache** for development to avoid re-paying for identical LLM calls during testing and iteration. `set_llm_cache(InMemoryCache())` requires one line.

**Upgrade to Redis** when you run more than one instance of your application. An in-memory cache on process A doesn't help requests hitting process B.

**Never cache tool results** — the entire point of tools is to return live data.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Dramatic cost reduction for repeated questions | Stale data risk if TTL is too long |
| Near-zero latency for cache hits | Cache invalidation is hard when documents change |
| Seamless to add — 10–20 lines of code | In-memory cache lost on restart |
| High ROI on static knowledge questions | Caching wrong answers amplifies bugs |
| Redis cache scales across multiple processes | Redis adds infrastructure complexity |

## 💻 Basic Example

```python
import os
import hashlib
import time
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.caches import InMemoryCache
from langchain_core.globals import set_llm_cache

load_dotenv()

# ── LangChain built-in LLM cache ─────────────────────────────────────────
# One line to cache all identical LLM calls.
# Useful during development to avoid paying for repeated identical prompts.
set_llm_cache(InMemoryCache())

llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)

# First call: goes to LLM API
result1 = llm.invoke("What does P1 mean in retail operations?")

# Second identical call: served from cache instantly, no API call
result2 = llm.invoke("What does P1 mean in retail operations?")

# Both produce the same result; second is instant
print(result1.content == result2.content)  # True


# ── Simple TTL response cache ─────────────────────────────────────────────
class SimpleTTLCache:
    """TTL-based cache for RAG responses.

    Stores (answer, sources, confidence) keyed by question hash.
    Entries expire after `ttl_seconds`.
    Thread-safe for single-process use.
    """

    def __init__(self, ttl_seconds: int = 300):  # 5 minutes default
        self._store: dict[str, tuple[dict, float]] = {}  # key → (value, expiry)
        self.ttl_seconds = ttl_seconds
        self.hits = 0
        self.misses = 0

    def _key(self, question: str) -> str:
        """Normalize and hash the question to produce a cache key."""
        normalized = question.strip().lower()
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def get(self, question: str) -> dict | None:
        """Return cached result or None if cache miss / expired."""
        key = self._key(question)
        entry = self._store.get(key)
        if entry is None:
            self.misses += 1
            return None
        value, expiry = entry
        if time.time() > expiry:
            del self._store[key]    # remove expired entry
            self.misses += 1
            return None
        self.hits += 1
        return value

    def set(self, question: str, result: dict) -> None:
        """Store a result with TTL expiry."""
        key = self._key(question)
        self._store[key] = (result, time.time() + self.ttl_seconds)

    @property
    def hit_rate(self) -> float:
        """Cache hit rate as a fraction 0.0–1.0."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


# Usage:
cache = SimpleTTLCache(ttl_seconds=300)

def ask_with_cache(question: str, rag_chain) -> dict:
    """Check cache first; call RAG chain only on cache miss."""
    cached = cache.get(question)
    if cached:
        return {**cached, "cache_hit": True}

    result = rag_chain.invoke({"question": question, "history": []})
    answer_dict = {
        "answer": result.answer,
        "sources": result.sources,
        "confidence": result.confidence,
    }
    cache.set(question, answer_dict)
    return {**answer_dict, "cache_hit": False}
```

## 🔧 Real-World Example

RetailOps' actual cache module (`app/cache.py`) — a simple in-memory TTL cache, exposed as a module-level singleton. The cache class itself knows nothing about routes or conversations; the service layer (`app/services.py`) decides *what* may be cached. Those rules were tightened after the first version cached too much (tool answers, follow-ups), so this section describes the current, safer behavior.

Current behavior in one place (all of this is from `app/cache.py` and `app/services.py`):
- The cache key is the SHA-256 of the question text, lower-cased and stripped. It does not include the route or `DOCUMENT_VERSION`.
- **Only the first question of a conversation is looked up or stored.** If the session already has history, the cache is skipped entirely, because the same words mean different things in context ("What about part-timers?" after a vacation question is not the same as after a returns question). Follow-ups are always answered in context. This also means a repeat of a question *within one conversation* is not a hit; the cache serves the FAQ pattern, where many people ask the same standalone question as their first question.
- **Only `general` and `rag` answers are stored** (`CACHEABLE_ROUTES = {"general", "rag"}`). `tools` answers come from live operational data, so they are never cached, and neither are errors.
- Entries live 300 seconds and are held in a plain `dict` inside one process (lost on restart, not shared between workers). Expired entries are removed only when they are looked up again.
- A cache hit returns before `run_router()` runs, but the service still records the user and AI messages in that session's memory, so the conversation stays whole. The hit gets its own `request_id` and its own `latency_ms` (a fraction of a millisecond), with `cache_hit` set to `True`.
- `POST /index/rebuild` calls `response_cache.clear()`, so answers built from the old documents are dropped immediately.
- Cache hits are not logged; the signals are the `cache_hit` field in the response, `(served from cache)` in the CLI, and `cache_size` on `/health`.

> **Lesson from this project:** the payoff is large and easy to measure. In a live run, `What does P1 mean?` took about 2,000 ms the first time (router, multi-query, rerank, answer) and 0.35 ms when a second session asked it. The harder part was deciding *what* may be cached: the first version cached every successful route for 5 minutes (stale stock levels) and ignored conversation context (a follow-up could be served another conversation's answer). The rules above are the fixes.

```python
import hashlib
import time


# ══════════════════════════════════════════════════════════════════════════
# app/cache.py — RetailOps response cache (actual implementation)
#
# A plain in-memory, TTL-based cache. It knows nothing about routes, sessions
# or document versions: app/services.py decides what may be cached, and
# POST /index/rebuild calls clear(). No Redis — that is an upgrade path below.
# ══════════════════════════════════════════════════════════════════════════

class SimpleTTLCache:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self.store: dict[str, tuple[float, dict]] = {}

    def _key(self, text: str) -> str:
        normalized = text.strip().lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def get(self, text: str) -> dict | None:
        key = self._key(text)

        if key not in self.store:
            return None

        created_at, value = self.store[key]

        if time.time() - created_at > self.ttl_seconds:
            del self.store[key]
            return None

        return value

    def set(self, text: str, value: dict) -> None:
        key = self._key(text)
        self.store[key] = (time.time(), value)

    def size(self) -> int:
        return len(self.store)

    def clear(self) -> None:
        self.store.clear()


# Module-level singleton — every part of the app shares this one cache.
response_cache = SimpleTTLCache(ttl_seconds=300)


# ── Usage in app/services.py (actual code) ────────────────────────────────
# import time
# import uuid
#
# from app.cache import response_cache
# from app.memory import DEFAULT_SESSION, add_ai_message, add_user_message, get_messages
# from app.router import run_router
#
# # Tool answers come from live operational data, so they are never cached.
# CACHEABLE_ROUTES = {"general", "rag"}
#
#
# class RetailOpsAssistantService:
#     def ask(self, question: str, session_id: str = DEFAULT_SESSION) -> dict:
#         start_time = time.perf_counter()
#
#         # Only the first question of a conversation is cached or served from
#         # the cache. With earlier turns the same words can mean something else.
#         first_turn = not get_messages(session_id)
#
#         cached = response_cache.get(question) if first_turn else None
#
#         if cached:
#             result = dict(cached)
#             result["cache_hit"] = True
#             result["request_id"] = str(uuid.uuid4())
#             result["latency_ms"] = round((time.perf_counter() - start_time) * 1000, 2)
#
#             # A hit skips run_router(), so record the turn here.
#             add_user_message(question, session_id)
#             add_ai_message(result["answer"], session_id)
#
#             return result
#
#         result = run_router(question, session_id)
#         result["cache_hit"] = False
#
#         if first_turn and result["route"] in CACHEABLE_ROUTES:
#             response_cache.set(question, result)
#
#         return result
#
#
# assistant_service = RetailOpsAssistantService()


# ── Enterprise upgrade path: a shared cache (Redis) ───────────────────────
# Not implemented. Swap the in-memory dict for Redis so the cache is shared
# across processes and survives restarts. With a shared cache you should also
# put DOCUMENT_VERSION in the key, because one process's clear() no longer
# empties the others:
#
# def _make_key(self, question: str) -> str:
#     payload = f"{question.strip().lower()}|{DOCUMENT_VERSION}"
#     return hashlib.sha256(payload.encode()).hexdigest()[:20]
#
# import redis
# r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
# r.setex(key, ttl_seconds, json.dumps(result))  # TTL handled by Redis
```

## 🏭 Production Best Practices

1. **Make caching route-aware (done)** — The tools route queries inventory, vendor, and incident data that changes over time, so stale answers are wrong answers. **How:** `app/services.py` only calls `response_cache.set()` when `result["route"] in CACHEABLE_ROUTES`, and that set is `{"general", "rag"}`, so `tools` answers and errors are never stored. (An earlier version cached every non-error route for 5 minutes, including tool answers.)

2. **Invalidate the cache when documents change (partly done)** — `SimpleTTLCache._key()` hashes only the normalized question text, not `DOCUMENT_VERSION`. RetailOps covers the common case differently: `POST /index/rebuild` calls `response_cache.clear()`, and a restarted process starts with an empty cache, so old answers do not outlive a rebuild in a single process. **Remaining gap:** with several processes or a shared Redis cache, one process's `clear()` does not reach the others, so put the version in the key there: `payload = f"{question.strip().lower()}|{DOCUMENT_VERSION}"` before hashing.

3. **Set a TTL — never cache indefinitely** — Policies change. HR documents get updated. An answer that was correct last month may be wrong today. RetailOps already does this: `response_cache = SimpleTTLCache(ttl_seconds=300)` gives a 5-minute TTL out of the box. **How:** `SimpleTTLCache(ttl_seconds=300)`.

4. **Track cache size/hit rate as a metric** — Knowing how much the cache is actually helping matters. RetailOps' `SimpleTTLCache` currently only exposes `size()` (number of entries) — there's no built-in hit/miss counter. **Recommended fix:** add `hits`/`misses` counters to `SimpleTTLCache` and log them periodically.

5. **Replace in-memory cache with Redis for production (not implemented)** — `SimpleTTLCache` stores everything in a plain `dict` in process memory — it's lost on every restart and isn't shared across multiple instances of the app. **Recommended fix:** swap the `dict` store for Redis with `r.setex(key, ttl_seconds, json.dumps(value))`.

6. **Normalize question text before hashing** — "What is P1?" and "what is p1?" should hit the same cache entry. RetailOps already does this in `SimpleTTLCache._key()`: `normalized = text.strip().lower()` before `hashlib.sha256(...)`.

7. **Don't cache context-dependent answers (done)** — A follow-up question only makes sense with the conversation before it. **How:** `RetailOpsAssistantService.ask()` only uses the cache when the session has no history yet (`first_turn = not get_messages(session_id)`), so follow-ups are always answered in context and never stored for other people. The trade-off is that a question repeated later in the *same* conversation is not a hit; putting the history in the key instead would have the same effect, because the history changes after every turn. This needed per-session memory (doc 24) to be meaningful: each session id starts empty.

## ⚠️ Common Mistakes to Avoid

⚠️ **Caching tools route responses** — Inventory levels, sales data, and incident status change constantly. RetailOps made exactly this mistake at first (every non-error route was cached for 5 minutes) and now restricts caching to `general` and `rag` — see Production Best Practice #1 above.

⚠️ **No TTL** — A cache without expiry is a stale data time bomb. Policy documents get updated; without TTL, users may receive last month's vacation policy indefinitely. RetailOps avoids this today via `SimpleTTLCache(ttl_seconds=300)`.

⚠️ **Not invalidating on document updates** — Rebuilding the vector store without invalidating the response cache means the new document content is retrieved but the cache still returns old answers for up to `ttl_seconds`. RetailOps clears the cache in `POST /index/rebuild` (`SimpleTTLCache.clear()`), but there is still no document-version-aware key, which matters once the cache is shared between processes — see Production Best Practice #2.

⚠️ **Using in-memory cache across multiple processes** — When you run 3 instances of your application behind a load balancer, each has its own in-memory cache (this is exactly how RetailOps' `SimpleTTLCache` singleton behaves today). Requests for the same question hit different instances and result in cache misses most of the time. Use Redis for any multi-instance deployment.

⚠️ **Confusing cache with memory** — Cache stores *computed results* for performance optimization. Memory stores *conversation history* for context. A cached answer doesn't know about the current session; memory does. Different purposes, different implementations.

## 🔗 How It Connects to Other Concepts

- **Router Pattern** (doc 23) — The route determines whether caching applies: `rag`/`general` are cacheable, `tools` never (`CACHEABLE_ROUTES` in `app/services.py`)
- **RAG Chains** (doc 18) — RAG answers are the primary cache target — they're expensive (retrieval + reranking + LLM) and stable (documents change slowly)
- **Tools & Function Calling** (doc 20) — Tools return live data, so their answers are never cached
- **FastAPI Integration** (doc 25) — `app/services.py`'s `RetailOpsAssistantService.ask()` checks `response_cache` before invoking the router; `POST /index/rebuild` clears it
- **Observability** (doc 26) — Log `cache_hit=True/False` on every request and track cache size as a production metric. RetailOps returns `cache_hit` in the response, prints `(served from cache)` in the CLI and reports `cache_size` on `/health`, but does not write a log line for cache hits yet
- **Memory** (doc 24) — The cache is only used on the first turn of a session; a cache hit skips `run_router()`, so the service records the user and AI messages itself to keep the session's history complete

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Storing computed pipeline results by question hash, served instantly on cache hit |
| **Why** | Repeated identical questions cost as much as unique ones without caching; TTL cache serves them at <5ms with no LLM cost |
| **When** | First-turn questions on the RAG and general routes; never for the tools route (live data) or for follow-ups |
| **Types** | Response cache (what RetailOps has — `SimpleTTLCache`), LLM call cache (built-in), embedding cache, Redis (production) |
| **Production gotcha** | Decide *what* may be cached, not just how: RetailOps caches only first-turn `general`/`rag` answers and clears the cache on index rebuild. Still in-memory and per process, and the key has no document version (needed once the cache is shared) |

## ➡️ Next Steps

- **Example file:** `app/cache.py` — RetailOps `SimpleTTLCache` and the `response_cache` singleton; `app/services.py` — where it is used. There is no `examples/` script for this doc: start the API (`uvicorn app.api:app --reload`) and POST the same question to `/chat` twice with *different* `session_id` values (for example `"a"` then `"b"`), and watch `cache_hit` flip from `false` to `true` in the response. Using the same session both times is not a hit, because the second ask is no longer the first turn of a conversation. The CLI (`python -m app.main`) can't show a hit: it is one process with one session, and the cache starts empty every time it starts, so `(served from cache)` only appears when the cache was filled by a *different* session in the same process (which is what the API demo above does).
- **Previous doc:** `../28_testing/README.md`
- **Next doc:** `../30_security/README.md` — protecting your AI assistant from prompt injection, unauthorized access, and data leakage
- **Official docs:** https://python.langchain.com/docs/integrations/llm_caching/
