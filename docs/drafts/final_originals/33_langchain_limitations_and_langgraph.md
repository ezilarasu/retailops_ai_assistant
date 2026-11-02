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
✅ Building tool-calling agents — AgentExecutor handles the ReAct loop  
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
❌ Don't use LangGraph for single-turn tool calls — AgentExecutor is simpler  
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

from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

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
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
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

LangGraph's most valuable feature: a human-in-the-loop approval workflow that chains genuinely can't express — plus RetailOps' planned migration strategy.

```python
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver  # or SqliteSaver for persistence
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

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
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    research = llm.invoke([HumanMessage(content=f"Research: {state['question']}")])
    return {"research": research.content, "approval_status": "pending"}


def recommend_node(state: WorkflowState) -> dict:
    """Generate a recommendation based on research — runs automatically."""
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
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

# ── RetailOps Migration Strategy ─────────────────────────────────────────
#
# Current architecture is LangChain — appropriate for current requirements.
#
# Phase 1 (current):    LangChain chains for RAG, tools, router
# Phase 2 (planned):    Keep LangChain RAG/tools; LangGraph for routing
# Phase 3 (future):     LangGraph approval workflows (refund escalation)
# Phase 4 (future):     Persistent memory across sessions
# Phase 5 (future):     Multi-agent (research + reviewer + planner)
#
# Key migration principle: KEEP existing LangChain components.
# LangGraph CALLS your chains inside its nodes — don't rewrite, wrap.
#
# def rag_node(state):
#     result = ask_rag(state["question"], state["history"])  # existing chain
#     return {"answer": result["answer"], "sources": result["sources"]}
#
# The RAG chain is unchanged. The graph just orchestrates when it runs.
```

## 🏭 Production Best Practices

1. **Start with LangChain — add LangGraph only when the workflow genuinely requires it** — LangGraph adds real complexity: state design, graph compilation, checkpoint backends. If your use case is RAG + tools + router, LangChain handles it well. Add LangGraph when you hit a concrete limitation, not speculatively. **How:** Ask: "Do I need human approval, persistent state across days, or multi-agent coordination?" If no, stay with LangChain.

2. **Keep existing LangChain components when migrating** — LangGraph nodes call your existing chains — they don't replace them. Your RAG chain, retriever, and tools work inside LangGraph nodes without modification. You add a graph wrapper; you don't rewrite the logic. **How:** `def rag_node(state): result = ask_rag(state["question"], history); return {"answer": result["answer"]}`.

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

- **Agents** (doc 21) — AgentExecutor is sufficient for most agent use cases; LangGraph's agent support adds persistence and interrupt capabilities on top
- **Router Pattern** (doc 23) — RetailOps' current router is a LangChain chain; a LangGraph version would make routing state-aware and pauseable
- **Memory** (doc 24) — In-memory session history is a LangChain pattern; LangGraph checkpoints provide the persistence layer for cross-session memory
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

- **Example file:** `app/langgraph_workflow.py` — human-in-the-loop approval workflow, RetailOps migration phases
- **Next doc:** `34_project_architecture.md` — the complete RetailOps architecture map, component relationships, and how all 30+ concepts connect
- **Official docs:** https://langchain-ai.github.io/langgraph/
