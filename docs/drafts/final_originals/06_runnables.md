# Runnables
> The universal interface that makes every LangChain component composable.

## 📌 What Is It?

A **Runnable** is the fundamental building block of LangChain. Every component — prompt templates, chat models, output parsers, retrievers, tools, and composed chains — implements the Runnable interface.

The Runnable interface means one thing: every component accepts input and produces output through the same three methods:
```python
component.invoke(input)   # run once
component.batch(inputs)   # run multiple in parallel
component.stream(input)   # yield output incrementally
```

Think of it like Python's iterator protocol — once you know `__iter__` and `__next__`, every iterable works the same way. Runnables are the same idea for LLM pipelines.

## ❓ Why Does It Exist?

**Without Runnables**, every LangChain component had its own API:
```python
prompt.run(...)        # old prompt interface
model.call(...)        # old model interface
parser.execute(...)    # hypothetical parser
retriever.get(...)     # hypothetical retriever
```

You couldn't compose them without custom glue code, and you couldn't batch or stream across all of them without per-component implementations.

**With Runnables**, every component works the same way:
```python
prompt.invoke(data)
llm.invoke(messages)
parser.invoke(response)
retriever.invoke(question)
chain.invoke(inputs)     # a chain of runnables is itself a Runnable
```

This is the foundation that makes LCEL's pipe syntax (`|`) possible. When two things have the same interface, connecting them is trivial.

## ⏰ When Should You Use It?

✅ Any time you compose components into a pipeline  
✅ Any time you want to run the same logic on multiple inputs  
✅ Any time you need streaming output for a UI  
✅ When inserting a Python function into a pipeline (`RunnableLambda`)  
✅ When running two independent operations simultaneously (`RunnableParallel`)  

❌ You don't "use" Runnables directly — you work with them. Every LangChain component already is a Runnable.  

## 🗂️ Types / Variants

| Type | Class | What It Does |
|---|---|---|
| **Standard interface** | All components | `invoke`, `batch`, `stream`, `astream` on every component |
| **Wrap a function** | `RunnableLambda` | Makes any Python function composable in LCEL pipelines |
| **Parallel execution** | `RunnableParallel` | Runs multiple Runnables on the same input simultaneously |
| **Conditional routing** | `RunnableBranch` | Routes input to different Runnables based on a condition |
| **Pass-through** | `RunnablePassthrough` | Passes input unchanged (useful for keeping original data in parallel branches) |
| **Add fields** | `RunnableAssign` | Adds computed fields to an existing dict without replacing other keys |

## 🔀 When to Use Which Type

**`RunnableLambda`** whenever you need custom Python logic inside a pipeline — preprocessing, validation, formatting, logging. Wrap the function, pipe it in.

**`RunnableParallel`** when two or more operations are independent and can run at the same time. Classic use: retrieve context AND rewrite the question simultaneously (reduces latency by the slower of the two).

**`RunnableBranch`** for lightweight conditional routing based on simple predicates. For application-level routing (RAG vs tools vs chat), a structured-output router chain is more flexible.

**`RunnablePassthrough`** inside `RunnableParallel` when you need to forward the original input to the next step unchanged — e.g., passing `question` alongside retrieved `context`.

**`RunnableAssign`** when enriching existing data mid-pipeline — e.g., adding `context` to a dict that already has `question` and `history`.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Consistent interface — one mental model for all components | Abstraction can hide what's happening (use LangSmith to see) |
| Automatic streaming propagation through entire pipeline | New developers need to understand data flow |
| Batch and async work everywhere without extra code | `RunnableParallel` results can be confusing when debugging |
| Composable — chains are Runnables and can be piped into chains | |

## 💻 Basic Example

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

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{question}"),
])
parser = StrOutputParser()

# ── Every component is a Runnable with the same interface ─────────────────
# invoke() — runs the full component once
response = llm.invoke("What is a context window?")
print(type(response))      # AIMessage
print(response.content)

# batch() — runs multiple inputs in parallel, returns list
results = llm.batch([
    "What is RAG?",
    "What is LCEL?",
])
for r in results:
    print(r.content[:80])

# stream() — yields tokens as they arrive
for chunk in llm.stream("Explain temperature."):
    print(chunk.content, end="", flush=True)
print()

# ── A composed chain is also a Runnable ───────────────────────────────────
chain = prompt | llm | parser
# chain.invoke(), chain.batch(), chain.stream() all work — same interface
result = chain.invoke({"question": "What is a vector database?"})
print(result)

# ── RunnableLambda: wrap a Python function ────────────────────────────────
def preprocess(data: dict) -> dict:
    """Strip whitespace from the question before it reaches the prompt."""
    data["question"] = data["question"].strip()
    return data

pipeline = RunnableLambda(preprocess) | chain
print(pipeline.invoke({"question": "  What is chunking?  "}))
```

## 🔧 Real-World Example

This shows how RetailOps uses all the Runnable utilities together to build its parallel RAG preparation pipeline.

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
    RunnableAssign,
)
from pydantic import BaseModel, Field

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# ── Rewriter chain — standalone Runnable ─────────────────────────────────
rewrite_prompt = ChatPromptTemplate.from_messages([
    ("system", "Rewrite the follow-up as a standalone question. Return only the question."),
    ("human", "History: {history}\nFollow-up: {question}"),
])
rewriter = rewrite_prompt | llm | StrOutputParser()

# ── Simulated retriever ───────────────────────────────────────────────────
def retrieve_documents(question: str) -> str:
    """In production: calls your vector store. Returns formatted context."""
    return f"[Mock context for: {question}]"

retriever = RunnableLambda(retrieve_documents)

# ── RunnableParallel: run retrieval and rewriting simultaneously ──────────
# Both operations are independent — run them in parallel to save latency.
# Input: {"question": "...", "history": "..."}
# Output: {"question": "...", "context": "..."}
parallel_prep = RunnableParallel({
    "question": RunnablePassthrough() | RunnableLambda(lambda x: x["question"]),
    "context":  RunnableLambda(lambda x: retrieve_documents(x["question"])),
})

# ── RAG chain ─────────────────────────────────────────────────────────────
rag_prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer ONLY using the provided context. If not found, say 'I don't know.'"),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])
rag_chain = rag_prompt | llm | StrOutputParser()

# ── Full pipeline: parallel prep → RAG chain ─────────────────────────────
full_pipeline = parallel_prep | rag_chain

# ── RunnableAssign: add a field without replacing other keys ──────────────
# Useful when enriching data mid-pipeline
enrich = RunnableAssign({"context": retriever})
# Input:  {"question": "..."}
# Output: {"question": "...", "context": "..."}

# ── Async streaming for FastAPI ────────────────────────────────────────────
import asyncio

async def stream_response(question: str) -> None:
    """Stream tokens to a web client."""
    simple_chain = (
        ChatPromptTemplate.from_messages([
            ("system", "You are RetailOps AI Assistant."),
            ("human", "{question}"),
        ])
        | llm
        | StrOutputParser()
    )
    async for chunk in simple_chain.astream({"question": question}):
        print(chunk, end="", flush=True)
    print()

# ── Batch evaluation run ───────────────────────────────────────────────────
simple_chain = (
    ChatPromptTemplate.from_messages([("human", "{question}")])
    | llm
    | StrOutputParser()
)

test_questions = [
    {"question": "What is hybrid search?"},
    {"question": "What is a cross-encoder?"},
    {"question": "What is MMR retrieval?"},
]

# batch() runs all 3 in parallel — much faster than a loop with invoke()
results = simple_chain.batch(test_questions)
for q, r in zip(test_questions, results):
    print(f"Q: {q['question'][:40]}")
    print(f"A: {r[:80]}")
    print()

asyncio.run(stream_response("Explain the difference between RAG and fine-tuning."))
```

## 🏭 Production Best Practices

1. **Use `batch()` for evaluation, not `invoke()` in a loop** — `chain.batch(inputs)` runs all inputs in parallel. Running `chain.invoke()` for 100 golden-dataset questions sequentially takes 100× longer. **How:** `results = chain.batch([{"question": q} for q in questions])`.

2. **Use `astream()` in FastAPI streaming endpoints** — For chat interfaces, stream tokens as they arrive. **How:**
   ```python
   async def chat_stream(q: str):
       async for chunk in chain.astream({"question": q}):
           yield chunk
   ```

3. **Keep `RunnableLambda` functions small and focused** — A `RunnableLambda` wrapping 50 lines of business logic is untestable. Extract the logic to a named function, unit test it, then wrap it. **Why:** The function itself is pure Python and easy to test in isolation.

4. **Use `RunnableParallel` for independent operations** — If retrieval and question rewriting don't depend on each other, run them in parallel. **Why:** Latency becomes `max(t1, t2)` instead of `t1 + t2`.

5. **Remember: composed chains are Runnables** — `chain = prompt | llm | parser` is itself a Runnable. You can pipe chains into other chains: `full_pipeline = prep_chain | rag_chain`. This is how layered architectures are built.

6. **LangSmith shows Runnable internals** — With tracing enabled, every Runnable step shows its input, output, and latency in the LangSmith UI. This is the only practical way to debug unexpected behavior in a complex pipeline.

## ⚠️ Common Mistakes to Avoid

⚠️ **Thinking chains and Runnables are different** — A chain is just composed Runnables. `chain = prompt | llm | parser` means `chain` is itself a Runnable with `invoke`, `batch`, and `stream`.

⚠️ **Not understanding data flow** — Each Runnable transforms data. A `ChatPromptTemplate` receives a `dict` and outputs a `ChatPromptValue`. The LLM receives messages and outputs an `AIMessage`. `StrOutputParser` receives `AIMessage` and outputs `str`. If data shapes don't match at each step, the pipeline fails. Print intermediate outputs when debugging.

⚠️ **Overusing `RunnableLambda`** — Every `RunnableLambda` is a black box to LangSmith — it won't show what it does internally. When complex logic is needed, consider whether it belongs in a separate chain step with its own prompt and model, which will be properly traced.

⚠️ **Putting business logic in prompts** — Conditional logic, data validation, and transformations belong in `RunnableLambda`, not embedded as text instructions in a prompt. Prompt instructions influence the LLM; Python functions are deterministic.

## 🔗 How It Connects to Other Concepts

- **LCEL** (doc 05) — LCEL's `|` pipe works *because* everything is a Runnable; the pipe passes one Runnable's output to the next's `invoke`
- **Chat Models** (doc 01) — Chat models are Runnables; that's why `llm.invoke()`, `llm.batch()`, `llm.stream()` all work
- **Prompt Templates** (doc 03) — Prompt templates are Runnables; `prompt.invoke({"question": q})` returns the formatted messages
- **Output Parsers** (next: doc 07) — Parsers are Runnables; the last step that transforms `AIMessage` into a usable type
- **Retrievers** (doc 13) — Retrievers are Runnables; `retriever.invoke(question)` returns `list[Document]`
- **LangGraph** (doc 33) — LangGraph nodes run LCEL chains (Runnables) as the computation at each step

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Universal interface (`invoke/batch/stream`) implemented by every LangChain component |
| **Why** | Consistent programming model — composable, batchable, streamable everywhere |
| **When** | Implicitly always — every component you use is a Runnable |
| **Types** | `RunnableLambda` (custom function), `RunnableParallel` (concurrent), `RunnableBranch` (conditional), `RunnablePassthrough` (forward unchanged), `RunnableAssign` (add fields) |
| **Production gotcha** | Use `batch()` for evaluation (parallel); use `astream()` for streaming endpoints; composed chains are Runnables too |

## ➡️ Next Steps

- **Example file:** `app/chains.py` — RetailOps composed Runnables in production chains
- **Next doc:** `07_output_parsers.md` — the final Runnable in most chains, converting model output to usable types
- **Official docs:** https://python.langchain.com/docs/concepts/runnables/
