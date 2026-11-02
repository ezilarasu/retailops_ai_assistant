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

✅ Any time you build a tool-calling agent — modern AgentExecutor uses ReAct internally  
✅ Multi-step tasks where step N depends on the output of step N-1  
✅ Debugging agent behavior — understanding the thought/action/observation trace  
✅ When you need to explain why an agent made a particular decision  

❌ Don't use for single-step tool calls — the overhead isn't worth it  
❌ Don't confuse ReAct with tool calling — tool calling is the capability; ReAct is the reasoning strategy  
❌ Don't expect zero latency — each thought-action-observation cycle requires an LLM call  

## 🗂️ Types / Variants

| Pattern | Description | Best For |
|---|---|---|
| **Tool-calling ReAct** | Model uses native function-calling API; framework manages the loop | Production agents with Groq/OpenAI/Anthropic models |
| **Text-based ReAct** | Model formats thoughts/actions as text; parsed by framework | Legacy models without function-calling support |
| **LangGraph ReAct** | Explicit graph nodes for Thought, Action, Observation | Complex agents needing persistence, branching, human-in-the-loop |
| **Single-step** | One tool call with no iteration | Simple lookup questions (not really ReAct, but uses the same tools) |

## 🔀 When to Use Which Type

**Tool-calling ReAct (via `create_tool_calling_agent`)** is the production default. The model outputs a structured tool call (not raw text), which is more reliable and easier to parse. Works with all major providers.

**LangGraph ReAct** is the upgrade path when your agent needs: state that persists across multiple user turns, conditional branching based on tool results, or human approval before taking certain actions.

**Avoid text-based ReAct** for new projects — it relies on prompt-based formatting ("Action: tool_name\nAction Input: args") which is fragile and depends on the model following formatting instructions perfectly.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Adaptive: uses tool results to decide next step | Each iteration = one LLM call; 3 iterations = 3× cost |
| Handles multi-step tasks with unknown sequences | Harder to test than chains — non-deterministic |
| Full reasoning trace for debugging | Can loop without a `max_iterations` guard |
| Model's native function-calling is reliable | Thought traces are internal — users don't see reasoning |
| Works with any `@tool`-decorated function | Poor tool descriptions → wrong tool selection |

## 💻 Basic Example

```python
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

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


# ── Agent with verbose=True to see the ReAct loop ─────────────────────────
tools = [get_low_stock_items, get_store_sales]

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are RetailOps AI. Use tools to answer operational questions."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),  # the model writes its reasoning here
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,       # ← prints each Thought, Action, Observation to stdout
    max_iterations=3,
)

# ── Single-step ReAct ─────────────────────────────────────────────────────
result = agent_executor.invoke({"input": "What items are low in stock at store 101?"})
# Verbose output:
# > Entering new AgentExecutor chain...
# Invoking: `get_low_stock_items` with `{'store_id': '101'}`
# DENIM-4421 (3 units, threshold 20), JACKET-001 (8 units, threshold 25)
# Store 101 has two low-stock items: ...
print(result["output"])

# ── Multi-step ReAct ──────────────────────────────────────────────────────
result = agent_executor.invoke({
    "input": "Which stores have low stock and what did they earn today?"
})
# The agent calls get_low_stock_items("all"), reads the result, then calls
# get_store_sales for each store it found — two iterations before answering
print(result["output"])
```

## 🔧 Real-World Example

RetailOps' production implementation showing how to observe the full ReAct trace, return intermediate steps for debugging, and handle the multi-step compound query pattern.

```python
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# ══════════════════════════════════════════════════════════════════════════
# app/agent.py — RetailOps ReAct agent
#
# The ReAct loop is managed by AgentExecutor internally:
#   1. LLM receives question + available tools → produces tool call
#   2. Framework executes tool → appends result to agent_scratchpad
#   3. LLM receives updated scratchpad → decides: call another tool or answer
#   4. Repeat until final answer or max_iterations reached
# ══════════════════════════════════════════════════════════════════════════

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

from app.tools import get_low_stock_items, get_store_sales, get_open_incidents

TOOLS = [get_low_stock_items, get_store_sales, get_open_incidents]

AGENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are RetailOps AI Assistant.

Available tools:
- get_low_stock_items: inventory below reorder threshold (by store or all stores)
- get_store_sales: revenue and transaction counts for a store
- get_open_incidents: active IT incidents by priority

For compound questions, call tools in sequence — each observation informs the next step.
Do not guess data; always use tool results."""),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])


def build_tool_agent(return_steps: bool = False) -> AgentExecutor:
    """Build the RetailOps ReAct agent.

    Args:
        return_steps: If True, response includes intermediate_steps with
                      the full thought/action/observation trace.
                      Useful for debugging and UI that shows "thinking" state.
    """
    agent = create_tool_calling_agent(llm, TOOLS, AGENT_PROMPT)
    return AgentExecutor(
        agent=agent,
        tools=TOOLS,
        verbose=os.getenv("AGENT_VERBOSE", "false").lower() == "true",
        max_iterations=3,
        handle_parsing_errors=True,
        return_intermediate_steps=return_steps,
    )


def trace_agent_steps(result: dict) -> None:
    """Print the ReAct trace from an agent result with return_intermediate_steps=True.

    Shows exactly which tools were called, what arguments were used,
    and what each tool returned — the full Thought/Action/Observation sequence.
    """
    if "intermediate_steps" not in result:
        print("No intermediate steps — run with return_steps=True")
        return

    for i, (action, observation) in enumerate(result["intermediate_steps"], 1):
        print(f"\n--- Step {i} ---")
        print(f"Tool:  {action.tool}")           # e.g., "get_low_stock_items"
        print(f"Input: {action.tool_input}")      # e.g., {"store_id": "all"}
        print(f"Result: {observation[:200]}")     # first 200 chars of tool output

    print(f"\nFinal answer: {result['output']}")


# ── Example: compound question triggers multi-step ReAct ─────────────────
# agent = build_tool_agent(return_steps=True)
# result = agent.invoke({
#     "input": "Which stores have low stock and what were their sales today?"
# })
# trace_agent_steps(result)
#
# Output:
# --- Step 1 ---
# Tool:  get_low_stock_items
# Input: {'store_id': 'all'}
# Result: Low stock items (3 total): Store 101 | SKU DENIM-4421 ...
#
# --- Step 2 ---
# Tool:  get_store_sales
# Input: {'store_id': '101', 'period': 'today'}
# Result: Store 101 sales (today): Revenue: $12,450.00 ...
#
# Final answer: Stores 101 and 102 have low-stock items...
```

## 🏭 Production Best Practices

1. **Enable `verbose=True` during development** — This prints the complete ReAct trace (tool selections, arguments, observations) to stdout. Without it, debugging wrong agent behavior means guessing. **How:** `AGENT_VERBOSE=true` in `.env`; the agent reads `os.getenv("AGENT_VERBOSE")`.

2. **Use `return_intermediate_steps=True` for debugging sessions** — Gives you the full trace programmatically — each `(AgentAction, observation)` pair. More structured than verbose logging. **How:** `AgentExecutor(return_intermediate_steps=True)` then read `result["intermediate_steps"]`.

3. **Set `max_iterations=3` as default** — Most operational questions need at most 3 tool calls. Setting a limit prevents the agent from looping when it can't find a satisfying answer. **How:** Start at 3; increase only if specific query patterns genuinely need more steps.

4. **Keep tool docstrings specific about when to use them** — The model reads docstrings to decide whether a tool is relevant. Vague docstrings produce wrong tool selection. "Get data" is too vague. "Use when the user asks about low stock, inventory levels, or items to reorder" is concrete. **How:** Include trigger phrases in every docstring.

5. **Trace agent runs in LangSmith** — LangSmith shows the full ReAct loop as a tree: each LLM call, tool invocation, and observation with timing and token counts. Essential for understanding latency and cost in production. **How:** `LANGCHAIN_TRACING_V2=true` in `.env`.

6. **Measure tool call frequency** — If the agent calls the same tool 3 times in one session, either the tool is returning bad data or the docstring isn't clear about what it does. **How:** Track tool names from `result["intermediate_steps"]` and log counts per question.

## ⚠️ Common Mistakes to Avoid

⚠️ **Confusing ReAct with tool calling** — Tool calling is the model's ability to invoke functions. ReAct is the reasoning strategy: alternate between thinking and acting, use each observation to inform the next step. `create_tool_calling_agent` implements ReAct using the model's tool-calling capability.

⚠️ **Not logging the intermediate steps** — When the agent gives a wrong answer, the first question is: which tool was called, and what did it return? Without logging intermediate steps, you can't answer this. Add `return_intermediate_steps=True` to any agent used for debugging.

⚠️ **Expecting agents to work without observability** — Agents are non-deterministic. On the same question, different LLM runs may call tools in different orders. LangSmith or verbose logging is not optional for production agents.

⚠️ **No `max_iterations` guard** — An agent with no iteration limit that fails to find a satisfying answer will keep calling tools until it hits the model's context limit, incurring significant cost. Always set `max_iterations`.

⚠️ **Using ReAct for simple single-tool questions** — If the answer always comes from one specific tool, a simple chain calling that tool is 3× faster and cheaper. Use `AgentExecutor` only when the tool combination is genuinely unknown at design time.

## 🔗 How It Connects to Other Concepts

- **Agents** (doc 21) — ReAct is the internal reasoning loop that agents implement; `AgentExecutor` manages the Thought → Action → Observation cycle
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
| **Types** | Tool-calling ReAct (standard), text-based ReAct (legacy), LangGraph (stateful/complex) |
| **Production gotcha** | Set `max_iterations`; enable verbose/intermediate steps for debugging; log tool selections and observations |

## ➡️ Next Steps

- **Example file:** `app/agent.py` — RetailOps `build_tool_agent()` with `trace_agent_steps()` for debugging
- **Next doc:** `23_router_pattern.md` — how the router classifies intent and directs questions to the agent, RAG chain, or general chat
- **Official docs:** https://python.langchain.com/docs/concepts/agents/
