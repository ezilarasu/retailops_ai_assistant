# History-Aware Retrieval
> Rewriting follow-up questions before retrieval — so the retriever understands what "them" refers to.

## 📌 What Is It?

**History-aware retrieval** is the practice of rewriting a user's follow-up question into a self-contained standalone question before passing it to the retriever.

```
Without history-aware retrieval:
  Turn 1: "How many vacation days do employees receive?"
  Turn 2: "What about part-time employees?"  ← retriever gets this
  Result: poor retrieval — "part-time employees" matches nothing in vacation policy

With history-aware retrieval:
  Turn 1: "How many vacation days do employees receive?"
  Turn 2: "What about part-time employees?"
           ↓ rewriter (uses turn 1 as context)
           "What is the vacation days policy for part-time employees?"  ← retriever gets this
  Result: strong retrieval — complete question finds the relevant chunk
```

The rewriter is a short LangChain chain: `(history + follow-up) → LLM → standalone question → retriever`.

## ❓ Why Does It Exist?

Retrievers are stateless. They take a string and return documents — they have no memory of previous turns. When a user says "What about them?" or "How does that apply to managers?", the retriever has no idea what "them" or "that" refers to.

Retrieval quality drops sharply on follow-up questions unless they're rewritten first. The LLM, on the other hand, can use conversation history to infer what "them" means and produce a complete, context-rich query.

**Alternative: inject the full chat history into the retrieval query.** This works but sends unnecessary tokens to the retriever (which doesn't need the full conversation — just an unambiguous question) and creates noise that degrades embedding similarity.

## ⏰ When Should You Use It?

✅ Any multi-turn conversational RAG system  
✅ When users ask follow-up questions with pronouns ("it", "them", "that")  
✅ When users ask clarifying or scoping questions after an initial answer  
✅ Chatbots, support assistants, any interface with a "conversation" paradigm  

❌ Don't use for single-turn Q&A — no history means no rewriting needed  
❌ Don't pass the entire chat history directly to the retriever — rewrite instead  
❌ Don't confuse this with memory — rewriting improves retrieval, not conversation recall  

## 🗂️ Types / Variants

| Approach | How It Works | Best For |
|---|---|---|
| **Question rewriter chain** | `(history + question) → LLM → standalone question` | Full control; easy to tune the rewrite prompt |
| **`create_history_aware_retriever`** | LangChain built-in that handles rewriting automatically | Quick setup with standard retriever |
| **Suffix-only injection** | Append last N turns to the query string | Simple fallback when LLM rewriting adds too much latency |

## 🔀 When to Use Which Type

**Use a custom question rewriter chain** for production — the prompt is easy to tune, you can log both the original and rewritten questions, and you have full control over when rewriting is applied (skip it if the question looks standalone).

**Use `create_history_aware_retriever`** for prototyping — it's less code and works well for demos.

**Avoid suffix injection** for production — appending raw conversation history as a prefix to the query creates noisy embeddings and increases token usage for no real benefit.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Dramatically improves retrieval on follow-up questions | Adds one LLM call per conversational turn (~100–200ms) |
| Lightweight — only one rewrite per question | Poor rewrite prompt produces poor rewritten questions |
| Keeps retriever simple — it still just takes a string | Log the rewritten question or debugging becomes very hard |
| Complements multi-query — chain them together | |

## 💻 Basic Example

```python
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# ── Question rewriter chain ───────────────────────────────────────────────
REWRITE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Given the conversation history and a follow-up question,
rewrite the follow-up as a standalone question that can be understood without
any prior context.

Rules:
- Return ONLY the rewritten question, nothing else
- Do not explain or add commentary
- If the question is already standalone, return it unchanged"""),
    ("human", "Conversation history:\n{history}\n\nFollow-up question: {question}"),
])

rewriter = REWRITE_PROMPT | llm | StrOutputParser()

# ── Test cases ────────────────────────────────────────────────────────────
examples = [
    {
        "history": "User: How many vacation days do employees receive?\nAssistant: Employees receive 18 paid vacation days annually.",
        "question": "What about part-time employees?",
    },
    {
        "history": "User: What does P1 mean?\nAssistant: P1 means a full store outage.",
        "question": "What should managers do?",
    },
    {
        "history": "User: What is the returns policy?\nAssistant: Returns must be within 30 days with receipt.",
        "question": "What if the item is damaged?",
    },
]

for ex in examples:
    rewritten = rewriter.invoke(ex)
    print(f"Original:  {ex['question']}")
    print(f"Rewritten: {rewritten}")
    print()
# → "What is the vacation days policy for part-time employees?"
# → "What should managers do during a P1 incident?"
# → "What is the return policy for damaged items?"
```

## 🔧 Real-World Example

RetailOps' conversational RAG — question rewriting feeds into multi-query retrieval, which feeds into hybrid search, which feeds into the LLM.

```python
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from langchain_core.documents import Document

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# ══════════════════════════════════════════════════════════════════════════
# app/chains.py — RetailOps question rewriter and conversational RAG
#
# Full conversational pipeline:
#   (history + question) → rewrite → multi-query → hybrid → rerank → LLM
# ══════════════════════════════════════════════════════════════════════════

QUESTION_REWRITE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a query optimizer for a retail operations knowledge base.

Given conversation history and a follow-up question, rewrite the question as a
complete standalone question suitable for document retrieval.

Rules:
- Return ONLY the rewritten question, nothing else
- Incorporate relevant context from history (who/what is being discussed)
- If the question is already standalone, return it unchanged
- Keep the rewritten question concise (under 25 words)"""),
    ("human", "History:\n{history}\n\nFollow-up: {question}"),
])


def build_question_rewriter():
    """Build a chain that rewrites follow-up questions into standalone queries.

    Input:  {"history": str, "question": str}
    Output: str — standalone question ready for retrieval
    """
    return QUESTION_REWRITE_PROMPT | llm | StrOutputParser()


def format_chat_history(messages: list[dict]) -> str:
    """Format conversation history for the rewrite prompt.

    Args:
        messages: [{"role": "user"|"assistant", "content": str}, ...]

    Returns:
        Formatted string for the history variable
    """
    if not messages:
        return "No previous conversation."

    lines = []
    for msg in messages[-4:]:  # only last 4 turns to keep context tight
        role = "User" if msg["role"] == "user" else "Assistant"
        lines.append(f"{role}: {msg['content']}")

    return "\n".join(lines)


def build_conversational_rag_chain(retriever, rewriter=None):
    """Build a full conversational RAG chain with optional question rewriting.

    Args:
        retriever: Any retriever Runnable (hybrid, reranking, etc.)
        rewriter: Optional question rewriter chain. If None, question is used as-is.

    Input:  {"question": str, "history": list[dict]}
    Output: str answer
    """
    RAG_PROMPT = ChatPromptTemplate.from_messages([
        ("system", """You are RetailOps AI Assistant.
Answer ONLY using the provided context. Always cite the source document.
If the answer is not in the context, say "I don't know based on available documents." """),
        ("human", "Context:\n{context}\n\nQuestion: {question}"),
    ])

    def format_docs(docs: list[Document]) -> str:
        return "\n\n".join(
            f"[Source: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
            for doc in docs
        )

    def prepare_retrieval_query(inputs: dict) -> str:
        """Rewrite follow-up question if rewriter available, else use original."""
        raw_question = inputs["question"]
        history = inputs.get("history", [])

        if not rewriter or not history:
            # No history or no rewriter — use question as-is
            return raw_question

        history_str = format_chat_history(history)
        rewritten = rewriter.invoke({"history": history_str, "question": raw_question})

        # Log for debugging (in production: use LangSmith or structured logging)
        if rewritten != raw_question:
            print(f"[rewriter] '{raw_question}' → '{rewritten}'")

        return rewritten

    return (
        RunnableParallel({
            "context": RunnableLambda(prepare_retrieval_query)
                       | retriever
                       | RunnableLambda(format_docs),
            "question": RunnablePassthrough() | RunnableLambda(lambda x: x["question"]),
        })
        | RAG_PROMPT
        | llm
        | StrOutputParser()
    )


# ── Usage example ─────────────────────────────────────────────────────────
# rewriter = build_question_rewriter()
# chain = build_conversational_rag_chain(retriever, rewriter=rewriter)
#
# Turn 1 (no history):
# answer = chain.invoke({"question": "How many vacation days?", "history": []})
#
# Turn 2 (with history):
# answer = chain.invoke({
#     "question": "What about part-time?",
#     "history": [
#         {"role": "user", "content": "How many vacation days?"},
#         {"role": "assistant", "content": "18 days annually."},
#     ],
# })
# → rewriter produces: "What is the vacation policy for part-time employees?"
# → retriever finds the right chunk
```

## 🏭 Production Best Practices

1. **Log both the original and rewritten question** — When retrieval fails, comparing the two reveals whether the rewriter is producing good standalone questions. Bad rewrites are the most common failure mode. **How:** `print(f"[rewriter] '{original}' → '{rewritten}'")`; use LangSmith in production.

2. **Only rewrite when there's actual history** — If this is the first turn, skip rewriting. The original question is already standalone, and rewriting it adds latency for no benefit. **How:** `if not history: return original_question`.

3. **Limit history to the last 4 turns** — Long chat history creates a noisy context for the rewriter. The last 2–4 turns contain the relevant context 95% of the time. **How:** `messages[-4:]`.

4. **Return the original question if the rewriter produces something strange** — Validate the rewritten question isn't empty or wildly different from the original. A simple length check catches most failures. **How:** `if len(rewritten) < 10 or len(rewritten) > 200: return original`.

5. **Chain with multi-query after rewriting** — Rewriting produces one better question. Multi-query then expands that to 3–4 alternate phrasings. The two techniques stack multiplicatively. **How:** `standalone = rewriter.invoke(...); queries = query_generator.invoke(standalone)`.

6. **Distinguish rewriting from memory** — The rewriter improves retrieval; it does not make the LLM "remember" previous answers. Memory (doc 24) is separate — it stores conversation context in the LLM's prompt. **Why:** Conflating them leads to over-engineering; they solve different problems.

## ⚠️ Common Mistakes to Avoid

⚠️ **Passing the full chat history directly to the retriever** — A retriever embedding the entire conversation history as its query produces a mixed-signal vector that doesn't match any specific document chunk. Rewrite to a focused single question first.

⚠️ **Not logging the rewritten question** — If retrieval fails for a follow-up question, you need to see what the rewriter produced. Without logging, you can't tell whether the failure is in rewriting or retrieval.

⚠️ **Treating rewriting as memory** — The rewriter produces a better search query; it doesn't give the LLM access to what was said in previous turns. For the LLM to reference previous answers, use memory (doc 24) separately.

⚠️ **Rewriting even when history is empty** — On the first turn, the "rewriter" just receives the original question plus an empty history. It typically returns the question unchanged, but wastes an LLM call. Skip rewriting when `len(history) == 0`.

⚠️ **Tuning the RAG prompt instead of the rewrite prompt** — When conversational retrieval fails, developers often blame the RAG prompt. The rewrite step is usually the bottleneck. Inspect the rewritten question before touching anything else.

## 🔗 How It Connects to Other Concepts

- **Retrievers** (doc 13) — The rewriter's output feeds directly into the retriever; a better question produces better retrieval
- **Multi-Query Retrieval** (doc 16) — Chain rewriting before multi-query: one rewritten standalone question → expanded to 3 variants → retrieved
- **Memory** (doc 24) — Memory stores what was said; history-aware retrieval improves how we search based on what was said — two separate concerns
- **RAG Chains** (next: doc 18) — History-aware retrieval is one component in the full RAG chain alongside hybrid search and reranking
- **Prompt Engineering** (doc 04) — The rewrite prompt follows the "constraint + role + output format" pattern

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Rewriting follow-up questions into standalone, context-complete questions before retrieval |
| **Why** | Retrievers are stateless — "What about them?" produces poor retrieval without knowing who "them" refers to |
| **When** | Any multi-turn conversational RAG; skip on first turn (no history yet) |
| **Types** | Custom rewriter chain (recommended), `create_history_aware_retriever` (quick setup) |
| **Production gotcha** | Log original and rewritten questions; skip when no history; chain with multi-query after rewriting; separate from memory |

## ➡️ Next Steps

- **Example file:** `app/chains.py` — RetailOps `build_question_rewriter()` and `build_conversational_rag_chain()`
- **Next doc:** `18_rag_chains.md` — assembling all retrieval components into a complete end-to-end RAG pipeline
- **Official docs:** https://python.langchain.com/docs/how_to/contextual_compression/
