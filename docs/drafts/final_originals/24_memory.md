# Memory
> Giving the LLM a short-term memory so users don't have to repeat themselves every turn.

## 📌 What Is It?

**Memory** is the mechanism for storing and injecting conversation history so the LLM can refer back to what was said earlier in the same session. Without memory, every message is a blank slate — the LLM has no idea what was discussed in the previous turn.

```
Without memory:
  Turn 1: "What does P1 mean?"
  → "P1 means a full store outage."

  Turn 2: "What should managers do?"
  → "Managers for what? I don't have context."   ← doesn't know about P1

With memory:
  Turn 1: "What does P1 mean?"
  → "P1 means a full store outage."

  Turn 2: "What should managers do?"
  → "During a P1 incident, managers should..."   ← uses the P1 context
```

Memory works by appending each turn to a conversation buffer, then injecting the recent history into every subsequent prompt. The LLM sees the current question *and* the recent conversation context — which gives it the information needed to handle follow-up questions.

## ❓ Why Does It Exist?

LLMs are stateless by design. Every API call is independent — the model has no built-in ability to remember what was said before. If you want conversation continuity, you must provide the prior context yourself.

Memory automates this: instead of the caller manually tracking and formatting conversation history, the memory component manages the buffer and provides it in the format the prompt needs.

**Important distinction — memory vs. RAG:**
- **Memory** stores *conversation history* — what the user and assistant said this session
- **RAG** stores *knowledge* — policies, documents, SOPs that the LLM doesn't have in training

These solve different problems and are often used together.

**Important distinction — memory vs. history-aware retrieval:**
- **Memory** injects conversation history into the *LLM prompt* — so the LLM can refer to prior answers
- **History-aware retrieval** uses conversation history to *rewrite the search query* — so the retriever finds the right document

Again, these solve different problems and both are needed for a full conversational RAG system.

## ⏰ When Should You Use It?

✅ Any multi-turn conversational interface (chatbots, support assistants)  
✅ When users ask follow-up questions using pronouns ("it", "that", "them")  
✅ When you need the LLM to reference something it said in a prior turn  
✅ When building an assistant that should feel like a continuous conversation  

❌ Don't use memory for single-turn APIs where each request is independent  
❌ Don't inject the entire conversation history — it grows without bound and degrades quality  
❌ Don't use memory as a substitute for RAG — memory stores the conversation; RAG stores knowledge  
❌ Don't assume in-memory history survives restarts — it won't without a persistence layer  

## 🗂️ Types / Variants

| Type | How It Works | Best For |
|---|---|---|
| **Buffer window memory** | Keep the last N messages; discard older ones | Most chatbots; controls token cost |
| **Full buffer memory** | Keep all messages in the session | Short sessions where full context matters |
| **Summary memory** | Summarize older conversation; keep summary + recent messages | Long sessions; token-constrained environments |
| **Persistent memory** | Store history in Redis, Postgres, or a database | Enterprise apps; history must survive restarts |
| **LangGraph checkpoints** | Graph state checkpointed per step | Complex agents needing full session state |

## 🔀 When to Use Which Type

**Use buffer window memory (last 10–20 messages)** for most production chatbots. It gives the LLM enough context for follow-ups without growing the prompt without bound. The last 4–6 exchanges cover 95% of real follow-up patterns.

**Use summary memory** for long conversations (>20 turns) where injecting all messages would exceed the context window or significantly increase cost. The LLM generates a running summary that replaces the oldest messages.

**Use persistent memory (Redis/Postgres)** for enterprise applications where users expect their conversation history to survive page refreshes, app restarts, or device switches. Session IDs map each user to their stored history.

**Use LangGraph checkpoints** when building complex multi-step agents that need to pause, resume, or allow human approval mid-conversation. It's the production upgrade path beyond `AgentExecutor`.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Enables natural multi-turn conversation | History grows → more tokens → higher cost per turn |
| Users don't need to repeat context | Large history can add noise to the prompt |
| Simple implementation — a list of message dicts | In-memory history lost on restart |
| Works with any chain or agent via prompt injection | Memory management (window size, summarization) adds complexity |
| Separates conversation state from business logic | Different from RAG — easy to confuse their purposes |

## 💻 Basic Example

```python
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# ── Prompt with memory slot ───────────────────────────────────────────────
# MessagesPlaceholder injects the conversation history list into the prompt
PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are RetailOps AI Assistant. Answer questions about retail operations."),
    MessagesPlaceholder(variable_name="history"),  # ← conversation history goes here
    ("human", "{input}"),
])

chain = PROMPT | llm

# ── Simple in-memory conversation buffer ─────────────────────────────────
class ConversationBuffer:
    """Stores conversation history as a list of LangChain message objects."""

    def __init__(self, max_messages: int = 10):
        self.messages: list = []
        self.max_messages = max_messages  # keep last N messages (window)

    def add_turn(self, human: str, ai: str) -> None:
        """Append one user/assistant exchange to the buffer."""
        self.messages.append(HumanMessage(content=human))
        self.messages.append(AIMessage(content=ai))
        # Trim to window: keep only the last max_messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

    def get_history(self) -> list:
        """Return message history for prompt injection."""
        return self.messages


# ── Multi-turn conversation ───────────────────────────────────────────────
buffer = ConversationBuffer(max_messages=10)

def chat(question: str) -> str:
    """Send a message and get a response with conversation history."""
    response = chain.invoke({
        "history": buffer.get_history(),  # inject prior turns
        "input": question,
    })
    answer = response.content
    buffer.add_turn(human=question, ai=answer)  # save this turn
    return answer


# Turn 1
print(chat("What does P1 mean?"))
# → "P1 means a full store outage..."

# Turn 2 — references the P1 context from turn 1
print(chat("What should managers do?"))
# → "During a P1 incident, managers should..." (knows "managers" = P1 context)

# Turn 3 — still in context
print(chat("How long does it typically take to resolve?"))
# → "P1 outages typically..." (still references P1)
```

## 🔧 Real-World Example

RetailOps' production memory module — session-based buffer with window trimming, integration with the RAG chain and question rewriter, and a clean API for the service layer.

```python
import os
import logging
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════
# app/memory.py — RetailOps conversation memory
#
# Manages conversation history per session.
# Used by:
#   - app/services.py: inject history into RAG chain and question rewriter
#   - app/api.py: clear history on /memory/clear endpoint
#
# Current implementation: in-memory (lost on restart)
# Enterprise upgrade: replace _sessions dict with Redis or Postgres
# ══════════════════════════════════════════════════════════════════════════

MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))

# Session store: maps session_id → list of message dicts
# In production, replace with Redis or a database
_sessions: dict[str, list[dict]] = {}


def get_history(session_id: str) -> list[dict]:
    """Get conversation history for a session.

    Returns:
        List of {"role": "user"|"assistant", "content": str} dicts.
        Returns empty list if session doesn't exist.
    """
    return _sessions.get(session_id, [])


def add_turn(session_id: str, question: str, answer: str) -> None:
    """Append one user/assistant exchange to the session history.

    Applies window trimming to keep the last MAX_HISTORY_MESSAGES messages.
    """
    if session_id not in _sessions:
        _sessions[session_id] = []

    _sessions[session_id].append({"role": "user", "content": question})
    _sessions[session_id].append({"role": "assistant", "content": answer})

    # Window trimming: keep only the most recent messages
    if len(_sessions[session_id]) > MAX_HISTORY_MESSAGES:
        _sessions[session_id] = _sessions[session_id][-MAX_HISTORY_MESSAGES:]

    logger.debug(
        f"Memory updated: session={session_id}, "
        f"total_messages={len(_sessions[session_id])}"
    )


def clear_history(session_id: str) -> None:
    """Clear conversation history for a session."""
    _sessions.pop(session_id, None)
    logger.info(f"Cleared history for session: {session_id}")


def format_for_rewriter(history: list[dict]) -> str:
    """Format history as a string for the question rewriter prompt.

    Used by build_question_rewriter() in app/chains.py to rewrite
    follow-up questions into standalone questions.

    Returns last 4 turns (8 messages) to keep rewriter context tight.
    """
    if not history:
        return "No previous conversation."

    # Only use the last 4 exchanges for rewriting
    recent = history[-8:]
    lines = []
    for msg in recent:
        role = "User" if msg["role"] == "user" else "Assistant"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)


def format_for_prompt(history: list[dict]) -> list:
    """Format history as LangChain message objects for MessagesPlaceholder.

    Used when injecting memory directly into a ChatPromptTemplate
    with MessagesPlaceholder(variable_name="history").
    """
    messages = []
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    return messages


# ── Usage in app/services.py ──────────────────────────────────────────────
#
# def ask(question: str, session_id: str) -> dict:
#     history = get_history(session_id)
#
#     # Pass raw history to RAG chain (chain handles formatting internally)
#     result = rag_chain.invoke({"question": question, "history": history})
#
#     # Save this exchange to memory
#     add_turn(session_id, question=question, answer=result.answer)
#
#     return {"answer": result.answer, "sources": result.sources}
```

## 🏭 Production Best Practices

1. **Limit memory to the last 10–20 messages** — Each additional message in history adds tokens to every subsequent prompt call. A 100-turn conversation with full history costs 10× more per turn than a 10-turn window. Most follow-up questions reference only the last 2–4 exchanges. **How:** `messages = messages[-MAX_HISTORY_MESSAGES:]` after each `add_turn`.

2. **Store history as plain dicts, not LangChain objects** — `[{"role": "user", "content": "..."}]` is serializable to JSON, easy to store in Redis or Postgres, and easy to format for different prompt templates. Storing `HumanMessage`/`AIMessage` objects creates tight coupling. **How:** Convert to LangChain objects at the last moment, in `format_for_prompt()`.

3. **Use session IDs to separate user conversations** — In a multi-user API, all sessions share the same process. Without session IDs, user A's history contaminates user B's context. **How:** Accept `session_id` in every memory function; use a dict or Redis key per session.

4. **Replace the in-memory dict with Redis for production** — `_sessions: dict[str, list]` is lost on restart and doesn't scale beyond a single process. Redis gives you persistence, TTL-based expiry, and horizontal scaling. **How:** `redis_client.setex(f"session:{session_id}", ttl=3600, json.dumps(history))`.

5. **Keep memory and RAG clearly separated** — Memory answers "what did we talk about this session?" RAG answers "what do the company documents say?" Don't use memory to cache RAG results, and don't use RAG to retrieve conversation history. **How:** Memory uses `app/memory.py`; RAG uses the vector store — different modules, different calls.

6. **Log memory size per request** — When users report slow responses or wrong answers, memory size is often the cause — too much history inflating the prompt. **How:** `logger.debug(f"History size: {len(history)} messages")` per request.

## ⚠️ Common Mistakes to Avoid

⚠️ **Injecting the entire conversation into every prompt** — A 50-turn conversation injected as-is adds thousands of tokens to every subsequent call. The cost and latency grow linearly with session length. Always apply a window (last N messages) or summarization.

⚠️ **Confusing memory with RAG** — Memory stores *conversation history* (what was said this session). RAG stores *knowledge* (company documents, policies). A common mistake: storing RAG answers in the conversation buffer and calling it "memory". They're different systems for different purposes.

⚠️ **Assuming in-memory history survives restarts** — The `_sessions: dict` approach is fine for development and demos. In production, any restart (deploy, crash, scaling event) loses all sessions. Use Redis or Postgres for persistence.

⚠️ **Not applying memory trimming** — Without `messages[-MAX_HISTORY_MESSAGES:]`, history grows unbounded. A week-long chat session would have hundreds of messages, all injected into every prompt. Add trimming from day one.

⚠️ **Confusing memory with history-aware retrieval** — Memory injects history into the *LLM prompt* (so the LLM can reference prior answers). History-aware retrieval uses history to *rewrite the search query* (so the retriever finds the right document). You need both for a complete conversational RAG system — they solve different problems.

## 🔗 How It Connects to Other Concepts

- **History-Aware Retrieval** (doc 17) — Uses the same conversation history, but for query rewriting before retrieval — not prompt injection
- **RAG Chains** (doc 18) — The conversational RAG chain accepts `{"question": str, "history": list}` — memory provides the history
- **Router Pattern** (doc 23) — The router operates on the current question only; memory is applied *after* routing, inside the RAG or general chat chain
- **FastAPI Integration** (doc 25) — The API receives a `session_id` per request; the service layer uses it to retrieve and update memory
- **LangSmith** (doc 27) — Traces show the prompt including injected history — useful for seeing how memory affects LLM behavior

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Conversation history buffer that injects prior turns into each prompt |
| **Why** | LLMs are stateless; memory gives them context for follow-up questions |
| **When** | Any multi-turn conversational interface; skip for single-turn APIs |
| **Types** | Buffer window (standard), summary (long sessions), persistent (production), LangGraph checkpoints (complex agents) |
| **Production gotcha** | Apply window trimming; store as plain dicts; use session IDs; replace in-memory dict with Redis for production |

## ➡️ Next Steps

- **Example file:** `app/memory.py` — RetailOps `get_history()`, `add_turn()`, `clear_history()`, `format_for_rewriter()`
- **Next doc:** `25_fastapi_integration.md` — wrapping all these components in a production HTTP API
- **Official docs:** https://python.langchain.com/docs/concepts/chat_history/
