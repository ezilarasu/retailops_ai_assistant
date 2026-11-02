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

**Use LangGraph checkpoints** when building complex multi-step agents that need to pause, resume, or allow human approval mid-conversation. It's the production upgrade path when a plain chat history isn't enough. RetailOps has a LangGraph version with a checkpointer in `app/graph/` (see doc 33).

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

llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)

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

RetailOps' actual memory module is intentionally simple: one `InMemoryChatMessageHistory` object from `langchain_core` **per session id**, kept in a plain dict and wrapped in four small functions. Each function takes an optional `session_id` (default `"default"`), so two users who send different ids never see each other's turns. It is still in-process memory: it is lost on restart, it is not shared between workers, and nothing ever trims or expires a session. Those are real limitations worth knowing before you build on top of it.

```python
# ══════════════════════════════════════════════════════════════════════════
# app/memory.py — RetailOps conversation memory (actual implementation)
#
# Used by:
#   - app/router.py: reads get_messages(session_id) to build the history for the
#     router, the tools agent, the general chat and the RAG rewrite, and calls
#     add_user_message()/add_ai_message() after each turn (all routes)
#   - app/services.py: a cache hit records the turn here too, and only a
#     conversation's FIRST question is ever cached (doc 29)
#   - app/api.py: /chat takes an optional session_id; /memory/clear?session_id=...
#     calls clear_memory(session_id)
#
# Enterprise upgrade: swap this module for a persistent, expiring store
# (e.g. Redis- or Postgres-backed chat history, one key per session_id).
# ══════════════════════════════════════════════════════════════════════════

from langchain_core.chat_history import InMemoryChatMessageHistory

DEFAULT_SESSION = "default"

# One conversation history per session id, kept in this process's memory only.
_histories: dict[str, InMemoryChatMessageHistory] = {}


def _history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in _histories:
        _histories[session_id] = InMemoryChatMessageHistory()

    return _histories[session_id]


def add_user_message(message: str, session_id: str = DEFAULT_SESSION):
    _history(session_id).add_user_message(message)


def add_ai_message(message: str, session_id: str = DEFAULT_SESSION):
    _history(session_id).add_ai_message(message)


def get_messages(session_id: str = DEFAULT_SESSION):
    history = _histories.get(session_id)

    return history.messages if history else []


def clear_memory(session_id: str = DEFAULT_SESSION):
    _histories.pop(session_id, None)


# ── Usage in app/router.py (run_router) ───────────────────────────────────
#
# history = get_messages(session_id)
# decision = route_question(question, history)        # last 6 messages as "type: content" lines
# ...
# add_user_message(question, session_id)              # after the answer is produced
# add_ai_message(answer, session_id)
#
# ── Usage in app/chains.py (RAG route) ────────────────────────────────────
# chat_history = format_history(get_messages())   # last 6 messages as "type: content" lines
# rewritten_question = rewrite_question(question, chat_history, rewriter_chain)
```

**Where history is actually used in RetailOps** (all four places read the same per-session history, trimmed to the last 6 messages):

| Route | Sees chat history? |
|---|---|
| Router (classifying the question) | Yes — the last 6 messages, formatted as `type: content` lines, go into the router prompt |
| `rag` | Yes, indirectly — the question-rewriting step (doc 17) turns "What about part-time employees?" into a standalone search query (it is skipped on a conversation's first question). The final answer prompt only sees the retrieved context and the rewritten question |
| `general` | Yes — the last 6 messages fill an optional `history` slot in `general_chat_prompt`, so "What was the first thing I said to you?" is answered correctly |
| `tools` | Yes — `run_router()` passes the last 6 messages to the agent, followed by the new question |

So follow-ups work on every route: "What about part-time employees?" is rewritten into a standalone search query, and "What about store 310?" after an inventory question reaches the agent together with the earlier turns, so it knows you mean low-stock items. `examples/11_memory_followup.py` tries exactly these cases.

> **Lesson from this project:** a memory that only *some* parts of the pipeline read gives confusing results. For a while the router saw the history but the tools agent and the general chat did not. The router correctly sent "What about store 310?" to the tools route, and then the agent, seeing only those four words, asked "what information are you looking for?". Likewise "What was the first thing I said to you?" got "you haven't asked anything". Passing the last 6 messages to every route fixed both. When you add memory, check *every* place a model is called and decide on purpose whether it needs the history.

Two things memory does *not* do yet: there is no cap on how many sessions or messages are kept (a long-lived server would grow without bound), and the history lives only in this process.

## 🏭 Production Best Practices

1. **Limit memory to the last 10–20 messages** — Each additional message in history adds tokens to every subsequent prompt call. A 100-turn conversation with full history costs 10× more per turn than a 10-turn window. Most follow-up questions reference only the last 2–4 exchanges. **How:** `messages = messages[-MAX_HISTORY_MESSAGES:]` after each `add_turn`. RetailOps sends only the last 6 messages (`HISTORY_WINDOW` in `app/router.py`) to the router, the tools agent, the general chat and the RAG rewrite, so prompt size stays flat; the stored history itself is not trimmed.

2. **Store history as plain dicts, not LangChain objects** — `[{"role": "user", "content": "..."}]` is serializable to JSON, easy to store in Redis or Postgres, and easy to format for different prompt templates. Storing `HumanMessage`/`AIMessage` objects creates tight coupling. **How:** Convert to LangChain objects at the last moment, in `format_for_prompt()`.

3. **Use session IDs to separate user conversations** — In a multi-user API, all sessions share the same process. Without session IDs, user A's history contaminates user B's context. **How:** Accept `session_id` in every memory function and keep one history per id, as RetailOps does (`_histories: dict[str, InMemoryChatMessageHistory]` in `app/memory.py`, with `/chat` accepting `session_id`). Generate the id on the server or tie it to a logged-in user: a client that can guess another user's id can read that conversation (the API key authenticates callers, but does not separate them).

4. **Replace the in-memory history with Redis for production** — an in-process object such as RetailOps' `InMemoryChatMessageHistory` (or a dict like `_sessions: dict[str, list]`) is lost on restart and doesn't scale beyond a single process. Redis gives you persistence, TTL-based expiry, and horizontal scaling. **How:** `redis_client.setex(f"session:{session_id}", ttl=3600, json.dumps(history))`.

5. **Keep memory and RAG clearly separated** — Memory answers "what did we talk about this session?" RAG answers "what do the company documents say?" Don't use memory to cache RAG results, and don't use RAG to retrieve conversation history. **How:** Memory uses `app/memory.py`; RAG uses the vector store — different modules, different calls.

6. **Log memory size per request** — When users report slow responses or wrong answers, memory size is often the cause — too much history inflating the prompt. **How:** `logger.debug(f"History size: {len(history)} messages")` per request.

## ⚠️ Common Mistakes to Avoid

⚠️ **Injecting the entire conversation into every prompt** — A 50-turn conversation injected as-is adds thousands of tokens to every subsequent call. The cost and latency grow linearly with session length. Always apply a window (last N messages) or summarization.

⚠️ **Confusing memory with RAG** — Memory stores *conversation history* (what was said this session). RAG stores *knowledge* (company documents, policies). A common mistake: storing RAG answers in the conversation buffer and calling it "memory". They're different systems for different purposes.

⚠️ **Assuming in-memory history survives restarts** — The in-memory approach (RetailOps' `InMemoryChatMessageHistory`) is fine for development and demos. In production, any restart (deploy, crash, scaling event) loses all sessions. Use Redis or Postgres for persistence.

⚠️ **Not applying memory trimming** — Without `messages[-MAX_HISTORY_MESSAGES:]`, history grows unbounded. A week-long chat session would have hundreds of messages, all injected into every prompt. Add trimming from day one.

⚠️ **Confusing memory with history-aware retrieval** — Memory injects history into the *LLM prompt* (so the LLM can reference prior answers). History-aware retrieval uses history to *rewrite the search query* (so the retriever finds the right document). You need both for a complete conversational RAG system — they solve different problems.

## 🔗 How It Connects to Other Concepts

- **History-Aware Retrieval** (doc 17) — Uses the same conversation history, but for query rewriting before retrieval — not prompt injection
- **RAG Chains** (doc 18) — `run_router()` invokes the RAG chain with `{"question": ..., "messages": history}`; inside it, `retrieve_context` formats the last 6 messages for the question-rewrite step (falling back to `get_messages()` if `messages` is omitted)
- **Router Pattern** (doc 23) — The router prompt receives the last 6 messages so follow-ups are classified correctly, and `run_router()` saves each turn to that session's memory after answering
- **FastAPI Integration** (doc 25) — `/chat` takes an optional `session_id`, and `/memory/clear?session_id=...` clears just that session's history
- **LangSmith** (doc 27) — Traces show the prompt including injected history — useful for seeing how memory affects LLM behavior

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Conversation history buffer that injects prior turns into each prompt |
| **Why** | LLMs are stateless; memory gives them context for follow-up questions |
| **When** | Any multi-turn conversational interface; skip for single-turn APIs |
| **Types** | Buffer window (standard), summary (long sessions), persistent (production), LangGraph checkpoints (complex agents) |
| **Production gotcha** | Apply window trimming; RetailOps keeps one history per `session_id`, but only in this process and with no size or age limit, so replace it with Redis for production |

## ➡️ Next Steps

- **Example file:** `app/memory.py` — RetailOps `add_user_message()`, `add_ai_message()`, `get_messages()`, `clear_memory()` (each takes an optional `session_id`)
- **Runnable demo:** see `RUN.md` in this folder (`examples/11_memory_followup.py`)
- **Next doc:** `../25_fastapi_integration/README.md` — wrapping all these components in a production HTTP API
- **Official docs:** https://python.langchain.com/docs/concepts/chat_history/
