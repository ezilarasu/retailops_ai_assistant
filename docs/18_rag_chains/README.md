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
 ↓ Question rewriter (follow-ups only: history-aware → standalone question)
 ↓ Multi-query generator (1 question → 3 alternate phrasings)
 ↓ Hybrid retriever (vector search with k=RETRIEVAL_K + up to 10 BM25 results, per query)
 ↓ Merge + deduplicate
 ↓ Cross-encoder reranker (keeps up to RETRIEVAL_K of the merged candidates, 2 in .env.example, dropping clearly irrelevant ones)
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
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

load_dotenv()

llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)
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

`examples/06_basic_rag_with_parser.py` is this same basic pattern on the real RetailOps data: the MMR retriever from `get_retriever()`, the real `rag_prompt`, and a `StrOutputParser` at the end (so it returns plain text, no sources). The real `rag_prompt` has two variables, `{context}` and `{rewritten_question}`; this example does no question rewriting, so it passes the original question as `rewritten_question`.

## 🔧 Real-World Example

The full RetailOps RAG chain — structured output, source attribution, history-aware rewriting, and the production prompt constraint. This is `app/chains.py`, using the document helpers from `app/rag.py`. The listing below is the real code with the timing and per-document logging lines removed for readability.

Things to know before you read it:

- **The chain is assembled from separate pieces.** `build_retriever()` (load, chunk, index, hybrid retriever), `build_question_rewriter_chain()`, and `build_rag_generator()` (prompt + structured model) are built once by `get_container()` in `app/container.py`. `build_rag_chain(retriever, rewriter_chain, generator)` just wires them together. Sharing the pieces is what lets the `/debug/retrieval` endpoint and the LangGraph version (doc 33) reuse the same retriever instead of building their own. Called with no arguments (as `examples/07_structured_rag_output.py` does), `build_rag_chain()` builds everything itself.
- **Building the retriever is the slow part**, which is why the app creates it once instead of per request. Re-adding the same chunks to the persisted Chroma collection on every start is harmless: chunks have stable IDs and Chroma replaces them instead of duplicating them (doc 12).
- **A first question skips the rewrite call.** `rewrite_question()` returns the question unchanged when there is no chat history, so a first-turn RAG question makes three LLM calls (router, multi-query, answer) rather than four.
- **The real prompt** (`rag_prompt` in `app/prompts.py`) uses the rewritten question as its `{rewritten_question}` variable. It tells the model to answer only from the context, not to use outside knowledge, to answer "I don't know based on the available RetailOps documents." when the context lacks the answer, to cite source names, and to set `confidence` to high, medium or low depending on how directly the context supports the answer.
- **Output** is a `RAGResponse` (`answer`, `sources`, `confidence`) from `llm.with_structured_output(RAGResponse)` — no output parser is involved (docs 07–08).

> **Lesson from this project:** measure where the time goes before optimizing. With the model calls themselves taking a few hundred milliseconds each, one RAG question took 27.7 seconds in our first log. About 22 of those seconds were waiting after "429 Too Many Requests" rate-limit replies (a model with too small a per-minute token limit, and four model calls per question), and about 2 seconds were a reranker being reloaded on every question. After switching models, loading the reranker once and skipping the first-turn rewrite, a first-turn RAG question takes roughly 1.5–2.5 seconds end to end (retrieval, including the multi-query model call, accounts for about 0.6–0.9 s of that; the log line `rag_stage_timing` shows it). The pipeline did not change shape; waiting and reloading were the cost.

```python
from langchain_core.output_parsers import StrOutputParser

from app.config import settings
from app.llm import get_llm
from app.memory import get_messages
from app.multi_query import retrieve_with_multi_query
from app.prompts import question_rewrite_prompt, rag_prompt
from app.rag import chunk_documents, load_documents
from app.schemas import RAGResponse
from app.vectorstore import build_vectorstore, get_hybrid_retriever

# ══════════════════════════════════════════════════════════════════════════
# app/chains.py — RetailOps end-to-end RAG chain
# Note: app/rag.py only holds document loading/splitting helpers
# (load_documents, split_documents, semantic_split_documents, chunk_documents) —
# the chain itself lives here in app/chains.py.
# ══════════════════════════════════════════════════════════════════════════

def format_history(messages):
    """Format the last 6 conversation messages for the rewriter prompt."""
    return "\n".join(
        f"{message.type}: {message.content}"
        for message in messages[-6:]
        if hasattr(message, "content")
    )


def format_docs(docs):
    """Format retrieved docs as context blocks with source + rerank score."""
    formatted = []

    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        score = doc.metadata.get("rerank_score", "not_available")

        formatted.append(
            f"Source: {source}\n"
            f"Rerank Score: {score}\n"
            f"Content:\n{doc.page_content}"
        )

    return "\n\n".join(formatted)


def build_retriever():
    """Load, chunk, index and wrap the documents in the hybrid (vector + BM25 + rerank) retriever."""
    chunks = chunk_documents(load_documents())  # semantic or recursive, per ENABLE_SEMANTIC_CHUNKING
    db = build_vectorstore(chunks)

    return get_hybrid_retriever(db, chunks)


def build_question_rewriter_chain():
    """Build the history-aware question rewriter chain (doc 17)."""
    llm = get_llm()
    parser = StrOutputParser()

    return question_rewrite_prompt | llm | parser


def rewrite_question(question: str, chat_history: str, rewriter_chain) -> str:
    """Turn a follow-up into a standalone question using the chat history.

    The first question of a conversation has no history, so there is nothing to
    resolve and the extra LLM call is skipped.
    """
    if not chat_history.strip():
        return question

    return rewriter_chain.invoke({
        "question": question,
        "chat_history": chat_history,
    })


def retrieve_documents(rewritten_question: str, retriever) -> list:
    if settings.enable_multi_query:
        return retrieve_with_multi_query(
            question=rewritten_question,
            retriever=retriever,
            final_top_k=settings.retrieval_k,
        )

    return retriever.invoke(rewritten_question)


def build_rag_generator():
    """The answer step: prompt + model that returns a RAGResponse (answer, sources, confidence)."""
    structured_llm = get_llm().with_structured_output(RAGResponse)

    return rag_prompt | structured_llm


def build_rag_chain(retriever=None, rewriter_chain=None, generator=None):
    """Build the full production RAG chain.

    Rewrites the question using chat history, optionally expands it via
    multi-query, retrieves + reranks, then answers with a structured LLM.
    The container passes in shared pieces; with no arguments it builds its own.

    Input:  {"question": str, "messages": list[BaseMessage]} (messages optional)
    Output: RAGResponse(answer, sources, confidence)
    """
    retriever = retriever or build_retriever()
    rewriter_chain = rewriter_chain or build_question_rewriter_chain()
    generator = generator or build_rag_generator()

    def retrieve_context(inputs):
        question = inputs["question"]

        chat_history = format_history(
            inputs.get("messages", get_messages())
        )
        rewritten_question = rewrite_question(question, chat_history, rewriter_chain)

        # History-aware rewrite feeds multi-query + hybrid retrieval
        retrieved_docs = retrieve_documents(rewritten_question, retriever)

        return {
            "question": question,
            "rewritten_question": rewritten_question,
            "context": format_docs(retrieved_docs),
        }

    return retrieve_context | generator


# ── Application-level usage ────────────────────────────────────────────────
# The app builds the pieces once in get_container() (app/container.py).
# For a standalone script:
#
# rag_chain = build_rag_chain()
#
# # Conversation history is passed via "messages" (BaseMessage list);
# # omit it and the chain falls back to app.memory.get_messages() (the default session).
# result = rag_chain.invoke({"question": "How many vacation days?"})
# print(result.answer)     # "Employees receive 18 paid vacation days annually."
# print(result.sources)    # ["hr_policy.txt"]
# print(result.confidence) # "high"
```

## 🏭 Production Best Practices

1. **Always use "Answer ONLY from context" in the system prompt** — This is the single most important prompt constraint in a RAG system. Without it, the LLM uses its training data to fill in gaps and hallucinations become unpredictable. **How:** `"Answer ONLY using the provided Context. Never use prior knowledge."`

2. **Use structured output (`RAGResponse`) instead of plain text** — Structured output gives you answer + sources + confidence as typed fields. The sources field enables attribution in the UI; the confidence field enables escalation logic. **How:** `llm.with_structured_output(RAGResponse)`.

3. **Always include source metadata in formatted context** — `[Source: hr_policy.txt]` before each chunk lets the LLM populate `sources` accurately. Without it, the LLM can't attribute answers correctly. **How:** `f"[Source: {doc.metadata.get('source')}]\n{doc.page_content}"`.

4. **Build incrementally and evaluate at each step** — Start with basic RAG → evaluate → add rewriting if conversational quality is low → add multi-query if recall is low → add hybrid if exact terms fail. Don't add everything at once. **How:** Run the evaluation pipeline (doc 19) after each addition.

5. **Handle the "not found" case explicitly** — Tell the LLM exactly what to say when the answer isn't in context. Vague instructions produce vague "I don't know" responses. **How:** `"If not found, set answer to: 'I don't know based on available documents.'"` — this exact string is easier to detect programmatically. (RetailOps' prompt uses "I don't know based on the available RetailOps documents.")

6. **Use `temperature=0` for the RAG LLM** — RAG is about retrieval + synthesis, not creativity. Deterministic output makes evaluation and debugging reproducible. **How:** `ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)`.

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

- **Example file:** `app/chains.py` — RetailOps `build_rag_chain()` and the pieces it is built from (`build_retriever()`, `rewrite_question()`, `retrieve_documents()`, `build_rag_generator()`); conversation history is handled as an input via `messages`/`chat_history`, not a separate function; `app/rag.py` holds only the document loading/splitting helpers it depends on
- **Runnable demo:** see `RUN.md` in this folder (`examples/05_basic_rag_chain.py`, `examples/06_basic_rag_with_parser.py`); `examples/07_structured_rag_output.py` (doc 08) prints the answer, sources and confidence fields separately
- **Next doc:** `../19_rag_evaluation/README.md` — measuring retrieval quality, answer correctness, groundedness, and completeness
- **Official docs:** https://python.langchain.com/docs/tutorials/rag/
