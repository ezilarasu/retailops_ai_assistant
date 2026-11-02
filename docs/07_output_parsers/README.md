# Output Parsers
> The last step in every chain — converting raw LLM output into types your application can use.

## 📌 What Is It?

An **Output Parser** is a Runnable that sits at the end of an LCEL chain and converts the LLM's raw `AIMessage` into whatever type your application actually needs — a `str`, `dict`, `list`, or a Pydantic object.

Without a parser, every LLM call returns an `AIMessage`:
```python
response = llm.invoke("What is RAG?")
# → AIMessage(content="RAG stands for Retrieval Augmented Generation...")
```

With `StrOutputParser`:
```python
chain = prompt | llm | StrOutputParser()
result = chain.invoke({"question": "What is RAG?"})
# → "RAG stands for Retrieval Augmented Generation..."
```

Think of it like a USB adapter: the LLM speaks one format, your application speaks another, and the parser bridges the gap.

## ❓ Why Does It Exist?

LLMs always return `AIMessage` objects. Applications usually need something simpler.

**Without parsers**, every consumer of a chain must know to call `.content`:
```python
response = chain.invoke(input)
# Different code everywhere:
text = response.content        # if it's an AIMessage
data = json.loads(response.content)  # if you expect JSON
```

**With parsers**, the chain itself handles conversion — callers just get the type they need:
```python
chain = prompt | llm | StrOutputParser()
answer = chain.invoke(input)   # already a str, no .content needed
```

This makes chains composable — the output of one chain can flow directly as input to the next without manual extraction.

## ⏰ When Should You Use It?

✅ Almost always — `StrOutputParser` should be the default final step in conversational chains  
✅ When chaining multiple chains and the output feeds into the next input  
✅ When the downstream code expects `str`, `dict`, or `list` rather than `AIMessage`  
✅ For general chat, question rewriting, multi-query generation, and any free-text generation  

❌ When you need structured data with validation — use `with_structured_output()` instead (see doc 08)  
❌ When you need to access `AIMessage` metadata (token usage, model name) — access `.content` manually  

## 🗂️ Types / Variants

| Type | Class | Output Type | Best For |
|---|---|---|---|
| String parser | `StrOutputParser` | `str` | General chat, text generation, rewriting |
| JSON parser | `JsonOutputParser` | `dict` | When the LLM is prompted to return JSON (but not constrained to) |
| Pydantic parser | `PydanticOutputParser` | Pydantic model | Structured data extraction with format instructions in the prompt |
| List parser | `CommaSeparatedListOutputParser` | `list[str]` | When model returns comma-separated values |
| Structured output | `llm.with_structured_output(Schema)` | Pydantic model | **Preferred** for production structured data — model is *constrained*, not just prompted |

## 🔀 When to Use Which Type

**Use `StrOutputParser`** for everything that produces conversational or free-text output: general chat chains, question rewriters, multi-query generators, summarization, and any chain where text is the end product.

**Use `with_structured_output(Schema)`** (doc 08) when your code must parse the response — routing decisions, RAG responses with sources and confidence, evaluation scores. This is more reliable than `JsonOutputParser` because the model is constrained at the API level, not just prompted.

**Use `JsonOutputParser` or `PydanticOutputParser`** as a fallback for models that don't support native function calling / structured output (some local Ollama models). Pair with format instructions in the prompt.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Makes chains composable — output ready to pipe | Only converts format; does not constrain model output |
| Removes `.content` boilerplate everywhere | `JsonOutputParser` can fail if the model doesn't follow format instructions |
| `StrOutputParser` is streaming-friendly — works with `stream()` | |
| Typed output makes downstream code cleaner | |

## 💻 Basic Example

```python
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import (
    StrOutputParser,
    JsonOutputParser,
    CommaSeparatedListOutputParser,
)

load_dotenv()

llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)

# ── StrOutputParser: AIMessage → str ─────────────────────────────────────
str_chain = (
    ChatPromptTemplate.from_messages([("human", "{question}")])
    | llm
    | StrOutputParser()   # converts AIMessage to plain string
)

answer = str_chain.invoke({"question": "What is LCEL?"})
print(type(answer))   # str
print(answer)

# ── StrOutputParser works with stream() ──────────────────────────────────
for chunk in str_chain.stream({"question": "Explain vector databases."}):
    print(chunk, end="", flush=True)   # chunk is str, not AIMessage
print()

# ── CommaSeparatedListOutputParser ───────────────────────────────────────
list_parser = CommaSeparatedListOutputParser()

list_chain = (
    ChatPromptTemplate.from_messages([
        ("human", "List 5 common RAG optimizations, comma-separated. No explanation."),
    ])
    | llm
    | list_parser
)

optimizations = list_chain.invoke({})
print(type(optimizations))  # list
print(optimizations)        # ['hybrid search', 'reranking', 'semantic chunking', ...]

# ── Without parser: what you get from raw llm.invoke() ───────────────────
raw_response = llm.invoke("What is chunking?")
print(type(raw_response))   # AIMessage
print(raw_response.content) # you must call .content manually
```

## 🔧 Real-World Example

This is a simplified version of how RetailOps uses parsers in `app/chains.py` and `app/multi_query.py`. Notice that conversational chains (general chat, question rewriting, multi-query) use `StrOutputParser`, while structured data (routing, RAG responses) uses `with_structured_output()` instead of a parser. In the real multi-query code, the split-into-lines step is a plain Python function (`generate_queries()`) rather than a `RunnableLambda` in the chain; the version below shows the LCEL way to do the same thing.

```python
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field

load_dotenv()

llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)

# ══════════════════════════════════════════════════════════════════════════
# CHAIN 1: General chat — StrOutputParser (free text, streaming-friendly)
# ══════════════════════════════════════════════════════════════════════════
general_chain = (
    ChatPromptTemplate.from_messages([
        ("system", "You are RetailOps AI Assistant. Be concise."),
        ("human", "{question}"),
    ])
    | llm
    | StrOutputParser()  # returns str, ready for JSON response or stream
)

answer = general_chain.invoke({"question": "What is a planogram?"})
print(f"Answer type: {type(answer)}")   # str
print(f"Answer: {answer[:100]}")

# ══════════════════════════════════════════════════════════════════════════
# CHAIN 2: Question rewriter — StrOutputParser (rewritten question is text)
# ══════════════════════════════════════════════════════════════════════════
rewriter_chain = (
    ChatPromptTemplate.from_messages([
        ("system", "Rewrite the follow-up as a standalone question. Return only the question."),
        ("human", "History: {history}\nFollow-up: {question}"),
    ])
    | llm
    | StrOutputParser()  # rewritten question is a string — pipe directly to retriever
)

standalone = rewriter_chain.invoke({
    "history": "User asked about vacation days for full-time employees.",
    "question": "What about part-time?",
})
print(f"Rewritten: {standalone}")
# → "What is the vacation day policy for part-time employees?"
# This string feeds directly into the retriever

# ══════════════════════════════════════════════════════════════════════════
# CHAIN 3: Multi-query generator — StrOutputParser then split
# ══════════════════════════════════════════════════════════════════════════
from langchain_core.runnables import RunnableLambda

multi_query_chain = (
    ChatPromptTemplate.from_messages([
        ("system", "Generate 3 alternative phrasings. One per line. No numbering."),
        ("human", "Question: {question}"),
    ])
    | llm
    | StrOutputParser()
    | RunnableLambda(lambda text: [q.strip() for q in text.strip().split("\n") if q.strip()])
)

alternatives = multi_query_chain.invoke({"question": "How much PTO do employees get?"})
print(f"Type: {type(alternatives)}")  # list
print(f"Alternatives: {alternatives}")

# ══════════════════════════════════════════════════════════════════════════
# CHAIN 4: Router — with_structured_output() (NOT StrOutputParser)
# When routing logic depends on the response, constrain the schema
# ══════════════════════════════════════════════════════════════════════════
class RouteDecision(BaseModel):
    route: str = Field(description="Exactly one of: general, rag, tools")
    reason: str = Field(description="Why this route was chosen")

router_chain = (
    ChatPromptTemplate.from_messages([
        ("system", "Route: general (small talk), rag (policies/docs), tools (live data)."),
        ("human", "{question}"),
    ])
    | llm.with_structured_output(RouteDecision)  # constrained, not just parsed
)

decision = router_chain.invoke({"question": "How many units of SKU-123 are in stock?"})
print(f"Route: {decision.route}")     # "tools"
print(f"Why: {decision.reason}")

# ══════════════════════════════════════════════════════════════════════════
# CHAIN 5: Composing chains — StrOutputParser enables piping
# ══════════════════════════════════════════════════════════════════════════
# Rewriter output (str) → retriever input (str) — works because parser converted it
async def full_conversational_flow(history: str, question: str) -> None:
    """Rewrite → stream answer. Parser makes the rewritten question directly usable."""
    standalone_q = rewriter_chain.invoke({"history": history, "question": question})

    # standalone_q is already a str — pipe directly to general chain
    async for chunk in general_chain.astream({"question": standalone_q}):
        print(chunk, end="", flush=True)
    print()

import asyncio
asyncio.run(full_conversational_flow(
    history="User asked about vacation policy.",
    question="What about sick leave?",
))
```

## 🏭 Production Best Practices

1. **Default to `StrOutputParser` for conversational chains** — Every chain that produces text for display should end with `StrOutputParser()`. It's streaming-compatible, composable, and removes the `.content` extraction from every consumer.

2. **Use `with_structured_output()` over `JsonOutputParser` for structured data** — `with_structured_output()` constrains the model at the API level using function calling. `JsonOutputParser` only prompts the model to return JSON — it can ignore the instruction. **How:** `llm.with_structured_output(MySchema)` (see doc 08 for full details).

3. **Chain parsers to transformations using `RunnableLambda`** — When you need to further process parser output (e.g., split a string into a list, strip a prefix), add a `RunnableLambda` after the parser inside the chain. **How:** `| StrOutputParser() | RunnableLambda(lambda t: t.strip().split("\n"))`.

4. **Treat parsed output types as contracts** — If your chain ends with `StrOutputParser`, the downstream code expects `str`. If the parser changes, downstream code breaks. Document the output type in the chain definition. **How:** Add a type hint comment: `# returns: str`.

5. **Use `StrOutputParser` for streaming** — `AIMessage` chunks during streaming contain partial content. `StrOutputParser` handles this transparently — it works in both `stream()` and `invoke()` modes. `JsonOutputParser` also supports streaming (yields partial dicts), but only if the JSON is valid when complete.

## ⚠️ Common Mistakes to Avoid

⚠️ **Manually calling `.content` everywhere** — If you're writing `response.content` throughout your codebase, you've forgotten to add `StrOutputParser()` to the chain. One parser in the chain removes the need for `.content` everywhere.

⚠️ **Using `JsonOutputParser` for routing decisions** — The model can ignore format instructions and return free text. Use `llm.with_structured_output(RouteDecision)` for any output your application logic depends on.

⚠️ **Forgetting parsers break streaming** — `PydanticOutputParser` and some custom parsers accumulate the full response before parsing — they don't stream. `StrOutputParser` and `JsonOutputParser` do stream. Verify streaming behavior before using a parser in a streaming endpoint.

⚠️ **Overcomplicating with custom parsers** — Before writing a custom output parser class, check if `StrOutputParser() | RunnableLambda(your_function)` achieves the same result with less code.

## 🔗 How It Connects to Other Concepts

- **Runnables** (doc 06) — Parsers are Runnables; they plug into `prompt | llm | parser` chains
- **LCEL** (doc 05) — Parsers are always the final `|` step, transforming model output to application types
- **Structured Output** (next: doc 08) — The alternative to output parsers for structured data; constrains output rather than converting it
- **RAG Chains** (doc 18) — RAG uses `StrOutputParser` for conversational output and `with_structured_output()` for typed `RAGResponse` objects
- **LangSmith** (doc 27) — Parser output is visible as the final step in every LangSmith trace

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Runnables that convert LLM `AIMessage` output into `str`, `dict`, `list`, or Pydantic objects |
| **Why** | Removes `.content` boilerplate; makes chains composable; enables downstream code to use typed values |
| **When** | The final step in any chain where callers should receive a usable type, not a raw `AIMessage` |
| **Types** | `StrOutputParser` (default for text), `JsonOutputParser` (dict), `CommaSeparatedListOutputParser` (list); `with_structured_output()` for validated objects |
| **Production gotcha** | Use `StrOutputParser` for text/streaming chains; use `with_structured_output()` for parsed structured data — it's more reliable than `JsonOutputParser` |

## ➡️ Next Steps

- **Example file:** `app/chains.py` — all RetailOps chains use `StrOutputParser` or `with_structured_output()`
- **Runnable demo:** `examples/06_basic_rag_with_parser.py` also shows a parser in a RAG chain — see `18_rag_chains/RUN.md` for how to run it
- **Next doc:** `../08_structured_output/README.md` — the production-grade alternative for structured data
- **Official docs:** https://python.langchain.com/docs/concepts/output_parsers/
