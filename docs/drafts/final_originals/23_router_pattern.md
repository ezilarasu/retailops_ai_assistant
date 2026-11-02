# Router Pattern
> The traffic controller that sends each question to the right workflow — RAG, tools, or general chat.

## 📌 What Is It?

A **router** is a component that classifies the intent of an incoming question and directs it to the appropriate processing workflow. Instead of running every question through the same pipeline, the router decides upfront which path will handle it best.

RetailOps uses three routes:

```
Question
  ↓
Router (LLM classifies intent → RouteDecision)
  ├── "general"  → Direct LLM response  (no retrieval, no tools)
  ├── "rag"      → RAG chain            (retrieve from knowledge base)
  └── "tools"    → Tool-calling agent   (query live operational data)
```

Examples of how questions map to routes:

```
"Who are you?"                  → general  (no data needed)
"What is the return policy?"    → rag      (answer in documents)
"Which items are low in stock?" → tools    (live inventory data)
"Hello, how are you?"           → general
"What does P1 mean?"            → rag
"Show store 101 sales today."   → tools
```

The router uses `with_structured_output(RouteDecision)` to classify reliably — it returns a typed `route` field rather than a free-text string that needs parsing.

## ❓ Why Does It Exist?

Without routing, every question goes through the same expensive pipeline:

```
Without routing:
  "Hello" → retrieve documents → rerank → LLM → "Hello!"
  Cost: 3 LLM calls + vector search + cross-encoder
  
With routing:
  "Hello" → router → general → LLM → "Hello!"
  Cost: 1 LLM call (router) + 1 LLM call (answer) = 2 LLM calls
```

Routing also improves accuracy: questions about live inventory should never go to RAG (the data would be stale), and policy questions should never go to the tool agent (the agent might hallucinate if it can't find the answer in the inventory/sales data).

**The three-workflow separation matches the three types of enterprise questions:**
- Knowledge questions → documents change slowly → RAG
- Operational questions → data changes constantly → tools
- Conversational questions → no data needed → direct LLM

## ⏰ When Should You Use It?

✅ When your application handles multiple categories of questions  
✅ When some questions need RAG and others need live data  
✅ When you want to avoid unnecessary retrieval for simple questions  
✅ Any production AI assistant with more than one capability  

❌ Don't route if your app only does one thing (pure RAG, pure chat)  
❌ Don't create too many routes — 3–5 is a sweet spot; more creates overlapping categories  
❌ Don't use string parsing to extract the route — use `with_structured_output` for reliability  

## 🗂️ Types / Variants

| Approach | How It Works | Best For |
|---|---|---|
| **LLM router** | LLM classifies intent via structured output | General-purpose; handles nuanced phrasing |
| **Keyword/rule-based router** | Check for keywords like "sales", "stock", "policy" | High-speed routing for predictable input patterns |
| **Hybrid router** | Rules first; LLM fallback for ambiguous cases | Production systems that need speed + accuracy |
| **Embedding similarity router** | Embed question; compare to route exemplars | Useful when you have labeled examples of each route |

## 🔀 When to Use Which Type

**Use the LLM router** (RetailOps approach) for production assistants with diverse user inputs. Natural language questions are phrased unpredictably; LLM classification handles edge cases that rules miss. The latency cost (~100ms) is low relative to the downstream workflows it routes to.

**Use a hybrid router** at scale: pre-filter obvious cases with rules (e.g., greetings always → general), then use the LLM only for ambiguous questions. This reduces LLM call frequency by 30–50% in typical enterprise chat.

**Avoid pure keyword matching** for production — "what are the policies around low stock replenishment?" matches "low stock" (tools keyword) but should route to RAG (policy document). Keywords produce routing errors on compound questions.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Lower cost — only runs the needed workflow | Adds one LLM call per request for routing |
| Lower latency — "Hello" skips the full RAG pipeline | Wrong routing is invisible — hard to detect without eval |
| Higher accuracy — each workflow is optimized for its task | More routes = more complexity to maintain and test |
| Structured output makes routing reliable and testable | Ambiguous questions can route incorrectly |
| Clean separation — each workflow can be tuned independently | Need to evaluate routing quality separately from answer quality |

## 💻 Basic Example

```python
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# ── RouteDecision schema ──────────────────────────────────────────────────
class RouteDecision(BaseModel):
    route: str = Field(
        description="The route to take: 'general', 'rag', or 'tools'",
    )
    reason: str = Field(
        description="Brief explanation of why this route was chosen"
    )

# ── Router prompt ─────────────────────────────────────────────────────────
ROUTER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a router for the RetailOps AI Assistant.
Classify the user's question into exactly one of these routes:

- general: greetings, general knowledge, questions about yourself, coding help
- rag: questions about policies, procedures, SOPs, incident definitions, HR rules
- tools: questions about current inventory, live sales data, or open incidents

Return the route and a brief reason."""),
    ("human", "Question: {question}"),
])

# ── Router chain ──────────────────────────────────────────────────────────
router_chain = ROUTER_PROMPT | llm.with_structured_output(RouteDecision)

# ── Test routing ──────────────────────────────────────────────────────────
test_questions = [
    "Hello, how are you?",
    "What is the return policy for damaged items?",
    "Which items are low in stock at store 101?",
    "What does P1 mean?",
    "Show me today's sales for store 102.",
]

for question in test_questions:
    decision = router_chain.invoke({"question": question})
    print(f"[{decision.route:8s}] {question}")
    print(f"         Reason: {decision.reason}\n")

# Output:
# [general ] Hello, how are you?
# [rag     ] What is the return policy for damaged items?
# [tools   ] Which items are low in stock at store 101?
# [rag     ] What does P1 mean?
# [tools   ] Show me today's sales for store 102.
```

## 🔧 Real-World Example

RetailOps' complete router — the `route_question()` function used by the main application to direct each question to the right workflow.

```python
import os
import logging
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Literal

load_dotenv()

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════
# app/router.py — RetailOps intent router
#
# Called by app/services.py before every question.
# Returns RouteDecision(route, reason).
# The route field drives which workflow runs:
#   "general" → direct LLM call
#   "rag"     → build_conversational_rag_chain()
#   "tools"   → build_tool_agent()
# ══════════════════════════════════════════════════════════════════════════

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)


class RouteDecision(BaseModel):
    """Structured routing decision returned by the router."""

    route: Literal["general", "rag", "tools"] = Field(
        description="Which workflow should handle this question"
    )
    reason: str = Field(
        description="One-sentence explanation of the routing decision"
    )


ROUTER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a router for RetailOps AI Assistant — an assistant for retail store employees.

Classify each question into exactly one route:

**general**
  Use for: greetings, meta questions ("who are you?"), general Python/coding help,
           questions unrelated to retail operations
  Examples: "Hello", "What can you help with?", "Explain Python lists"

**rag**
  Use for: questions answerable from company documents, policies, SOPs, runbooks
  Examples: "What is the return policy?", "What does P1 mean?",
            "How many vacation days do employees get?", "What is the escalation process?"

**tools**
  Use for: questions requiring CURRENT operational data (changes hourly/daily)
  Examples: "Which items are low in stock?", "Show store 102 sales today",
            "Are there any open incidents?", "What's the current inventory for SKU DENIM-4421?"

Key decision rule:
- If the answer lives in a document (policy, SOP, runbook) → rag
- If the answer requires querying live data (inventory, sales, incidents) → tools
- Everything else → general"""),
    ("human", "{question}"),
])

# Build router chain once at module load time
_router_chain = ROUTER_PROMPT | llm.with_structured_output(RouteDecision)


def route_question(question: str) -> RouteDecision:
    """Classify a question and return the appropriate route.

    Args:
        question: The user's raw input text

    Returns:
        RouteDecision with route ("general" | "rag" | "tools") and reason

    Always returns a valid RouteDecision — falls back to "general" on error.
    """
    try:
        decision = _router_chain.invoke({"question": question})
        logger.info(
            "Routing decision",
            extra={"route": decision.route, "reason": decision.reason, "question": question[:100]},
        )
        return decision
    except Exception as e:
        # Safe fallback: if router fails, general chat is lowest-risk response
        logger.error(f"Router error: {e}. Defaulting to 'general'.")
        return RouteDecision(route="general", reason=f"Router error fallback: {e}")


# ── Usage in app/services.py ──────────────────────────────────────────────
#
# def ask(question: str, history: list) -> dict:
#     decision = route_question(question)
#
#     if decision.route == "general":
#         answer = general_chain.invoke({"input": question})
#     elif decision.route == "rag":
#         result = rag_chain.invoke({"question": question, "history": history})
#         answer = result.answer
#     elif decision.route == "tools":
#         result = tool_agent.invoke({"input": question})
#         answer = result["output"]
#
#     return {"answer": answer, "route": decision.route}
```

## 🏭 Production Best Practices

1. **Use `Literal["general", "rag", "tools"]` for the route field** — This makes the structured output schema enforce valid values. An invalid route string causes a validation error immediately rather than a confusing downstream failure. **How:** `route: Literal["general", "rag", "tools"] = Field(...)`.

2. **Log every routing decision** — When users report wrong answers, the first question is: did the question route to the right workflow? Without logging `(question, route, reason)`, you can't diagnose this. **How:** `logger.info("Routing", extra={"route": decision.route, "question": question[:100]})`.

3. **Add a fallback for router errors** — The router can fail if the LLM returns malformed output. A safe fallback (route to "general") ensures the application still responds rather than returning a 500 error. **How:** Wrap `_router_chain.invoke()` in try/except and return `RouteDecision(route="general", ...)`.

4. **Write route descriptions as decision rules, not labels** — The router prompt needs to say exactly when each route applies, with examples. "Use for operational data" is too vague. "Use for questions that require CURRENT data (inventory, sales, incidents) that changes hourly" is concrete. **How:** Include example questions for each route in the system prompt.

5. **Evaluate routing accuracy** — Build a small routing test set (20–30 questions with expected routes) and measure routing accuracy after prompt changes. A routing error on "What is the return policy?" (routed to tools instead of rag) produces a wrong answer that's hard to trace back to routing. **How:** `assert route_question("What is P1?").route == "rag"`.

6. **Initialize the router once, not per request** — The router chain (`ROUTER_PROMPT | llm.with_structured_output(RouteDecision)`) is stateless and safe to reuse. Build it once at startup and reuse for every request. **How:** Build `_router_chain` at module load time (see real-world example above).

## ⚠️ Common Mistakes to Avoid

⚠️ **Not routing at all** — Running every question through RAG adds unnecessary latency and cost for questions like "Hello" or "What can you help with?" A router makes the system both cheaper and more accurate by sending each question to the right workflow.

⚠️ **Too many overlapping routes** — If "store performance" can mean either RAG (performance SOP) or tools (live sales data), the router will be inconsistent. Keep routes mutually exclusive with clear examples. Start with 3; add a 4th only when you have a clear use case.

⚠️ **Parsing route from text output** — Extracting route from `"I think this should go to rag because..."` requires fragile string matching that breaks on edge cases. Always use `with_structured_output(RouteDecision)` so the route is a typed field.

⚠️ **Not testing routing separately from answer quality** — A question can route correctly and still produce a wrong answer (bad retrieval), or route incorrectly and happen to produce a decent answer. Test routing accuracy independently with a labeled routing test set.

⚠️ **Confusing routers with agents** — A router picks the *workflow* (RAG, tools, chat). An agent picks the *tool* within the tools workflow. They operate at different levels. The router runs once per question; the agent may call multiple tools per question.

## 🔗 How It Connects to Other Concepts

- **RAG Chains** (doc 18) — The `rag` route executes the full conversational RAG chain with retrieval, reranking, and structured output
- **Agents** (doc 21) — The `tools` route triggers the ReAct agent, which then selects individual tools
- **Structured Output** (doc 08) — `RouteDecision` uses `with_structured_output()` — the same pattern as `RAGResponse` and `JudgeResult`
- **Tools & Function Calling** (doc 20) — The `tools` route leads to the tool agent; routing determines which questions reach it
- **FastAPI Integration** (doc 25) — The router runs inside `assistant_service.ask()` — the service layer calls the router before deciding which chain to invoke

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | LLM-based intent classifier that maps each question to one of three workflows |
| **Why** | Different questions need different systems; routing avoids expensive unnecessary pipelines |
| **When** | Any application with multiple capabilities (RAG + tools + chat); single-capability apps don't need routing |
| **Types** | LLM router (standard), keyword/rule-based (fast), hybrid (rules + LLM fallback) |
| **Production gotcha** | Use `Literal` type for route field; log all decisions; evaluate routing accuracy separately; add error fallback |

## ➡️ Next Steps

- **Example file:** `app/router.py` — RetailOps `RouteDecision` schema and `route_question()` function
- **Next doc:** `24_memory.md` — how the application maintains conversation history across turns for follow-up questions
- **Official docs:** https://python.langchain.com/docs/how_to/routing/
