# FastAPI Integration
> Turning a Python script into a production API that any client can call.

## 📌 What Is It?

**FastAPI integration** means wrapping your LangChain chains and agents in an HTTP API so that web apps, mobile clients, Slack bots, or other services can call your AI assistant over the network.

During development, you run chains directly in Python scripts. In production, clients need an endpoint:

```
Development:
  python script.py → chain.invoke({"question": "..."}) → print(answer)

Production:
  Client (web/mobile/Slack)
    → POST /chat {"question": "..."}
    → FastAPI endpoint
    → service layer → router → chain/agent
    → {"answer": "...", "route": "rag", "sources": [...]}
```

FastAPI is the standard choice for this in the Python AI ecosystem because it provides:
- Pydantic request/response validation (the same library used for `RAGResponse`, `RouteDecision`)
- Automatic OpenAPI docs at `/docs`
- Async support for streaming responses
- Fast startup and low overhead

## ❓ Why Does It Exist?

A LangChain application running only as a Python script can't be used by web browsers, mobile apps, or other backend services. An API makes the assistant accessible to any HTTP client.

Beyond access, an API enforces structure: every request goes through validation, every response has a consistent schema, errors return clean JSON rather than Python tracebacks. This is what "production-ready" means.

**The architecture problem it also solves:** without a service layer, developers tend to put business logic directly in API endpoints. FastAPI integration done right separates three concerns:
1. **API layer** (`app/api.py`) — request validation, response formatting, error handling
2. **Service layer** (`app/services.py`) — `RetailOpsAssistantService.ask()`: checks the response cache, then calls `run_router()`, which handles routing, chain invocation and conversation memory
3. **Chain layer** (`app/router.py`, `app/chains.py`, `app/tools.py`) — the actual LangChain components

## ⏰ When Should You Use It?

✅ Any time non-Python clients need to use your assistant  
✅ When multiple teams need to integrate with your AI system  
✅ When you need request validation, logging, auth, and error handling in one place  
✅ When the same logic needs to serve web, mobile, and Slack simultaneously  

❌ Don't add FastAPI for internal scripts or one-off analysis tools  
❌ Don't put business logic inside endpoints — use a service layer  
❌ Don't reinitialize chains per request — build them once and reuse them  
❌ Don't expose stack traces in error responses — always return clean JSON  

## 🗂️ Types / Variants

| Pattern | Description | Best For |
|---|---|---|
| **Sync endpoints** | `def chat(...)` — standard request/response | Simple Q&A where streaming isn't needed |
| **Streaming endpoints** (not in RetailOps today) | `async def chat(...)` + `StreamingResponse` | Chat UIs that show text as it's generated |
| **Background tasks** (not in RetailOps today) | `BackgroundTasks` for async work after response | Logging, analytics, sending notifications |
| **WebSocket endpoints** (not in RetailOps today) | Persistent connection for real-time updates | Full duplex chat (less common for LangChain apps) |

## 🔀 When to Use Which Type

**Use sync endpoints** to start — they're simpler to test and debug. RetailOps' endpoints are all synchronous. Most enterprise internal tools don't need streaming.

**Add streaming** when building a user-facing chat interface where users wait for long LLM responses. Streaming reduces perceived latency significantly — users see the answer building in real time instead of waiting for the full response.

**Use background tasks** for work that shouldn't block the response: logging to LangSmith, updating analytics, sending Slack notifications on P1 incidents detected by the assistant.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Any HTTP client can use the assistant | Adds infrastructure complexity vs. a script |
| Pydantic validation rejects malformed input early | Requires deployment, monitoring, scaling |
| Automatic `/docs` at no cost | Streaming requires async knowledge |
| Clean separation: API / service / chains | Session management (memory) becomes stateful |
| Easy to add auth, rate limiting, CORS | Error handling must be explicit at every layer |

## 💻 Basic Example

```python
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

app = FastAPI(title="RetailOps AI", version="1.0")
llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)

# ── Request / response schemas ────────────────────────────────────────────
class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)

class ChatResponse(BaseModel):
    answer: str
    route: str = "general"

# ── Build chains once at startup ──────────────────────────────────────────
# Never build chains inside endpoint functions — it's expensive and slow
_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are RetailOps AI Assistant."),
    ("human", "{input}"),
])
_chain = _prompt | llm | StrOutputParser()

# ── Endpoints ─────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    """Health check — used by load balancers and deployment systems."""
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Ask the assistant a question. Returns answer and route."""
    try:
        answer = _chain.invoke({"input": request.question})
        return ChatResponse(answer=answer)
    except Exception as e:
        # Never expose raw exception to clients — log it, return clean error
        raise HTTPException(status_code=500, detail="Unable to process request.")


# Run with: uvicorn main:app --reload
# Visit: http://localhost:8000/docs for interactive API documentation
```

## 🔧 Real-World Example

RetailOps' real API (`app/api.py`, shown as in the repo): a thin HTTP layer over the service layer, with API-key auth, a health check, a debug endpoint, and admin endpoints.

```python
# ══════════════════════════════════════════════════════════════════════════
# app/api.py — RetailOps FastAPI application
#
# Architecture:
#   Client → FastAPI (api.py)
#          → assistant_service.ask()   (services.py: cache check)
#          → run_router()              (router.py: classify, run the route, save memory)
#          → rag chain | tool agent | general chain   (chains.py, built once by container.py)
#
# Run from the repository root:  uvicorn app.api:app --reload
# ══════════════════════════════════════════════════════════════════════════
from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse

from app.cache import response_cache
from app.container import get_container
from app.debug import debug_retrieval
from app.exceptions import HTTP_STATUS_BY_CODE
from app.health import get_health_status
from app.indexing import rebuild_index
from app.logging_config import configure_logging
from app.memory import DEFAULT_SESSION, clear_memory
from app.schemas import ChatRequest, ChatResponse
from app.security import check_api_key_configured, verify_api_key
from app.services import assistant_service

configure_logging()
check_api_key_configured()              # refuses the placeholder API key unless APP_ENV=local

app = FastAPI(
    title="RetailOps AI Assistant",
    version="1.0.0",
    description="Production-style LangChain RAG assistant for retail operations.",
)


@app.get("/health")                     # no API key needed
def health_check():
    return get_health_status()          # status, version, model names, cache size, component checks


@app.post("/chat", response_model=ChatResponse, dependencies=[Depends(verify_api_key)])
def chat(request: ChatRequest):
    result = assistant_service.ask(request.question, request.session_id)

    if result["route"] == "error":      # run_router() never raises: it returns an error dict with a code
        return JSONResponse(
            status_code=HTTP_STATUS_BY_CODE.get(result.get("error"), 500),
            content=result,
        )

    return result


@app.post("/memory/clear", dependencies=[Depends(verify_api_key)])
def clear_chat_memory(session_id: str = DEFAULT_SESSION):
    clear_memory(session_id)            # clears one session's history, not everyone's
    return {"status": "memory cleared", "session_id": session_id}


@app.post("/index/rebuild", dependencies=[Depends(verify_api_key)])
def rebuild_vector_index():
    result = rebuild_index()

    # The running chains still hold the old index (and an in-memory BM25 copy of the old
    # chunks), and cached answers came from the old documents. Drop both, then rebuild the
    # chains on the fresh index so no restart is needed.
    get_container.cache_clear()
    response_cache.clear()
    get_container()

    return result


@app.post("/debug/retrieval", dependencies=[Depends(verify_api_key)])
def debug_retrieval_endpoint(request: ChatRequest):
    return debug_retrieval(request.question, request.session_id)


# ── The pieces it relies on ───────────────────────────────────────────────
# app/schemas.py:
#   class ChatRequest(BaseModel):  question: str
#                                  session_id: str = "default"   (max 100 characters)
#   class ChatResponse(BaseModel): request_id, route, reason, answer,
#                                  sources (optional), confidence (optional),
#                                  latency_ms, cache_hit
#
# app/security.py:
#   def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
#       # hmac.compare_digest: the check takes the same time however close the guess was
#       if x_api_key is None or not hmac.compare_digest(x_api_key.encode(), settings.app_api_key.encode()):
#           raise HTTPException(status_code=401, detail="Invalid or missing API key.")
#
# app/services.py:
#   class RetailOpsAssistantService:
#       def ask(self, question, session_id="default"):
#           # first question of a conversation: cache lookup; then run_router(); cache write
#           # (follow-ups and tools answers are never cached; a hit still records the turn in memory)
#
# app/exceptions.py:
#   HTTP_STATUS_BY_CODE = {"model_refused": 422, "rate_limited": 429,
#                          "model_unavailable": 503, "llm_error": 502, "internal_error": 500}
#
# app/container.py:
#   @lru_cache(maxsize=1)
#   def get_container(): ...   # builds index, retriever, rewriter, chains, agent once, on first use
```

**What to notice**

- **No lifespan hook.** The chains are built lazily by `get_container()` the first time something needs them — either the first `/chat` request or the first `/health` call (which reports `"degraded"` if the build fails). That first call is slow (index check, model loads); later calls reuse the cached container. The terminal CLI (`python -m app.main`) avoids this by calling `get_container()` once at start-up, before it asks for your first question; the API does not, so the first API request still pays the cost.
- **`/debug/retrieval` is cheap now.** It reuses the retriever and question rewriter the running app already built (`get_container()`), so nothing is re-chunked or re-indexed (about 0.7 s, and the index entry count stays the same). It still calls the LLM for the question-rewrite (follow-ups only) and multi-query steps, so it is not free. It returns the rewritten question and, for each retrieved chunk, the rank, source, rerank/BM25 scores and a content preview.
- **Admin endpoints** (`/memory/clear`, `/index/rebuild`) use the same single API key as `/chat`. Anyone with the key can clear any session's history or rebuild the index. `/index/rebuild` rebuilds the index in place, clears the response cache and rebuilds the chains, so the running app picks up changed documents without a restart.
- **Sessions:** `/chat` accepts an optional `session_id` (default `"default"`). Requests with the same id share chat history; different ids are isolated (doc 24). Use a server-generated or per-user id: the API key does not stop one client from guessing another's session id.
- **Errors:** `/chat` never returns a traceback. A failed request comes back as JSON with a `request_id` (find it in the logs), a short `error` code and a user-safe `answer`, with a matching status: `422 model_refused` (the model declined, e.g. a prompt-injection style request), `429 rate_limited`, `503 model_unavailable` (the configured model is gone), `502 llm_error` (provider failure after one retry), `500 internal_error` (anything unexpected).

> **Lesson from this project:** an admin endpoint that changes data your running components have already loaded must refresh those components too. `/index/rebuild` once deleted the index folder while the app still held it open, and the next question failed with "attempt to write a readonly database" until you restarted. The fix has three parts: delete the Chroma *collection* in place (not the folder), clear the caches that came from the old documents, and rebuild the container so the retriever and its in-memory BM25 copy match the new index.

**How you would add the missing pieces (not in this repo):**

```python
# 1) Build the container at startup instead of on the first request (lifespan hook)
from contextlib import asynccontextmanager
from app.container import get_container

@asynccontextmanager
async def lifespan(app: FastAPI):
    get_container()      # slow work happens here, before the first request arrives
    yield

app = FastAPI(title="RetailOps AI Assistant", lifespan=lifespan)

# 2) A streaming endpoint (shown for the general route only — it is a plain prompt | llm | parser chain)
from fastapi.responses import StreamingResponse

@app.post("/chat/stream", dependencies=[Depends(verify_api_key)])
async def chat_stream(request: ChatRequest):
    chain = get_container().general_chat_chain

    async def generate():
        async for chunk in chain.astream({"question": request.question}):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain")
```

## 🏭 Production Best Practices

1. **Initialize chains once, not per request** — Loading the embedding model, connecting to Chroma, and building LCEL pipelines takes seconds. Doing this per request would make your API unusably slow. **How:** build the chains in one place and cache it. RetailOps does this with `get_container()` (`@lru_cache`), which builds everything on first use. To move that cost to startup, call it from a FastAPI `lifespan` hook (see the snippet above).

2. **Use Pydantic models for all request and response schemas** — This gives you automatic validation, clear API contracts, and free OpenAPI documentation. **How:** Define `ChatRequest(BaseModel)` and `ChatResponse(BaseModel)` with `Field(description=...)` on each field — the descriptions appear in the `/docs` UI. (RetailOps' `ChatRequest` has just a `question` field; adding `min_length`/`max_length` is an easy hardening step.)

3. **Always add a `/health` endpoint** — Load balancers, Kubernetes liveness probes, and deployment pipelines require a health endpoint to know if the service is up. **How:** RetailOps' `/health` returns status, version, model name, cache size, and whether each chain was built (`get_health_status()` in `app/health.py`). It also reports both model names (`llm_model` and `tools_llm_model`). Note it builds the container on first call, so a probe can be slow right after a restart.

4. **Never return stack traces to clients** — Python tracebacks leak internal implementation details. **How:** catch exceptions close to where they happen and return a clean error with an ID. `run_router()` wraps the whole request in `try/except`, logs the full traceback with the `request_id` (`logger.exception`), and returns an `error` result carrying a short code; `/chat` turns the code into an HTTP status (422, 429, 503, 502 or 500) with a JSON body.

5. **Add a `/debug/retrieval` endpoint** — When users report wrong RAG answers, the first question is always "did the retriever find the right document?" A debug endpoint that returns the retrieved chunks lets you diagnose this in seconds. **How:** `debug_retrieval()` in `app/debug.py` returns the rewritten question plus each chunk's rank, source, scores and a preview. Protect it with the API key and keep it off public deployments: it returns document text.

6. **Separate the service layer from the API layer** — API endpoints should not call chains directly. `assistant_service.ask()` owns the cross-cutting logic (caching, then routing); `run_router()` owns routing, chain invocation and memory. Endpoints own the HTTP contract: validation, response formatting, auth. This makes the logic testable without HTTP and reusable from the CLI (`python -m app.main` uses the same service). **How:** `api.py` calls `assistant_service.ask()`; the service calls `run_router()`.

## ⚠️ Common Mistakes to Avoid

⚠️ **Creating chains inside endpoint functions** — Every request would reload the embedding model, reconnect to the vector store, and rebuild the LCEL pipeline. That takes seconds per request and defeats the purpose of an API. Build chains once and reuse them (`get_container()`).

⚠️ **No input validation** — Without Pydantic models, a missing `question` field or a 10,000-character question goes straight to the LLM. `min_length=1, max_length=1000` in the schema catches these at the boundary before any chain runs. (RetailOps' `ChatRequest` does not limit the length of `question` yet; only `session_id` is capped, at 100 characters.)

⚠️ **Business logic in endpoint functions** — When routing logic, memory management, and chain invocation are all inside `@app.post("/chat")`, testing requires making HTTP requests. Extract to a service layer that can be unit-tested with plain Python function calls.

⚠️ **No health endpoint** — Kubernetes and most cloud platforms won't route traffic to a service without a successful health check. Add `/health` from day one.

⚠️ **Exposing raw exceptions** — `raise e` or leaving an unhandled exception in an endpoint returns a 500 with a full Python traceback to the client. This leaks your code structure and looks like a broken product. Always catch and return a clean error message.

## 🔗 How It Connects to Other Concepts

- **Router Pattern** (doc 23) — The service layer calls `run_router()` for every request that misses the cache; the API endpoint just calls `assistant_service.ask()`
- **RAG Chains** (doc 18) — The `rag` route invokes `build_rag_chain()` — the API exposes this capability over HTTP
- **Memory** (doc 24) — `run_router()` calls `get_messages(session_id)`, `add_user_message()`, and `add_ai_message()` for each request; `/chat` passes the request's `session_id` through, and `/memory/clear?session_id=...` clears one session
- **Agents** (doc 21) — The `tools` route invokes `build_tool_agent()` — the API gives external clients access to the agent
- **Observability** (doc 26) — FastAPI middleware can log request latency; LangSmith traces each chain invocation triggered by the API

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | FastAPI HTTP wrapper around LangChain chains — routes, validates, and returns structured responses |
| **Why** | Web/mobile/Slack clients can't call Python functions directly; an API makes the assistant universally accessible |
| **When** | Any production deployment; skip for internal scripts or one-off analysis |
| **Types** | Sync endpoints (standard), streaming (chat UIs), background tasks (logging/analytics) |
| **Production gotcha** | Build chains once (RetailOps builds them lazily on first use); use Pydantic schemas; separate service layer; add `/health`; never return stack traces |

## ➡️ Next Steps

- **Example files:** `app/api.py`, `app/services.py`, `app/schemas.py`, `app/container.py`, `app/health.py`, `app/debug.py` — RetailOps complete API architecture. Try it: `uvicorn app.api:app --reload`, then open http://localhost:8000/docs (no `RUN.md` — this doc has no standalone example script)
- **Next doc:** `../26_observability/README.md` — logging, tracing, latency measurement, and why observability is non-negotiable for production AI
- **Official docs:** https://fastapi.tiangolo.com/
