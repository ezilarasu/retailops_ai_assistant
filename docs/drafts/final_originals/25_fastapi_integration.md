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
2. **Service layer** (`app/services.py`) — business logic: routing, chain invocation, memory management
3. **Chain layer** (`app/router.py`, `app/rag.py`, `app/tools.py`) — the actual LangChain components

## ⏰ When Should You Use It?

✅ Any time non-Python clients need to use your assistant  
✅ When multiple teams need to integrate with your AI system  
✅ When you need request validation, logging, auth, and error handling in one place  
✅ When the same logic needs to serve web, mobile, and Slack simultaneously  

❌ Don't add FastAPI for internal scripts or one-off analysis tools  
❌ Don't put business logic inside endpoints — use a service layer  
❌ Don't reinitialize chains per request — build them once at startup  
❌ Don't expose stack traces in error responses — always return clean JSON  

## 🗂️ Types / Variants

| Pattern | Description | Best For |
|---|---|---|
| **Sync endpoints** | `def chat(...)` — standard request/response | Simple Q&A where streaming isn't needed |
| **Streaming endpoints** | `async def chat(...)` + `StreamingResponse` | Chat UIs that show text as it's generated |
| **Background tasks** | `BackgroundTasks` for async work after response | Logging, analytics, sending notifications |
| **WebSocket endpoints** | Persistent connection for real-time updates | Full duplex chat (less common for LangChain apps) |

## 🔀 When to Use Which Type

**Use sync endpoints** to start — they're simpler to test and debug. Most enterprise internal tools don't need streaming.

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
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

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

RetailOps' production API — the full architecture with service layer, container pattern, streaming, debug endpoints, and API key authentication.

```python
import os
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional

load_dotenv()
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════
# app/api.py — RetailOps FastAPI application
#
# Architecture:
#   Client → FastAPI (api.py)
#          → AssistantService (services.py)
#          → route_question() → Router
#          → build_conversational_rag_chain() | build_tool_agent()
#
# Files:
#   app/api.py       — this file: endpoints, validation, error handling
#   app/services.py  — business logic: routing, chain invocation, memory
#   app/schemas.py   — shared Pydantic models
#   app/router.py    — RouteDecision classification
#   app/rag.py       — RAG chain builder
#   app/agent.py     — tool agent builder
#   app/memory.py    — session memory management
# ══════════════════════════════════════════════════════════════════════════

# ── Schemas ───────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000,
                          description="The user's question")
    session_id: str = Field(default="default",
                            description="Session ID for conversation history")

class ChatResponse(BaseModel):
    answer: str
    route: str                        # "general" | "rag" | "tools"
    sources: list[str] = []           # source documents (RAG route only)
    confidence: Optional[str] = None  # "high" | "medium" | "low" (RAG only)
    session_id: str


class DebugRetrievalRequest(BaseModel):
    question: str
    k: int = Field(default=4, ge=1, le=20)


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


# ── Container pattern: initialize once, reuse per request ─────────────────
# Building chains involves loading models, connecting to vectorstore,
# and constructing LCEL pipelines. This is expensive (~2-5 seconds).
# Do it once at startup; hold references for the application lifetime.

_service = None  # AssistantService instance, initialized at startup


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize expensive resources at startup; clean up at shutdown."""
    global _service
    logger.info("Initializing RetailOps AI...")
    from app.services import AssistantService
    _service = AssistantService()   # builds chains, loads vectorstore
    logger.info("RetailOps AI ready.")
    yield
    logger.info("Shutting down RetailOps AI.")


app = FastAPI(
    title="RetailOps AI Assistant",
    version="1.0.0",
    description="AI assistant for retail operations — answers policy questions and operational data queries.",
    lifespan=lifespan,
)


# ── Authentication ────────────────────────────────────────────────────────
API_KEY = os.getenv("API_KEY", "")

def verify_api_key(x_api_key: str = Header(default="")):
    """Validate API key from x-api-key header.

    Dependency injected into protected endpoints.
    For enterprise: replace with OAuth2 / Azure AD / Okta.
    """
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key.")
    return x_api_key


# ── Endpoints ─────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    """Health check for load balancers and deployment pipelines."""
    return {"status": "ok", "version": "1.0.0"}


@app.post("/chat", response_model=ChatResponse, dependencies=[Depends(verify_api_key)])
def chat(request: ChatRequest):
    """Ask the AI assistant a question.

    The assistant automatically routes to:
    - general: direct LLM response (greetings, general questions)
    - rag: retrieval from HR policies, IT runbooks, store SOPs
    - tools: live inventory, sales, and incident data

    Conversation history is maintained per session_id.
    """
    try:
        result = _service.ask(
            question=request.question,
            session_id=request.session_id,
        )
        return ChatResponse(
            answer=result["answer"],
            route=result["route"],
            sources=result.get("sources", []),
            confidence=result.get("confidence"),
            session_id=request.session_id,
        )
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        # Never expose internal errors to clients
        raise HTTPException(status_code=500, detail="Unable to process request.")


@app.post("/chat/stream", dependencies=[Depends(verify_api_key)])
async def chat_stream(request: ChatRequest):
    """Streaming version of /chat — yields answer tokens as they're generated.

    For chat UIs that show text being written in real time.
    """
    async def generate():
        try:
            async for chunk in _service.ask_stream(
                question=request.question,
                session_id=request.session_id,
            ):
                yield chunk
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield "[Error: unable to complete response]"

    return StreamingResponse(generate(), media_type="text/plain")


@app.post("/debug/retrieval", dependencies=[Depends(verify_api_key)])
def debug_retrieval(request: DebugRetrievalRequest):
    """Retrieve and return raw chunks for a question — for debugging RAG.

    Most wrong RAG answers are retrieval failures.
    This endpoint shows exactly which documents the retriever found,
    their scores, and their content — without running the LLM.
    """
    try:
        chunks = _service.retrieve_chunks(question=request.question, k=request.k)
        return {"question": request.question, "chunks": chunks}
    except Exception as e:
        logger.error(f"Debug retrieval error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Retrieval failed.")


@app.post("/memory/clear", dependencies=[Depends(verify_api_key)])
def clear_memory(session_id: str = "default"):
    """Clear conversation history for a session."""
    from app.memory import clear_history
    clear_history(session_id)
    return {"status": "cleared", "session_id": session_id}
```

## 🏭 Production Best Practices

1. **Initialize chains at startup, not per request** — Loading the embedding model, connecting to Chroma, and building LCEL pipelines takes 2–5 seconds. Doing this per request would make your API unusably slow. **How:** Use FastAPI's `lifespan` context manager to build chains once; store in a module-level variable or dependency injection container.

2. **Use Pydantic models for all request and response schemas** — This gives you automatic validation, clear API contracts, and free OpenAPI documentation. **How:** Define `ChatRequest(BaseModel)` and `ChatResponse(BaseModel)` with `Field(description=...)` on each field — the descriptions appear in the `/docs` UI.

3. **Always add a `/health` endpoint** — Load balancers, Kubernetes liveness probes, and deployment pipelines require a health endpoint to know if the service is up. A health check that returns `{"status": "ok"}` is the minimum. **How:** `@app.get("/health") def health(): return {"status": "ok"}`.

4. **Never return stack traces to clients** — Python tracebacks leak internal implementation details and look terrible in production. Catch exceptions at the endpoint level and return `HTTPException(status_code=500, detail="Unable to process request.")`. **How:** Wrap all `_service.ask()` calls in try/except; log the full traceback server-side with `logger.error(..., exc_info=True)`.

5. **Add a `/debug/retrieval` endpoint** — When users report wrong RAG answers, the first question is always "did the retriever find the right document?" A debug endpoint that returns raw chunks for a question lets you diagnose this in seconds. **How:** Call the retriever directly (not the full RAG chain) and return the chunks with their scores.

6. **Separate the service layer from the API layer** — API endpoints should not call chains directly. `AssistantService.ask()` owns the business logic: routing, chain invocation, memory management, error handling. Endpoints own the HTTP contract: validation, response formatting, auth. This separation makes the service testable without HTTP and reusable from CLI or other interfaces. **How:** `api.py` calls `service.ask()`; `service.ask()` calls chains.

## ⚠️ Common Mistakes to Avoid

⚠️ **Creating chains inside endpoint functions** — Every request would reload the embedding model, reconnect to the vector store, and rebuild the LCEL pipeline. This takes 2–5 seconds per request and defeats the purpose of an API. Build chains once at startup.

⚠️ **No input validation** — Without Pydantic models, a missing `question` field or a 10,000-character question goes straight to the LLM. `min_length=1, max_length=1000` in the schema catches these at the boundary before any chain runs.

⚠️ **Business logic in endpoint functions** — When routing logic, memory management, and chain invocation are all inside `@app.post("/chat")`, testing requires making HTTP requests. Extract to a service layer that can be unit-tested with plain Python function calls.

⚠️ **No health endpoint** — Kubernetes and most cloud platforms won't route traffic to a service without a successful health check. Add `/health` from day one.

⚠️ **Exposing raw exceptions** — `raise e` or leaving an unhandled exception in an endpoint returns a 500 with a full Python traceback to the client. This leaks your code structure and looks like a broken product. Always catch and return a clean error message.

## 🔗 How It Connects to Other Concepts

- **Router Pattern** (doc 23) — The service layer calls `route_question()` before every request; the API endpoint just calls `service.ask()`
- **RAG Chains** (doc 18) — The `rag` route invokes `build_conversational_rag_chain()` — the API exposes this capability over HTTP
- **Memory** (doc 24) — The service layer calls `get_history(session_id)` and `add_turn()` for each request; the API passes `session_id` from the request body
- **Agents** (doc 21) — The `tools` route invokes `build_tool_agent()` — the API gives external clients access to the agent
- **Observability** (doc 26) — FastAPI middleware can log request latency; LangSmith traces each chain invocation triggered by the API

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | FastAPI HTTP wrapper around LangChain chains — routes, validates, and returns structured responses |
| **Why** | Web/mobile/Slack clients can't call Python functions directly; an API makes the assistant universally accessible |
| **When** | Any production deployment; skip for internal scripts or one-off analysis |
| **Types** | Sync endpoints (standard), streaming (chat UIs), background tasks (logging/analytics) |
| **Production gotcha** | Initialize chains at startup; use Pydantic schemas; separate service layer; add `/health`; never return stack traces |

## ➡️ Next Steps

- **Example files:** `app/api.py`, `app/services.py`, `app/schemas.py` — RetailOps complete API architecture
- **Next doc:** `26_observability.md` — logging, tracing, latency measurement, and why observability is non-negotiable for production AI
- **Official docs:** https://fastapi.tiangolo.com/
