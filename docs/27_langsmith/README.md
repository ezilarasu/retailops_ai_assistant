# LangSmith
> X-ray vision into your LangChain application — see exactly what every prompt said, what was retrieved, and why the LLM answered the way it did.

## 📌 What Is It?

**LangSmith** is the observability and evaluation platform made by the LangChain team, built specifically for AI applications. It automatically captures every LangChain component execution — LLM calls, retrievers, tools, agents — as a structured trace tree, without any code changes beyond setting a few environment variables. (It needs a LangSmith account and API key; there is a free tier. It is optional for this project — set `LANGSMITH_TRACING=false` in `.env` to run without it.)

```
Without LangSmith:
  Wrong answer → look at logs → "route=rag, latency=2.1s" → still don't know why

With LangSmith:
  Wrong answer → open trace → see:
    ├── Router: classified as "rag" ✓
    ├── Retriever: returned ["store_operations_sop.txt", "returns_refunds_policy.txt"]
    │   → expected "hr_policy.txt" ← retrieval failure found immediately
    ├── Reranker: kept the top few (RETRIEVAL_K) of the merged candidates
    └── LLM: received context (shown in full), produced answer
```

Every execution of a chain, agent, retriever, or LLM call becomes a "run". A complete request from question to answer becomes a "trace" — a tree of runs with timing, inputs, outputs, and token counts at every node.

## ❓ Why Does It Exist?

Traditional application debuggers (logs, stack traces) tell you about code failures. AI application failures are different:

- The LLM receives a wrong prompt → you need to see the exact prompt text
- The retriever fetches the wrong document → you need to see what was retrieved
- The agent calls the wrong tool → you need to see the reasoning trace
- Quality degrades after a prompt change → you need before/after comparison

Structured logs help, but they can't capture the full prompt (too long to log), the retrieved document content (sensitive), or the agent's internal reasoning (complex structure). LangSmith captures all of this in a purpose-built UI with filtering, comparison, and evaluation capabilities.

## ⏰ When Should You Use It?

✅ Enable from day one — it runs passively in the background with no code changes  
✅ When debugging wrong answers — traces show exactly which step failed  
✅ After changing any prompt, retrieval strategy, or model  
✅ When running RAG evaluations — LangSmith stores results and allows comparison  
✅ For latency analysis — every node in the trace shows execution time  

❌ Don't rely on LangSmith alone — structured logs are still needed for system events  
❌ Don't send sensitive PII to LangSmith without reviewing their data policy  
❌ Don't wait until production problems appear to enable it  

## 🗂️ Types / Variants

| Feature | What It Does | When to Use |
|---|---|---|
| **Tracing** | Captures every run as a tree; shows inputs/outputs/timing | Always enabled; default usage |
| **Datasets** | Collections of (input, expected output) pairs for evaluation | Store golden dataset in LangSmith for repeatable evals |
| **Evaluations** | Run a chain against a dataset; score results with LLM judge | After every significant system change |
| **Prompts hub** | Version-controlled prompt storage with A/B comparison | When iterating on prompts across environments |
| **Monitoring** | Aggregated metrics across all traces (latency, error rate) | Production dashboards |

## 🔀 When to Use Which Type

**Always enable tracing** — it costs nothing to set up and provides a full trace for every LangChain component. The environment variables below are the only setup required.

**Use datasets + evaluations** when you want your golden dataset and evaluation scores stored centrally (rather than in local JSON files). This gives you a history of evaluation runs and visual before/after comparison for every system change.

**Use the prompts hub** when you have multiple environments (dev/staging/prod) and want prompt changes to be reviewed and versioned rather than changed directly in code.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Zero code changes — just set env vars | Requires LangSmith API key (free tier available) |
| Shows full prompt text including retrieved context | Traces leave your environment (data privacy consideration) |
| Captures retrieval results, tool calls, agent reasoning | Free tier has trace limits; production may need paid plan |
| Visual tree for multi-step agents and RAG pipelines | Adds slight latency for trace upload (async, ~5ms) |
| Before/after comparison for prompt and retrieval changes | Debugging still requires understanding LangChain architecture |

## 💻 Basic Example

```python
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# ── Enable LangSmith — just set these env vars ──────────────────────────
# In your .env file (these are the same names used in this repo's .env.example):
#   LANGSMITH_TRACING=true
#   LANGSMITH_API_KEY=your_langsmith_key_here
#   LANGSMITH_PROJECT=retailops-ai-assistant
# (Older LangChain versions used LANGCHAIN_TRACING_V2 / LANGCHAIN_API_KEY /
#  LANGCHAIN_PROJECT; the LANGSMITH_* names are the current ones.)
#
# That's it. Every LangChain component now sends traces automatically.
# No code changes, no decorators, no middleware.

llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are RetailOps AI. Answer questions about retail operations."),
    ("human", "{question}"),
])

chain = prompt | llm | StrOutputParser()

# ── This call is automatically traced ────────────────────────────────────
result = chain.invoke({"question": "What does P1 mean?"})
print(result)

# In LangSmith, you'll see a trace with:
#   ├── ChatPromptTemplate: input {"question": "What does P1 mean?"}
#   │   output: formatted messages with system + human content
#   ├── ChatGroq: input: messages, output: AIMessage, tokens: 12 input / 45 output
#   └── StrOutputParser: input: AIMessage, output: "P1 means full store outage..."
#
# Each node shows: inputs, outputs, latency (ms), token counts
```

## 🔧 Real-World Example

RetailOps' actual pattern is simpler than a wrapper function: `app/router.py` calls `.invoke(..., config=trace_config(route, request_id))` directly, inline, at each of the four points where it invokes a chain or agent. `trace_config()` itself lives in `app/tracing.py` and just builds a plain dict with `tags` and `metadata` — no decorators, no client-side dataset upload helpers, no `@traceable` usage in the current codebase.

```python
# ══════════════════════════════════════════════════════════════════════════
# app/tracing.py — RetailOps trace metadata builder (actual implementation)
# ══════════════════════════════════════════════════════════════════════════
from app.config import settings


def trace_config(route: str, request_id: str) -> dict:
    return {
        "tags": [
            "retailops",
            route,
            settings.app_env,
        ],
        "metadata": {
            "request_id": request_id,
            "environment": settings.app_env,
            "app_version": settings.app_version,
            "route": route,
        },
    }


# ══════════════════════════════════════════════════════════════════════════
# app/router.py — actual call sites (run_router), each invoking a chain
# or agent with config=trace_config(route, request_id) passed directly
# ══════════════════════════════════════════════════════════════════════════

# Router classification (run_router calls route_question, which wraps the chain call
# in invoke_with_retry and passes the config straight through)
decision = route_question(
    question,
    history,                                   # this session's earlier messages (doc 24)
    config=trace_config("router", request_id),
)

# "general" route
answer = invoke_with_retry(lambda: container.general_chat_chain.invoke(
    {"question": question, "history": history[-HISTORY_WINDOW:]},
    config=trace_config("general", request_id),
))

# "rag" route
result = invoke_with_retry(lambda: container.rag_chain.invoke(
    {"question": question, "messages": history},
    config=trace_config("rag", request_id),
))

# "tools" route
result = invoke_with_retry(lambda: container.tool_agent.invoke(
    {"messages": [*history[-HISTORY_WINDOW:], {"role": "user", "content": question}]},
    config=trace_config("tools", request_id),
))
```

Each call site builds its own `trace_config(route, request_id)` inline — there's no `invoke_with_metadata()` wrapper. (`invoke_with_retry()` is the retry helper from `app/llm.py`, see doc 21; it just calls the lambda, so the config reaches LangSmith unchanged.) `request_id` is generated once per call to `run_router()` (`request_id = str(uuid.uuid4())`) and reused across all four call sites for that request, so every trace and log line for a single request shares the same ID (see doc 26 for how the same `request_id` shows up in logs).

> **Lesson from this project:** tracing is on by default in `.env.example`, which means every question you test, plus the document text retrieved for it, is sent to LangSmith. That is exactly what you want when debugging your own data, and exactly what you do *not* want from an automated test run or a loop of example scripts. While building this project we ran the test suite, the examples and the evals with `LANGSMITH_TRACING=false` set on the command line so test traffic stayed on the machine. Decide deliberately which environments trace, and switch it off wherever the data should not leave.

## 🏭 Production Best Practices

1. **Enable tracing immediately with `.env`** — Set `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY`, and `LANGSMITH_PROJECT` in your `.env` file from the first day of development. The trace data will be invaluable when the first wrong answer appears. **How:** copy `.env.example` to `.env` and fill in `LANGSMITH_API_KEY` (it ships with `LANGSMITH_TRACING=true`; set it to `false` if you have no key). Remember traces contain the full question and the retrieved document text, so review LangSmith's data policy before sending real user data.

2. **Tag traces with route, version, and environment** — Without tags, all traces are mixed together. With tags, you can filter to "show me all RAG traces from v0.2 where route=rag" and immediately compare with v0.1. **How:** RetailOps does this via `config=trace_config(route, request_id)` (`app/tracing.py`), a plain dict with `tags` and `metadata`, passed directly to `.invoke()` at each call site in `app/router.py` — no `RunnableConfig` object or wrapper function needed, since `.invoke()` accepts a plain dict for `config`.

3. **Use `@traceable` on non-LangChain functions** *(not used in this repo today)* — Plain Python functions (a routing helper, a history formatter, custom retrieval code) won't appear in traces automatically. Decorating them with `@traceable` makes them visible as nodes in the tree, closing the gap between what LangSmith captures and what your code actually does. **How:** `from langsmith import traceable; @traceable(name="route_question")`. RetailOps' hand-written retrieval code (`HybridRetriever`, `retrieve_with_multi_query`) is a good candidate.

4. **Upload your golden dataset to LangSmith** *(not in this repo — evals here are local)* — Running evaluations locally produces JSON reports (`evals/results/`). Running them via LangSmith stores the history, lets you compare runs side by side, and provides visual diff when quality changes. **How:** Use the LangSmith `Client()` to create a dataset from your question file (for RetailOps, `evals/rag_questions.jsonl`) and upload the examples; see the official docs linked below for the exact calls.

5. **Check retrieval traces first when answers are wrong** — The most common debugging pattern: user reports wrong answer → open trace → find the retrieval step → check which documents were returned → usually reveals the wrong source was retrieved. **How:** In RetailOps the retrieval logic is plain Python (`retrieve_context` in `app/chains.py` calling `HybridRetriever`), not a built-in LangChain retriever, so there is no ready-made "retriever" node; look at the `retrieve_context` step and the prompt input of the LLM node to see the context that was passed, and use the `retrieved_doc` log lines (doc 26) or the `/debug/retrieval` endpoint for the per-document sources and scores. If you used a built-in retriever such as `EnsembleRetriever`, it would appear as its own node.

6. **Monitor token counts per trace** — LangSmith shows input and output tokens for every LLM call. This lets you identify which query patterns are expensive and whether adding context (multi-query, longer history) is actually worth the token cost. **How:** In LangSmith UI, open any trace and click the LLM node — token counts appear in the metadata panel.

## ⚠️ Common Mistakes to Avoid

⚠️ **Thinking LangSmith replaces structured logs** — LangSmith captures LangChain execution details (prompts, retrieved docs, tokens). Structured logs capture system events (routing decisions, latency aggregations, errors, request IDs). Both are needed. LangSmith is the AI debugger; structured logs are the system diary.

⚠️ **Not tagging traces** — Untagged traces from dev, staging, and prod all look identical in the LangSmith UI. Without environment and version tags, you can't tell which environment produced a trace or compare before/after a code change.

⚠️ **Only enabling LangSmith after a production problem** — By the time users report wrong answers, you want months of trace history to understand whether the problem is new or has been occurring all along. Enable from day one.

⚠️ **Ignoring the retrieval node in traces** — Most developers open a trace and go straight to the LLM node to check the prompt. The retriever node is more valuable — it shows exactly which documents were fetched and their scores, which diagnoses the most common failure class.

⚠️ **Not building an evaluation dataset in LangSmith** — Running local eval scripts produces reports that live on a developer's laptop. Building a LangSmith dataset gives the whole team access to evaluation history, enables automated eval on CI/CD, and provides visual comparison between system versions.

## 🔗 How It Connects to Other Concepts

- **Observability** (doc 26) — LangSmith handles AI-specific traces; structured logs handle system events; both are needed
- **RAG Evaluation** (doc 19) — Local evaluation produces JSON reports; LangSmith stores them centrally with visual comparison
- **RAG Chains** (doc 18) — Every component of the RAG chain appears as a traced node: retriever, reranker, prompt, LLM
- **Agents** (doc 21) — Agent ReAct loops show as trace trees: each Thought → Action → Observation step is a node
- **FastAPI Integration** (doc 25) — `/chat` calls into `run_router()`, which builds `trace_config(route, request_id)` and passes it as `config=` on each chain/agent `.invoke()` call to tag traces with route and request info

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Automated trace capture for every LangChain component — prompts, retrieved docs, tool calls, token counts |
| **Why** | AI failures are silent (no stack trace); traces turn "why did this answer wrong?" from guessing into investigation |
| **When** | Enable from day one with `LANGSMITH_TRACING=true`; use actively during debugging and after each system change |
| **Types** | Tracing (always on), datasets (golden examples), evaluations (quality scoring), prompts hub (versioning) |
| **Production gotcha** | Tag traces with route/version/env; use `@traceable` for plain-Python code such as hand-written retrievers; check the retrieval step first when debugging; traces contain real question and document text |

## ➡️ Next Steps

- **Setup:** Set `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` in `.env` (see `.env.example`). Code to read: `app/tracing.py` and the `config=trace_config(...)` calls in `app/router.py`. There is no separate `examples/` script for this doc — run `python -m app.main`, ask a question, then open your project in LangSmith.
- **Previous doc:** `../26_observability/README.md`
- **Next doc:** `../28_testing/README.md` — unit tests, integration tests, and evaluation tests for LangChain applications
- **Official docs:** https://docs.smith.langchain.com/
