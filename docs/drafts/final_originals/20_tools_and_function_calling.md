# Tools & Function Calling
> Giving the LLM hands — the ability to query live data and execute actions, not just generate text.

## 📌 What Is It?

A **tool** is a Python function decorated with `@tool` that an LLM can decide to call. **Function calling** is the model capability that lets an LLM select which tool to use and what arguments to pass — automatically, from natural language.

```python
@tool
def get_low_stock_items(store_id: str) -> str:
    """Get items currently below reorder threshold for a given store.
    Use when the user asks about inventory levels or low stock."""
    # reads inventory data and returns a formatted string
    ...
```

The LLM sees the tool name, its docstring, and its parameter schema. From those, it decides: "this question is about inventory → call `get_low_stock_items` with `store_id='101'`". The framework executes the tool and feeds the result back to the LLM, which then generates a natural language answer.

The key distinction: **tools are code** (Python functions that actually run). **Function calling is the LLM's decision mechanism** (how the model selects which tool and what arguments). Together they form the agent tool-use loop.

## ❓ Why Does It Exist?

RAG is great for static knowledge — HR policies, store SOPs, IT runbooks. But some questions need *current* data that changes constantly:

```
"Which items are low in stock?"     → inventory changes hourly
"How many incidents are open?"       → incidents open and close throughout the day
"What were store 102's sales today?" → sales update every minute
```

Loading this data into a vector store would mean it's stale within hours. Tools solve this: instead of indexing the data, the LLM calls a function that reads the current data at query time.

**The RAG vs Tools decision rule:**
- Static knowledge that rarely changes → RAG
- Live operational data that changes frequently → Tools

## ⏰ When Should You Use It?

✅ Real-time data: inventory levels, order statuses, open incidents  
✅ Structured data queries: "which items," "how many," "what total"  
✅ Any data that would be stale if indexed in a vector store  
✅ Actions that need to happen: creating tickets, updating records  

❌ Don't use tools for documentation, policies, or manuals — RAG is better  
❌ Don't make tools do too much — one responsibility per tool  
❌ Don't skip error handling — tool failures should return safe messages, not tracebacks  
❌ Don't trust user-provided tool arguments without validation  

## 🗂️ Types / Variants

| Pattern | How It Works | Best For |
|---|---|---|
| **`@tool` decorator** | Simple function → LangChain tool with auto-generated schema | Most common; clean, readable |
| **`StructuredTool.from_function`** | Explicit schema control | When type annotations need customization |
| **`Tool` (legacy)** | Single string input/output | Simple tools without structured args |
| **`create_tool_calling_agent`** | Agent loop: LLM → tool call → result → LLM | Multi-step workflows with tool use |

## 🔀 When to Use Which Type

**Use `@tool` decorator for everything** — it automatically generates the JSON schema from Python type annotations and uses the docstring as the tool description. Clean, readable, and tested.

**Use `create_tool_calling_agent`** when the LLM needs to call multiple tools in sequence or decide dynamically which combination of tools to use.

**Avoid the legacy `Tool` class** — it only supports a single string input. Use `@tool` with typed parameters instead.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Live data — always current, never stale | Tools can fail — requires robust error handling |
| Structured data access with typed arguments | LLM can call the wrong tool if descriptions are poor |
| Works with the routing pattern (RAG vs tools) | Multi-step tool use adds latency |
| `@tool` automatically generates the schema | Arguments come from LLM — validate before using |
| Enables actions (create ticket, update record) | More complex than simple RAG |

## 💻 Basic Example

```python
import os
import csv
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# ── Define tools with clear docstrings ───────────────────────────────────
@tool
def get_low_stock_items(store_id: str) -> str:
    """Get items that are currently below their reorder threshold for a specific store.
    Use when the user asks about inventory levels, low stock, or items to reorder.
    Args: store_id — the store number (e.g., '101', '102')
    """
    # In production: query inventory database
    # For demo: return mock data
    mock_data = {
        "101": [{"sku": "DENIM-4421", "stock": 3, "threshold": 20},
                {"sku": "JACKET-001", "stock": 8, "threshold": 25}],
        "102": [{"sku": "SHIRT-022", "stock": 2, "threshold": 15}],
    }
    items = mock_data.get(store_id, [])
    if not items:
        return f"No low-stock items found for store {store_id}."
    return "\n".join(f"SKU {i['sku']}: {i['stock']} units (threshold: {i['threshold']})" for i in items)


@tool
def get_open_incidents() -> str:
    """Get a summary of currently open IT incidents.
    Use when the user asks about active incidents, outages, or IT issues."""
    # In production: query incident management system
    return "Open incidents:\n- INC-1001 (P1): Store 102 POS outage — assigned to IT team\n- INC-1015 (P2): Store 101 Wi-Fi intermittent — under investigation"


# ── Create a tool-calling agent ───────────────────────────────────────────
tools = [get_low_stock_items, get_open_incidents]

# Function calling works natively with Groq — the model selects tools by itself
AGENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are RetailOps AI Assistant. Use tools to answer operational questions."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),  # required for tool-calling agents
])

agent = create_tool_calling_agent(llm, tools, AGENT_PROMPT)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# ── Test tool selection ───────────────────────────────────────────────────
result = agent_executor.invoke({"input": "Which items are low in stock at store 101?"})
print(result["output"])
# LLM selects get_low_stock_items, passes store_id="101"

result = agent_executor.invoke({"input": "Are there any open incidents right now?"})
print(result["output"])
# LLM selects get_open_incidents
```

## 🔧 Real-World Example

RetailOps' complete tool suite — three focused tools with error handling, validation, and the tool-calling agent that powers the `tools` route in the router pattern.

```python
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# ══════════════════════════════════════════════════════════════════════════
# app/tools.py — RetailOps operational data tools
#
# These tools handle questions that need CURRENT data:
# - Inventory levels (change hourly)
# - Sales data (change continuously)
# - Incident status (open/closed throughout day)
#
# The router (app/router.py) directs "tools" questions here.
# RAG handles everything else (static knowledge: policies, SOPs, runbooks).
# ══════════════════════════════════════════════════════════════════════════

DATA_DIR = os.getenv("DATA_DIR", "data/")


def _safe_read_csv(filename: str) -> list[dict]:
    """Read a CSV file safely, returning empty list on failure."""
    import csv
    path = Path(DATA_DIR) / filename
    if not path.exists():
        return []
    try:
        with open(path, encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


@tool
def get_low_stock_items(store_id: str = "all") -> str:
    """Get inventory items that are below their reorder threshold.

    Use when users ask about:
    - Low stock or inventory levels
    - Which items need to be reordered
    - Inventory alerts for a specific store

    Args:
        store_id: Store number to filter by (e.g., '101'). Use 'all' for all stores.
    """
    rows = _safe_read_csv("inventory.csv")
    if not rows:
        return "Unable to retrieve inventory data. Please check the data directory."

    # Filter to low-stock items
    low_stock = [
        r for r in rows
        if int(r.get("stock_level", 0)) < int(r.get("reorder_threshold", 0))
        and (store_id == "all" or r.get("store_id") == store_id)
    ]

    if not low_stock:
        return f"No low-stock items found{' for store ' + store_id if store_id != 'all' else ''}."

    lines = [f"Low stock items ({len(low_stock)} total):"]
    for item in low_stock[:10]:  # limit to 10 to avoid token overflow
        lines.append(
            f"  Store {item['store_id']} | SKU {item['sku']} | "
            f"{item['stock_level']} units (reorder at {item['reorder_threshold']})"
        )
    if len(low_stock) > 10:
        lines.append(f"  ... and {len(low_stock) - 10} more items")

    return "\n".join(lines)


@tool
def get_store_sales(store_id: str, period: str = "today") -> str:
    """Get sales summary for a specific store.

    Use when users ask about:
    - Store revenue or sales figures
    - How a store is performing
    - Sales data for a specific date or period

    Args:
        store_id: Store number (e.g., '101', '102')
        period: Time period — 'today', 'week', or 'month'
    """
    rows = _safe_read_csv("sales.csv")
    if not rows:
        return "Unable to retrieve sales data. Please check the data directory."

    store_rows = [r for r in rows if r.get("store_id") == store_id and r.get("period") == period]

    if not store_rows:
        return f"No sales data found for store {store_id} ({period})."

    row = store_rows[0]
    return (
        f"Store {store_id} sales ({period}):\n"
        f"  Revenue: ${float(row.get('revenue', 0)):,.2f}\n"
        f"  Transactions: {row.get('transactions', 'N/A')}\n"
        f"  Avg basket: ${float(row.get('avg_basket', 0)):,.2f}"
    )


@tool
def get_open_incidents(priority: str = "all") -> str:
    """Get currently open IT incidents.

    Use when users ask about:
    - Active or open incidents
    - Current outages or IT issues
    - P1, P2, or P3 incident status

    Args:
        priority: Filter by priority — 'P1', 'P2', 'P3', or 'all'
    """
    rows = _safe_read_csv("incidents.csv")
    if not rows:
        return "Unable to retrieve incident data. Please check the data directory."

    open_incidents = [
        r for r in rows
        if r.get("status", "").lower() == "open"
        and (priority == "all" or r.get("priority") == priority)
    ]

    if not open_incidents:
        return f"No open incidents{' with priority ' + priority if priority != 'all' else ''}."

    lines = [f"Open incidents ({len(open_incidents)} total):"]
    for inc in open_incidents:
        lines.append(
            f"  [{inc['priority']}] {inc['incident_id']}: {inc['description']} "
            f"(Store {inc.get('store_id', 'N/A')})"
        )
    return "\n".join(lines)


# ── Tool-calling agent ────────────────────────────────────────────────────
TOOLS = [get_low_stock_items, get_store_sales, get_open_incidents]

AGENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are RetailOps AI Assistant.
You have access to tools that query live operational data.
Use tools to answer questions about inventory, sales, and incidents.
Always report the actual data returned by the tool — do not make up numbers."""),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])


def build_tool_agent() -> AgentExecutor:
    """Build the tool-calling agent for operational data queries.

    Used by the router when question route = "tools".
    Returns AgentExecutor — invoke({"input": question}) → {"output": str}
    """
    agent = create_tool_calling_agent(llm, TOOLS, AGENT_PROMPT)
    return AgentExecutor(
        agent=agent,
        tools=TOOLS,
        verbose=bool(os.getenv("AGENT_VERBOSE", "false").lower() == "true"),
        max_iterations=3,    # prevent infinite tool loops
        handle_parsing_errors=True,  # return error message instead of raising
    )
```

## 🏭 Production Best Practices

1. **Write tool docstrings as instructions to the LLM** — The docstring is the LLM's only guide for when to use the tool. "Get inventory data" is too vague. "Use when the user asks about inventory levels, low stock, or items to reorder" is concrete and guides correct tool selection. **How:** Include example trigger phrases in the docstring.

2. **One responsibility per tool** — A tool that fetches inventory AND creates tickets is hard to test, debug, and the LLM may call it at the wrong time. Small focused tools are more reliably selected. **How:** If a tool does more than one thing, split it.

3. **Return safe error messages instead of raising exceptions** — If `inventory.csv` doesn't exist, returning `"Unable to retrieve inventory data"` is better than crashing the agent. The LLM can include this message in its answer. **How:** Wrap tool bodies in `try/except`.

4. **Validate arguments before using them** — The LLM generates tool arguments from natural language. `store_id="Store 101"` vs `store_id="101"` are both plausible and one will fail a lookup. Normalize and validate. **How:** `store_id = store_id.strip().lstrip("store ").lstrip("Store ")`.

5. **Log every tool call with its arguments and result** — When the agent gives a wrong answer, you need to know which tool was called and what it returned. **How:** Set `verbose=True` during development; use LangSmith in production to trace every tool invocation.

6. **Set `max_iterations`** — Tool-calling agents can loop. An agent that calls `get_store_sales` 10 times trying to get a better result will incur significant LLM costs. **How:** `AgentExecutor(max_iterations=3)`.

## ⚠️ Common Mistakes to Avoid

⚠️ **Using RAG for live operational data** — Indexing inventory or incidents in a vector store means the data is immediately stale. Every inventory change requires a reindex. Use tools that query live data instead.

⚠️ **Poor tool docstrings** — If the docstring doesn't clearly explain when to use the tool, the LLM will call the wrong one or none at all. The docstring is the most important part of a tool definition.

⚠️ **Huge tools** — A single tool that takes 15 parameters, handles 5 different operations, and returns 500 lines of data is hard for the LLM to use correctly. Break it up.

⚠️ **No error handling** — Tools fail. Files are missing, APIs time out, data has unexpected formats. Every tool must handle failures gracefully and return a human-readable error string.

⚠️ **Confusing tools with function calling** — A *tool* is the Python function (the code that runs). *Function calling* is the LLM's mechanism for deciding which tool to use. You write tools; the model does function calling automatically.

## 🔗 How It Connects to Other Concepts

- **Router Pattern** (doc 23) — The router decides `route="tools"` for operational questions; the tool agent handles those questions while RAG handles policy questions
- **Structured Output** (doc 08) — `with_structured_output()` uses function calling under the hood; both mechanisms use the model's tool-use capability
- **Agents** (doc 21) — The tool-calling agent is one type of agent; tools are what all agents use to interact with the world
- **Document Loaders** (doc 09) — Loaders are the RAG equivalent of tools: both connect the LLM to external data, but loaders work at index time and tools work at query time

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | `@tool`-decorated Python functions the LLM can call, with function calling as the model's selection mechanism |
| **Why** | Live operational data (inventory, incidents, sales) is too dynamic for RAG — tools query it in real time |
| **When** | Data that changes frequently; structured queries; actions like creating tickets |
| **Types** | `@tool` decorator (standard), `StructuredTool` (explicit schema), `create_tool_calling_agent` (multi-tool agents) |
| **Production gotcha** | Write docstrings as LLM instructions; one responsibility per tool; always handle errors; set `max_iterations` on agents |

## ➡️ Next Steps

- **Example file:** `app/tools.py` — RetailOps `get_low_stock_items()`, `get_store_sales()`, `get_open_incidents()`, `build_tool_agent()`
- **Next doc:** `21_agents.md` — how agents combine tools, reasoning, and memory to handle complex multi-step tasks
- **Official docs:** https://python.langchain.com/docs/concepts/tools/
