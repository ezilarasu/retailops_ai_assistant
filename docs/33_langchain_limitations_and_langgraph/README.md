# LangChain Limitations & LangGraph
> Where LangChain's pipeline model reaches its limits — and how LangGraph extends it into stateful workflows.

## 📌 What Is It?

**LangChain** excels at building pipelines: linear sequences of steps where a question flows through a retriever, prompt, LLM, and parser to produce an answer. For RAG, tools, and simple agents, this chain model is exactly right.

**LangGraph** is a framework built on top of LangChain that models workflows as graphs — nodes connected by edges — rather than as linear chains. It was created specifically to handle what chains can't: state, loops, conditional branching, human approval steps, and persistent workflows.

```
LangChain chain (pipeline):
  Input → Step A → Step B → Step C → Output
  Best for: RAG, tools, prompt pipelines, simple agents

LangGraph graph (state machine):
  ┌─────────────────────────────────────────┐
  │  State: {question, documents, decisions}│
  │                                         │
  │  [Retrieve] → [Analyze] → [Approve?]    │
  │                               ↓      ↘  │
  │                          [Execute]  [Reject]
  └─────────────────────────────────────────┘
  Best for: long-running workflows, human approval, multi-agent, persistent state
```

LangGraph is not a replacement for LangChain — it uses LangChain components (retrievers, LLMs, tools) inside its graph nodes. The key addition is **state**: a shared dictionary that flows through the graph and can be persisted across pauses, restarts, and approvals.

## ❓ Why Does It Exist?

LangChain's chain model assumes a request starts, flows through steps, and ends — all in one synchronous execution. This is perfect for most AI assistant use cases.

But enterprise workflows break this assumption:

```
Example: Vendor approval workflow

  AI researches vendor options        ← Step 1 (runs now)
  Manager reviews recommendation      ← Step 2 (runs tomorrow)
  AI generates final report           ← Step 3 (runs after approval)

A chain ends after Step 1. The rest can't happen.
```

Other examples that chains can't handle naturally:
- **Retries**: call a tool, it fails, retry 3 times with backoff
- **Loops**: keep researching until a confidence threshold is met
- **Complex branching**: 5+ conditional paths through a business process
- **Multi-agent coordination**: 3 agents sharing state and passing work to each other
- **Checkpointing**: crash recovery — resume from step 7 of 15

LangGraph adds a graph execution engine on top of LangChain to handle all of these.

## ⏰ When Should You Use It?

**LangChain is enough when:**  
✅ Building RAG systems — retrieval + generation is a natural pipeline  
✅ Building tool-calling agents — `create_agent` (LangChain 1.x) handles the tool-calling loop for you  
✅ Simple routing — router → RAG/tools/general is a chain  
✅ Prompt pipelines and evaluation — all linear workflows  
✅ Most AI assistant use cases (including all of RetailOps)  

**LangGraph becomes necessary when:**  
✅ Human approval steps are required — workflow must pause and wait  
✅ Workflow must persist across minutes, hours, or days  
✅ Multiple agents need to share and update state  
✅ Complex branching with 5+ conditional paths  
✅ Checkpointing is required (resume after crash or interruption)  
✅ Audit trails of workflow decisions are required  

❌ Don't use LangGraph for simple RAG — unnecessary complexity  
❌ Don't use LangGraph for single-turn tool calls — `create_agent` is simpler (it is built on LangGraph internally, so you get the loop without writing the graph)  
❌ Don't rewrite your existing LangChain code in LangGraph — migrate incrementally  

## 🗂️ Types / Variants

| Concept | Description | When It Matters |
|---|---|---|
| **State** | Shared dict flowing through graph nodes; the core LangGraph primitive | Any time you need data to persist across nodes |
| **Nodes** | Individual units of work (functions); equivalent to chain steps | Replacing individual pipeline steps with graph nodes |
| **Edges** | Connections between nodes; define execution flow | Always — they wire the graph together |
| **Conditional Edges** | Edges that route based on state; enables branching | Approval workflows, error routing, loop termination |
| **Checkpoints** | Saved state snapshots; enable pause/resume | Long-running workflows, crash recovery |
| **Human-in-the-Loop** | Pause graph, wait for human input, resume | Approval workflows, review steps |
| **Multi-Agent** | Multiple agent nodes with shared state | Research + review + execution pipelines |

## 🔀 When to Use Which Type

**Conditional edges** are the most frequently needed LangGraph primitive. Even moderate complexity — "if approved, go to Execute; if rejected, go to Notify" — requires conditional routing that chains handle clumsily.

**Checkpoints** are required for any workflow that may take longer than a single request or that needs crash recovery. They save state to a backend (SQLite, Redis, Postgres) and restore it on resume.

**Human-in-the-loop** combines conditional edges and checkpoints: the graph reaches an "awaiting approval" node, saves its state as a checkpoint, and resumes when a human provides input (approve/reject).

**Multi-agent** graphs are the most complex pattern — use only when you genuinely need multiple specialized agents that produce and consume each other's outputs. Most use cases are better served by a single agent with more tools.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Handles workflows LangChain genuinely can't express | Significantly more complex than chains |
| Built on LangChain — existing retrievers/tools work inside graph nodes | State design requires upfront thought |
| Checkpointing enables long-running workflows and crash recovery | Debugging graph execution is harder than debugging linear chains |
| Human-in-the-loop is a first-class feature | Overkill for simple RAG and tool-calling use cases |
| Multi-agent coordination with shared state | Learning curve for graph-based thinking |
| Visual graph representation for complex workflows | |

## 💻 Basic Example

```python
# A simple LangGraph workflow that mirrors the chain pattern,
# to show the structural difference before adding graph-specific features.

import os
from dotenv import load_dotenv
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()  # reads GROQ_API_KEY and LLM_MODEL from .env

# ── Step 1: Define state ─────────────────────────────────────────────────
# State is the shared dict that flows through all nodes.
# TypedDict gives you type safety and IDE support.

class RAGState(TypedDict):
    question: str       # set at input
    documents: list     # set by retrieve node
    answer: str         # set by generate node


# ── Step 2: Define nodes (units of work) ─────────────────────────────────

def retrieve(state: RAGState) -> RAGState:
    """Retrieve documents and add to state."""
    # In a real system: use your retriever here
    docs = [{"content": "P1 means a full store outage.", "source": "it_support_kb.txt"}]
    return {"documents": docs}  # partial update — merges into state


def generate(state: RAGState) -> RAGState:
    """Generate answer using retrieved documents."""
    llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)
    context = "\n".join(d["content"] for d in state["documents"])
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Answer using this context:\n{context}"),
        ("human", "{question}"),
    ])
    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke({"context": context, "question": state["question"]})
    return {"answer": answer}


# ── Step 3: Build graph ───────────────────────────────────────────────────

graph = StateGraph(RAGState)
graph.add_node("retrieve", retrieve)      # add nodes
graph.add_node("generate", generate)
graph.set_entry_point("retrieve")         # first node
graph.add_edge("retrieve", "generate")   # edge: retrieve → generate
graph.add_edge("generate", END)           # end after generate

compiled = graph.compile()

# ── Step 4: Invoke ───────────────────────────────────────────────────────
result = compiled.invoke({"question": "What does P1 mean?"})
print(result["answer"])
# State after execution: {question: "...", documents: [...], answer: "..."}
```

## 🔧 Real-World Example

LangGraph's most valuable feature: a human-in-the-loop approval workflow that chains genuinely can't express — followed by an honest tour of the LangGraph version that already exists in `app/graph/`.

```python
import os
from dotenv import load_dotenv
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver  # or SqliteSaver for persistence
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

load_dotenv()  # reads GROQ_API_KEY and LLM_MODEL from .env

# ══════════════════════════════════════════════════════════════════════════
# Human-in-the-Loop Approval Workflow
#
# This is the canonical pattern that LangChain can't express:
# workflow pauses at an "awaiting approval" node, saves state,
# and resumes when a human approves or rejects.
#
# Use case: AI recommends a vendor, manager must approve before execution.
# ══════════════════════════════════════════════════════════════════════════

class WorkflowState(TypedDict):
    question: str
    research: str
    recommendation: str
    approval_status: Literal["pending", "approved", "rejected"]
    final_output: str


# ── Nodes ─────────────────────────────────────────────────────────────────

def research_node(state: WorkflowState) -> dict:
    """Research the question — runs automatically."""
    llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)
    research = llm.invoke([HumanMessage(content=f"Research: {state['question']}")])
    return {"research": research.content, "approval_status": "pending"}


def recommend_node(state: WorkflowState) -> dict:
    """Generate a recommendation based on research — runs automatically."""
    llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)
    rec = llm.invoke([HumanMessage(
        content=f"Based on research:\n{state['research']}\n\nGive a recommendation."
    )])
    return {"recommendation": rec.content}


def await_approval_node(state: WorkflowState) -> dict:
    """Checkpoint node — workflow pauses here until a human acts.

    In practice, this node saves state and the graph is interrupted.
    The human provides approval via a separate API call that resumes the graph.
    """
    # Just returns current state — the interrupt happens via graph configuration
    return {}


def execute_node(state: WorkflowState) -> dict:
    """Execute the approved recommendation — runs after approval."""
    return {"final_output": f"Executed: {state['recommendation']}"}


def reject_node(state: WorkflowState) -> dict:
    """Handle rejection — notify and close workflow."""
    return {"final_output": "Workflow rejected by manager."}


# ── Conditional routing ───────────────────────────────────────────────────

def route_after_approval(state: WorkflowState) -> Literal["execute", "reject"]:
    """Route based on approval decision.

    This is called after await_approval_node — the state will have been
    updated by the human's API call before the graph resumes.
    """
    return "execute" if state["approval_status"] == "approved" else "reject"


# ── Build graph ───────────────────────────────────────────────────────────

workflow = StateGraph(WorkflowState)
workflow.add_node("research", research_node)
workflow.add_node("recommend", recommend_node)
workflow.add_node("await_approval", await_approval_node)
workflow.add_node("execute", execute_node)
workflow.add_node("reject", reject_node)

workflow.set_entry_point("research")
workflow.add_edge("research", "recommend")
workflow.add_edge("recommend", "await_approval")
# Conditional edge: routes to execute or reject based on approval_status
workflow.add_conditional_edges("await_approval", route_after_approval, {
    "execute": "execute",
    "reject": "reject",
})
workflow.add_edge("execute", END)
workflow.add_edge("reject", END)

# MemorySaver enables checkpointing — state survives pauses
checkpointer = MemorySaver()
app = workflow.compile(
    checkpointer=checkpointer,
    interrupt_before=["await_approval"],  # pause here, wait for human
)

# ── RetailOps: two parallel implementations ──────────────────────────────
#
# 1. The main app path is plain LangChain with hand-written orchestration:
#    app/router.py run_router() classifies the question and branches into
#    general / rag / tools. app/services.py, app/api.py and app/main.py all
#    use this path. It does NOT use LangGraph.
#
# 2. A LangGraph version of the same workflow lives in app/graph/. It is a
#    learning implementation that is NOT wired into the API or CLI; you run
#    it through examples/example_23..28 (see RUN.md).
#
# What app/graph/ contains today:
#   graph.py       build_retailops_graph(): validation -> router ->
#                  general | rag | tools | error; the tools branch continues
#                  to an approval node before END. Compiled with an
#                  InMemorySaver checkpointer (use a thread_id in config).
#                  Its module docstring says what it is: a parallel demo that
#                  the CLI and API do not use. After general, rag and tools,
#                  error_or(...) conditional edges send a failed turn to
#                  error_node instead of carrying on.
#   state.py       RetailOpsState (TypedDict): question, messages, route,
#                  answer, sources, confidence, timings, approval fields, plus
#                  rewritten_question and context for the RAG subgraph.
#   nodes.py       validation_node, route_node (reuses route_question from
#                  app/router.py), general_node, tools_node, error_node,
#                  approval_node. Nodes call the SAME LangChain pieces the main
#                  app uses, fetched with get_container() when the node runs
#                  (not at import, so importing or building the graph needs no
#                  API key) — the "LangGraph orchestrates, LangChain works"
#                  principle. Model calls go through invoke_with_retry, and
#                  provider failures become typed errors (RetailOpsError).
#                  route_node starts debug and timings empty every turn, so a
#                  reused thread_id does not carry the last turn's timings.
#                  general_node and tools_node get the earlier turns
#                  (history_before_question(state)[-6:]). approval_node() calls
#                  langgraph.types.interrupt() to pause and wait for a human
#                  decision; resume with Command(resume={...}) (see
#                  examples/example_28_approval.py).
#   rag_subgraph.py  the "rag" node is a real subgraph with three steps:
#                  rewrite -> retrieve -> generate. Each step calls the shared
#                  helpers in app/chains.py (rewrite_question,
#                  retrieve_documents, format_docs) and the shared pieces on
#                  get_container() (.rewriter_chain, .retriever,
#                  .rag_generator), the same ones run_router()'s RAG chain
#                  uses. A @step decorator skips the remaining steps once one
#                  fails and records route="error", so the parent graph's
#                  error_or edge routes to error_node.
#   react_agent_graph.py     langgraph.prebuilt.create_react_agent over app/tools.py
#   prebuilt_tools_graph.py  the same idea built by hand with ToolNode; its LLM
#                  is created inside build_prebuilt_tools_graph(), not at import
#
# tools_node() takes the answer from the last message of the agent's
# {"messages": [...]} result, exactly as run_router() does. The tool agent
# (here and in react_agent_graph.py / prebuilt_tools_graph.py) uses
# settings.tools_llm_model (TOOLS_LLM_MODEL, default openai/gpt-oss-120b), the
# same dedicated tool-calling model as the main app (doc 21).
#
# Treat app/graph/ as a worked example of the concepts: examples 23-28 run end
# to end, but the CLI and API still use run_router().
#
# Key migration principle (still true): KEEP existing LangChain components.
# LangGraph CALLS your chains inside its nodes — don't rewrite, wrap.
```

> **Lesson from this project:** a graph that compiles is not a graph that works. The first version of `app/graph/` built and ran without errors, yet its RAG step was a placeholder that returned no answer and its tools step read a key that the agent never returns, so answers came back empty or as a dumped dictionary. Only the examples that print the final answer (23, 24, 25, 28) exposed it. Run a graph end to end on one question per route before you trust it, and send failed nodes to an error node with a conditional edge instead of letting the next step run on bad state.

## 🏭 Production Best Practices

1. **Start with LangChain — add LangGraph only when the workflow genuinely requires it** — LangGraph adds real complexity: state design, graph compilation, checkpoint backends. If your use case is RAG + tools + router, LangChain handles it well. Add LangGraph when you hit a concrete limitation, not speculatively. **How:** Ask: "Do I need human approval, persistent state across days, or multi-agent coordination?" If no, stay with LangChain.

2. **Keep existing LangChain components when migrating** — LangGraph nodes call your existing chains — they don't replace them. Your RAG chain, retriever, and tools work inside LangGraph nodes without modification. You add a graph wrapper; you don't rewrite the logic. **How:** `def answer_node(state): result = rag_chain.invoke({"question": state["question"]}); return {"answer": result.answer}`. RetailOps' RAG subgraph (`app/graph/rag_subgraph.py`) does essentially this: its `generate` step calls `get_container().rag_generator`, the same object the non-graph RAG chain uses, and its `rewrite` and `retrieve` steps call the same helpers (see the Real-World Example above).

3. **Design state carefully before building the graph** — State is the contract between all nodes. Too broad (giant state object) creates coupling; too narrow means nodes can't access what they need. Define state as a TypedDict with only the fields that actually need to flow between nodes. **How:** For each node, ask "what does it read?" and "what does it write?" — only those fields belong in state.

4. **Add checkpoints for any workflow that might be interrupted** — Checkpoints are cheap (MemorySaver for dev, SqliteSaver or RedisSaver for production) and essential for long-running workflows. Without them, crashes restart the entire workflow from scratch. **How:** `app = workflow.compile(checkpointer=MemorySaver())` — then pass a `thread_id` in `config` to identify the workflow instance.

5. **Use conditional edges, not conditional logic inside nodes** — Putting `if approved: do_this() else: do_that()` inside a node defeats the purpose of a graph. Conditional edges make the branching visible in the graph structure, testable in isolation, and easy to trace. **How:** `workflow.add_conditional_edges("approval_check", route_fn, {"approved": "execute", "rejected": "reject"})`.

6. **Treat LangGraph as the orchestrator, LangChain as the worker** — The best architectures use LangGraph to manage workflow flow (when things happen, in what order, with what branching) and LangChain to do the actual AI work (retrieval, generation, tool calling). **How:** LangGraph graph → calls LangChain RAG chain in nodes → uses LangChain tools and retrievers.

## ⚠️ Common Mistakes to Avoid

⚠️ **Using LangGraph for simple RAG** — A retrieval chain is three lines with LCEL. Adding a graph wrapper turns it into 40 lines. LangGraph is powerful precisely because it adds complexity — don't add that complexity until you need it.

⚠️ **Treating LangGraph as a replacement** — LangGraph is a workflow orchestration layer that uses LangChain. Your chains, retrievers, and tools don't need to be rewritten — they get called from inside graph nodes.

⚠️ **Skipping state design** — Jumping straight to graph nodes without defining state leads to messy partial updates, unexpected key collisions, and hard-to-debug behavior. Define your TypedDict state schema first; then build nodes to match it.

⚠️ **Skipping checkpoints for long workflows** — If a 30-step procurement workflow fails at step 28, restarting from scratch is unacceptable. Checkpointing is mandatory for any workflow that can be interrupted. Add it from day one.

⚠️ **Building multi-agent systems prematurely** — Multi-agent LangGraph graphs are the most complex pattern available. Most systems that claim to need multi-agent actually need a single agent with more tools. Start with one agent, add specialization only when there's a concrete bottleneck.

## 🔗 How It Connects to Other Concepts

- **Agents** (doc 21) — `create_agent` (which runs on LangGraph under the hood) is sufficient for most agent use cases; writing your own graph adds persistence, custom state and interrupt capabilities on top
- **Router Pattern** (doc 23) — RetailOps' main router (`run_router()`) is a LangChain chain plus an `if` ladder; the LangGraph version in `app/graph/` turns the same decision into conditional edges, which makes routing state-aware and pauseable
- **Memory** (doc 24) — RetailOps' `run_router()` keeps an in-memory history per `session_id` (`app/memory.py`); LangGraph checkpoints (`InMemorySaver` in `app/graph/graph.py`, keyed by `thread_id`) are the per-conversation persistence layer, and swap to SQLite/Postgres/Redis for durability
- **Production RAG Patterns** (doc 32) — Workflow orchestration and persistent state are the primary gaps between production baseline and enterprise grade
- **FastAPI Integration** (doc 25) — LangGraph apps are exposed via FastAPI the same way as chains; checkpoint thread IDs map to session IDs

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | LangChain's chain model, where it reaches its limits, and how LangGraph extends it to stateful workflows |
| **Why** | Chains can't pause for human approval, persist across days, or coordinate multiple agents with shared state |
| **When** | LangChain for RAG/tools/simple agents; LangGraph for approval workflows, long-running processes, multi-agent |
| **Types** | State, nodes, edges, conditional edges, checkpoints, human-in-the-loop, multi-agent |
| **Production gotcha** | Keep LangChain components; add LangGraph only for genuine workflow needs; design state before building nodes |

## ➡️ Next Steps

- **Example files:** `app/graph/nodes.py` — see `approval_node()` for the real human-in-the-loop implementation using `langgraph.types.interrupt()`; `app/graph/graph.py` (`build_retailops_graph()`), `app/graph/state.py` (`RetailOpsState`), `app/graph/react_agent_graph.py` (`build_react_agent_graph()`), `app/graph/prebuilt_tools_graph.py` (`build_prebuilt_tools_graph()`), and `app/graph/rag_subgraph.py` (`build_rag_subgraph()`, the real rewrite -> retrieve -> generate subgraph used as the graph's `rag` node) for the rest of RetailOps' LangGraph implementation
- **Runnable demo:** see `RUN.md` in this folder (`examples/example_23_langgraph_router.py`, `examples/example_24_langgraph_memory.py`, `examples/example_25_langgraph_streaming.py`, `examples/example_26_prebuilt_toolnode.py`, `examples/example_27_create_react_agent.py`, `examples/example_28_approval.py`)
- **Previous doc:** `../32_production_rag_patterns/README.md`
- **Next doc:** `../34_project_architecture/README.md` — the complete RetailOps architecture map, component relationships, and how all the concepts connect
- **Official docs:** https://langchain-ai.github.io/langgraph/
