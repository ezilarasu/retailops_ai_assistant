# Observability & Structured Logging
> Knowing what your AI system actually did — not guessing.

## 📌 What Is It?

**Observability** is the ability to understand what happened inside a system by examining its outputs: logs, metrics, and traces. In a traditional application, a stack trace tells you where a bug is. In an AI system, failures are subtler — the system still produces an answer, but it's wrong, incomplete, or hallucinated.

The three pillars:

```
Logs     → What events happened? (question received, route selected, tool called)
Metrics  → How is the system performing? (latency, error rate, cache hit rate)
Traces   → What path did a request take? (router → retriever → reranker → LLM)
```

**Structured logging** is the specific practice of logging events as machine-readable data (JSON or dicts with named fields) rather than unstructured text strings. Instead of `print("error")`, you log `{"event": "retrieval_failed", "question": "...", "latency_ms": 450}`.

Why it matters for AI: when a user reports "the assistant gave the wrong answer about the vacation policy", you need to know:
1. What route was selected? (routing error?)
2. What documents were retrieved? (retrieval error?)
3. What did the LLM receive? (context formatting error?)
4. What exactly did the LLM produce? (generation error?)

Without structured logs and traces, you're guessing at which layer failed.

## ❓ Why Does It Exist?

Traditional software fails with exceptions. AI systems fail silently — they produce a confident-sounding wrong answer. This is worse than a stack trace because:

- There's no error to catch
- The user sees a plausible response
- You don't know whether the failure was in routing, retrieval, reranking, or generation

Without observability, the only way to investigate is to re-run the same question interactively and hope to reproduce it. With structured logs and traces, every production request leaves behind enough evidence to reconstruct exactly what happened.

**Monitoring vs observability:** monitoring detects problems ("latency > 5s"). Observability explains them ("latency > 5s because the cross-encoder reranker took 800ms on 15 candidates"). You need both.

## ⏰ When Should You Use It?

✅ From day one — not after you have production problems  
✅ Every component that can fail: router, retriever, reranker, LLM, tools  
✅ Any time you're diagnosing a wrong answer  
✅ Before and after every system change to detect regressions  

❌ Don't use `print()` statements in production — use structured logging  
❌ Don't log sensitive information: PII, passwords, full document content with personal data  
❌ Don't log only at the top level — you need per-stage timing to find bottlenecks  

## 🗂️ Types / Variants

| Type | What It Captures | Tool |
|---|---|---|
| **Structured logs** | Events with named fields (route, latency, sources) | Python `logging` module + JSON formatter |
| **Stage-level timing** | Latency per pipeline step (retrieval, reranking, LLM) | `time.perf_counter()` around each stage |
| **Retrieval logs** | Retrieved document sources and rerank scores | Logged after each retrieval call |
| **LangSmith traces** | Full execution tree with prompts, tools, token counts | `LANGCHAIN_TRACING_V2=true` |
| **Metrics** | Aggregated counts/rates (error rate, cache hit rate) | Prometheus, Datadog, CloudWatch |

## 🔀 When to Use Which Type

**Always have structured logs** — they're free and give you the baseline: question, route, latency, sources, error flag.

**Add stage-level timing** from the start — knowing total latency is not enough. Knowing retrieval took 50ms but the cross-encoder took 800ms tells you exactly where to optimize.

**Use LangSmith traces** for debugging — they capture the full prompt text, retrieved documents, and token counts in a visual tree. Much richer than logs. See doc 27.

**Add metrics** (Prometheus/Datadog) when you need alerting and dashboards. Metrics answer "how often does this happen" across many requests; logs answer "what happened in this specific request".

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Turns "why did this fail?" from guesswork into investigation | Adds code to every pipeline stage |
| Stage-level timing reveals actual bottlenecks | Poorly structured logs are as useless as no logs |
| Retrieval logs diagnose the most common RAG failure type | Logging sensitive data creates compliance risk |
| Structured logs are searchable and filterable | High-volume logging increases storage cost |
| Enables before/after comparison for system changes | |

## 💻 Basic Example

```python
import os
import time
import logging
import json
from dotenv import load_dotenv

load_dotenv()

# ── Structured JSON logger ────────────────────────────────────────────────
class JsonFormatter(logging.Formatter):
    """Formats log records as JSON lines for log aggregation tools."""
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        # Merge any extra fields passed via logger.info(..., extra={...})
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        return json.dumps(log_data)


def setup_logging():
    """Configure structured JSON logging for the application."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler])


setup_logging()
logger = logging.getLogger(__name__)


# ── Stage-level timing context manager ────────────────────────────────────
class Timer:
    """Context manager that measures elapsed time in milliseconds."""
    def __init__(self, name: str):
        self.name = name
        self.elapsed_ms = 0

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed_ms = round((time.perf_counter() - self._start) * 1000, 1)


# ── Logging a complete RAG request ────────────────────────────────────────
def handle_question(question: str, retriever, rag_chain) -> dict:
    """Handle a question with per-stage timing and structured logging."""

    # Log request receipt
    logger.info("request_received", extra={"extra_fields": {
        "question_len": len(question),
    }})

    # Time retrieval separately from LLM
    with Timer("retrieval") as t_retrieval:
        docs = retriever.invoke(question)

    sources = [doc.metadata.get("source", "unknown") for doc in docs]
    logger.info("retrieval_complete", extra={"extra_fields": {
        "num_docs": len(docs),
        "sources": sources,
        "retrieval_ms": t_retrieval.elapsed_ms,
    }})

    # Time LLM generation
    with Timer("llm") as t_llm:
        result = rag_chain.invoke({"question": question, "history": []})

    logger.info("request_complete", extra={"extra_fields": {
        "route": "rag",
        "sources": result.sources,
        "confidence": result.confidence,
        "retrieval_ms": t_retrieval.elapsed_ms,
        "llm_ms": t_llm.elapsed_ms,
        "total_ms": t_retrieval.elapsed_ms + t_llm.elapsed_ms,
    }})

    return {"answer": result.answer, "sources": result.sources}
```

## 🔧 Real-World Example

RetailOps' production logging setup — request ID propagation, stage-level timing across all pipeline components, and retrieval debugging logs.

```python
import os
import time
import logging
import json
import uuid
from contextvars import ContextVar
from dotenv import load_dotenv

load_dotenv()

# ══════════════════════════════════════════════════════════════════════════
# app/logging_config.py — RetailOps structured logging
#
# Every request gets a unique request_id that propagates through all logs.
# This lets you grep all logs for a single request across components.
#
# Stage-level timings let you identify bottlenecks precisely:
#   retrieval_ms, rerank_ms, llm_ms, total_ms
#
# Retrieval logs capture sources and scores — the most common RAG failure
# diagnostic.
# ══════════════════════════════════════════════════════════════════════════

# ContextVar holds the current request ID for the duration of a request
_request_id: ContextVar[str] = ContextVar("request_id", default="")


class RetailOpsFormatter(logging.Formatter):
    """JSON formatter that automatically includes the request_id context variable."""

    def format(self, record):
        log_obj = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "event": record.getMessage(),
            "logger": record.name,
            "request_id": _request_id.get(""),
        }
        # Merge extra fields (passed via extra={...})
        for key, val in getattr(record, "extra_fields", {}).items():
            log_obj[key] = val
        return json.dumps(log_obj)


def configure_logging(level: str = "INFO") -> None:
    """Call once at application startup to configure JSON logging."""
    handler = logging.StreamHandler()
    handler.setFormatter(RetailOpsFormatter())
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers = [handler]


def new_request_id() -> str:
    """Generate a new request ID and set it in the context variable."""
    request_id = f"req_{uuid.uuid4().hex[:8]}"
    _request_id.set(request_id)
    return request_id


# ── Production logging pattern in app/services.py ─────────────────────────
logger = logging.getLogger("retailops")


def log_retrieval(question: str, docs: list, elapsed_ms: float) -> None:
    """Log retrieval results — the most important debug signal for RAG."""
    sources = [d.metadata.get("source", "?") for d in docs]
    scores = [round(d.metadata.get("relevance_score", 0.0), 3) for d in docs]

    logger.info("retrieval_complete", extra={"extra_fields": {
        "question_snippet": question[:80],
        "num_docs": len(docs),
        "sources": sources,
        "scores": scores,
        "retrieval_ms": elapsed_ms,
    }})


def log_request(question: str, route: str, sources: list,
                confidence: str, timings: dict) -> None:
    """Log a completed request with all diagnostic fields."""
    logger.info("request_complete", extra={"extra_fields": {
        "route": route,
        "sources": sources,
        "confidence": confidence,
        **timings,            # retrieval_ms, rerank_ms, llm_ms, total_ms
    }})


def log_error(stage: str, error: Exception, question: str) -> None:
    """Log an error with enough context to diagnose it."""
    logger.error("pipeline_error", extra={"extra_fields": {
        "stage": stage,
        "error_type": type(error).__name__,
        "error_msg": str(error)[:200],
        "question_snippet": question[:80],
    }})


# ── FastAPI middleware: assign request ID per HTTP request ─────────────────
# In app/api.py:
#
# @app.middleware("http")
# async def request_id_middleware(request: Request, call_next):
#     request_id = new_request_id()
#     response = await call_next(request)
#     response.headers["X-Request-ID"] = request_id
#     return response
#
# Every log line for that request will include "request_id": "req_a1b2c3d4"
# making it trivial to grep all logs for a single failing request.
```

## 🏭 Production Best Practices

1. **Use structured JSON logs from day one** — Plain text logs can't be filtered by field value. When you need all logs where `route=rag` or `retrieval_ms > 1000`, you need JSON. **How:** Replace all `print()` with `logger.info("event", extra={"extra_fields": {...}})`.

2. **Add a request ID to every log line** — When a user reports a problem, the first step is finding the relevant logs. Without a request ID, you're searching through thousands of log lines by timestamp. With one, you grep for `req_abc123` and see the complete lifecycle. **How:** Use Python's `ContextVar` to propagate a UUID across all log calls within a request (see real-world example).

3. **Log retrieval results explicitly** — Most wrong RAG answers come from retrieving the wrong document, not from the LLM generating incorrect text. Logging `sources`, `scores`, and `num_docs` after every retrieval call makes the most common failure type immediately diagnosable. **How:** `log_retrieval(question, docs, elapsed_ms)` after every `retriever.invoke()`.

4. **Track per-stage latency, not just total latency** — "The request took 3 seconds" is not actionable. "Retrieval took 150ms, cross-encoder took 900ms, LLM took 1,800ms" tells you exactly where to optimize. **How:** Wrap each stage in a `Timer` context manager and log `retrieval_ms`, `rerank_ms`, `llm_ms` separately.

5. **Never log PII or sensitive document content** — Logs are often stored in less-secure systems (log aggregators, developer consoles). If full document text or user PII ends up in logs, you've created a compliance risk. **How:** Log only `question_snippet` (first 80 chars), source filenames (not content), and scores.

6. **Log routing decisions** — When the assistant gives a wrong answer, the second question (after retrieval) is: was it routed to the right workflow? Log `route` and `reason` from `RouteDecision` on every request. **How:** `logger.info("routing", extra={"extra_fields": {"route": decision.route, "reason": decision.reason}})`.

## ⚠️ Common Mistakes to Avoid

⚠️ **Using `print()` statements** — `print()` output goes to stdout with no structure, no severity level, no filtering capability. In production log aggregators (CloudWatch, Datadog, ELK), unstructured text is nearly impossible to query. Replace with `logger.info()` from day one.

⚠️ **Logging only at the top level** — A single log line per request ("request completed in 2.3s") tells you nothing about which stage was slow or which document was retrieved. Log at every meaningful stage.

⚠️ **No request ID propagation** — Without request IDs, correlating log lines from router, retriever, reranker, and LLM for a single request requires timestamp matching — fragile and unreliable. Use a ContextVar-based request ID.

⚠️ **Logging full document content** — Retrieving the full text of HR policy documents or incident runbooks into log files creates a security and compliance risk. Log filenames and scores, not content.

⚠️ **Not logging errors with context** — `logger.error(str(e))` loses critical information. `logger.error("retrieval_failed", extra={"stage": "cross_encoder", "error": str(e), "question": q[:80]})` tells you exactly which stage failed and for what input.

## 🔗 How It Connects to Other Concepts

- **LangSmith** (doc 27) — LangSmith captures AI-specific traces (prompts, retrieved docs, token counts); structured logs capture system events (routing decisions, latency, errors) — they complement each other
- **RAG Evaluation** (doc 19) — Evaluation measures quality at batch level; observability measures quality per request in production
- **FastAPI Integration** (doc 25) — FastAPI middleware assigns request IDs; endpoint handlers call the logging functions
- **Router Pattern** (doc 23) — Every routing decision should be logged with `route` and `reason` fields
- **Cross-Encoder Reranking** (doc 15) — Reranking is often the latency bottleneck; stage-level timing reveals this

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Structured logging, per-stage timing, and retrieval debugging that let you reconstruct what happened in any request |
| **Why** | AI systems fail silently with wrong answers; observability turns "why is this wrong?" from guesswork into investigation |
| **When** | From day one; not after you have production problems |
| **Types** | Structured logs, stage-level timing, retrieval logs, LangSmith traces, metrics |
| **Production gotcha** | Use request IDs; log retrieval results; track per-stage latency; never log PII or document content |

## ➡️ Next Steps

- **Example files:** `app/logging_config.py`, `app/services.py` — RetailOps `configure_logging()`, `log_retrieval()`, `log_request()`
- **Next doc:** `27_langsmith.md` — AI-specific tracing for prompts, retrieved documents, tool calls, and evaluation
- **Official docs:** https://docs.python.org/3/library/logging.html
