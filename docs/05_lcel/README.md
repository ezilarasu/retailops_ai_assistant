# LCEL (LangChain Expression Language)
> The pipe syntax that turns individual components into composable, production-ready pipelines.

## 📌 What Is It?

**LCEL (LangChain Expression Language)** is the modern way to connect LangChain components together into pipelines using the `|` pipe operator.

Think of Unix pipes:
```bash
cat file.txt | grep "error" | sort | uniq
```

LCEL is the same idea for LLM pipelines:
```python
chain = prompt | llm | parser
```

Each `|` passes the output of the left component as the input of the right component. The result is a new `Runnable` — a complete pipeline that supports `invoke`, `stream`, and `batch` just like any individual component does.

## ❓ Why Does It Exist?

**Before LCEL**, composing a simple chain required manual plumbing:

```python
# Pre-LCEL: verbose and non-composable
formatted_prompt = prompt.invoke({"question": question})
response = llm.invoke(formatted_prompt)
result = parser.invoke(response)
```

This works for one-off scripts, but it has problems at scale:
- You can't stream the pipeline without rewriting every step
- You can't batch multiple inputs without writing a loop
- You can't trace the pipeline in LangSmith without manual instrumentation
- You can't compose pipelines into larger pipelines

**With LCEL:**
```python
chain = prompt | llm | parser

# invoke, stream, batch, and LangSmith tracing all work automatically
result = chain.invoke({"question": question})
```

LCEL also automatically propagates streaming — if the LLM streams, the entire pipeline streams. You don't wire this yourself.

## ⏰ When Should You Use It?

✅ Connecting a prompt to a model  
✅ Connecting a model to a parser  
✅ Building any multi-step LLM pipeline  
✅ Any pipeline that needs to stream, batch, or run async  
✅ Any pipeline you want traced automatically in LangSmith  
✅ Composing smaller chains into larger ones  

❌ A single component used in isolation (just call `.invoke()` directly)  
❌ Complex stateful workflows with loops and approvals (use LangGraph instead)  

## 🗂️ Types / Variants

LCEL itself is a single concept, but it's used with several composition utilities:

| Utility | Class | What It Does |
|---|---|---|
| Sequential pipeline | `A \| B \| C` | Output of A → input of B → input of C |
| Parallel execution | `RunnableParallel` | Runs multiple chains on the same input simultaneously |
| Conditional routing | `RunnableBranch` | Routes to different chains based on a condition |
| Custom function | `RunnableLambda` | Wraps any Python function as a Runnable |
| Pass-through | `RunnablePassthrough` | Passes input unchanged (useful for merging data) |

## 🔀 When to Use Which Type

**Sequential `|` pipeline** is the default. Use for any linear flow: prompt → model → parser, or retriever → prompt → model.

**`RunnableParallel`** when you need to run two independent operations on the same input and combine results — e.g., search two different indexes at once to reduce latency. (Don't parallelise steps where one needs the other's output — in RetailOps, the question must be rewritten before retrieval, so those run in sequence.)

**`RunnableBranch`** for conditional routing at the chain level — e.g., short questions go to one chain, long questions to another. Note: for application-level routing (RAG vs tools vs chat), a structured-output router chain is more flexible.

**`RunnableLambda`** to insert any Python function (validation, formatting, transformation, logging) into a pipeline without breaking the Runnable interface.

**`RunnablePassthrough`** when you need to pass a value through one branch of a parallel chain unchanged — e.g., pass the original question alongside retrieved context.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Declarative and readable at a glance | Less explicit for beginners (flow isn't obvious at first) |
| Automatic streaming propagation | Debugging a pipeline requires LangSmith |
| Batch and async work out of the box | Complex data transformations can be awkward |
| LangSmith traces every step | |
| Chains can be composed into larger chains | |
| Every pipeline has a consistent interface | |

## 💻 Basic Example

```python
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough

load_dotenv()

llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)

# ── Simple sequential pipeline ────────────────────────────────────────────
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{question}"),
])

chain = prompt | llm | StrOutputParser()

# invoke — runs the full pipeline once
result = chain.invoke({"question": "What is a context window?"})
print(result)

# stream — yields tokens as they arrive
for chunk in chain.stream({"question": "Explain temperature in LLMs."}):
    print(chunk, end="", flush=True)
print()

# batch — runs multiple inputs in parallel
results = chain.batch([
    {"question": "What is RAG?"},
    {"question": "What is function calling?"},
])
for r in results:
    print(r)

# ── RunnableLambda — insert a Python function into the pipeline ───────────
def uppercase_question(data: dict) -> dict:
    """Pre-process: strip whitespace from the question."""
    data["question"] = data["question"].strip()
    return data

cleaned_chain = RunnableLambda(uppercase_question) | prompt | llm | StrOutputParser()
print(cleaned_chain.invoke({"question": "  What is tokenization?  "}))
```

## 🔧 Real-World Example

This is a simplified version of the LCEL patterns in RetailOps' `app/chains.py`. Notice how small chains compose into larger ones. The `RunnableParallel` step at the end is a teaching example of running independent steps side by side — RetailOps itself does not use it: in the real RAG chain the question is rewritten first and retrieval uses the rewritten question, so those two steps can't run in parallel (the real chain is `retrieve_context | generator`, where `retrieve_context` is a plain Python function that LCEL wraps for you and `generator` is itself a small chain, `rag_prompt | llm.with_structured_output(RAGResponse)`; see `build_rag_chain()` in `app/chains.py`).

```python
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import (
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)
from pydantic import BaseModel, Field

load_dotenv()

llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)

# ── Chain 1: General chat ─────────────────────────────────────────────────
general_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are RetailOps AI Assistant. Be concise."),
    ("human", "{question}"),
])
general_chain = general_prompt | llm | StrOutputParser()

# ── Chain 2: Question rewriter ────────────────────────────────────────────
rewrite_prompt = ChatPromptTemplate.from_messages([
    ("system", "Rewrite the follow-up question as a standalone question. Return ONLY the rewritten question."),
    ("human", "History: {history}\nFollow-up: {question}\nStandalone:"),
])
rewriter_chain = rewrite_prompt | llm | StrOutputParser()

# ── Chain 3: RAG chain with structured output ─────────────────────────────
class RAGResponse(BaseModel):
    answer: str = Field(description="Answer based only on the provided context")
    confidence: str = Field(description="high | medium | low")

rag_prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer ONLY using the provided context. If not found, say 'I don't know.'"),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])
rag_chain = rag_prompt | llm.with_structured_output(RAGResponse)

# ── Chain 4: Routing chain ────────────────────────────────────────────────
class RouteDecision(BaseModel):
    route: str = Field(description="Exactly one of: general, rag, tools")

router_prompt = ChatPromptTemplate.from_messages([
    ("system", "Route: general (small talk), rag (policy/docs), tools (live data). Return one word."),
    ("human", "{question}"),
])
router_chain = router_prompt | llm.with_structured_output(RouteDecision)

# ── RunnableParallel: run independent steps side by side ──────────────────
# Both branches below only need the original question, so they can run in
# parallel instead of one after the other. (Don't parallelise steps where one
# needs the other's output — rewriting must finish before retrieval.)
# (In production, "retriever" is your actual vector store retriever)

def mock_retrieve(question: str) -> str:
    """Placeholder: in production, this calls your vector store retriever."""
    return "Employees receive 18 days of paid vacation annually. (Source: HR Policy v2)"

parallel_prep = RunnableParallel({
    "context": RunnableLambda(lambda x: mock_retrieve(x["question"])),
    "question": RunnablePassthrough() | RunnableLambda(lambda x: x["question"]),
})

# Chain parallel prep into the RAG chain
full_rag_pipeline = parallel_prep | rag_chain

# ── Async streaming for FastAPI endpoints ─────────────────────────────────
import asyncio

async def stream_general_answer(question: str) -> None:
    """Stream tokens for a chat UI endpoint."""
    async for chunk in general_chain.astream({"question": question}):
        print(chunk, end="", flush=True)
    print()

# ── Test the chains ────────────────────────────────────────────────────────
# Routing
decision = router_chain.invoke({"question": "What is the overtime policy?"})
print(f"Route: {decision.route}")  # → Route: rag

# RAG with parallel prep
result = full_rag_pipeline.invoke({"question": "How many vacation days do we get?"})
print(result.answer)      # "Employees receive 18 days of paid vacation annually."
print(result.confidence)  # "high"

# Rewriter
standalone = rewriter_chain.invoke({
    "history": "User asked about vacation days.",
    "question": "What about sick leave?",
})
print(standalone)  # → "What is the sick leave policy for employees?"

# Streaming
asyncio.run(stream_general_answer("Explain cross-encoder reranking."))
```

## 🏭 Production Best Practices

1. **Build small, named chains — then compose them** — Define `general_chain`, `rag_chain`, `router_chain` separately. Each should do one thing. **Why:** Small chains are independently testable. A bug in routing doesn't mix with a bug in generation.

2. **Use `chain.batch()` for evaluation runs** — When testing your golden dataset (50–200 questions), use `chain.batch(inputs)` instead of calling `chain.invoke()` in a loop. Batch runs requests in parallel. **How:** `results = chain.batch([{"question": q} for q in test_questions])`.

3. **Use `astream()` in FastAPI endpoints** — Stream LLM tokens to the client as they arrive for ChatGPT-style UX. **How:**
   ```python
   async def chat_endpoint(question: str):
       async for chunk in chain.astream({"question": question}):
           yield chunk
   ```

4. **Use `RunnableParallel` for independent operations** — If two chain steps don't depend on each other (e.g., retrieval and question rewriting), run them in parallel. **Why:** Reduces latency by the slower of the two operations instead of adding both.

5. **Keep business logic out of LCEL pipelines** — Prompts in templates, parsing in parsers, data transformation in `RunnableLambda`. **Why:** Complex logic inside chain steps is impossible to unit test. Extract to functions, wrap with `RunnableLambda`.

6. **Enable LangSmith to trace LCEL pipelines** — With `LANGSMITH_TRACING=true` (and `LANGSMITH_API_KEY` set), every step in every pipeline is logged — the prompt sent, the response received, latency, and token counts. **Why:** There's no other way to debug a production LCEL pipeline that behaves unexpectedly.

## ⚠️ Common Mistakes to Avoid

⚠️ **Building one giant LCEL pipeline** — A 20-step pipeline with retrieval, rewriting, routing, generation, and evaluation all in one `|` chain is undebuggable and untestable. Build small named chains and compose them.

⚠️ **Using LCEL for workflows with state or loops** — LCEL is a pipeline (A→B→C). If you need branching, retries, human approval, or persistent state, that's LangGraph territory. Using LCEL for complex workflows produces fragile workarounds.

⚠️ **Not using `batch()` for evaluation** — Running `chain.invoke()` in a Python `for` loop for 100 evaluation questions takes 100× longer than `chain.batch()`. Batch runs requests in parallel.

⚠️ **Mixing data transformation and prompt logic** — Don't put retrieval results formatting inside the prompt string. Use `RunnableLambda` to preprocess data before it reaches the prompt template.

⚠️ **Forgetting that LCEL chains are Runnables** — A composed chain (`chain = prompt | llm | parser`) is itself a Runnable. You can pipe chains into chains: `full_pipeline = chain_a | chain_b`. Use this to build layered architectures.

## 🔗 How It Connects to Other Concepts

- **Runnables** (next: doc 06) — Every component in an LCEL chain is a Runnable; understanding the interface explains why `|` works
- **Chat Models** (doc 01) — Chat models are Runnables and participate in LCEL pipelines as the `llm` step
- **Prompt Templates** (doc 03) — Prompt templates are always the first Runnable in a chain
- **Output Parsers** (doc 07) — Parsers are always the last Runnable, converting model output to usable types
- **RAG Chains** (doc 18) — Production RAG is built as composed LCEL chains
- **LangGraph** (doc 33) — LangGraph orchestrates LCEL chains as nodes in a stateful workflow graph

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Pipe syntax (`\|`) for composing LangChain Runnables into pipelines |
| **Why** | Automatic streaming, batching, async, and LangSmith tracing for any pipeline — no manual wiring |
| **When** | Any multi-step LLM pipeline; anything that needs to stream, batch, or be traced |
| **Types** | Sequential `\|`, `RunnableParallel` (concurrent), `RunnableBranch` (conditional), `RunnableLambda` (custom function) |
| **Production gotcha** | Small named chains > one giant chain; use `batch()` for evaluation; use `astream()` for streaming endpoints; complex stateful workflows → use LangGraph |

## ➡️ Next Steps

- **Example file:** `app/chains.py` — RetailOps LCEL chain definitions (general, RAG, router, rewriter)
- **Next doc:** `../06_runnables/README.md` — the interface that makes LCEL work
- **Official docs:** https://python.langchain.com/docs/concepts/lcel/
