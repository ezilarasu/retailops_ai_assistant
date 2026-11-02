# RAG Chains (End-to-End)
> Putting it all together — retrieval + generation in a complete, production-ready pipeline.

## 📌 What Is It?

A **RAG chain** (Retrieval-Augmented Generation) is an LCEL pipeline that combines document retrieval with LLM generation to answer questions from a knowledge base.

The simplest possible RAG chain:
```python
rag_chain = (
    RunnableParallel({"context": retriever | format_docs, "question": RunnablePassthrough()})
    | rag_prompt
    | llm
    | StrOutputParser()
)
```

The RetailOps production RAG chain adds history-aware rewriting, multi-query expansion, hybrid search, cross-encoder reranking, and structured output with source attribution:

```
User question
 ↓ Question rewriter (history-aware → standalone question)
 ↓ Multi-query generator (1 question → 3 alternate phrasings)
 ↓ Hybrid retriever (vector search + BM25, k=10 candidates per query)
 ↓ Merge + deduplicate
 ↓ Cross-encoder reranker (top 4 from merged candidates)
 ↓ RAG prompt (context + question → structured LLM)
 ↓ RAGResponse(answer, sources, confidence)
```

Every component from docs 11–17 feeds into this pipeline.

## ❓ Why Does It Exist?

LLMs are trained on public data up to a knowledge cutoff. Enterprise knowledge — HR policies, store SOPs, incident runbooks, product documentation — is private and never in the training data.

RAG solves this by injecting relevant knowledge at query time:
```
Without RAG:
  "What is the vacation policy?" → LLM guesses from training data → unreliable

With RAG:
  "What is the vacation policy?" → retrieve hr_policy.txt chunks → LLM answers from evidence
```

The key constraint: the RAG prompt must say **"Answer ONLY using the provided context."** This prevents hallucination — the LLM doesn't fill in gaps from training data.

## ⏰ When Should You Use It?

✅ Any time you need an LLM to answer from a private knowledge base  
✅ Internal assistants for HR, IT, operations, compliance  
✅ Customer-facing support bots grounded in your documentation  
✅ Whenever you need source attribution alongside answers  

❌ Don't use RAG for real-time operational data (inventory counts, live orders) — use Tools  
❌ Don't use RAG for data that changes more than once a day  
❌ Don't skip the "Answer ONLY from context" constraint — without it, the LLM will hallucinate  

## 🗂️ Types / Variants

| Type | Components | Best For |
|---|---|---|
| **Basic RAG** | Single retriever + RAG prompt + LLM | Prototyping, simple document Q&A |
| **Conversational RAG** | + Question rewriter + chat history | Multi-turn conversations |
| **Production RAG** | + Multi-query + hybrid + reranking | High-accuracy enterprise deployments |
| **Structured RAG** | + `with_structured_output(RAGResponse)` | APIs that need answer + sources + confidence |

## 🔀 When to Use Which Type

**Start with basic RAG** — get it working end-to-end before adding complexity. Many systems work well with just an MMR retriever and a grounded prompt.

**Add conversational RAG** as soon as users start asking follow-up questions. History-aware rewriting is a low-effort, high-impact upgrade.

**Upgrade to production RAG** when evaluation shows retrieval is the bottleneck — low source accuracy, questions about exact codes/SKUs failing, or incomplete answers.

**Use structured RAG** whenever the output feeds into application logic (a UI that renders sources separately, an API returning JSON, an evaluation pipeline that needs to check fields).

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Answers from private knowledge without fine-tuning | Retrieval quality caps answer quality — garbage in, garbage out |
| Source attribution builds user trust | Requires good chunking, embeddings, and retrieval pipeline |
| "Answer only from context" constraint reduces hallucination | More moving parts than a simple LLM call |
| LCEL makes each stage swappable | Evaluation is essential — hard to know quality without it |
| Structured output enables downstream logic | |

## 💻 Basic Example

```python
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Build a minimal vector store
docs = [
    Document(page_content="Employees receive 18 days of paid vacation annually.", metadata={"source": "hr_policy.txt"}),
    Document(page_content="P1 incidents mean full store outage. Report immediately to IT.", metadata={"source": "it_kb.txt"}),
    Document(page_content="Returns must be processed within 30 days of purchase.", metadata={"source": "returns_policy.txt"}),
]
vectorstore = Chroma.from_documents(docs, embedding=embeddings)
retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 3})

# ── The grounded RAG prompt ───────────────────────────────────────────────
RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are RetailOps AI Assistant.
Answer ONLY using the provided context. Do not use prior knowledge.
If the answer is not in the context, say: "I don't know based on available documents." """),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])

def format_docs(docs: list[Document]) -> str:
    """Convert list of Documents into context string with source labels."""
    return "\n\n".join(
        f"[Source: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
        for doc in docs
    )

# ── Basic RAG chain ───────────────────────────────────────────────────────
rag_chain = (
    RunnableParallel({
        "context": retriever | RunnableLambda(format_docs),  # retrieve and format
        "question": RunnablePassthrough(),                   # pass question through
    })
    | RAG_PROMPT
    | llm
    | StrOutputParser()
)

# Input is just the question string for basic RAG
answer = rag_chain.invoke("How many vacation days do employees get?")
print(answer)
# → "Employees receive 18 days of paid vacation annually."

# Streaming for UI integration
for chunk in rag_chain.stream("What does P1 mean?"):
    print(chunk, end="", flush=True)
print()
```

## 🔧 Real-World Example

The full RetailOps RAG chain — structured output, source attribution, history-aware rewriting, and the production prompt constraint. This is `app/rag.py`.

```python
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from langchain_core.documents import Document
from pydantic import BaseModel, Field

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# ══════════════════════════════════════════════════════════════════════════
# app/rag.py — RetailOps end-to-end RAG chain
# ══════════════════════════════════════════════════════════════════════════

# ── Structured response schema ────────────────────────────────────────────
class RAGResponse(BaseModel):
    answer: str = Field(
        description="Answer based ONLY on the provided context. "
                    "If not found, write: 'I don't know based on available documents.'"
    )
    sources: list[str] = Field(
        description="List of source document filenames cited in the answer"
    )
    confidence: str = Field(
        description="Confidence in the answer: high | medium | low"
    )


# ── Production RAG prompt ─────────────────────────────────────────────────
RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are RetailOps AI Assistant — a helpful assistant for retail store employees.

STRICT RULES:
1. Answer ONLY using the provided Context. Never use prior knowledge.
2. If the answer is not in the Context, set answer to "I don't know based on available documents."
3. List every source document you reference in the sources field.
4. Set confidence based on how directly the context answers the question:
   - high: context directly and completely answers the question
   - medium: context partially answers or requires inference
   - low: context only tangentially relates to the question"""),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])


def format_docs(docs: list[Document]) -> str:
    """Format retrieved docs as numbered context blocks with source labels."""
    if not docs:
        return "No relevant documents found."

    blocks = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "unknown")
        blocks.append(f"[{i}] Source: {source}\n{doc.page_content}")
    return "\n\n".join(blocks)


def build_rag_chain(retriever):
    """Build the basic RAG chain.

    Input:  {"question": str}  (or just str for simple chains)
    Output: RAGResponse(answer, sources, confidence)
    """
    structured_llm = llm.with_structured_output(RAGResponse)

    return (
        RunnableParallel({
            "context": retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough() | RunnableLambda(
                lambda x: x["question"] if isinstance(x, dict) else x
            ),
        })
        | RAG_PROMPT
        | structured_llm
    )


def build_conversational_rag_chain(retriever, rewriter=None):
    """Build RAG chain that handles multi-turn conversations.

    Adds history-aware question rewriting before retrieval.

    Input:  {"question": str, "history": list[dict]}
    Output: RAGResponse(answer, sources, confidence)
    """
    structured_llm = llm.with_structured_output(RAGResponse)

    def get_retrieval_query(inputs: dict) -> str:
        """Rewrite follow-up to standalone if history present."""
        question = inputs["question"]
        history = inputs.get("history", [])

        if not rewriter or not history:
            return question

        # Format last 4 turns for the rewriter
        history_lines = []
        for msg in history[-4:]:
            role = "User" if msg.get("role") == "user" else "Assistant"
            history_lines.append(f"{role}: {msg['content']}")
        history_str = "\n".join(history_lines)

        rewritten = rewriter.invoke({"history": history_str, "question": question})
        return rewritten

    return (
        RunnableParallel({
            "context": RunnableLambda(get_retrieval_query)
                       | retriever
                       | RunnableLambda(format_docs),
            "question": RunnablePassthrough() | RunnableLambda(lambda x: x["question"]),
        })
        | RAG_PROMPT
        | structured_llm
    )


# ── Application-level usage ────────────────────────────────────────────────
# From main.py / FastAPI:
#
# vectorstore = initialize_vectorstore()
# retriever = build_reranking_retriever(vectorstore, all_docs)  # hybrid + reranking
# rewriter = build_question_rewriter()
# rag_chain = build_conversational_rag_chain(retriever, rewriter=rewriter)
#
# # First turn:
# result = rag_chain.invoke({"question": "How many vacation days?", "history": []})
# print(result.answer)     # "Employees receive 18 paid vacation days annually."
# print(result.sources)    # ["hr_policy.txt"]
# print(result.confidence) # "high"
#
# # Follow-up:
# result = rag_chain.invoke({
#     "question": "What about part-time?",
#     "history": [
#         {"role": "user", "content": "How many vacation days?"},
#         {"role": "assistant", "content": result.answer},
#     ],
# })
# # Rewriter produces: "What is the vacation policy for part-time employees?"
```

## 🏭 Production Best Practices

1. **Always use "Answer ONLY from context" in the system prompt** — This is the single most important prompt constraint in a RAG system. Without it, the LLM uses its training data to fill in gaps and hallucinations become unpredictable. **How:** `"Answer ONLY using the provided Context. Never use prior knowledge."`

2. **Use structured output (`RAGResponse`) instead of plain text** — Structured output gives you answer + sources + confidence as typed fields. The sources field enables attribution in the UI; the confidence field enables escalation logic. **How:** `llm.with_structured_output(RAGResponse)`.

3. **Always include source metadata in formatted context** — `[Source: hr_policy.txt]` before each chunk lets the LLM populate `sources` accurately. Without it, the LLM can't attribute answers correctly. **How:** `f"[Source: {doc.metadata.get('source')}]\n{doc.page_content}"`.

4. **Build incrementally and evaluate at each step** — Start with basic RAG → evaluate → add rewriting if conversational quality is low → add multi-query if recall is low → add hybrid if exact terms fail. Don't add everything at once. **How:** Run the evaluation pipeline (doc 19) after each addition.

5. **Handle the "not found" case explicitly** — Tell the LLM exactly what to say when the answer isn't in context. Vague instructions produce vague "I don't know" responses. **How:** `"If not found, set answer to: 'I don't know based on available documents.'"` — this exact string is easier to detect programmatically.

6. **Use `temperature=0` for the RAG LLM** — RAG is about retrieval + synthesis, not creativity. Deterministic output makes evaluation and debugging reproducible. **How:** `ChatGroq(model="llama-3.3-70b-versatile", temperature=0)`.

## ⚠️ Common Mistakes to Avoid

⚠️ **No "Answer only from context" constraint** — Without this, the LLM will supplement missing context with training data, and hallucinations are indistinguishable from real answers. This is the most common production RAG failure.

⚠️ **No source attribution** — When a user gets a wrong answer, they need to know where it came from to verify or escalate. Without sources, trust collapses. Always return the source document names.

⚠️ **Using vector-only retrieval** — The full pipeline (hybrid + reranking) exists for a reason. Skipping it means failing on exact-term queries and missing answers that a better retriever would have found.

⚠️ **No retrieval evaluation** — Tuning the RAG prompt when the problem is actually retrieval quality is a common trap. Always diagnose whether failures are retrieval failures or generation failures first.

⚠️ **Sending raw `AIMessage` to application code** — Add `StrOutputParser()` or `with_structured_output()` at the chain end. Callers should receive clean types, not LangChain objects.

## 🔗 How It Connects to Other Concepts

- **History-Aware Retrieval** (doc 17) — Rewriting feeds into the retrieval step; conversational RAG builds on top of basic RAG
- **Hybrid Search** (doc 14) — The retriever in the RAG chain; replaces simple vector search for better coverage
- **Cross-Encoder Reranking** (doc 15) — The reranker sits between retrieval and context formatting; improves precision
- **Structured Output** (doc 08) — `RAGResponse` schema provides typed answer + sources + confidence
- **RAG Evaluation** (next: doc 19) — Measures how well this chain performs; reveals which component is the bottleneck

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | LCEL pipeline combining document retrieval with grounded LLM generation to answer questions from private knowledge |
| **Why** | LLMs don't know your private data; RAG injects relevant evidence at query time to produce grounded answers |
| **When** | Any internal knowledge assistant, support bot, or documentation Q&A system |
| **Types** | Basic RAG, Conversational RAG (+ rewriting), Production RAG (+ multi-query + hybrid + reranking), Structured RAG |
| **Production gotcha** | Always use "Answer ONLY from context"; use `RAGResponse` structured output; include source labels in context; evaluate retrieval separately from generation |

## ➡️ Next Steps

- **Example file:** `app/rag.py` — RetailOps `build_rag_chain()` and `build_conversational_rag_chain()`
- **Next doc:** `19_rag_evaluation.md` — measuring retrieval quality, answer correctness, groundedness, and completeness
- **Official docs:** https://python.langchain.com/docs/tutorials/rag/
