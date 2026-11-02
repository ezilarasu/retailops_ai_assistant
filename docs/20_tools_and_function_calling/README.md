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
| **`create_agent`** (LangChain 1.x) | Agent loop: LLM → tool call → result → LLM, repeated until the model answers | Multi-step workflows with tool use — this is what RetailOps uses |
| **`create_tool_calling_agent` + `AgentExecutor`** (legacy) | The older way to build the same loop | Reading older tutorials and code; prefer `create_agent` for new work |

## 🔀 When to Use Which Type

**Use `@tool` decorator for everything** — it automatically generates the JSON schema from Python type annotations and uses the docstring as the tool description. Clean, readable, and tested.

**Use `create_agent`** when the LLM needs to call multiple tools in sequence or decide dynamically which combination of tools to use. (You will see `create_tool_calling_agent` + `AgentExecutor` in older tutorials — it is the legacy form of the same idea. See doc 21.)

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
# A self-contained demo with mock data, so you can see tool selection in isolation.
# (RetailOps' real tools read data/ — see the Real-World Example below.)
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain.agents import create_agent   # LangChain 1.x agent builder

load_dotenv()

# RetailOps' default model (the app reads it from LLM_MODEL in .env); GROQ_API_KEY must be set in .env
llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)

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

# Function calling works natively with Groq — the model selects tools by itself.
# create_agent needs only the model, the tools, and a system prompt.
agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="You are RetailOps AI Assistant. Use tools to answer operational questions.",
)

# ── Test tool selection ───────────────────────────────────────────────────
# The agent takes a list of messages and returns the whole conversation,
# so the final answer is the content of the last message.
result = agent.invoke({"messages": [{"role": "user", "content": "Which items are low in stock at store 101?"}]})
print(result["messages"][-1].content)
# LLM selects get_low_stock_items, passes store_id="101"

result = agent.invoke({"messages": [{"role": "user", "content": "Are there any open incidents right now?"}]})
print(result["messages"][-1].content)
# LLM selects get_open_incidents
```

## 🔧 Real-World Example

RetailOps' real tool suite (`app/tools.py`) — three focused tools that read the files in `data/` and return safe messages on failure — plus the agent built from them (`build_tool_agent()` in `app/chains.py`) that powers the `tools` route in the router pattern.

```python
# ══════════════════════════════════════════════════════════════════════════
# app/tools.py — RetailOps operational data tools (shown as in the repo,
# lightly trimmed). Run from the repository root: DATA_DIR is the relative
# path "data".
#
# These tools handle questions that need CURRENT data (inventory, vendors,
# incidents). The router (app/router.py) sends "tools" questions to the agent
# that uses them; RAG handles static knowledge (policies, SOPs, runbooks).
# ══════════════════════════════════════════════════════════════════════════
import json
from pathlib import Path

import pandas as pd
from langchain_core.tools import tool

DATA_DIR = Path("data")


@tool
def get_low_stock_items(store_id: str) -> str:
    """
    Get low-stock inventory items for a store.

    A low-stock item is one where on_hand is less than reorder_point.
    Requires:
    - store_id

    If the user does not provide a store_id, ask the user which store they want to check.
    """
    try:
        df = pd.read_csv(DATA_DIR / "inventory.csv")
        store_df = df[df["store_id"].astype(str) == str(store_id)]
        low_stock_df = store_df[store_df["on_hand"] < store_df["reorder_point"]]

        if low_stock_df.empty:
            return f"No low-stock items found for store {store_id}."

        return json.dumps(low_stock_df.to_dict(orient="records"), indent=2)
    except Exception:
        # Safe message instead of a traceback — the LLM can relay this to the user
        return f"Unable to retrieve low-stock items for store {store_id}."


@tool
def get_vendor_for_sku(sku: str) -> str:
    """
    Get vendor contact details for a product SKU.
    """
    try:
        inventory_df = pd.read_csv(DATA_DIR / "inventory.csv")
        vendors_df = pd.read_csv(DATA_DIR / "vendors.csv")

        sku_rows = inventory_df[inventory_df["sku"].str.upper() == sku.upper()]
        if sku_rows.empty:
            return f"No inventory item found for SKU {sku}."

        vendor_id = sku_rows.iloc[0]["vendor_id"]
        vendor_rows = vendors_df[vendors_df["vendor_id"] == vendor_id]
        if vendor_rows.empty:
            return f"No vendor found for vendor_id {vendor_id}."

        return json.dumps(vendor_rows.iloc[0].to_dict(), indent=2)
    except Exception:
        return f"Unable to retrieve vendor details for SKU {sku}."


@tool
def get_open_incidents(store_id: str) -> str:
    """
    Get open or in-progress incidents for a store.
    """
    try:
        with open(DATA_DIR / "incidents.json", "r") as file:
            incidents = json.load(file)

        results = [
            incident for incident in incidents
            if str(incident["store_id"]) == str(store_id)
            and incident["status"] in ["open", "in_progress"]
        ]
        if not results:
            return f"No open or in-progress incidents found for store {store_id}."

        return json.dumps(results, indent=2)
    except Exception:
        return f"Unable to retrieve open or in-progress incidents for store {store_id}."


# ══════════════════════════════════════════════════════════════════════════
# app/chains.py — build_tool_agent() lives here, not in app/tools.py.
# It wires the tools above into an agent with create_agent (LangChain 1.x).
# ══════════════════════════════════════════════════════════════════════════
from langchain.agents import create_agent
from app.config import settings
from app.llm import get_llm  # ChatGroq; get_llm(model) picks the model, GROQ_API_KEY comes from .env


def build_tool_agent():
    tools = [get_low_stock_items, get_vendor_for_sku, get_open_incidents]

    return create_agent(
        # The tool agent has its own model setting (TOOLS_LLM_MODEL, default openai/gpt-oss-120b)
        model=get_llm(settings.tools_llm_model),
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


# How the router calls it (app/router.py, "tools" route). The last 6 messages of the
# conversation go in first, so a follow-up like "What about store 310?" makes sense:
#   result = container.tool_agent.invoke({
#       "messages": [
#           *history[-6:],                                # earlier turns of this session
#           {"role": "user", "content": question},
#       ]
#   })
#   answer = result["messages"][-1].content   # the last message is the final answer
```

Try the tools on their own (no LLM, no API key) with `examples/08_tools_structured_data.py`, or the agent with `examples/09_agent_with_tools.py`.

## 🏭 Production Best Practices

1. **Write tool docstrings as instructions to the LLM** — The docstring is the LLM's only guide for when to use the tool. "Get inventory data" is too vague. "Use when the user asks about inventory levels, low stock, or items to reorder" is concrete and guides correct tool selection. **How:** Include example trigger phrases in the docstring.

2. **One responsibility per tool** — A tool that fetches inventory AND creates tickets is hard to test, debug, and the LLM may call it at the wrong time. Small focused tools are more reliably selected. **How:** If a tool does more than one thing, split it.

3. **Return safe error messages instead of raising exceptions** — If `inventory.csv` doesn't exist, returning `"Unable to retrieve inventory data"` is better than crashing the agent. The LLM can include this message in its answer. **How:** Wrap tool bodies in `try/except`.

4. **Validate arguments before using them** — The LLM generates tool arguments from natural language. `store_id="Store 101"` vs `store_id="101"` are both plausible and one will fail a lookup. Normalize and validate. **How:** `store_id = store_id.strip().lower().removeprefix("store ").strip()`. (RetailOps' tools currently compare `str(store_id)` as-is, so `"Store 101"` would miss — a good first improvement.)

5. **Log every tool call with its arguments and result** — When the agent gives a wrong answer, you need to know which tool was called and what it returned. **How:** During development, print the agent's messages (`for m in result["messages"]: print(m.type, m.content)` — tool calls and tool results are in there; see doc 22). In production, use LangSmith to trace every tool invocation.

6. **Cap the number of agent steps** — Tool-calling agents can loop. An agent that calls `get_vendor_for_sku` 10 times trying to get a better result will incur significant LLM costs. **How:** agents built with `create_agent` run on LangGraph, which stops after a step limit (`recursion_limit`, 25 by default). Lower it per call: `agent.invoke(inputs, config={"recursion_limit": 8})`. (The legacy `AgentExecutor` used `max_iterations=3` for the same purpose.) RetailOps relies on the default today and does not set its own limit.

7. **Choose the model for tool calling deliberately, and retry only what a retry can fix** — Not every model is equally good at producing valid tool calls. In two measurements of the question "Which items are low stock in store 102, and who is the vendor for each?", `openai/gpt-oss-20b` failed with `output_parse_failed` in 6 of 8 and 8 of 8 runs, while `openai/gpt-oss-120b` succeeded 8 of 8. RetailOps therefore gives the tool agent its own model: `settings.tools_llm_model` (`TOOLS_LLM_MODEL`, default `openai/gpt-oss-120b`; an empty value falls back to `LLM_MODEL`), while routing, chat and RAG keep the faster `LLM_MODEL`. `invoke_with_retry()` in `app/llm.py` retries once when the model's output cannot be parsed, which rescues an occasional hiccup, but it cannot fix a model that fails most of the time. **How:** measure your own multi-tool questions on each candidate model (8 runs each is enough to see the difference) before you pick.

## ⚠️ Common Mistakes to Avoid

⚠️ **Using RAG for live operational data** — Indexing inventory or incidents in a vector store means the data is immediately stale. Every inventory change requires a reindex. Use tools that query live data instead.

⚠️ **Poor tool docstrings** — If the docstring doesn't clearly explain when to use the tool, the LLM will call the wrong one or none at all. The docstring is the most important part of a tool definition.

⚠️ **Huge tools** — A single tool that takes 15 parameters, handles 5 different operations, and returns 500 lines of data is hard for the LLM to use correctly. Break it up.

⚠️ **No error handling** — Tools fail. Files are missing, APIs time out, data has unexpected formats. Every tool must handle failures gracefully and return a human-readable error string.

⚠️ **Confusing tools with function calling** — A *tool* is the Python function (the code that runs). *Function calling* is the LLM's mechanism for deciding which tool to use. You write tools; the model does function calling automatically.

## 🔗 How It Connects to Other Concepts

- **Router Pattern** (doc 23) — The router decides `route="tools"` for operational questions; the tool agent handles those questions while RAG handles policy questions
- **Structured Output** (doc 08) — `with_structured_output()` can be implemented with function calling (depending on the model and method), so both mechanisms rely on the model's tool-use capability
- **Agents** (doc 21) — The tool-calling agent is one type of agent; tools are what all agents use to interact with the world
- **Document Loaders** (doc 09) — Loaders are the RAG equivalent of tools: both connect the LLM to external data, but loaders work at index time and tools work at query time

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | `@tool`-decorated Python functions the LLM can call, with function calling as the model's selection mechanism |
| **Why** | Live operational data (inventory, incidents, sales) is too dynamic for RAG — tools query it in real time |
| **When** | Data that changes frequently; structured queries; actions like creating tickets |
| **Types** | `@tool` decorator (standard), `StructuredTool` (explicit schema), `create_agent` (multi-tool agents; `create_tool_calling_agent` + `AgentExecutor` is the legacy form) |
| **Production gotcha** | Write docstrings as LLM instructions; one responsibility per tool; always handle errors; cap agent steps (`recursion_limit`) |

## ➡️ Next Steps

- **Example file:** `app/tools.py` — RetailOps `get_low_stock_items()`, `get_vendor_for_sku()`, `get_open_incidents()`; `build_tool_agent()` lives in `app/chains.py`
- **Runnable demo:** see `RUN.md` in this folder (`examples/08_tools_structured_data.py`)
- **Next doc:** `../21_agents/README.md` — how agents combine tools, reasoning, and memory to handle complex multi-step tasks
- **Official docs:** https://python.langchain.com/docs/concepts/tools/
