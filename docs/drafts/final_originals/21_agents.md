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

In LangChain, agents are built with `create_tool_calling_agent` + `AgentExecutor`. The LLM sees the available tools and decides which to call. The framework runs the tool and feeds the result back to the LLM, which then decides whether to call another tool or produce a final answer.

## ❓ Why Does It Exist?

Some questions require multiple tools in an order that can't be predicted in advance:

```
"Which stores have low inventory and what were their sales today?"
→ Need: get_low_stock_items() + get_store_sales()
→ Order depends on which stores come back from inventory tool
```

A chain can't handle this — you'd need to hardcode every possible combination of tools and branching logic. An agent handles it dynamically: it calls inventory, sees "stores 101 and 102", then decides to call sales for each.

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
| **Tool-calling agent** | LLM selects tools via native function-calling API | Standard multi-tool agents; works with Groq, OpenAI, Anthropic |
| **ReAct agent** | Explicit Thought → Action → Observation loop in prompt | Older models without native function calling |
| **Structured chat agent** | Tools with structured schemas, JSON output | Complex tool arguments |
| **LangGraph agent** | Stateful graph with explicit nodes and edges | Complex multi-step workflows needing persistence |

## 🔀 When to Use Which Type

**Use `create_tool_calling_agent`** for production — it uses the model's native function-calling capability, which is more reliable than prompting the model to format tool calls as text. Works with Groq, OpenAI, Anthropic models.

**Use LangGraph** when the agent needs persistent state across turns, complex branching logic, or human-in-the-loop approval steps. It's the right tool when `AgentExecutor` starts feeling limiting.

**Avoid the legacy `initialize_agent`** — it's deprecated. The current API is `create_tool_calling_agent` + `AgentExecutor`.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Handles tasks where path is unknown in advance | More expensive — each tool call requires an LLM decision |
| Adapts to different inputs dynamically | More latency — sequential reasoning steps add up |
| Can call multiple tools in the right order | Harder to test — behavior is non-deterministic |
| Works with any `@tool`-decorated function | Can loop — requires `max_iterations` guard |
| Observability via LangSmith traces per step | Poor tool descriptions cause wrong tool selection |

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
tools = [get_inventory, get_sales]

# agent_scratchpad is required — it's where the LLM writes its reasoning
AGENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are RetailOps AI. Use tools to answer operational questions."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),  # required for tool-calling agents
])

agent = create_tool_calling_agent(llm, tools, AGENT_PROMPT)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,       # prints the reasoning loop to stdout
    max_iterations=3,   # prevents infinite loops
)

# ── Invoke ────────────────────────────────────────────────────────────────
result = agent_executor.invoke({"input": "What items are low in stock at store 101?"})
print(result["output"])
# Agent selects get_inventory with store_id="101"

result = agent_executor.invoke({"input": "Show inventory and sales for store 102."})
print(result["output"])
# Agent calls get_inventory("102"), observes result, then calls get_sales("102")
```

## 🔧 Real-World Example

RetailOps' production agent — wraps the three operational tools with error handling, configurable verbosity, and the `build_tool_agent()` factory used by the router.

```python
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# ══════════════════════════════════════════════════════════════════════════
# app/agent.py — RetailOps tool-calling agent
#
# This agent handles the "tools" route from the router.
# It receives operational questions and decides which combination of
# inventory, sales, and incident tools to call.
# ══════════════════════════════════════════════════════════════════════════

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# Import the actual tool implementations from app/tools.py
from app.tools import get_low_stock_items, get_store_sales, get_open_incidents

TOOLS = [get_low_stock_items, get_store_sales, get_open_incidents]

AGENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are RetailOps AI Assistant — an operational data assistant.

You have tools that query live data:
- get_low_stock_items: inventory levels by store
- get_store_sales: revenue and transaction counts
- get_open_incidents: active IT incidents by priority

Use the appropriate tool(s) to answer the question.
If a question requires data from multiple tools, call them in sequence.
Always base your answer on the tool results — do not make up data."""),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])


def build_tool_agent() -> AgentExecutor:
    """Build the RetailOps tool-calling agent.

    Called by the router when route = "tools".
    Returns AgentExecutor — call invoke({"input": question}) → {"output": str}

    The agent loop:
      1. LLM reads the question and available tools
      2. LLM selects a tool and provides arguments
      3. Framework executes the tool
      4. Result (observation) is fed back to LLM
      5. LLM decides: call another tool, or produce final answer
    """
    agent = create_tool_calling_agent(llm, TOOLS, AGENT_PROMPT)
    return AgentExecutor(
        agent=agent,
        tools=TOOLS,
        verbose=bool(os.getenv("AGENT_VERBOSE", "false").lower() == "true"),
        max_iterations=3,          # prevent infinite tool loops
        handle_parsing_errors=True, # return error string instead of raising
        return_intermediate_steps=bool(
            os.getenv("AGENT_RETURN_STEPS", "false").lower() == "true"
        ),
    )


# ── Multi-tool example: how the agent handles compound questions ──────────
#
# Question: "Which stores have low stock and what were their sales today?"
#
# Iteration 1:
#   Thought: I need inventory data first.
#   Action: get_low_stock_items(store_id="all")
#   Observation: "Low stock items (3 total): Store 101 | SKU DENIM-4421 ..."
#
# Iteration 2:
#   Thought: Store 101 has low stock. I need its sales data.
#   Action: get_store_sales(store_id="101", period="today")
#   Observation: "Store 101 sales (today): Revenue: $12,450.00 ..."
#
# Final answer: "Stores 101 and 102 have low-stock items. Store 101's
#   revenue today was $12,450 (88 transactions)..."
```

## 🏭 Production Best Practices

1. **Set `max_iterations=3`** — Without a limit, an agent can loop indefinitely trying to get a better result. Three iterations handles almost all real-world tool sequences while preventing runaway costs. **How:** `AgentExecutor(max_iterations=3)`.

2. **Write agent prompts that explain each tool's purpose** — The agent prompt is the agent's briefing document. If it doesn't list the tools and their intended use, the LLM will under-use or misuse them. **How:** Include a bullet for each tool: `- get_low_stock_items: inventory levels by store`.

3. **Use `handle_parsing_errors=True`** — When the LLM produces a malformed tool call, this returns a safe error string instead of raising an exception that crashes the agent. **How:** `AgentExecutor(handle_parsing_errors=True)`.

4. **Log intermediate steps in development** — `return_intermediate_steps=True` gives you the full thought/action/observation trace. Without it, debugging wrong agent behavior is guesswork. **How:** `AgentExecutor(return_intermediate_steps=True)` during development; disable in production to reduce response payload size.

5. **Don't use agents for simple single-tool questions** — If the answer always comes from one tool, a simple chain calling that tool is faster and cheaper. Agents shine when the tool combination is unknown at design time. **How:** Use `AgentExecutor` only in the `tools` route; use direct LCEL chains elsewhere.

6. **Trace every agent run with LangSmith** — Agent behavior is non-deterministic. LangSmith captures the full thought/action/observation loop, which is essential for diagnosing wrong tool selection or incorrect answers. **How:** `LANGCHAIN_TRACING_V2=true` in `.env`.

## ⚠️ Common Mistakes to Avoid

⚠️ **Using agents for everything** — Agents add latency and cost. A simple question like "translate this text" does not need an agent. Use chains for fixed workflows; reserve agents for tasks that require dynamic tool selection.

⚠️ **No `max_iterations` limit** — An agent that calls `get_store_sales` 10 times trying to get a satisfying answer will incur significant API costs. Always set a limit.

⚠️ **Confusing agents with tools** — A *tool* is a Python function (a capability). An *agent* is the decision-making system that chooses which tools to call. You write tools; the agent uses them.

⚠️ **Confusing agents with routers** — A *router* picks which workflow to run (RAG, tools, chat). An *agent* picks which *tools* to call within the tools workflow. They operate at different levels of the architecture.

⚠️ **No observability** — When an agent gives a wrong answer, you need to know exactly which tools were called, with what arguments, and what they returned. Without `verbose=True` or LangSmith tracing, debugging becomes very difficult.

## 🔗 How It Connects to Other Concepts

- **Tools & Function Calling** (doc 20) — Agents use `@tool`-decorated functions; function calling is the model mechanism agents use to select tools
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
| **Types** | Tool-calling agent (standard), ReAct (older models), LangGraph (stateful/complex) |
| **Production gotcha** | Set `max_iterations`; write tool descriptions in agent prompt; don't use agents for simple tasks |

## ➡️ Next Steps

- **Example file:** `app/agent.py` — RetailOps `build_tool_agent()` with `get_low_stock_items`, `get_store_sales`, `get_open_incidents`
- **Next doc:** `22_react_pattern.md` — the Thought → Action → Observation reasoning loop that agents use internally
- **Official docs:** https://python.langchain.com/docs/concepts/agents/
