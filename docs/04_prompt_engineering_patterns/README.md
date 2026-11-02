# Prompt Engineering Patterns
> The techniques that determine whether your LLM application is reliable or unpredictable.

## 📌 What Is It?

**Prompt Engineering** is the process of designing the *content* of prompts to reliably guide an LLM toward the desired behavior, format, and accuracy.

Think of a prompt as a program written in natural language:
```
Bad program:  "Sort my data"
Good program: "Sort the list in ascending order. Return only the sorted list. No explanation."
```

The same logic applies to LLMs. A vague instruction produces a vague response. A precise instruction with a defined role, constraints, and output format produces a predictable, useful response.

This document covers the patterns — **what to put inside** your `ChatPromptTemplate`. The previous doc covered the templates themselves.

## ❓ Why Does It Exist?

LLMs are probabilistic. They predict the next most likely token. Small changes to your prompt shift those probabilities — sometimes dramatically.

Without intentional prompt design:
```
Prompt:  "Explain Python."
Output:  Generic 500-word essay. May include code, may not. May be too advanced.
```

With intentional prompt design:
```
Prompt:  "You are a Python instructor teaching beginners.
          Explain Python in 3 bullet points: what it is, one use case, one example.
          Maximum 100 words."
Output:  Exactly 3 concise bullet points. Every time.
```

Prompt engineering is also the highest-leverage RAG optimization. The most common RAG failure mode isn't a bad model — it's a prompt that allows hallucination, permits vague answers, or doesn't constrain output format.

## ⏰ When Should You Use It?

✅ Every time you write a prompt — prompt engineering isn't optional  
✅ When model outputs are inconsistent across runs  
✅ When the model is hallucinating despite having correct context  
✅ When output format is critical (routing, classification, extraction)  
✅ When you need to constrain the model to a specific knowledge domain  

❌ There is no "don't use" scenario — every prompt benefits from intentional design  

The question is which *patterns* to apply, not whether to apply them.

## 🗂️ Types / Variants

| Pattern | What It Does | Best For |
|---|---|---|
| **Zero-Shot** | Task with no examples | Simple classification, summarization, general Q&A |
| **Few-Shot** | Task with examples provided | Extraction, formatting, complex classification |
| **Role Prompting** | Assigns a persona to the model | Influencing tone, depth, vocabulary |
| **Constraint Prompting** | Defines explicit limits | Preventing hallucination, capping length, enforcing format |
| **Structured Prompting** | Requests machine-readable output | Routing decisions, evaluations, parsed responses |
| **Chain-of-Thought** | Asks model to reason step-by-step | Math, multi-step logic, complex reasoning |
| **RAG Prompts** | Grounds answers to provided context | Document Q&A, policy lookup, knowledge retrieval |
| **Routing Prompts** | Classifies request into a workflow | Intent detection, routing to RAG vs tools vs chat |
| **History-Aware Prompts** | Rewrites follow-ups as standalone queries | Conversational RAG with memory |
| **Multi-Query Prompts** | Generates alternative phrasings | Improving RAG recall for ambiguous questions |

## 🔀 When to Use Which Type

**Start with Role + Constraint + Output Format for every prompt.** This baseline gives you persona, limits, and predictable structure.

**Add Few-Shot** when zero-shot produces inconsistent formatting or when the task has subtle rules that examples communicate better than instructions.

**Use RAG prompts** whenever your chain injects retrieved context — always include "answer only using the provided context" to prevent hallucination.

**Use Routing prompts** when the model must choose between workflows. Combine with `with_structured_output()` for reliable route values.

**Use History-Aware prompts** when your RAG chain has conversation memory — retrievers need complete questions, not "what about part-time employees?"

**Reserve Chain-of-Thought** for genuinely complex reasoning tasks. Modern models (GPT-4o, Claude 3.5, Llama 3.3) often reason well without explicit CoT prompts.

## ⚖️ Pros & Cons

| Pattern | ✅ Benefit | ❌ Cost |
|---|---|---|
| Zero-Shot | Simple, cheap | Less reliable for complex tasks |
| Few-Shot | Higher accuracy | Uses context window (tokens = cost) |
| Role Prompting | Shapes behavior effectively | No cost — always use |
| Constraint | Prevents hallucination | Prompts become longer |
| Structured | Reliable machine-readable output | Needs paired `with_structured_output()` |
| Chain-of-Thought | Better reasoning | More tokens, higher latency |
| Multi-Query | Higher recall | 3× more LLM calls |

## 💻 Basic Example

```python
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field

load_dotenv()

llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)

# ── Pattern 1: Zero-Shot ──────────────────────────────────────────────────
zero_shot = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{question}"),
])
chain = zero_shot | llm | StrOutputParser()
print(chain.invoke({"question": "What is RAG?"}))

# ── Pattern 2: Role + Constraint (baseline for every production prompt) ───
role_constraint = ChatPromptTemplate.from_messages([
    ("system", """You are a retail operations expert.
Answer in plain language suitable for warehouse staff.
Maximum 3 sentences. No jargon."""),
    ("human", "{question}"),
])
chain = role_constraint | llm | StrOutputParser()
print(chain.invoke({"question": "What is cycle counting?"}))

# ── Pattern 3: Few-Shot ───────────────────────────────────────────────────
few_shot = ChatPromptTemplate.from_messages([
    ("system", """Classify the question type. Return ONLY the label.

Example: "How many vacation days do we get?" → policy
Example: "How many units of SKU-123 do we have?" → inventory
Example: "What is the weather today?" → out_of_scope"""),
    ("human", "{question}"),
])
chain = few_shot | llm | StrOutputParser()
print(chain.invoke({"question": "What is the overtime pay rate?"}))
# → "policy"
```

## 🔧 Real-World Example

This shows the prompt patterns used in RetailOps, in simplified teaching form. The real prompts are in `app/prompts.py` (RAG, router, rewrite), `app/multi_query.py` (multi-query) and `evals/judge.py` (LLM-as-judge). Two differences to know about: the real `RouteDecision` has only `route` and `reason` (no `confidence`), and RetailOps' router prompts don't include few-shot examples — the examples below show the pattern so you can add them yourself. Each prompt applies a specific combination of patterns.

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
# PATTERN: RAG Prompt — Role + Constraint + Grounding
# Critical rule: "answer ONLY using provided context"
# This single constraint eliminates most hallucinations in RAG systems.
# ══════════════════════════════════════════════════════════════════════════
rag_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are RetailOps AI Assistant.
Answer ONLY using the provided context.
Do NOT use your own knowledge or make assumptions beyond the context.
If the answer is not present in the context, respond with exactly:
"I don't know based on the available documents."
Cite the source document name when possible."""),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])

# ══════════════════════════════════════════════════════════════════════════
# PATTERN: Routing Prompt — Structured Output + Few-Shot examples
# The model must choose exactly one route. Pair with with_structured_output()
# to guarantee a valid route value, not free text.
# ══════════════════════════════════════════════════════════════════════════
class RouteDecision(BaseModel):
    route: str = Field(description="Exactly one of: general, rag, tools")
    confidence: str = Field(description="high | medium | low")

router_prompt = ChatPromptTemplate.from_messages([
    ("system", """Route each question to the correct workflow.

Routes:
- general: greetings, small talk, general knowledge not in company docs
- rag: company policies, procedures, HR docs, vendor agreements, SOPs
- tools: real-time operational data (inventory counts, order status, incidents)

Examples:
"How are you?" → general
"What is the return policy?" → rag
"How many units of SKU-456 are in stock?" → tools
"What happens if I work overtime?" → rag"""),
    ("human", "Question: {question}"),
])
router_chain = router_prompt | llm.with_structured_output(RouteDecision)

# ══════════════════════════════════════════════════════════════════════════
# PATTERN: History-Aware Rewrite — converts follow-ups to standalone queries
# Retrievers can't understand "what about them?" without conversation context.
# This rewrite makes every retrieval query self-contained.
# ══════════════════════════════════════════════════════════════════════════
rewrite_prompt = ChatPromptTemplate.from_messages([
    ("system", """Rewrite the follow-up question as a complete standalone question
that can be understood without reading the conversation history.
Return ONLY the rewritten question. No explanation, no preamble."""),
    ("human", """Conversation history:
{history}

Follow-up question: {question}

Standalone question:"""),
])
rewriter_chain = rewrite_prompt | llm | StrOutputParser()

# ══════════════════════════════════════════════════════════════════════════
# PATTERN: Multi-Query — generates alternative phrasings for better recall
# "How much PTO do we get?" also needs "vacation days" and "paid leave" etc.
#
# NOTE: In RetailOps this prompt is NOT defined in app/prompts.py alongside
# the others above. It's built inline inside build_multi_query_chain() in
# app/multi_query.py, right next to the function that uses it.
# ══════════════════════════════════════════════════════════════════════════
multi_query_prompt = ChatPromptTemplate.from_messages([
    ("system", """Generate 3 different phrasings of the question below.
These alternatives will be used to improve document search recall.
Return exactly 3 questions, one per line. No numbering or bullet points."""),
    ("human", "Question: {question}"),
])
multi_query_chain = multi_query_prompt | llm | StrOutputParser()
# In the real codebase this is app.multi_query.build_multi_query_chain(),
# and generate_queries(question) calls it + dedupes/limits the results.

# ══════════════════════════════════════════════════════════════════════════
# PATTERN: LLM-as-Judge — evaluation prompt with Chain-of-Thought reasoning
# Used to evaluate RAG answers against golden dataset expected answers.
# ══════════════════════════════════════════════════════════════════════════
class JudgeResult(BaseModel):
    correct: bool = Field(description="Is the answer factually correct?")
    grounded: bool = Field(description="Is every claim supported by the context?")
    complete: bool = Field(description="Does the answer address the full question?")
    reasoning: str = Field(description="Brief explanation of the evaluation")

judge_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert evaluator for a retail AI assistant.
Evaluate the answer against the expected answer and context.
Think step by step before deciding each score."""),
    ("human", """Question: {question}
Context provided: {context}
Expected answer: {expected}
Actual answer: {actual}

Evaluate: Is it correct, grounded in context, and complete?"""),
])
judge_chain = judge_prompt | llm.with_structured_output(JudgeResult)

# ── Test the routing chain ─────────────────────────────────────────────────
decision = router_chain.invoke({"question": "What is our overtime pay policy?"})
print(f"Route: {decision.route}, Confidence: {decision.confidence}")
# → Route: rag, Confidence: high

# ── Test the rewriter chain ────────────────────────────────────────────────
standalone = rewriter_chain.invoke({
    "history": "User asked about vacation days for full-time employees.",
    "question": "What about part-time?",
})
print(standalone)
# → "What is the vacation day policy for part-time employees?"

# ── Test the multi-query chain ─────────────────────────────────────────────
alternatives = multi_query_chain.invoke({"question": "How much PTO do we get?"})
print(alternatives)
```

## 🏭 Production Best Practices

1. **Always include Role + Constraint + Format** — These three patterns combined form the baseline for every production prompt. Role shapes behavior, constraints prevent hallucination, format makes output parseable. If you add nothing else, add these three.

2. **Ground RAG prompts with explicit "context only" instructions** — Always include: *"Answer ONLY using the provided context. If the answer is not in the context, say 'I don't know.'"* **Why:** Without this, the model will use training knowledge to fill gaps, producing confident hallucinations that look correct.

3. **Use `with_structured_output()` for routing and classification prompts** — Free-text responses from routing prompts break your dispatcher. A structured response guarantees a valid route value. **How:** `router_chain = router_prompt | llm.with_structured_output(RouteDecision)`.

4. **Use few-shot examples sparingly and measure their cost** — Each example consumes tokens on every request. 3 examples × 50 tokens × 10,000 daily requests = 1.5M extra tokens per day. Use examples only when zero-shot underperforms. **How:** Add to system message, measure improvement with your golden dataset.

5. **Evaluate prompt changes — never assume improvement** — A prompt that fixes one failure case often breaks another. **How:** Run every prompt version through your full golden dataset before deploying. Compare pass rates.

6. **Version prompts with comments** — Document why a prompt changed:
   ```python
   # v2: Added explicit "do not make assumptions" after hallucination in prod 2024-11-15
   rag_prompt = ChatPromptTemplate.from_messages([...])
   ```

## ⚠️ Common Mistakes to Avoid

⚠️ **Vague instructions** — `"Explain Python."` produces generic output. `"Explain Python to a beginner. Include one example. Maximum 100 words."` produces what you need. Specificity is everything.

⚠️ **No output format specification** — `"Summarize this document"` produces different formats on every call. Always specify: `"Return a JSON object with keys: summary, risks, recommendations."` or use `with_structured_output()`.

⚠️ **Allowing the model to use its own knowledge in RAG** — The single biggest source of RAG hallucinations. The context says "18 days vacation" but the model "knows" common policies are 15 days and confidently says 15. Fix: add "ONLY use the provided context. Do not use prior knowledge."

⚠️ **One giant prompt doing multiple tasks** — A prompt that routes AND answers AND evaluates will do all three poorly. Split into focused prompts for each job.

⚠️ **Not testing against adversarial inputs** — Test your prompts with ambiguous questions, empty context, contradictory information, and off-topic requests. Edge cases break production prompts far more often than happy-path cases.

## 🔗 How It Connects to Other Concepts

- **Prompt Templates** (doc 03) — The container for these patterns; `ChatPromptTemplate` holds the pattern implementations
- **Structured Output** (doc 08) — The output half of structured prompting; prompts constrain *input*, structured output constrains *response schema*
- **RAG Chains** (doc 18) — RAG prompts are the difference between grounded answers and hallucinations
- **Multi-Query Retrieval** (doc 16) — The multi-query pattern generates alternative phrasings to improve recall
- **History-Aware Retrieval** (doc 17) — The rewrite pattern makes follow-up questions work with retrievers
- **RAG Evaluation** (doc 19) — LLM-as-judge prompts measure answer quality systematically
- **Router Pattern** (doc 23) — Routing prompts + structured output is how intent classification works

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Techniques for designing prompts that reliably guide LLM behavior |
| **Why** | Small prompt changes have large output effects; intentional design prevents hallucination and inconsistency |
| **When** | Every prompt — prompt engineering is not optional |
| **Types** | Zero-Shot, Few-Shot, Role, Constraint, Structured, CoT, RAG, Routing, History-Aware, Multi-Query |
| **Production gotcha** | Always add Role + Constraint + Format; ground RAG prompts to context only; use structured output for routing; evaluate every prompt change with golden dataset |

## ➡️ Next Steps

- **Example file:** `app/prompts.py` — all RetailOps prompt patterns in one place
- **Next doc:** `../05_lcel/README.md` — how to compose these prompts into pipelines
- **Official docs:** https://python.langchain.com/docs/concepts/prompt_templates/
