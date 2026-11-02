# ReAct Pattern (Reason + Act)
> The reasoning loop that turns a single LLM call into a multi-step problem solver.

## 📌 What Is It?

**ReAct** (Reason + Act) is the agent architecture pattern where the model alternates between three steps until it has enough information to answer:

```
Thought  → the model reasons about what it needs
Action   → the model calls a tool with specific arguments
Observation → the tool returns a result; the model reads it
```

This loop repeats until the model decides it has enough information to produce a final answer.

A single-step example:

```
Question: "Which items are low in stock at store 101?"

Thought:  "I need to query the inventory for store 101."
Action:   get_low_stock_items(store_id="101")
Observation: "DENIM-4421 (3 units, threshold 20), JACKET-001 (8 units, threshold 25)"

Thought:  "I now have the data I need."
Answer:   "Store 101 has two items below reorder threshold: ..."
```

A two-step example (where step 2 depends on step 1):

```
Question: "Which stores have low stock and what did they earn today?"

Thought:  "First I need to find which stores have low stock."
Action:   get_low_stock_items(store_id="all")
Observation: "Store 101: 2 items, Store 102: 1 item"

Thought:  "Now I need today's sales for stores 101 and 102."
Action:   get_store_sales(store_id="101", period="today")
Observation: "Revenue: $12,450 (88 transactions)"

Action:   get_store_sales(store_id="102", period="today")
Observation: "Revenue: $9,320 (74 transactions)"

Answer:   "Stores 101 and 102 have low-stock items. Today's revenue: ..."
```

The key insight: the model uses tool results to make its next decision. This is what makes ReAct adaptive rather than mechanical.

## ❓ Why Does It Exist?

Before ReAct, agents would generate all their tool calls upfront — decide everything at once, then execute. This fails when tool call #2 depends on the result of tool call #1.

ReAct solves this by interleaving reasoning and acting: after each tool call, the model re-reads all previous observations and decides what to do next. The model is always reasoning from the most current information.

**Why the name matters:** "Reasoning" and "acting" were previously treated as separate — reasoning chains (chain-of-thought) told models to think step by step, but couldn't take actions. ReAct combined them.

## ⏰ When Should You Use It?

✅ Any time you build a tool-calling agent — `create_agent` (and the legacy `AgentExecutor`) run a ReAct-style loop internally  
✅ Multi-step tasks where step N depends on the output of step N-1  
✅ Debugging agent behavior — understanding the thought/action/observation trace  
✅ When you need to explain why an agent made a particular decision  

❌ Don't use for single-step tool calls — the overhead isn't worth it  
❌ Don't confuse ReAct with tool calling — tool calling is the capability; ReAct is the reasoning strategy  
❌ Don't expect zero latency — each thought-action-observation cycle requires an LLM call  

## 🗂️ Types / Variants

| Pattern | Description | Best For |
|---|---|---|
| **Tool-calling ReAct** | Model uses native function-calling API; framework manages the loop (`create_agent`) | Production agents with Groq/OpenAI/Anthropic models — **used by RetailOps** |
| **Text-based ReAct** | Model formats thoughts/actions as text; parsed by framework | Legacy models without function-calling support |
| **LangGraph ReAct** | The same loop written as explicit graph nodes (model node → tool node → back) | Learning how the loop works; agents needing persistence, branching, human-in-the-loop. In this repo: `app/graph/react_agent_graph.py` and `app/graph/prebuilt_tools_graph.py` |
| **Single-step** | One tool call with no iteration | Simple lookup questions (not really ReAct, but uses the same tools) |

## 🔀 When to Use Which Type

**Tool-calling ReAct (via `create_agent`)** is the production default. (Older tutorials use `create_tool_calling_agent` + `AgentExecutor`, the legacy form.) The model outputs a structured tool call (not raw text), which is more reliable and easier to parse. Works with all major providers.

**LangGraph ReAct** is the upgrade path when your agent needs: state that persists across multiple user turns, conditional branching based on tool results, or human approval before taking certain actions.

**Avoid text-based ReAct** for new projects — it relies on prompt-based formatting ("Action: tool_name\nAction Input: args") which is fragile and depends on the model following formatting instructions perfectly.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Adaptive: uses tool results to decide next step | Each iteration = one LLM call; 3 iterations = 3× cost |
| Handles multi-step tasks with unknown sequences | Harder to test than chains — non-deterministic |
| Full reasoning trace for debugging | Can loop without a step limit (`recursion_limit`) |
| Model's native function-calling is reliable | Thought traces are internal — users don't see reasoning |
| Works with any `@tool`-decorated function | Poor tool descriptions → wrong tool selection |

## 💻 Basic Example

```python
# A self-contained demo with mock tools. Needs GROQ_API_KEY in .env.
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain.agents import create_agent   # LangChain 1.x agent builder

load_dotenv()

llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)

# ── Tools ─────────────────────────────────────────────────────────────────
@tool
def get_low_stock_items(store_id: str = "all") -> str:
    """Get inventory items below reorder threshold.
    Use when asked about low stock or items to reorder.
    Args: store_id — store number ('101', '102') or 'all'
    """
    mock = {
        "101": "DENIM-4421 (3 units, threshold 20), JACKET-001 (8 units, threshold 25)",
        "102": "SHIRT-022 (2 units, threshold 15)",
    }
    if store_id == "all":
        return "\n".join(f"Store {k}: {v}" for k, v in mock.items())
    return mock.get(store_id, f"No low-stock items for store {store_id}.")


@tool
def get_store_sales(store_id: str, period: str = "today") -> str:
    """Get sales summary for a store.
    Use when asked about revenue or sales data.
    Args: store_id — store number; period — 'today', 'week', or 'month'
    """
    return f"Store {store_id} sales ({period}): Revenue $12,450.00 | 88 transactions"


agent = create_agent(
    model=llm,
    tools=[get_low_stock_items, get_store_sales],
    system_prompt="You are RetailOps AI. Use tools to answer operational questions.",
)

# ── Multi-step ReAct ──────────────────────────────────────────────────────
result = agent.invoke({
    "messages": [{"role": "user", "content": "Which stores have low stock and what did they earn today?"}]
})

# The result holds the whole conversation. Reading it shows the ReAct loop:
#   human message           -> the question
#   AI message (tool_calls) -> Action: get_low_stock_items(store_id="all")
#   tool message            -> Observation: "Store 101: ..., Store 102: ..."
#   AI message (tool_calls) -> Action: get_store_sales(...) for each store found
#   tool messages           -> Observations
#   AI message (no calls)   -> the final answer
for message in result["messages"]:
    calls = getattr(message, "tool_calls", None)
    print(message.type, "|", calls if calls else message.content)
```

## 🔧 Real-World Example

RetailOps' agent (`build_tool_agent()` in `app/chains.py`) and how to read its ReAct trace. The agent factory is the real code; the trace-printing helper below is an illustrative snippet you can write yourself — RetailOps does not ship a helper like it.

```python
# ══════════════════════════════════════════════════════════════════════════
# app/chains.py — build_tool_agent() (shown as in the repo)
#
# create_agent runs the ReAct loop for you:
#   1. LLM receives the question + available tools → produces a tool call
#   2. Framework runs the tool → appends the result as a tool message
#   3. LLM reads the updated messages → calls another tool or answers
#   4. Repeat until a final answer (or the step limit is reached)
# ══════════════════════════════════════════════════════════════════════════
from langchain.agents import create_agent

from app.config import settings
from app.llm import get_llm
from app.tools import get_low_stock_items, get_vendor_for_sku, get_open_incidents


def build_tool_agent():
    llm = get_llm(settings.tools_llm_model)  # the tool agent's own model (TOOLS_LLM_MODEL)
    tools = [get_low_stock_items, get_vendor_for_sku, get_open_incidents]

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


# ── Illustrative helper (not in the repo): print the Thought/Action/Observation trace ──
def print_react_trace(agent, question: str) -> str:
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})

    for message in result["messages"]:
        if message.type == "ai" and message.tool_calls:
            for call in message.tool_calls:           # Action: which tool, which arguments
                print(f"Action:      {call['name']}({call['args']})")
        elif message.type == "tool":                  # Observation: what the tool returned
            print(f"Observation: {message.content[:200]}")
        elif message.type == "ai":                    # Final answer
            print(f"Answer:      {message.content}")

    return result["messages"][-1].content


# Example (run from the repository root; needs GROQ_API_KEY; exact steps vary by model):
# print_react_trace(build_tool_agent(), "Which items are low in stock at store 102, and who supplies them?")
```

The `Thought` step is not a separate message with tool-calling agents: the model's reasoning is folded into its tool-call decision. If you want to see each node of the loop explicitly, run the LangGraph versions in this repo: `app/graph/react_agent_graph.py` (`build_react_agent_graph()`, built on `langgraph.prebuilt.create_react_agent`, example 27) and `app/graph/prebuilt_tools_graph.py` (`build_prebuilt_tools_graph()`, a hand-wired model → tools → model loop, example 26). Both print every message of the run.

## 🏭 Production Best Practices

1. **Print the message trace during development** — The agent's result contains every tool call and observation. Without looking at them, debugging wrong agent behavior means guessing. **How:** loop over `result["messages"]` as in the Basic Example (`message.tool_calls` for actions, `message.type == "tool"` for observations).

2. **Use LangSmith for the full picture** — The raw messages don't show timing or token counts. LangSmith shows the loop as a tree: each LLM call, tool invocation, and observation. **How:** `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY` in `.env` (`LANGCHAIN_TRACING_V2` is the older name). RetailOps adds tags and metadata (request ID, route) via `trace_config()` in `app/tracing.py`.

3. **Cap the number of steps** — Most operational questions need at most a few tool calls. A limit stops the agent from looping when it can't find a satisfying answer. **How:** LangGraph-based agents stop after `recursion_limit` steps (25 by default; model calls and tool calls each count): `agent.invoke(inputs, config={"recursion_limit": 8})`. The legacy `AgentExecutor` used `max_iterations=3`. RetailOps uses the default today.

4. **Keep tool docstrings specific about when to use them** — The model reads docstrings to decide whether a tool is relevant. Vague docstrings produce wrong tool selection. "Get data" is too vague. "Use when the user asks about low stock, inventory levels, or items to reorder" is concrete. **How:** Include trigger phrases in every docstring.

5. **Return safe error strings from tools** — A tool that raises can end the whole run; a tool that returns "Unable to retrieve ..." lets the model explain the problem. **How:** `try/except` inside each tool, as in `app/tools.py`.

6. **Measure tool call frequency** — If the agent calls the same tool 3 times in one question, either the tool is returning bad data or the docstring isn't clear about what it does. **How:** Count `tool_calls` names across `result["messages"]` and log them per question.

7. **Pick a model that can do the loop** — A ReAct loop is only as good as the model's tool calls: if one step produces output the framework cannot parse, the whole run fails. RetailOps uses `TOOLS_LLM_MODEL` (default `openai/gpt-oss-120b`) for the agent because `openai/gpt-oss-20b` failed compound questions in 6 of 8 and 8 of 8 runs while `gpt-oss-120b` succeeded 8 of 8; `invoke_with_retry()` (`app/llm.py`) retries one unparseable output but cannot rescue a model that fails most of the time. **How:** run your hardest multi-step question 8 times per candidate model and compare.

## ⚠️ Common Mistakes to Avoid

⚠️ **Confusing ReAct with tool calling** — Tool calling is the model's ability to invoke functions. ReAct is the reasoning strategy: alternate between thinking and acting, use each observation to inform the next step. `create_agent` implements ReAct using the model's tool-calling capability.

⚠️ **Not logging the intermediate steps** — When the agent gives a wrong answer, the first question is: which tool was called, and what did it return? Without logging the steps, you can't answer this. Keep `result["messages"]` (or a LangSmith trace) for any agent run you need to debug. Note that RetailOps' `run_router()` returns only the final answer to the caller.

⚠️ **Expecting agents to work without observability** — Agents are non-deterministic. On the same question, different LLM runs may call tools in different orders. LangSmith tracing or message logging is not optional for production agents.

⚠️ **No step limit** — An agent that fails to find a satisfying answer can keep calling tools, incurring significant cost. Know your limit (`recursion_limit`, default 25) and lower it where a handful of steps is enough.

⚠️ **Using ReAct for simple single-tool questions** — If the answer always comes from one specific tool, a simple chain calling that tool is 3× faster and cheaper. Use an agent only when the tool combination is genuinely unknown at design time.

## 🔗 How It Connects to Other Concepts

- **Agents** (doc 21) — ReAct is the internal reasoning loop that agents implement; `create_agent` manages the Thought → Action → Observation cycle
- **Tools & Function Calling** (doc 20) — Function calling is the mechanism; ReAct is the strategy that wraps it in a reasoning loop
- **Router Pattern** (doc 23) — The router sends `route="tools"` questions to the agent; the agent then runs its ReAct loop to answer them
- **LangSmith** (doc 27) — Captures each iteration of the ReAct loop as a trace node; essential for debugging agent behavior
- **Memory** (doc 24) — Memory handles conversation history across turns; ReAct handles reasoning within a single turn

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Thought → Action → Observation loop that lets agents reason before and after each tool call |
| **Why** | Multi-step questions need each tool result to inform the next step — a fixed sequence can't handle this |
| **When** | Any tool-calling agent; especially compound questions where step N depends on step N-1 output |
| **Types** | Tool-calling ReAct via `create_agent` (standard), text-based ReAct (legacy), explicit LangGraph versions (stateful/complex) |
| **Production gotcha** | Cap agent steps (`recursion_limit`); inspect `result["messages"]` or LangSmith traces for debugging; log tool selections and observations |

## ➡️ Next Steps

- **Example file:** `app/chains.py` — RetailOps `build_tool_agent()`; for step-by-step trace inspection see `app/graph/react_agent_graph.py` (`build_react_agent_graph()`) and `app/graph/prebuilt_tools_graph.py` (`build_prebuilt_tools_graph()`)
- **Runnable demo:** see `RUN.md` in this folder (`examples/example_26_prebuilt_toolnode.py`, `examples/example_27_create_react_agent.py`); the agent from doc 21 is in `examples/09_agent_with_tools.py`
- **Next doc:** `../23_router_pattern/README.md` — how the router classifies intent and directs questions to the agent, RAG chain, or general chat
- **Official docs:** https://python.langchain.com/docs/concepts/agents/
