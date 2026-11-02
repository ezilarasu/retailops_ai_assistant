# Prompt Templates
> Reusable, versioned prompts that make your LLM behavior consistent and maintainable.

## 📌 What Is It?

A **Prompt Template** is a reusable prompt with named placeholders that get filled at runtime. Instead of building prompt strings by hand on every call, you define the template once and inject variables when needed.

Think of it like an HTML template:
```
Template:  "Explain {topic} for a {level} developer."
Variables: topic="decorators", level="beginner"
Result:    "Explain decorators for a beginner developer."
```

In LangChain, prompt templates are also **Runnables** — they plug directly into LCEL pipelines:
```python
chain = prompt | llm | parser  # prompt is a Runnable like everything else
```

## ❓ Why Does It Exist?

**Without templates**, real production systems end up with prompt strings scattered across dozens of files, built with f-strings:

```python
# Scattered throughout the codebase:
prompt = f"Explain {topic}"
prompt = f"Answer the question: {question}. Context: {context}"
prompt = f"You are a {role}. {instruction}"
```

Problems:
- Hard to test — you can't unit-test a string buried in business logic
- Hard to version — how do you know when a prompt changed?
- Hard to reuse — the same prompt is duplicated in 3 places
- Hard to share — the system message is defined inline everywhere

**With Prompt Templates:**
```python
# Defined once in app/prompts.py
rag_prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer using ONLY the provided context."),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])

# Used everywhere, tested once
chain = rag_prompt | llm | parser
```

## ⏰ When Should You Use It?

✅ Any prompt that takes variables (context, question, history)  
✅ Any prompt used in more than one place  
✅ Any prompt you want to test, version, or evaluate  
✅ Any prompt used in an LCEL chain  
✅ Production systems where prompt changes must be tracked  

❌ A one-time script with a fixed prompt that never changes  
❌ Truly static prompts with no variables (you can still use templates, but it's optional)  

## 🗂️ Types / Variants

| Type | Class | Best For |
|---|---|---|
| Text prompt | `PromptTemplate` | Simple single-turn prompts; non-chat models |
| Chat prompt | `ChatPromptTemplate` | All production use — chat models with system/user/assistant messages |
| Few-shot prompt | `FewShotPromptTemplate` | Teaching by example — when instructions alone aren't precise enough |

## 🔀 When to Use Which Type

**Use `ChatPromptTemplate` for everything in production.** Modern LLMs are optimized for the System/User/Assistant message format, not raw text completion. `ChatPromptTemplate.from_messages()` maps directly to this.

**Use `PromptTemplate`** only if you're integrating with a legacy API that expects a raw text string rather than a messages list.

**Use `FewShotPromptTemplate`** when your task requires precision formatting or extraction that role + constraint prompting alone can't achieve. Examples: classifying short text snippets, extracting structured data from messy inputs, enforcing strict output schemas on older models.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Reusable — define once, use everywhere | Slightly more setup than a raw f-string |
| Testable — invoke with different variables | Variables must be explicitly declared |
| Composable — works in LCEL pipelines | Template errors (missing vars) caught at runtime, not parse time |
| Versionable — stored in one file | |
| Type-safe variable injection | |

## 💻 Basic Example

```python
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)

# ── ChatPromptTemplate: for chat models (use this in production) ─────────
chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Python instructor. Be concise and clear."),
    ("human", "Explain {topic} to a {level} developer."),  # variables in {}
])

# Inspect what the template produces before sending to the model
messages = chat_prompt.invoke({"topic": "decorators", "level": "beginner"})
print(messages)
# → ChatPromptValue with SystemMessage + HumanMessage

# Compose into a chain and run
chain = chat_prompt | llm | StrOutputParser()
answer = chain.invoke({"topic": "decorators", "level": "intermediate"})
print(answer)

# ── PromptTemplate: for simple text prompts ───────────────────────────────
text_prompt = PromptTemplate.from_template(
    "Summarize the following in one sentence:\n\n{document}"
)

text_chain = text_prompt | llm | StrOutputParser()
summary = text_chain.invoke({"document": "LangChain is a framework for building LLM apps..."})
print(summary)
```

## 🔧 Real-World Example

This is a simplified version of RetailOps' `app/prompts.py`. All prompts live in one file and are imported by the chains that need them. The real file has the same five roles (general chat, RAG, router, history-aware router, question rewrite) with longer wording, and it uses these variable names: the RAG prompt takes `{context}` and `{rewritten_question}`, and the router and rewrite prompts take `{chat_history}` and `{question}`. The code below uses shorter names (`{question}`, `{history}`) to keep the teaching clear. One real detail worth copying: the real `general_chat_prompt` has a `MessagesPlaceholder("history", optional=True)` between the system and human messages. That placeholder is how recent chat turns reach the general route (`run_router()` passes the last 6 messages as `history`). It is optional, so calling the chain with only `question` (as `examples/01_basic_chat_chain.py` does) still works. The real system message also lists what the assistant can actually do (answer from the RetailOps documents, look up low-stock items, vendors and incidents) and tells it not to claim anything else; before that was added the assistant described scheduling and sales reports it does not have.

```python
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field

load_dotenv()

llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)

# ══════════════════════════════════════════════════════════════════════════
# app/prompts.py — all prompts live here, imported by chains
# ══════════════════════════════════════════════════════════════════════════

# General chat — no context injection, conversational tone
general_chat_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are RetailOps AI Assistant.
You can answer questions from the RetailOps documents and look up stock,
vendors and incidents. Do not claim other capabilities.
Be concise. If unsure, say so."""),
    MessagesPlaceholder("history", optional=True),  # earlier turns, if the caller passes them
    ("human", "{question}"),
])

# RAG — strict grounding, source attribution required
rag_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are RetailOps AI Assistant.
Answer ONLY using the provided context.
Do NOT use your own knowledge or make assumptions.
If the answer is not in the context, say exactly:
"I don't know based on the available documents." """),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])

# Router — classify the question into exactly one route
router_prompt = ChatPromptTemplate.from_messages([
    ("system", """Classify the user question into exactly one route:
- general: greetings, small talk, general knowledge
- rag: questions about company policies, procedures, or documents
- tools: real-time data (inventory levels, order status, open incidents)

Return ONLY the route name. No explanation."""),
    ("human", "Question: {question}"),
])

# Question rewrite — convert follow-up into a standalone query
question_rewrite_prompt = ChatPromptTemplate.from_messages([
    ("system", """Rewrite the follow-up question as a standalone question
that can be understood without the conversation history.
Return ONLY the rewritten question. No explanation."""),
    ("human", """Conversation history:
{history}

Follow-up question: {question}

Standalone question:"""),
])

# NOTE: There is no standalone "multi-query prompt" exported from app/prompts.py.
# Multi-query generation lives in app/multi_query.py — build_multi_query_chain()
# defines its own inline prompt and wires it to the LLM. See doc 04 for that example.

# ══════════════════════════════════════════════════════════════════════════
# app/chains.py — chains import prompts and compose them with the model
# ══════════════════════════════════════════════════════════════════════════

# Each chain has one responsibility
general_chain = general_chat_prompt | llm | StrOutputParser()
question_rewriter = question_rewrite_prompt | llm | StrOutputParser()

# Test a chain
standalone_q = question_rewriter.invoke({
    "history": "User asked about vacation days.",
    "question": "What about part-time employees?",
})
print(standalone_q)
# → "What is the vacation day policy for part-time employees?"
```

## 🏭 Production Best Practices

1. **Store all prompts in `app/prompts.py`** — Prompts are application logic. A prompt change can break the entire system — treat it like code. **How:** Define named constants in one file. Import them from chains. Never embed prompt strings in business logic.

2. **Use `ChatPromptTemplate.from_messages()` for all production prompts** — The messages format (`system`, `human`, `ai`) maps directly to how modern models are trained. **Why:** Plain text prompts via `PromptTemplate` lose the system instruction boundary and produce less reliable behavior.

3. **Version your prompts with comments** — Note what changed and why when you modify a prompt. **How:**
   ```python
   # v3: Added "Do not use your own knowledge" after hallucination incident 2024-11
   rag_prompt = ChatPromptTemplate.from_messages([...])
   ```

4. **Keep each prompt focused on one task** — A prompt that does routing AND answering AND evaluation fails at all three. One responsibility per prompt, one prompt per chain.

5. **Evaluate prompts with your golden dataset** — Never assume a prompt change is better. Run it through your evaluation suite. **Why:** Prompt changes that improve one category often degrade another.

6. **Use `{variable}` names that are self-documenting** — `{context}` is better than `{c}`. `{question}` is better than `{q}`. The template is read by people, not just machines.

## ⚠️ Common Mistakes to Avoid

⚠️ **Hardcoding prompts inside chain definitions** — `chain = ChatPromptTemplate.from_messages([...]) | llm | parser` looks fine, but now you can't test the prompt independently, reuse it, or find it without reading chain code. Keep prompts in `app/prompts.py`.

⚠️ **One giant prompt doing multiple jobs** — A prompt that routes AND answers AND evaluates is impossible to maintain. When it breaks, you don't know which part failed. Split responsibilities.

⚠️ **No output format instruction** — Without "Return JSON only" or `with_structured_output()`, the model decides its own format. Your parser breaks when phrasing changes. Always constrain output format.

⚠️ **Not testing prompts at edge cases** — A prompt that works on 5 manual tests may fail on ambiguous questions, empty context, or adversarial input. Build a golden dataset with edge cases.

⚠️ **Treating prompts as static text** — Prompts are behavior definitions. A one-word change ("only" vs "primarily") can shift model behavior significantly. Track them in version control.

## 🔗 How It Connects to Other Concepts

- **Chat Models** (doc 01) — Prompts are formatted and sent to the model; `ChatPromptTemplate` outputs the `messages` list the model expects
- **LCEL** (next: doc 05) — `prompt | llm | parser` — prompts are always the first Runnable in an LCEL chain
- **Prompt Engineering Patterns** (doc 04) — The techniques (role prompting, constraint prompting, few-shot) that determine *what to put inside* a template
- **Structured Output** (doc 08) — Pairs with prompts: the template controls input format, structured output controls the response schema
- **RAG Chains** (doc 18) — The RAG prompt injects retrieved context via the `{context}` variable
- **Memory** (doc 24) — Conversation history is injected into prompts via `{history}` variables

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Reusable prompt definitions with named variables, stored as Runnables |
| **Why** | Maintainable, testable, versionable prompts instead of scattered f-strings |
| **When** | Any prompt that takes variables, is used in more than one place, or must be tested |
| **Types** | `ChatPromptTemplate` (production standard), `PromptTemplate` (text-only), `FewShotPromptTemplate` (examples) |
| **Production gotcha** | Always store prompts in `app/prompts.py`; one prompt per responsibility; include format constraints; evaluate before deploying changes |

## ➡️ Next Steps

- **Example file:** `app/prompts.py` — all RetailOps prompt templates in one place
- **Next doc:** `../04_prompt_engineering_patterns/README.md` — *what* to put inside those templates
- **Official docs:** https://python.langchain.com/docs/concepts/prompt_templates/
