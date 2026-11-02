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

**Important: don't cache live operational data.** Inventory levels, sales figures, and incident status change constantly. Caching the answer to "Which items are low in stock?" for 5 minutes means users see stale data. Tools route questions get their answers from live APIs — never cache them.

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
from langchain_core.cache import InMemoryCache
from langchain_core.globals import set_llm_cache

load_dotenv()

# ── LangChain built-in LLM cache ─────────────────────────────────────────
# One line to cache all identical LLM calls.
# Useful during development to avoid paying for repeated identical prompts.
set_llm_cache(InMemoryCache())

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

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

RetailOps' production cache module — route-aware caching (only caches RAG/general, skips tools), document version invalidation, and the Redis upgrade path.

```python
import os
import hashlib
import json
import time
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════
# app/cache.py — RetailOps response cache
#
# Only caches "rag" and "general" route responses.
# "tools" route is NEVER cached — live operational data changes constantly.
#
# Cache key includes DOCUMENT_VERSION env var so updating the knowledge
# base automatically invalidates all cached answers.
#
# Current: in-memory SimpleTTLCache (lost on restart)
# Enterprise upgrade: replace _cache with Redis (see upgrade_to_redis())
# ══════════════════════════════════════════════════════════════════════════

CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))   # 5 minutes
DOCUMENT_VERSION = os.getenv("DOCUMENT_VERSION", "v1")            # bump to invalidate


class RetailOpsCache:
    """Route-aware response cache for RetailOps.

    Caches: rag, general
    Never caches: tools (live data)
    """

    CACHEABLE_ROUTES = {"rag", "general"}

    def __init__(self, ttl_seconds: int = CACHE_TTL_SECONDS):
        self._store: dict[str, tuple[dict, float]] = {}
        self.ttl_seconds = ttl_seconds
        self._hits = 0
        self._misses = 0

    def _make_key(self, question: str, route: str) -> str:
        """Build a cache key from question + route + document version.

        Including DOCUMENT_VERSION means bumping the env var in `.env`
        invalidates the entire cache on next deploy — no manual clearing.
        """
        payload = f"{route}|{question.strip().lower()}|{DOCUMENT_VERSION}"
        return hashlib.sha256(payload.encode()).hexdigest()[:20]

    def get(self, question: str, route: str) -> dict | None:
        """Retrieve a cached result.

        Returns None if:
        - Route is "tools" (never cached)
        - No cache entry exists
        - Entry has expired
        """
        if route not in self.CACHEABLE_ROUTES:
            return None  # never cache tools route

        key = self._make_key(question, route)
        entry = self._store.get(key)
        if entry is None:
            self._misses += 1
            return None

        value, expiry = entry
        if time.time() > expiry:
            del self._store[key]
            self._misses += 1
            return None

        self._hits += 1
        logger.debug("cache_hit", extra={"extra_fields": {
            "route": route, "question_snippet": question[:60]
        }})
        return value

    def set(self, question: str, route: str, result: dict) -> None:
        """Store a result if the route is cacheable."""
        if route not in self.CACHEABLE_ROUTES:
            return  # silently skip non-cacheable routes

        key = self._make_key(question, route)
        self._store[key] = (result, time.time() + self.ttl_seconds)

    def invalidate_all(self) -> int:
        """Clear the entire cache. Returns number of entries removed."""
        count = len(self._store)
        self._store.clear()
        logger.info(f"Cache invalidated: {count} entries removed")
        return count

    def stats(self) -> dict:
        """Return cache statistics for monitoring."""
        total = self._hits + self._misses
        return {
            "entries": len(self._store),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 3) if total > 0 else 0.0,
            "ttl_seconds": self.ttl_seconds,
            "document_version": DOCUMENT_VERSION,
        }


# ── Redis upgrade path ────────────────────────────────────────────────────
def upgrade_to_redis() -> "RetailOpsRedisCache":
    """Enterprise upgrade: replace in-memory cache with Redis.

    Benefits:
    - Shared across all application instances (scales horizontally)
    - Survives application restarts
    - Built-in TTL support (Redis SETEX handles expiry natively)
    - Configurable max memory and eviction policies
    """
    import redis
    import json

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    r = redis.from_url(redis_url)

    class RedisCache:
        def get(self, question: str, route: str) -> dict | None:
            if route not in {"rag", "general"}:
                return None
            key = f"retailops:{route}:{hashlib.sha256(question.lower().encode()).hexdigest()[:16]}"
            value = r.get(key)
            return json.loads(value) if value else None

        def set(self, question: str, route: str, result: dict) -> None:
            if route not in {"rag", "general"}:
                return
            key = f"retailops:{route}:{hashlib.sha256(question.lower().encode()).hexdigest()[:16]}"
            r.setex(key, CACHE_TTL_SECONDS, json.dumps(result))  # TTL handled by Redis

    return RedisCache()


# ── Usage in app/services.py ──────────────────────────────────────────────
# _cache = RetailOpsCache()
#
# def ask(question, session_id):
#     decision = route_question(question)
#
#     # Check cache before running the pipeline
#     cached = _cache.get(question, decision.route)
#     if cached:
#         return {**cached, "cache_hit": True}
#
#     # Cache miss — run the full pipeline
#     result = run_pipeline(question, decision.route, session_id)
#     _cache.set(question, decision.route, result)
#     return {**result, "cache_hit": False}
```

## 🏭 Production Best Practices

1. **Never cache tools route responses** — The tools route queries live inventory, sales, and incident data. Caching these means users see stale counts. The only safe routes to cache are `rag` and `general`. **How:** Check `if route not in {"rag", "general"}: return None` before every cache read and write.

2. **Include document version in cache keys** — When you update your knowledge base documents and rebuild the vector store, all cached answers referencing the old content become stale. Including `DOCUMENT_VERSION` in the cache key means bumping the env var automatically invalidates everything on the next deploy. **How:** `payload = f"{route}|{question}|{DOCUMENT_VERSION}"` before hashing.

3. **Set a TTL — never cache indefinitely** — Policies change. HR documents get updated. An answer that was correct last month may be wrong today. A 5–30 minute TTL gives you cost savings without serving dangerously stale answers. **How:** `CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))`.

4. **Track cache hit rate as a metric** — Cache hit rate tells you how valuable the cache actually is. If hit rate is 5%, your users aren't asking repeated questions and the cache adds overhead for little benefit. If hit rate is 70%, the cache is saving significant cost. **How:** Log `cache.stats()` periodically; alert if hit rate drops unexpectedly.

5. **Replace in-memory cache with Redis for production** — `dict`-based caching is lost on every restart and isn't shared across multiple instances of your application. Redis provides persistence, shared access across all instances, and native TTL support. **How:** `r.setex(key, TTL, json.dumps(result))` — Redis handles expiry natively.

6. **Normalize question text before hashing** — "What is P1?" and "what is p1?" should hit the same cache entry. Strip whitespace and lowercase before hashing. **How:** `normalized = question.strip().lower()` before `hashlib.sha256(normalized.encode())`.

## ⚠️ Common Mistakes to Avoid

⚠️ **Caching tools route responses** — Inventory levels, sales data, and incident status change constantly. Caching "which items are low in stock?" means users see counts from 5 minutes ago. Only cache RAG and general route answers.

⚠️ **No TTL** — A cache without expiry is a stale data time bomb. Policy documents get updated; without TTL, users may receive last month's vacation policy indefinitely. Always set a reasonable TTL (5–30 minutes for most knowledge-base content).

⚠️ **Not invalidating on document updates** — Rebuilding the vector store without invalidating the response cache means the new document content is retrieved but the cache still returns old answers. Use document versioning in the cache key or add a `cache.invalidate_all()` call to your indexing pipeline.

⚠️ **Using in-memory cache across multiple processes** — When you run 3 instances of your application behind a load balancer, each has its own in-memory cache. Requests for the same question hit different instances and result in cache misses most of the time. Use Redis for any multi-instance deployment.

⚠️ **Confusing cache with memory** — Cache stores *computed results* for performance optimization. Memory stores *conversation history* for context. A cached answer doesn't know about the current session; memory does. Different purposes, different implementations.

## 🔗 How It Connects to Other Concepts

- **Router Pattern** (doc 23) — The route determines whether caching applies: `rag` and `general` are cacheable; `tools` never is — the router's output drives the cache decision
- **RAG Chains** (doc 18) — RAG answers are the primary cache target — they're expensive (retrieval + reranking + LLM) and stable (documents change slowly)
- **Tools & Function Calling** (doc 20) — Tools return live data that must never be cached
- **FastAPI Integration** (doc 25) — The service layer checks the cache before invoking chains; cache stats are exposed via a monitoring endpoint
- **Observability** (doc 26) — Log `cache_hit=True/False` on every request; track hit rate as a production metric

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Storing computed pipeline results by question hash, served instantly on cache hit |
| **Why** | Repeated identical questions cost as much as unique ones without caching; TTL cache serves them at <5ms with no LLM cost |
| **When** | RAG and general routes with repeated questions; never for tools route (live data) |
| **Types** | Response cache (standard), LLM call cache (built-in), embedding cache, Redis (production) |
| **Production gotcha** | Never cache tools route; always set TTL; include document version in cache key; use Redis for multi-instance deployments |

## ➡️ Next Steps

- **Example file:** `app/cache.py` — RetailOps `RetailOpsCache`, `SimpleTTLCache`, Redis upgrade path
- **Next doc:** `30_security.md` — protecting your AI assistant from prompt injection, unauthorized access, and data leakage
- **Official docs:** https://python.langchain.com/docs/integrations/llm_caching/
