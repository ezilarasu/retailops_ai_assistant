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
| **Question rewriter chain** *(what RetailOps uses)* | `(history + question) → LLM → standalone question` | Full control; easy to tune the rewrite prompt |
| **`create_history_aware_retriever`** *(built-in, not used by RetailOps)* | LangChain built-in that handles rewriting automatically | Quick setup with standard retriever |
| **Suffix-only injection** | Append last N turns to the query string | Simple fallback when LLM rewriting adds too much latency |

## 🔀 When to Use Which Type

**Use a custom question rewriter chain** for production — the prompt is easy to tune, you can log both the original and rewritten questions, and you have full control over when rewriting is applied (skip it if the question looks standalone).

**Use `create_history_aware_retriever`** for prototyping — it's less code and works well for demos. In LangChain 1.x it lives in `langchain_classic`:

```python
from langchain_classic.chains import create_history_aware_retriever

# prompt must contain a MessagesPlaceholder("chat_history") and the {input} variable
history_aware = create_history_aware_retriever(llm, base_retriever, rewrite_prompt)
docs = history_aware.invoke({"input": "What about part-time?", "chat_history": messages})
```

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

llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)

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

RetailOps' conversational RAG — the question rewriter chain feeds the rewritten, standalone question into multi-query retrieval, which feeds hybrid search, which feeds the LLM. This is the real `build_question_rewriter_chain()` from `app/chains.py`, used inside `build_rag_chain()`.

```python
from langchain_core.output_parsers import StrOutputParser

from app.llm import get_llm
from app.prompts import question_rewrite_prompt

# ══════════════════════════════════════════════════════════════════════════
# app/chains.py — RetailOps question rewriter
#
# Full conversational pipeline (inside build_rag_chain()):
#   (history + question) → rewrite → multi-query → hybrid → rerank → LLM
# ══════════════════════════════════════════════════════════════════════════

def build_question_rewriter_chain():
    """Build a chain that rewrites follow-up questions into standalone queries.

    Input:  {"question": str, "chat_history": str}
    Output: str — standalone question ready for retrieval
    """
    llm = get_llm()
    parser = StrOutputParser()

    return question_rewrite_prompt | llm | parser


def format_history(messages):
    """Format the last 6 conversation messages for the rewrite prompt."""
    return "\n".join(
        f"{message.type}: {message.content}"
        for message in messages[-6:]
        if hasattr(message, "content")
    )


# ── How the RAG chain (app/chains.py) uses the rewriter ───────────────────
# def rewrite_question(question, chat_history, rewriter_chain):
#     # The first question of a conversation has no history, so there is nothing
#     # to resolve: skip the LLM call and use the question as it is.
#     if not chat_history.strip():
#         return question
#
#     return rewriter_chain.invoke({
#         "question": question,
#         "chat_history": chat_history,
#     })
#
# # inside build_rag_chain(retriever, rewriter_chain, generator):
# def retrieve_context(inputs):
#     question = inputs["question"]
#     chat_history = format_history(inputs.get("messages", get_messages()))
#
#     rewritten_question = rewrite_question(question, chat_history, rewriter_chain)
#
#     # Rewritten question feeds retrieval (multi-query + hybrid + rerank)
#     retrieved_docs = retrieve_documents(rewritten_question, retriever)
#
#     return {
#         "question": question,
#         "rewritten_question": rewritten_question,
#         "context": format_docs(retrieved_docs),
#     }
#
# chain = retrieve_context | generator   # generator = rag_prompt | structured_llm
```

Things to notice in the real code (they differ from some best practices below):

- **It skips the rewrite on the first turn.** `rewrite_question()` returns the question unchanged when there is no history, so the first question of a conversation costs no extra LLM call (a first-turn RAG question makes three: router, multi-query, answer; the log shows `rewrite_ms` of about 0.01). Follow-ups cost one more call for the rewrite.
- **It keeps the last 6 messages** (about 3 turns), not 4.
- **The history is per session.** It comes from `get_messages(session_id)` in `app/memory.py`: `run_router()` passes that session's history into the RAG chain as `messages`, so the rewriter only sees the same user's earlier turns (doc 24). Clients choose the session with the optional `session_id` field of `/chat`; without one they share the `default` session.
- **Both questions are logged.** `build_rag_chain()` writes the original and rewritten question to the log (`rag_stage_timing ... original_question=... rewritten_question=...`), and the `/debug/retrieval` endpoint returns both.
- **The real prompt** (`question_rewrite_prompt` in `app/prompts.py`) says: rewrite the current question into a standalone search query, use chat history only to resolve references, return only the rewritten question, don't answer it, and don't add unsupported details.

> **Lesson from this project:** every model call counts, especially on a free tier with a tokens-per-minute limit. A RAG question used to make four model calls (router, rewrite, multi-query, answer); skipping the pointless first-turn rewrite brought the common case down to three, and the log shows the skipped step costing `rewrite_ms=0.01` instead of a few hundred milliseconds. Rewriting also still needs watching: in one early test run, the follow-up "What about part-time employees?" came back as "I don't know" because the reference was not resolved. Whenever a follow-up answer looks wrong, compare `original_question` and `rewritten_question` in the log (or call `/debug/retrieval`) before changing anything else.

## 🏭 Production Best Practices

1. **Log both the original and rewritten question** — When retrieval fails, comparing the two reveals whether the rewriter is producing good standalone questions. Bad rewrites are the most common failure mode. **How:** `print(f"[rewriter] '{original}' → '{rewritten}'")`; use LangSmith in production.

2. **Only rewrite when there's actual history** — If this is the first turn, skip rewriting. The original question is already standalone, and rewriting it adds latency for no benefit. **How:** `if not history: return original_question`. (RetailOps does exactly this in `rewrite_question()`.)

3. **Limit history to the last 4 turns** — Long chat history creates a noisy context for the rewriter. The last 2–4 turns contain the relevant context 95% of the time. **How:** `messages[-4:]` (RetailOps uses `messages[-6:]`).

4. **Return the original question if the rewriter produces something strange** — Validate the rewritten question isn't empty or wildly different from the original. A simple length check catches most failures. **How:** `if len(rewritten) < 10 or len(rewritten) > 200: return original`.

5. **Chain with multi-query after rewriting** — Rewriting produces one better question. Multi-query then expands that to 3–4 alternate phrasings. The two techniques stack multiplicatively. **How:** `standalone = rewriter.invoke(...); queries = query_generator.invoke(standalone)`.

6. **Distinguish rewriting from memory** — The rewriter improves retrieval; it does not make the LLM "remember" previous answers. Memory (doc 24) is separate — it stores conversation context in the LLM's prompt. **Why:** Conflating them leads to over-engineering; they solve different problems.

## ⚠️ Common Mistakes to Avoid

⚠️ **Passing the full chat history directly to the retriever** — A retriever embedding the entire conversation history as its query produces a mixed-signal vector that doesn't match any specific document chunk. Rewrite to a focused single question first.

⚠️ **Not logging the rewritten question** — If retrieval fails for a follow-up question, you need to see what the rewriter produced. Without logging, you can't tell whether the failure is in rewriting or retrieval.

⚠️ **Treating rewriting as memory** — The rewriter produces a better search query; it doesn't give the LLM access to what was said in previous turns. For the LLM to reference previous answers, use memory (doc 24) separately.

⚠️ **Rewriting even when history is empty** — On the first turn, the "rewriter" just receives the original question plus an empty history. It typically returns the question unchanged, but wastes an LLM call. Skip rewriting when there is no history (RetailOps used to rewrite every question and now skips the first one).

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
| **Production gotcha** | Log original and rewritten questions; skip when no history (RetailOps does); chain with multi-query after rewriting; separate from memory |

## ➡️ Next Steps

- **Example file:** `app/chains.py` — RetailOps `build_question_rewriter_chain()`, used inside `build_rag_chain()`
- **Next doc:** `../18_rag_chains/README.md` — assembling all retrieval components into a complete end-to-end RAG pipeline
- **Official docs:** https://python.langchain.com/docs/how_to/qa_chat_history_how_to/
