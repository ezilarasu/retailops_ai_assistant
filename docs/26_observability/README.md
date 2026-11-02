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
| **LangSmith traces** | Full execution tree with prompts, tools, token counts | `LANGSMITH_TRACING=true` (older name: `LANGCHAIN_TRACING_V2`) |
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

**What RetailOps actually does today** is intentionally minimal: `app/logging_config.py` contains a single function, `configure_logging()`, which sets up Python's standard `logging.basicConfig()` with a plain string format — not JSON, no context vars, no dedicated retrieval/request/error logging helpers. It also turns noisy libraries down to WARNING and hides model-loading progress bars (explained in the callout below the code).

```python
# ══════════════════════════════════════════════════════════════════════════
# app/logging_config.py — RetailOps logging (actual implementation)
#
# Called once at startup: from app/api.py (when the module is imported) and
# from app/main.py (the CLI).
# ══════════════════════════════════════════════════════════════════════════

import logging
import sys

# Libraries that log every HTTP request or model-file lookup at INFO. Left alone they
# bury the app's own log lines (route_selected, rag_stage_timing, retrieved_doc, ...).
# groq is not listed: its "Retrying request ... in N seconds" lines show rate limiting.
NOISY_LOGGERS = (
    "httpx",
    "httpcore",
    "sentence_transformers",
    "huggingface_hub",
    "urllib3",
    "filelock",
)


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
    )

    for name in NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)

    # Hide the "Loading weights" progress bars printed while models load.
    try:
        from huggingface_hub.utils import disable_progress_bars

        disable_progress_bars()
    except ImportError:
        pass

    try:
        from transformers.utils import logging as transformers_logging

        transformers_logging.disable_progress_bar()
    except ImportError:
        pass
```

> **Lesson from this project:** logging at INFO for the whole process sounds harmless until a library you use logs every HTTP request at INFO too. Before this change, one question printed roughly 150 lines (a dozen Hugging Face file lookups per model load, every Groq request), and the few lines that matter (`route_selected`, `rag_stage_timing`, `retrieved_doc`) were buried; three questions now print about 76 lines in total. The one library we deliberately did *not* quiet is `groq`: its "Retrying request ... in 20 seconds" line is how you discover that you are being rate limited and that most of a slow request was waiting, not computing. Turn logging down selectively, and keep the lines that explain surprises.

Request IDs do exist in RetailOps today — but they're generated in `app/router.py`, not in `logging_config.py`, and they aren't propagated via a `ContextVar`. Each call to `run_router()` generates its own `request_id = str(uuid.uuid4())` and passes it explicitly as a format argument to plain `logger.info(...)` calls (e.g. `"request_started request_id=%s question=%s"`, `"route_selected request_id=%s route=%s reason=%s"`, `"request_completed ... latency_ms=%s"`), and the same `request_id` is threaded through to `trace_config(route, request_id)` for LangSmith (see doc 27). So request correlation works today via plain-text log greping on `request_id=<uuid>`, not via structured JSON fields or a context variable.

Two honest limits of that approach: (1) log lines written *inside* the chains and retrievers (`rag_stage_timing` and `retrieved_doc` in `app/chains.py`, `hybrid_retrieval_timing` in `app/hybrid_retriever.py`) do **not** carry the `request_id`, because it isn't passed down to them — a `ContextVar` is exactly what would fix that; (2) the `request_started` line logs the full question text, which is fine for a demo but is something to trim or redact if questions can contain personal data.

What RetailOps *does* already log, all as plain text via the standard `logging` module:

| Log event | Where | Fields |
|---|---|---|
| `request_started` / `route_selected` / `request_completed` | `app/router.py` | `request_id`, `route`, `reason`, `latency_ms` (and `confidence` for rag) |
| `request_failed` (INFO-level pipeline, **WARNING** for a recognised failure) | `app/router.py` | `request_id`, `code` (`model_refused`, `rate_limited`, `model_unavailable`, `llm_error`), `latency_ms`, the first 300 characters of the provider's message |
| `request_failed` (**ERROR** with a full traceback, via `logger.exception`) | `app/router.py` | `request_id`, `latency_ms`, `error`: anything unexpected |
| `llm_retry` (WARNING) | `invoke_with_retry()` in `app/llm.py` | `attempt`, `error_type`, provider `code`: a transient model failure that is about to be retried once |
| `rag_stage_timing` | `build_rag_chain()` in `app/chains.py` | `rewrite_ms`, `retrieval_ms`, `multi_query`, original and rewritten question |
| `retrieved_doc` (one per document) | `app/chains.py` | `rank`, `source`, `rerank_score` |
| `hybrid_retrieval_timing` | `app/hybrid_retriever.py` | `candidates_ms`, `rerank_ms`, `total_ms`, candidate and final counts. Only logged when `ENABLE_MULTI_QUERY=false`: with multi-query on (the default) the pipeline asks the retriever for candidates directly and reranks once, so this line does not appear and `rag_stage_timing` carries the timing |

Stage timing here uses plain `time.perf_counter()` calls rather than the `Timer` helper from the Basic Example above — the `Timer` class is a teaching device and is not in `app/`. `app/exceptions.py` defines a small error hierarchy that `run_router()` really uses: `RetailOpsError` (base), `LLMError`, `ModelRefusalError`, `RateLimitError` and `ModelUnavailableError`, each carrying a short `code`, a user-safe message and an HTTP status. `invoke_with_retry()` in `app/llm.py` turns provider exceptions into these (retrying once for transient parse failures and connection problems), `run_router()` catches them, logs one WARNING line with the `code` and returns the safe message, and anything else falls through to a generic `except Exception` that logs the full traceback with `logger.exception(...)`. Expected failures stay quiet in the logs (one short line), while real bugs are loud.

**What a more mature system would add** (not implemented today): a JSON formatter, a `ContextVar`-based request ID that auto-propagates into every log line without passing it explicitly, and dedicated helpers like `log_retrieval()` / `log_request()` / `log_error()` for consistent structured fields. If you outgrow the plain-text format, that's the natural next step — but don't assume it's already there.

```python
# ── Illustrative upgrade path (NOT in the current codebase) ───────────────
# A JSON formatter + ContextVar-based request ID would look like this:
#
# from contextvars import ContextVar
# _request_id: ContextVar[str] = ContextVar("request_id", default="")
#
# class JsonFormatter(logging.Formatter):
#     def format(self, record):
#         return json.dumps({
#             "ts": self.formatTime(record),
#             "level": record.levelname,
#             "event": record.getMessage(),
#             "request_id": _request_id.get(""),
#         })
#
# This is a good direction to grow into — but app/logging_config.py
# does not do this today.
```

## 🏭 Production Best Practices

1. **Use structured JSON logs from day one** — Plain text logs can't be filtered by field value. When you need all logs where `route=rag` or `retrieval_ms > 1000`, you need JSON. **How:** Replace all `print()` with `logger.info("event", extra={"extra_fields": {...}})`.

2. **Add a request ID to every log line** — When a user reports a problem, the first step is finding the relevant logs. Without a request ID, you're searching through thousands of log lines by timestamp. RetailOps does this today by generating `request_id = str(uuid.uuid4())` once per call in `run_router()` (`app/router.py`) and passing it explicitly to the `logger.info(...)` calls in that file as a `%s` argument. Log lines written deeper in the pipeline (chains, hybrid retriever) don't carry it yet. A more mature version would use a `ContextVar` so every log call picks it up automatically instead of threading it through by hand.

3. **Log retrieval results explicitly** — Most wrong RAG answers come from retrieving the wrong document, not from the LLM generating incorrect text. Logging `sources`, `scores`, and `num_docs` after every retrieval call makes the most common failure type immediately diagnosable. RetailOps does this inline rather than through a helper: `build_rag_chain()` in `app/chains.py` logs a `retrieved_doc rank=… source=… rerank_score=…` line for every retrieved document. A dedicated `log_retrieval()` helper that also adds the `request_id` would be a good next step.

4. **Track per-stage latency, not just total latency** — "The request took 3 seconds" is not actionable. "Retrieval took 150ms, cross-encoder took 900ms, LLM took 1,800ms" tells you exactly where to optimize. **How:** Wrap each stage in a `Timer` context manager (or plain `time.perf_counter()` calls, which is what RetailOps does) and log `retrieval_ms`, `rerank_ms`, `llm_ms` separately. RetailOps already logs rewrite, retrieval, candidate and rerank timings; it does not time the final LLM call separately — only the whole request via `latency_ms`.

5. **Never log PII or sensitive document content** — Logs are often stored in less-secure systems (log aggregators, developer consoles). If full document text or user PII ends up in logs, you've created a compliance risk. **How:** Log only `question_snippet` (first 80 chars), source filenames (not content), and scores. (RetailOps' `request_started` line currently logs the whole question, so treat that as something to tighten before real user data flows through.)

6. **Log routing decisions** — When the assistant gives a wrong answer, the second question (after retrieval) is: was it routed to the right workflow? Log `route` and `reason` from `RouteDecision` on every request. **How:** RetailOps does this in `run_router()` with `logger.info("route_selected request_id=%s route=%s reason=%s", request_id, decision.route, decision.reason)`; with a JSON formatter the same call becomes `logger.info("routing", extra={"extra_fields": {"route": decision.route, "reason": decision.reason}})`.

## ⚠️ Common Mistakes to Avoid

⚠️ **Using `print()` statements** — `print()` output goes to stdout with no structure, no severity level, no filtering capability. In production log aggregators (CloudWatch, Datadog, ELK), unstructured text is nearly impossible to query. Replace with `logger.info()` from day one.

⚠️ **Logging only at the top level** — A single log line per request ("request completed in 2.3s") tells you nothing about which stage was slow or which document was retrieved. Log at every meaningful stage.

⚠️ **No request ID propagation** — Without request IDs, correlating log lines from router, retriever, reranker, and LLM for a single request requires timestamp matching — fragile and unreliable. Use a ContextVar-based request ID.

⚠️ **Logging full document content** — Retrieving the full text of HR policy documents or incident runbooks into log files creates a security and compliance risk. Log filenames and scores, not content.

⚠️ **Not logging errors with context** — `logger.error(str(e))` loses critical information. `logger.error("retrieval_failed", extra={"stage": "cross_encoder", "error": str(e), "question": q[:80]})` tells you exactly which stage failed and for what input.

## 🔗 How It Connects to Other Concepts

- **LangSmith** (doc 27) — LangSmith captures AI-specific traces (prompts, retrieved docs, token counts); structured logs capture system events (routing decisions, latency, errors) — they complement each other
- **RAG Evaluation** (doc 19) — Evaluation measures quality at batch level; observability measures quality per request in production
- **FastAPI Integration** (doc 25) — `app/api.py` calls `configure_logging()` once at import time; request IDs are actually generated per-call inside `run_router()` in `app/router.py`, not in FastAPI middleware
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

- **Example files:** `app/logging_config.py` — RetailOps `configure_logging()` (plain `logging.basicConfig`); `app/router.py` — per-request `request_id` generation and logging; `app/chains.py` and `app/hybrid_retriever.py` — stage timing and retrieved-document logs. There is no runnable `examples/` script for this doc: start the app (`python -m app.main`) and read the log lines it prints.
- **Previous doc:** `../25_fastapi_integration/README.md`
- **Next doc:** `../27_langsmith/README.md` — AI-specific tracing for prompts, retrieved documents, tool calls, and evaluation
- **Official docs:** https://docs.python.org/3/library/logging.html
