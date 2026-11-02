# LangSmith
> X-ray vision into your LangChain application — see exactly what every prompt said, what was retrieved, and why the LLM answered the way it did.

## 📌 What Is It?

**LangSmith** is Anthropic's LangChain's observability and evaluation platform built specifically for AI applications. It automatically captures every LangChain component execution — LLM calls, retrievers, tools, agents — as a structured trace tree, without any code changes beyond setting two environment variables.

```
Without LangSmith:
  Wrong answer → look at logs → "route=rag, latency=2.1s" → still don't know why

With LangSmith:
  Wrong answer → open trace → see:
    ├── Router: classified as "rag" ✓
    ├── Retriever: returned ["store_sop.txt", "returns_policy.txt"]
    │   → expected "hr_policy.txt" ← retrieval failure found immediately
    ├── Reranker: kept top 4 from 12 candidates
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

**Always enable tracing** — it costs nothing to set up and provides a full trace for every LangChain component. The two environment variables below are the only setup required.

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

# ── Enable LangSmith — just set these three env vars ────────────────────
# In your .env file:
#   LANGCHAIN_TRACING_V2=true
#   LANGCHAIN_API_KEY=ls__your_key_here
#   LANGCHAIN_PROJECT=RetailOps
#
# That's it. Every LangChain component now sends traces automatically.
# No code changes, no decorators, no middleware.

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

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

RetailOps' complete LangSmith setup — environment configuration, adding metadata tags to traces, using the `@traceable` decorator for non-LangChain functions, and running evaluations via LangSmith datasets.

```python
import os
from dotenv import load_dotenv
from langsmith import traceable, Client
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig

load_dotenv()

# ══════════════════════════════════════════════════════════════════════════
# LangSmith setup for RetailOps
#
# .env configuration:
#   LANGCHAIN_TRACING_V2=true
#   LANGCHAIN_API_KEY=ls__your_key_here
#   LANGCHAIN_PROJECT=RetailOps-AI
#
# After setting these, every chain/agent/retriever/LLM call
# is automatically traced. No other code changes needed.
# ══════════════════════════════════════════════════════════════════════════

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)


# ── Adding metadata to traces ─────────────────────────────────────────────
# Pass RunnableConfig to any chain invocation to tag the trace.
# Tags appear in LangSmith's filter bar and let you slice traces by
# route, version, or environment.

def invoke_with_metadata(chain, inputs: dict, route: str, session_id: str):
    """Invoke a chain and tag the LangSmith trace with metadata.

    All traces with route='rag' can then be filtered and inspected together.
    """
    config = RunnableConfig(
        metadata={
            "route": route,                              # "rag" | "tools" | "general"
            "session_id": session_id,
            "app_version": os.getenv("APP_VERSION", "0.1.0"),
            "environment": os.getenv("ENVIRONMENT", "development"),
        },
        tags=[route, os.getenv("ENVIRONMENT", "dev")],  # searchable tags
    )
    return chain.invoke(inputs, config=config)


# ── @traceable: trace non-LangChain functions ─────────────────────────────
# Use this decorator on custom Python functions that are called inside
# your pipeline but aren't LangChain objects. LangSmith will include
# them as nodes in the trace tree.

@traceable(name="route_question")
def route_question_traced(question: str) -> dict:
    """Route classification — traced so it appears in the full request trace."""
    from app.router import route_question
    decision = route_question(question)
    return {"route": decision.route, "reason": decision.reason}


@traceable(name="format_chat_history")
def format_history_traced(history: list[dict]) -> str:
    """Format history for rewriter — traced to show exactly what was passed."""
    if not history:
        return "No previous conversation."
    lines = []
    for msg in history[-4:]:
        role = "User" if msg["role"] == "user" else "Assistant"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)


# ── LangSmith client: create evaluation datasets programmatically ─────────
def upload_golden_dataset_to_langsmith(
    dataset_path: str = "evals/golden_dataset.json",
    dataset_name: str = "RetailOps RAG Golden Dataset",
) -> None:
    """Upload the local golden dataset to LangSmith for centralized evaluation.

    Once uploaded, you can run evaluations against this dataset from
    LangSmith's UI and compare before/after for each system change.
    """
    import json

    client = Client()  # reads LANGCHAIN_API_KEY from environment

    with open(dataset_path) as f:
        examples = json.load(f)

    # Create or get existing dataset
    try:
        dataset = client.create_dataset(dataset_name=dataset_name)
    except Exception:
        dataset = client.read_dataset(dataset_name=dataset_name)

    # Upload examples
    client.create_examples(
        inputs=[{"question": ex["question"]} for ex in examples],
        outputs=[{
            "expected_answer": ex["expected_answer"],
            "expected_source": ex["expected_source"],
        } for ex in examples],
        dataset_id=dataset.id,
    )
    print(f"Uploaded {len(examples)} examples to LangSmith dataset: {dataset_name}")


# ── Reading what LangSmith captures automatically ─────────────────────────
# For a RAG chain request, LangSmith traces show:
#
# Trace: "RetailOps RAG Request"  [total: 2,340ms]
#   ├── route_question             [45ms]
#   │     input:  "What does P1 mean?"
#   │     output: {route: "rag", reason: "..."}
#   ├── QuestionRewriter           [120ms]
#   │     input:  {history: "...", question: "What does P1 mean?"}
#   │     output: "What does P1 mean in the context of IT incidents?"
#   ├── EnsembleRetriever          [180ms]
#   │     input:  "What does P1 mean in the context of IT incidents?"
#   │     output: [Document(source="it_support_kb.txt"), ...]
#   ├── CrossEncoderReranker       [310ms]
#   │     input:  12 candidates
#   │     output: 4 reranked documents
#   ├── ChatGroq (RAG LLM)         [1,600ms]
#   │     input:  full prompt with context (shown in full)
#   │     output: RAGResponse(answer=..., sources=..., confidence=...)
#   │     tokens: 1,240 input / 89 output
#   └── StrOutputParser            [1ms]
#
# This tree lets you instantly see:
# - Which documents were retrieved (retrieval failure?)
# - What the full prompt looked like (prompt issue?)
# - Token counts (cost calculation?)
# - Which stage was slowest (latency optimization?)
```

## 🏭 Production Best Practices

1. **Enable tracing immediately with `.env`** — Set `LANGCHAIN_TRACING_V2=true`, `LANGCHAIN_API_KEY`, and `LANGCHAIN_PROJECT` in your `.env` file from the first day of development. The trace data will be invaluable when the first wrong answer appears. **How:** `echo "LANGCHAIN_TRACING_V2=true" >> .env`.

2. **Tag traces with route, version, and environment** — Without tags, all traces are mixed together. With tags, you can filter to "show me all RAG traces from v0.2 where route=rag" and immediately compare with v0.1. **How:** Pass `RunnableConfig(metadata={...}, tags=[...])` to every chain invocation.

3. **Use `@traceable` on non-LangChain functions** — Your routing function, history formatter, and custom utilities won't appear in traces automatically. Decorating them with `@traceable` makes them visible as nodes in the tree, closing the gap between what LangSmith captures and what your code actually does. **How:** `from langsmith import traceable; @traceable(name="route_question")`.

4. **Upload your golden dataset to LangSmith** — Running evaluations locally produces JSON reports. Running them via LangSmith stores the history, lets you compare runs side by side, and provides visual diff when quality changes. **How:** Use the LangSmith `Client()` to create a dataset and upload examples (see real-world example).

5. **Check retrieval traces first when answers are wrong** — The most common debugging pattern: user reports wrong answer → open trace → look at `EnsembleRetriever` node → check which documents were returned → usually reveals the wrong source was retrieved. **How:** In LangSmith UI, expand the retriever node and read the document sources.

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
- **FastAPI Integration** (doc 25) — Pass `RunnableConfig` with metadata from the API endpoint to tag traces with session and request info

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Automated trace capture for every LangChain component — prompts, retrieved docs, tool calls, token counts |
| **Why** | AI failures are silent (no stack trace); traces turn "why did this answer wrong?" from guessing into investigation |
| **When** | Enable from day one with `LANGCHAIN_TRACING_V2=true`; use actively during debugging and after each system change |
| **Types** | Tracing (always on), datasets (golden examples), evaluations (quality scoring), prompts hub (versioning) |
| **Production gotcha** | Tag traces with route/version/env; use `@traceable` for non-LangChain functions; check retrieval nodes first when debugging |

## ➡️ Next Steps

- **Setup:** Add `LANGCHAIN_TRACING_V2=true`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT` to `.env`
- **Next doc:** `28_testing.md` — unit tests, integration tests, and evaluation tests for LangChain applications
- **Official docs:** https://docs.smith.langchain.com/
