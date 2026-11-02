# Agents
> An LLM that doesn't just answer — it decides what to do, uses tools, and adapts based on results.

## 📌 What Is It?

An **agent** is an LLM-powered system that can reason about a problem, choose which tools to use, execute them, observe the results, and repeat until it can answer. Unlike a chain — which follows a fixed sequence of steps — an agent decides its own path at runtime.

```
Chain (fixed):          Agent (dynamic):
  Input                   Input
    ↓                       ↓
  Prompt                  Reason
    ↓                       ↓
  LLM                     Tool A
    ↓                       ↓
  Output                  Observe
                            ↓
                          Reason
                            ↓
                          Tool B
                            ↓
                          Observe
                            ↓
                          Answer
```

The analogy: a chain is a recipe — do steps 1, 2, 3 in order. An agent is a chef — look at what you have, decide what to make, adjust when ingredients are missing.

In LangChain 1.x, agents are built with `create_agent(model, tools, system_prompt=...)`. The LLM sees the available tools and decides which to call. The framework runs the tool and feeds the result back to the LLM, which then decides whether to call another tool or produce a final answer. (Older tutorials use `create_tool_calling_agent` + `AgentExecutor` — the legacy form of the same loop; `create_agent` is what RetailOps uses.)

## ❓ Why Does It Exist?

Some questions require multiple tools in an order that can't be predicted in advance:

```
"Which items are low in stock at store 101, and who's the vendor for each one?"
→ Need: get_low_stock_items() + get_vendor_for_sku()
→ Order depends on which SKUs come back from the inventory tool
```

A chain can't handle this — you'd need to hardcode every possible combination of tools and branching logic. An agent handles it dynamically: it calls inventory, sees which SKUs are low, then decides to look up a vendor for each.

**The core insight:** use agents when the path through the problem can't be defined ahead of time.

## ⏰ When Should You Use It?

✅ Multi-step tasks where the next action depends on the result of the previous one  
✅ Questions that might need different tools for different inputs  
✅ Workflows that require sequential tool calls with reasoning in between  
✅ Operational data queries: "show me inventory and sales for the stores with issues"  

❌ Don't use agents for simple Q&A — a RAG chain is faster and cheaper  
❌ Don't use agents for single-tool questions — just call the tool directly  
❌ Don't use agents when the workflow is always the same — use a chain  
❌ Don't use agents for document/policy questions — RAG handles those  

## 🗂️ Types / Variants

| Type | How It Works | Best For |
|---|---|---|
| **Tool-calling agent via `create_agent`** (LangChain 1.x) | LLM selects tools via the native function-calling API; runs as a LangGraph graph under the hood | Standard multi-tool agents; works with Groq, OpenAI, Anthropic — **used by RetailOps** (`build_tool_agent()`) |
| **Prebuilt LangGraph ReAct agent** (`langgraph.prebuilt.create_react_agent`) | Same loop, built directly from LangGraph | Learning how the loop works; RetailOps has this in `app/graph/react_agent_graph.py` (example 27) |
| **Hand-wired LangGraph tool loop** | You write the model node, `ToolNode`, and the "keep going?" edge yourself | Full control; see `app/graph/prebuilt_tools_graph.py` (example 26) |
| **Legacy `create_tool_calling_agent` + `AgentExecutor`** | The pre-1.0 way to run the same loop | Reading older code; avoid for new projects |
| **Prompt-based ReAct agent** | Explicit Thought → Action → Observation text in the prompt | Older models without native function calling |

## 🔀 When to Use Which Type

**Use `create_agent`** for most agents — it uses the model's native function-calling capability, which is more reliable than prompting the model to format tool calls as text. Works with Groq, OpenAI, Anthropic models.

**Use hand-written LangGraph** when the agent needs persistent state across turns, complex branching logic, or human-in-the-loop approval steps (see doc 33 and `app/graph/`). It's the right tool when the ready-made agent starts feeling limiting.

**Avoid the legacy `initialize_agent`** — it's deprecated. `create_tool_calling_agent` + `AgentExecutor` is the older replacement and is itself superseded by `create_agent` in LangChain 1.x.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Handles tasks where path is unknown in advance | More expensive — each tool call requires an LLM decision |
| Adapts to different inputs dynamically | More latency — sequential reasoning steps add up |
| Can call multiple tools in the right order | Harder to test — behavior is non-deterministic |
| Works with any `@tool`-decorated function | Can loop — needs a step limit (`recursion_limit`) |
| Observability via LangSmith traces per step | Poor tool descriptions cause wrong tool selection |

## 💻 Basic Example

```python
# A self-contained demo with mock data. Needs GROQ_API_KEY in .env.
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain.agents import create_agent   # LangChain 1.x agent builder

load_dotenv()

# RetailOps' default model (the app reads it from LLM_MODEL in .env); GROQ_API_KEY must be set in .env
llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)

# ── Define tools ──────────────────────────────────────────────────────────
@tool
def get_inventory(store_id: str) -> str:
    """Get low stock items for a store.
    Use when the user asks about inventory or items to reorder.
    Args: store_id — the store number (e.g., '101', '102')
    """
    data = {
        "101": "DENIM-4421 (3 units), JACKET-001 (8 units)",
        "102": "SHIRT-022 (2 units)",
    }
    return data.get(store_id, f"No low-stock data for store {store_id}.")


@tool
def get_sales(store_id: str) -> str:
    """Get today's sales summary for a store.
    Use when the user asks about revenue or sales figures.
    Args: store_id — the store number (e.g., '101', '102')
    """
    data = {"101": "$12,450 (88 transactions)", "102": "$9,320 (74 transactions)"}
    return data.get(store_id, f"No sales data for store {store_id}.")


# ── Build agent ───────────────────────────────────────────────────────────
# create_agent needs a model, a list of tools, and a system prompt.
# There is no scratchpad placeholder to manage — the agent keeps the whole
# conversation (including tool calls and results) in its list of messages.
agent = create_agent(
    model=llm,
    tools=[get_inventory, get_sales],
    system_prompt="You are RetailOps AI. Use tools to answer operational questions.",
)

# ── Invoke ────────────────────────────────────────────────────────────────
# Input: a list of messages. Output: the full message list; the last one is the answer.
result = agent.invoke({"messages": [{"role": "user", "content": "What items are low in stock at store 101?"}]})
print(result["messages"][-1].content)
# Agent selects get_inventory with store_id="101"

result = agent.invoke({"messages": [{"role": "user", "content": "Show inventory and sales for store 102."}]})
print(result["messages"][-1].content)
# Agent calls get_inventory("102"), observes the result, then calls get_sales("102")
```

## 🔧 Real-World Example

RetailOps' agent: the three operational tools from `app/tools.py` wired into `create_agent` by the `build_tool_agent()` factory in `app/chains.py`, which the router calls for the `tools` route.

```python
# ══════════════════════════════════════════════════════════════════════════
# app/chains.py — build_tool_agent() (shown as in the repo)
#
# This agent handles the "tools" route from the router. It receives
# operational questions and decides which combination of inventory, vendor,
# and incident tools to call. Run from the repository root; needs GROQ_API_KEY.
# ══════════════════════════════════════════════════════════════════════════
from langchain.agents import create_agent

from app.config import settings
from app.llm import get_llm   # ChatGroq; get_llm(model) picks the model, GROQ_API_KEY comes from .env
from app.tools import get_low_stock_items, get_vendor_for_sku, get_open_incidents


def build_tool_agent():
    # The tool agent has its own model setting (TOOLS_LLM_MODEL, default openai/gpt-oss-120b)
    llm = get_llm(settings.tools_llm_model)

    tools = [
        get_low_stock_items,
        get_vendor_for_sku,
        get_open_incidents,
    ]

    # create_agent builds the whole loop:
    #   1. LLM reads the question and the available tools
    #   2. LLM selects a tool and provides arguments
    #   3. the tool runs
    #   4. the result (observation) is fed back to the LLM
    #   5. LLM decides: call another tool, or produce the final answer
    return create_agent(
        model=llm,
        tools=tools,
        system_prompt="""
        You are RetailOps AI Assistant.

        You help retail operations teams answer questions using available tools.

        Tool rules:
        - Use inventory tools for stock and SKU questions.
        - Use vendor tools for vendor contact questions.
        - Use incident tools for store incident questions.
        - Do not invent data.
        - If a tool returns no results, clearly say no matching data was found.
        """,
    )


# ── How the router calls it (app/router.py, "tools" route) ────────────────
# The last 6 messages of the session go in first, so a follow-up such as
# "What about store 310?" makes sense to the agent:
#   result = container.tool_agent.invoke({
#       "messages": [
#           *history[-6:],
#           {"role": "user", "content": question},
#       ]
#   })
#   answer = result["messages"][-1].content
#
# ── A compound question (illustrative — exact wording varies by model) ────
# "Which items are low in stock at store 102, and who supplies them?"
#   1. The model calls get_low_stock_items(store_id="102")
#   2. It reads the returned items and calls get_vendor_for_sku(sku=...) for a SKU
#   3. It writes a final answer combining both results
# To see the real sequence for your question, print result["messages"] (doc 22).
```

Run it yourself with `examples/09_agent_with_tools.py`.

## 🏭 Production Best Practices

1. **Cap the number of agent steps** — Without a limit, an agent can loop trying to get a better result, and every loop costs tokens. **How:** `create_agent` agents run on LangGraph, which stops after `recursion_limit` steps (25 by default; each model call and each tool call counts as a step). Lower it per call: `agent.invoke(inputs, config={"recursion_limit": 8})`. The legacy `AgentExecutor` used `max_iterations=3`. RetailOps uses the default today.

2. **Write agent prompts that explain each tool's purpose** — The agent prompt is the agent's briefing document. If it doesn't list the tools and their intended use, the LLM will under-use or misuse them. **How:** Include a bullet for each tool: `- get_low_stock_items: inventory levels by store`.

3. **Make tools return safe error strings** — If a tool raises, the whole agent run can fail. Catching errors inside the tool and returning a readable message lets the model explain the problem to the user. **How:** wrap tool bodies in `try/except` and `return "Unable to retrieve ..."`, as every tool in `app/tools.py` does. (The legacy `AgentExecutor` had `handle_parsing_errors=True` for malformed tool calls.) Also wrap `agent.invoke` in the caller — `run_router()` runs it through `invoke_with_retry()` (one retry when the model's output can't be parsed) and turns provider failures into typed errors with a user-safe message (see doc 23).

4. **Inspect the message trace in development** — The agent's result already contains every step: the model's tool calls and each tool's output. Without looking at them, debugging wrong agent behavior is guesswork. **How:** `for m in result["messages"]: print(m.type, getattr(m, "tool_calls", None) or m.content)` — see doc 22. Don't return the full trace to end users in production.

5. **Don't use agents for simple single-tool questions** — If the answer always comes from one tool, a simple chain calling that tool is faster and cheaper. Agents shine when the tool combination is unknown at design time. **How:** Use the agent only in the `tools` route; use direct LCEL chains elsewhere.

6. **Trace every agent run with LangSmith** — Agent behavior is non-deterministic. LangSmith captures the full thought/action/observation loop, which is essential for diagnosing wrong tool selection or incorrect answers. **How:** `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY` in `.env` (`LANGCHAIN_TRACING_V2` is the older name for the same switch). RetailOps also passes tags and metadata to every call via `app/tracing.py`.

7. **Choose the model for tool calling deliberately, and retry only what a retry can fix** — Not every model is equally good at producing valid tool calls. In two measurements of the question "Which items are low stock in store 102, and who is the vendor for each?", `openai/gpt-oss-20b` failed with `output_parse_failed` in 6 of 8 and 8 of 8 runs, while `openai/gpt-oss-120b` succeeded 8 of 8. RetailOps therefore gives the tool agent its own model: `settings.tools_llm_model` (`TOOLS_LLM_MODEL`, default `openai/gpt-oss-120b`; an empty value falls back to `LLM_MODEL`), while routing, chat and RAG keep the faster `LLM_MODEL`. `invoke_with_retry()` in `app/llm.py` retries once when the model's output cannot be parsed, which rescues an occasional hiccup, but it cannot fix a model that fails most of the time. **How:** measure your own multi-tool questions on each candidate model (8 runs each is enough to see the difference) before you pick.

## ⚠️ Common Mistakes to Avoid

⚠️ **Using agents for everything** — Agents add latency and cost. A simple question like "translate this text" does not need an agent. Use chains for fixed workflows; reserve agents for tasks that require dynamic tool selection.

⚠️ **Using a small model for multi-tool questions and blaming the code** — If the agent works for simple questions but fails on compound ones, check the model before the prompt. On `openai/gpt-oss-20b` a compound question failed in 6 of 8 runs, and adding "call one tool at a time" to the system prompt did not help (0 of 8); switching the tool agent to `openai/gpt-oss-120b` did (8 of 8). Measure first, then decide. See best practice 7.

⚠️ **No step limit** — An agent that calls `get_vendor_for_sku` 10 times trying to get a satisfying answer will incur significant API costs. Know your limit (`recursion_limit`) and lower it for simple tools routes.

⚠️ **Confusing agents with tools** — A *tool* is a Python function (a capability). An *agent* is the decision-making system that chooses which tools to call. You write tools; the agent uses them.

⚠️ **Confusing agents with routers** — A *router* picks which workflow to run (RAG, tools, chat). An *agent* picks which *tools* to call within the tools workflow. They operate at different levels of the architecture.

⚠️ **No observability** — When an agent gives a wrong answer, you need to know exactly which tools were called, with what arguments, and what they returned. Without printing the message trace or using LangSmith tracing, debugging becomes very difficult.

## 🔗 How It Connects to Other Concepts

- **Tools & Function Calling** (doc 20; the previous concept) — Agents use `@tool`-decorated functions; function calling is the model mechanism agents use to select tools
- **ReAct Pattern** (doc 22) — The Thought → Action → Observation loop that modern agents implement internally
- **Router Pattern** (doc 23) — The router decides `route="tools"`, which triggers the agent; the agent then decides which tool to call
- **RAG Chains** (doc 18) — RAG answers knowledge questions; agents answer operational questions — the router separates them
- **LangSmith** (doc 27) — Essential for tracing agent reasoning loops in production

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | LLM system that reasons, selects tools dynamically, and iterates until it can answer |
| **Why** | Multi-step tasks with unknown tool sequences can't be solved by fixed chains |
| **When** | Multi-tool operational queries; questions where next action depends on prior result |
| **Types** | `create_agent` tool-calling agent (standard), prebuilt/hand-wired LangGraph agents, legacy `AgentExecutor`, prompt-based ReAct (older models) |
| **Production gotcha** | Cap agent steps (`recursion_limit`); write tool descriptions in the system prompt; don't use agents for simple tasks |

## ➡️ Next Steps

- **Example file:** `app/chains.py` — RetailOps `build_tool_agent()` with `get_low_stock_items`, `get_vendor_for_sku`, `get_open_incidents`
- **Runnable demo:** see `RUN.md` in this folder (`examples/09_agent_with_tools.py`); LangGraph variants in `examples/example_26_prebuilt_toolnode.py` and `examples/example_27_create_react_agent.py`
- **Next doc:** `../22_react_pattern/README.md` — the Thought → Action → Observation reasoning loop that agents use internally
- **Official docs:** https://python.langchain.com/docs/concepts/agents/
