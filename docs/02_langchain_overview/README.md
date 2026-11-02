# LangChain Overview
> The framework that turns raw LLM calls into production AI applications.

## 📌 What Is It?

LangChain is an application framework for building software powered by Large Language Models.

The analogy:
```
Python     = programming language
FastAPI    = web framework
LangChain  = LLM application framework
```

A single `client.chat.completions.create(...)` call is easy. But a production AI assistant needs prompt management, retrieval, tools, memory, structured outputs, tracing, and evaluation. LangChain provides the building blocks so you don't wire all of this from scratch.

The core idea is **composable Runnables** — every piece (prompt, model, retriever, parser, tool) follows the same interface, so they can be connected into pipelines with minimal glue code:

```python
# This one line is the entire LangChain philosophy
chain = prompt | llm | StrOutputParser()
```

## ❓ Why Does It Exist?

A simple chatbot is easy. A production assistant is not.

**Without LangChain:**
```python
# Every provider has a different API
response = openai_client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}]
)
# Manual parsing, different format from Anthropic's response
answer = response.choices[0].message.content

# Custom RAG: you write all of this yourself
chunks = split_documents(docs)
embeddings = compute_embeddings(chunks)
results = vector_search(embeddings, query)
context = format_context(results)
```

**With LangChain:**
```python
# Provider-independent
llm = ChatGroq(model=os.getenv("LLM_MODEL"))

# RAG infrastructure built-in
retriever = vectorstore.as_retriever()

# Compose the pipeline
chain = prompt | llm | StrOutputParser()
```

LangChain solves: prompt management, provider abstraction, RAG infrastructure, agent frameworks, structured output, and observability — in a composable way.

## ⏰ When Should You Use It?

✅ Building RAG (retrieval + generation)  
✅ Building AI assistants with tools and agents  
✅ Building AI APIs (FastAPI + LangChain)  
✅ When you need LangSmith tracing for free  
✅ When you may switch LLM providers  
✅ Any production app needing prompts + models + retrieval  

❌ A single throw-away LLM call with no retrieval or tools  
❌ A simple script where the raw `openai` SDK is enough  
❌ When you need absolute minimal dependencies  

## 🗂️ Types / Variants

LangChain itself is a framework composed of focused packages:

| Package | Purpose | When to Import |
|---|---|---|
| `langchain_core` | Base abstractions: Runnables, prompts, messages | Always — this is the foundation |
| `langchain_community` | 3rd-party integrations: loaders, vector stores, tools | Connecting to external services |
| `langchain_groq` | Groq provider (ChatGroq) | Using Llama/Mixtral via Groq |
| `langchain_openai` | OpenAI provider (ChatOpenAI, OpenAIEmbeddings) | GPT-4o, text-embedding-3 |
| `langchain_anthropic` | Anthropic provider (ChatAnthropic) | Claude models |
| `langchain_ollama` | Local models via Ollama | Private inference on local hardware |

## 🔀 When to Use Which Type

Always import base classes from `langchain_core` — `ChatPromptTemplate`, `StrOutputParser`, `RunnableLambda`. This is stable and future-proof.

Import from provider-specific packages (`langchain_groq`, `langchain_openai`) for models and embeddings.

Import from `langchain_community` for loaders (`TextLoader`, `PyPDFLoader`), vector stores, and third-party integrations.

**Avoid bare `langchain` imports** (`from langchain.prompts import ...`) — the monolithic `langchain` package is being phased out in favor of these focused packages.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Rapid development with built-in components | Extra abstraction layer |
| Provider independence (swap models in one line) | Learning curve |
| Free LangSmith tracing with zero extra code | Rapidly evolving APIs |
| RAG, agents, memory all built-in | Can encourage over-engineering |
| Strong ecosystem (LangGraph, LangSmith) | Additional dependencies and package complexity |

## 💻 Basic Example

```python
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()  # reads GROQ_API_KEY from .env

# Step 1: define the model
llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)

# Step 2: define a reusable prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{question}"),   # {question} is filled at runtime
])

# Step 3: compose into a chain with LCEL pipe syntax
chain = prompt | llm | StrOutputParser()

# Step 4: run it
answer = chain.invoke({"question": "What is LangChain?"})
print(answer)
```

This is the core pattern. Every more complex LangChain application — RAG, agents, routers — is built on this same foundation.

## 🔧 Real-World Example

RetailOps uses a router pattern: one chain classifies the question, then dispatches to three specialized chains. Notice how each chain is small and focused. This is a simplified sketch: the real dispatcher is `run_router()` in `app/router.py`, and the real RAG chain also retrieves its own context and returns a structured `RAGResponse` (you'll build up to that in docs 08 and 18).

```python
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field

load_dotenv()

llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)

# ── Routing schema ─────────────────────────────────────────────────────────
class RouteDecision(BaseModel):
    route: str = Field(description="Exactly one of: general, rag, tools")
    reason: str = Field(description="Why this route was chosen")

# ── Three small, focused chains ────────────────────────────────────────────
general_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are RetailOps AI Assistant. Answer general questions."),
    ("human", "{question}"),
])
general_chain = general_prompt | llm | StrOutputParser()

rag_prompt = ChatPromptTemplate.from_messages([
    ("system", """Answer ONLY using the provided context.
If the answer is not present, say: "I don't know based on available documents." """),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])
rag_chain = rag_prompt | llm | StrOutputParser()

# ── Router chain ───────────────────────────────────────────────────────────
router_prompt = ChatPromptTemplate.from_messages([
    ("system", """Route the question to the correct workflow:
- general: greetings, small talk, general knowledge questions
- rag: questions about company policies, procedures, or documents
- tools: real-time data questions about inventory, orders, or incidents"""),
    ("human", "Question: {question}"),
])
router_chain = router_prompt | llm.with_structured_output(RouteDecision)

# ── Dispatcher ─────────────────────────────────────────────────────────────
def handle_question(question: str, context: str = "") -> str:
    """Route the question and dispatch to the correct chain."""
    decision = router_chain.invoke({"question": question})

    if decision.route == "rag":
        return rag_chain.invoke({"question": question, "context": context})
    elif decision.route == "tools":
        return f"[Tool execution required — routing to agent]"
    else:
        return general_chain.invoke({"question": question})

# Test it
print(handle_question(
    question="How many vacation days do we get?",
    context="Employees receive 18 days of paid vacation annually.",
))
# → "Employees receive 18 days of paid vacation annually."
```

## 🏭 Production Best Practices

1. **Keep prompts in a dedicated file (`app/prompts.py`)** — Prompts are application logic. Scattering them through chain definitions makes versioning and testing impossible. **How:** Define named constants (`rag_prompt`, `router_prompt`), import them everywhere.

2. **Use structured output for any machine-parsed response** — When your code needs to process a model response (routing decisions, evaluations, structured answers), use `llm.with_structured_output(MySchema)`. **Why:** Eliminates brittle string parsing that breaks whenever the model's phrasing changes.

3. **Keep chains small and single-responsibility** — One chain, one job. A chain that retrieves, routes, answers, and evaluates is impossible to test. **How:** `general_chain`, `rag_chain`, `router_chain` — each independently testable.

4. **Enable LangSmith from day one** — Add to `.env`: `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY=...`, `LANGSMITH_PROJECT=retailops-ai-assistant` (older tutorials use the `LANGCHAIN_TRACING_V2` / `LANGCHAIN_*` names for the same settings). Every chain call is traced automatically. **Why:** Debugging production AI without traces is guesswork.

5. **Use `langchain_core` imports, not bare `langchain`** — `from langchain_core.prompts import ChatPromptTemplate` is stable and future-proof. The bare `langchain` package is being deprecated.

6. **Don't use LangChain when you don't need it** — A 20-line script that makes one API call doesn't benefit from LangChain's overhead. The framework earns its keep when you need RAG, tools, memory, or tracing together.

## ⚠️ Common Mistakes to Avoid

⚠️ **Using LangChain for trivial one-off calls** — If you're calling an LLM once with no retrieval or tools, the raw SDK is simpler. LangChain is for applications, not scripts.

⚠️ **Building giant chains** — A single 200-line LCEL pipeline is untestable and unmaintainable. Compose small named chains instead.

⚠️ **Skipping evaluation** — "It looks good in testing" is not a metric. Add a golden dataset and measure answer quality from the start.

⚠️ **Ignoring LangSmith** — The most common response to LangChain bugs is "I don't know what it's doing inside." LangSmith shows you exactly what prompt was sent, what the model returned, and how long it took.

⚠️ **Using agents when a chain is sufficient** — Agents execute multiple LLM calls in a loop and are expensive and unpredictable. If the workflow steps are known in advance, use a chain.

## 🔗 How It Connects to Other Concepts

- **Chat Models** (doc 01) — The LLM provider wrapper; the engine inside every chain
- **Prompt Templates** (next: doc 03) — Define the instructions sent to the model; always the first step in a chain
- **LCEL** (doc 05) — The `|` pipe syntax that connects all components into pipelines
- **Runnables** (doc 06) — The interface every LangChain component implements (invoke/batch/stream)
- **RAG Chains** (doc 18) — The most important LangChain application pattern
- **LangGraph** (doc 33) — The next layer when chains need state, loops, or approvals

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Framework for building LLM-powered applications using composable Runnables |
| **Why** | Eliminates custom glue code for prompts, retrieval, tools, tracing, and structured output |
| **When** | RAG, agents, AI APIs, assistants — any non-trivial LLM application |
| **Types** | `langchain_core` (base), `langchain_community` (integrations), provider packages (`langchain_groq`, etc.) |
| **Production gotcha** | Use `langchain_core` imports; keep prompts separate; small focused chains; enable LangSmith from day one |

## ➡️ Next Steps

- **Example file:** `app/chains.py` — how RetailOps builds and exports its chains
- **Next doc:** `../03_prompt_templates/README.md` — the first component in every chain
- **Official docs:** https://python.langchain.com/docs/introduction/
