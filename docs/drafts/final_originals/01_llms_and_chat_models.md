# LLMs & Chat Models
> The engine and interface behind every LangChain application.

## 📌 What Is It?

A **Large Language Model (LLM)** is a neural network trained on massive text datasets to predict the next token in a sequence. It doesn't "think" — it generates the most statistically probable continuation of whatever input you give it.

A **Chat Model** is LangChain's wrapper around an LLM provider (OpenAI, Groq, Anthropic, Ollama). It normalizes their different APIs into one consistent interface your code can use, regardless of the underlying provider.

Think of it like this:
```
LLM         = the engine
Chat Model  = the steering wheel your application holds
```

A common misconception is that LLMs retrieve stored facts. They don't. When you ask "What is our return policy?", the model doesn't look anything up — it generates the most probable sequence of tokens given your prompt and any context you provided. This is why RAG exists.

## ❓ Why Does It Exist?

**The problem:** Every LLM provider has a completely different API.

Without LangChain's Chat Model abstraction:
```python
# OpenAI
client.chat.completions.create(model="gpt-4o", messages=[...])

# Anthropic
client.messages.create(model="claude-3-5-sonnet-20241022", messages=[...])

# Groq
client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[...])
```

Different SDKs. Different response formats. Different parameter names. If you switch providers, you rewrite code.

With LangChain:
```python
response = llm.invoke("What is our return policy?")
```

Works for every provider. Swap `ChatGroq` → `ChatOpenAI` in one line.

## ⏰ When Should You Use It?

✅ Any time your application needs to call an LLM  
✅ When you want provider-independent code  
✅ When building RAG, agents, or structured-output pipelines  
✅ When you need streaming responses for a chat UI  
✅ When you want automatic LangSmith tracing  
✅ When you may need to swap providers later  

❌ A single throw-away LLM call where raw SDK is simpler  
❌ A tiny script with no retrieval, tools, or pipelines  
❌ When you need absolute minimal dependencies  

## 🗂️ Types / Variants

| Type | Package | Best For |
|---|---|---|
| `ChatGroq` | `langchain_groq` | Speed + low cost — Llama/Mixtral models, great for RAG |
| `ChatOpenAI` | `langchain_openai` | GPT-4o, strong tool calling, highest quality |
| `ChatAnthropic` | `langchain_anthropic` | Claude models, long context, strong reasoning |
| `ChatOllama` | `langchain_ollama` | Local/private inference, no API cost |
| `ChatGoogleGenerativeAI` | `langchain_google_genai` | Gemini models, multimodal tasks |

## 🔀 When to Use Which Type

**RAG & production APIs** → `ChatGroq` (Llama 3.3 70B) or `ChatOpenAI` (gpt-4o-mini). Fast, cheap, reliable for factual answering.

**Complex reasoning or agent tasks** → `ChatOpenAI` (gpt-4o) or `ChatAnthropic` (claude-3-5-sonnet). Worth the higher cost for multi-step logic.

**Long documents (100k+ tokens)** → `ChatAnthropic` — best long-context performance of any provider.

**Private/sensitive data** → `ChatOllama` — runs entirely on your machine, no data leaves.

**Cost-sensitive bulk processing** → `ChatGroq` — often 10–50× cheaper than GPT-4o at similar quality for RAG tasks.

A common production pattern: route 90% of requests to a fast/cheap model (Groq, gpt-4o-mini) and only escalate complex queries to a premium model.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| One interface for all providers | Extra abstraction layer vs raw SDK |
| Swap providers in one line | Adds package dependencies |
| Built-in `invoke`, `stream`, `batch` | Rapidly evolving APIs cause occasional breaking changes |
| Native LangSmith tracing | Some provider-specific features need workarounds |
| Works in LCEL pipelines | Slight initialization overhead |

## 💻 Basic Example

```python
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()  # reads GROQ_API_KEY from .env file

# Initialize the model — do this once, reuse everywhere
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,      # deterministic — required for consistent RAG answers
    max_tokens=500,     # cap output to control cost and latency
)

# invoke() — single synchronous call, returns AIMessage
response = llm.invoke("What is a context window?")
print(response.content)

# Pass structured messages explicitly
response = llm.invoke([
    SystemMessage(content="You are a retail operations assistant."),
    HumanMessage(content="What causes inventory shrinkage?"),
])
print(response.content)

# stream() — yield tokens one at a time for ChatGPT-style UX
for chunk in llm.stream("Explain temperature in one paragraph."):
    print(chunk.content, end="", flush=True)

# batch() — process multiple inputs in parallel
responses = llm.batch([
    "Explain RAG in one sentence",
    "Explain function calling in one sentence",
])
for r in responses:
    print(r.content)
```

## 🔧 Real-World Example

This mirrors RetailOps' `app/llm.py`. Notice the singleton initialization pattern, structured output, and temperature discipline.

```python
import os
import asyncio
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field

load_dotenv()

# ── Structured output schemas (app/schemas.py in RetailOps) ─────────────
class RAGResponse(BaseModel):
    answer: str = Field(description="Answer based only on the provided context")
    sources: list[str] = Field(description="Source document names cited")
    confidence: str = Field(description="Confidence level: high | medium | low")

class RouteDecision(BaseModel):
    route: str = Field(description="Exactly one of: general, rag, tools")
    reasoning: str = Field(description="Why this route was chosen")

# ── Singleton model initialization (app/llm.py) ──────────────────────────
def get_llm() -> ChatGroq:
    """Base LLM. temperature=0 for consistent, deterministic outputs."""
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        max_tokens=1000,
    )

def get_structured_llm(schema: type) -> ChatGroq:
    """LLM constrained to return a specific Pydantic schema."""
    return get_llm().with_structured_output(schema)

# ── General chat chain ────────────────────────────────────────────────────
llm = get_llm()

general_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are RetailOps AI Assistant. Be concise and accurate."),
    ("human", "{question}"),
])

general_chain = general_prompt | llm | StrOutputParser()

answer = general_chain.invoke({"question": "What does a warehouse picker do?"})
print(answer)

# ── Structured RAG chain ──────────────────────────────────────────────────
rag_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are RetailOps AI Assistant.
Answer ONLY using the provided context.
If the answer is not in the context, say: "I don't know based on available documents." """),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])

structured_llm = get_structured_llm(RAGResponse)
rag_chain = rag_prompt | structured_llm

result = rag_chain.invoke({
    "context": "Employees receive 18 days of paid vacation annually.",
    "question": "How many vacation days do employees receive?",
})

print(result.answer)      # "Employees receive 18 days of paid vacation annually."
print(result.confidence)  # "high"
print(result.sources)     # []

# ── Async streaming for web UI ────────────────────────────────────────────
async def stream_answer(question: str) -> None:
    """Stream tokens as they arrive — better UX for chat interfaces."""
    async for chunk in general_chain.astream({"question": question}):
        print(chunk, end="", flush=True)
    print()

asyncio.run(stream_answer("Explain the difference between RAG and fine-tuning."))
```

## 🏭 Production Best Practices

1. **Initialize the model once, reuse everywhere** — Define `get_llm()` in `app/llm.py` and import it everywhere. **Why:** Creating a new `ChatGroq(...)` on every request wastes connections and causes configuration drift where different handlers use different settings without realizing it.

2. **Use `temperature=0` for RAG and classification** — Deterministic outputs are mandatory for consistent answers. At `temperature=1`, the same question can produce different answers on each call, which destroys user trust. **How:** `ChatGroq(temperature=0)`. Reserve 0.5–0.7 for general assistants.

3. **Always set `max_tokens`** — Without a cap, a prompt bug or adversarial input can generate thousands of tokens per request, spiking costs. **How:** `max_tokens=500` for most RAG answers; increase only for tasks that genuinely need long output.

4. **Use `with_structured_output()` for parsed responses** — Any response your code must process (routing decisions, evaluations, structured answers) should return a Pydantic object, not a string. **Why:** Eliminates fragile `response.split(":")` parsing that breaks when the model's phrasing changes.

5. **Never hardcode API keys** — Use `python-dotenv`. **How:** `GROQ_API_KEY=...` in `.env`, call `load_dotenv()` at startup. LangChain reads provider keys from environment variables automatically.

6. **Stream user-facing chat responses** — Users perceive streaming as faster even when total latency is equal. **How:** `async for chunk in chain.astream({"question": q}): ...` in your FastAPI endpoint.

7. **Use LangSmith tracing from day one** — Set `LANGCHAIN_TRACING_V2=true` in `.env`. Every model call, token count, and latency is logged automatically. **Why:** Debugging a production AI system without traces is guesswork.

## ⚠️ Common Mistakes to Avoid

⚠️ **High temperature for RAG** — `temperature=1.0` causes different answers to the same question on every call. Always use `temperature=0` for retrieval-based tasks.

⚠️ **Recreating the model on every request** — `ChatGroq(...)` inside a FastAPI route handler means a new connection and config check on every request. Initialize once at startup.

⚠️ **Using the most expensive model for everything** — GPT-4o costs significantly more than Groq's Llama. Reserve premium models for complex reasoning; use fast/cheap models for routine RAG.

⚠️ **Assuming embeddings store knowledge** — Embeddings represent *meaning* (similarity), not facts. The LLM still needs context injected via RAG to answer questions about your documents.

⚠️ **Skipping `max_tokens`** — A single uncapped runaway response can spike your monthly bill. Always cap output.

⚠️ **Fine-tuning instead of RAG for company knowledge** — Fine-tuning changes behavior and style. RAG injects knowledge. For policies, FAQs, and documents: use RAG. It's cheaper, faster to update, and doesn't require retraining the model.

## 🔗 How It Connects to Other Concepts

- **Prompt Templates** (next: doc 03) — You almost never call `llm.invoke("raw string")` in production. Use `ChatPromptTemplate` to build structured messages, then pipe into the LLM.
- **LCEL** (doc 05) — Chat models are Runnables and participate in `prompt | llm | parser` pipelines.
- **Output Parsers** (doc 07) — `StrOutputParser` converts `AIMessage` → `str`; `with_structured_output()` converts it to a Pydantic object.
- **RAG Chains** (doc 18) — The LLM is the final generation step, receiving retrieved context as input.
- **Agents** (doc 21) — Agents use the LLM's function-calling capability to decide which tool to invoke.
- **LangSmith** (doc 27) — All LLM calls are automatically traced when LangSmith is enabled.

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | LangChain wrappers around LLM providers (Groq, OpenAI, Anthropic, Ollama) |
| **Why** | Unified `invoke/stream/batch` interface for all providers; integrates with LCEL, tracing, structured output |
| **When** | Any time your application needs to call an LLM |
| **Types** | `ChatGroq` (fast/cheap), `ChatOpenAI` (quality), `ChatAnthropic` (long context), `ChatOllama` (local) |
| **Production gotcha** | `temperature=0` for RAG; always set `max_tokens`; initialize once; use `with_structured_output()` for parsed responses |

## ➡️ Next Steps

- **Example file:** `app/llm.py` — RetailOps model initialization and structured output setup
- **Next doc:** `02_langchain_overview.md` — the full framework these models belong to
- **Official docs:** https://python.langchain.com/docs/integrations/chat/
