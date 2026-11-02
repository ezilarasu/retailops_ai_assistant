# Structured Output
> Force the model to return typed, validated data — not free-form text.

## 📌 What Is It?

**Structured Output** is a technique that constrains an LLM to return data matching a predefined Pydantic schema, rather than free-form text. The model doesn't just produce text that looks like JSON — it's forced at the API level to produce a valid structured response.

Without structured output:
```python
result = chain.invoke({"question": "Should this go to RAG or tools?"})
# → "I believe this should be routed to the RAG workflow."
# → "rag"
# → "The route is: rag"  (all possible, all different)
```

With structured output:
```python
result = chain.invoke({"question": "Should this go to RAG or tools?"})
# → RouteDecision(route="rag", reasoning="Policy question found in documents")
# Always. Typed. Validated. Accessable as result.route
```

Think of it like a typed API endpoint: instead of returning raw text that callers must parse, you define a schema and the model fills it in.

## ❓ Why Does It Exist?

LLMs are probabilistic. Without constraints, the same question can produce:
```
"The answer is 18 vacation days."
"Employees receive eighteen days of PTO."
"18 days."
```

All correct — but your application can't reliably process any of them. `if answer == "18"` fails on the first and second. Even with format instructions in the prompt ("return JSON only"), the model can ignore them.

`with_structured_output()` uses the model provider's function calling / tool use mechanism under the hood. The model *cannot* produce free text — it fills in a schema. This is a guarantee from the API, not a prompt instruction.

## ⏰ When Should You Use It?

✅ Routing decisions (`route: str` field your code branches on)  
✅ RAG responses that return answer + sources + confidence  
✅ Evaluation scores (correct/grounded/complete)  
✅ Data extraction from text (invoice fields, entity recognition)  
✅ Any response your application logic depends on  

❌ General conversational text — don't constrain free-form chat responses  
❌ Summarization and creative writing — constraints break natural language output  
❌ Any case where `StrOutputParser` is sufficient  

## 🗂️ Types / Variants

| Approach | How It Works | Best For |
|---|---|---|
| `llm.with_structured_output(Schema)` | Uses function calling — model is API-constrained | **Production standard** — all structured data |
| `PydanticOutputParser` | Prompts model to return JSON, then parses + validates | Fallback for models without function calling support |
| `JsonOutputParser` | Prompts model to return JSON, no Pydantic validation | Quick JSON without schema enforcement |
| JSON in prompt | `"Return JSON with keys: answer, confidence"` | Unreliable — model can ignore instructions |

## 🔀 When to Use Which Type

**Always use `with_structured_output(Schema)` in production.** It's constrained at the API level, not at the prompt level. The model cannot return free text — the API validates the response before it reaches your code.

**Use `PydanticOutputParser`** only for local models (Ollama, llama.cpp) that don't support function calling. Add format instructions to the prompt and parse the output.

**Never rely on JSON in a prompt** for anything your code branches on. The model will follow format instructions most of the time — until it doesn't, and your routing logic breaks.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| API-level guarantee — model cannot return wrong format | More setup (define Pydantic schema first) |
| Pydantic validation — type errors caught immediately | Not all providers support every schema type |
| Typed Python objects (`result.route`, `result.confidence`) | Doesn't work well for schemas with many optional fields |
| Eliminates fragile string parsing in application code | Not suitable for free-text responses |
| Works in LCEL chains: `prompt \| llm.with_structured_output(Schema)` | |

## 💻 Basic Example

```python
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# ── Step 1: Define a Pydantic schema ─────────────────────────────────────
class SentimentResult(BaseModel):
    sentiment: str = Field(description="positive, negative, or neutral")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    reasoning: str = Field(description="Brief explanation of the sentiment")

# ── Step 2: Bind the schema to the LLM ───────────────────────────────────
structured_llm = llm.with_structured_output(SentimentResult)

# ── Step 3: Build the chain ───────────────────────────────────────────────
prompt = ChatPromptTemplate.from_messages([
    ("system", "Analyze the sentiment of the customer review."),
    ("human", "Review: {review}"),
])

chain = prompt | structured_llm  # no parser needed — output is already SentimentResult

# ── Step 4: Invoke and use typed fields ───────────────────────────────────
result = chain.invoke({"review": "The return process was frustrating and slow."})

print(type(result))           # SentimentResult (Pydantic model)
print(result.sentiment)       # "negative"
print(result.confidence)      # 0.92
print(result.reasoning)       # "Customer expresses frustration with..."

# Use fields directly — no string parsing required
if result.sentiment == "negative" and result.confidence > 0.8:
    print("Flag for review")
```

## 🔧 Real-World Example

These are the actual schemas RetailOps uses across its RAG, routing, and evaluation pipelines.

```python
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# ══════════════════════════════════════════════════════════════════════════
# SCHEMA 1: RAGResponse — structured answer with attribution
# Used by the RAG chain to return answer + sources + confidence
# ══════════════════════════════════════════════════════════════════════════
class RAGResponse(BaseModel):
    answer: str = Field(
        description="Answer based ONLY on the provided context"
    )
    sources: list[str] = Field(
        description="List of source document names cited in the answer"
    )
    confidence: str = Field(
        description="Confidence level: high | medium | low"
    )

rag_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are RetailOps AI Assistant.
Answer ONLY using the provided context.
If the answer is not present, set answer to "I don't know based on available documents." """),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])

rag_chain = rag_prompt | llm.with_structured_output(RAGResponse)

rag_result = rag_chain.invoke({
    "context": "Employees receive 18 days of paid vacation annually. Source: hr_policy.txt",
    "question": "How many vacation days do employees get?",
})

print(rag_result.answer)      # "Employees receive 18 days of paid vacation annually."
print(rag_result.sources)     # ["hr_policy.txt"]
print(rag_result.confidence)  # "high"

# Application logic uses typed fields — no string parsing needed
if rag_result.confidence == "low":
    print("[Warning: low-confidence answer — consider escalating]")

# ══════════════════════════════════════════════════════════════════════════
# SCHEMA 2: RouteDecision — intent classification for workflow selection
# Used by the router to select: general | rag | tools
# ══════════════════════════════════════════════════════════════════════════
class RouteDecision(BaseModel):
    route: str = Field(
        description="Exactly one of: general, rag, tools"
    )
    reasoning: str = Field(
        description="Why this route was chosen"
    )
    confidence: str = Field(
        description="high | medium | low"
    )

router_prompt = ChatPromptTemplate.from_messages([
    ("system", """Route the question:
- general: greetings, small talk, general knowledge
- rag: company policies, procedures, HR documents
- tools: real-time data (inventory, orders, incidents)"""),
    ("human", "Question: {question}"),
])

router_chain = router_prompt | llm.with_structured_output(RouteDecision)

decision = router_chain.invoke({"question": "What is the overtime policy?"})

print(decision.route)      # "rag"
print(decision.reasoning)  # "Overtime policy is a company policy found in HR documents"

# Application branches on a typed field — not string matching
if decision.route == "rag":
    print("→ Routing to RAG pipeline")
elif decision.route == "tools":
    print("→ Routing to tool agent")

# ══════════════════════════════════════════════════════════════════════════
# SCHEMA 3: JudgeResult — evaluation of RAG answer quality
# Used by the LLM-as-judge evaluation pipeline
# ══════════════════════════════════════════════════════════════════════════
class JudgeResult(BaseModel):
    correct: bool = Field(
        description="Is the answer factually correct per the expected answer?"
    )
    grounded: bool = Field(
        description="Is every claim in the answer supported by the provided context?"
    )
    complete: bool = Field(
        description="Does the answer address the full question without missing key information?"
    )
    score: float = Field(
        description="Overall quality score from 0.0 to 1.0"
    )
    reasoning: str = Field(
        description="Step-by-step evaluation explaining each score"
    )

judge_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert evaluator. Think step by step before scoring."),
    ("human", """Question: {question}
Context: {context}
Expected: {expected}
Actual: {actual}

Evaluate correctness, groundedness, and completeness."""),
])

judge_chain = judge_prompt | llm.with_structured_output(JudgeResult)

eval_result = judge_chain.invoke({
    "question": "How many vacation days do employees receive?",
    "context": "Employees receive 18 days of paid vacation annually.",
    "expected": "18 days",
    "actual": "Employees receive 18 days of paid vacation annually.",
})

print(eval_result.correct)    # True
print(eval_result.grounded)   # True
print(eval_result.complete)   # True
print(eval_result.score)      # 1.0

# Programmatic evaluation — typed booleans, no string matching
passed = eval_result.correct and eval_result.grounded and eval_result.complete
print(f"Test passed: {passed}")
```

## 🏭 Production Best Practices

1. **Use `with_structured_output()` for any response your code branches on** — Routing, evaluation, classification, extraction. If your code does `if result.route == "rag"`, that field must come from a schema, not a parsed string. **Why:** Prompt-based JSON instructions are not guaranteed. Function calling is.

2. **Keep schemas focused — minimum viable fields** — A schema with 15 fields is hard for the model to fill reliably. Separate concerns: `RAGResponse` for answers, `RouteDecision` for routing, `JudgeResult` for evaluation. **Rule:** if you can't explain why each field is needed, remove it.

3. **Add `Field(description=...)` to every field** — The description is passed to the model as part of the schema. Good descriptions produce better outputs. `answer: str = Field(description="Answer based ONLY on the provided context")` guides the model more precisely than `answer: str`.

4. **Version schemas as API contracts** — A schema change that removes or renames a field breaks all downstream code that accesses it. Treat schemas like API versions. Add new optional fields rather than renaming existing ones.

5. **Use `temperature=0` with structured output** — Temperature controls randomness. For typed responses that must be consistent, determinism is mandatory. A routing decision that returns "rag" 90% of the time and "RAG" 10% of the time causes bugs.

6. **Validate field values with Pydantic `Field` constraints** — For enum-like fields, add validation: `route: Literal["general", "rag", "tools"]`. Pydantic raises a `ValidationError` if the model returns an invalid value, which you can catch and handle.

## ⚠️ Common Mistakes to Avoid

⚠️ **Using `JsonOutputParser` for routing** — `JsonOutputParser` relies on the model following format instructions. `with_structured_output()` uses function calling — the model cannot produce invalid output. For any routing decision, use `with_structured_output()`.

⚠️ **Giant schemas** — A 20-field schema for a routing decision adds latency and confuses the model. Each schema should have the minimum fields needed. Separate concerns into separate schemas.

⚠️ **No field descriptions** — `route: str` tells the model almost nothing. `route: str = Field(description="Exactly one of: general, rag, tools")` tells it exactly what to put there. Always add descriptions.

⚠️ **Structured output for conversational text** — Wrapping a general chat chain in `with_structured_output(ChatResponse)` when a plain string would do adds unnecessary latency and complexity. Use structured output only when the schema adds value.

⚠️ **Checking string equality on unvalidated fields** — If `route` can be "rag", "RAG", "Rag", or "retrieval", your `if decision.route == "rag"` check silently fails 30% of the time. Use `Literal["general", "rag", "tools"]` to enforce valid values.

## 🔗 How It Connects to Other Concepts

- **Output Parsers** (doc 07) — The alternative for text output; parsers *convert* output, structured output *constrains* it
- **Prompt Engineering Patterns** (doc 04) — Structured prompting pairs with `with_structured_output()` — prompt defines what to output, schema defines the format
- **Router Pattern** (doc 23) — `RouteDecision` + `with_structured_output()` is the core of every router chain
- **RAG Chains** (doc 18) — `RAGResponse` with answer, sources, and confidence is the standard structured output for RAG
- **RAG Evaluation** (doc 19) — `JudgeResult` is the evaluation schema; structured output makes evaluation programmatic
- **Tools & Function Calling** (doc 20) — `with_structured_output()` uses function calling under the hood

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | API-level constraint that forces the LLM to return a Pydantic schema instead of free text |
| **Why** | Reliable, typed, validated responses — no fragile string parsing for application logic |
| **When** | Routing, RAG responses with attribution, evaluation scores, data extraction — any response code branches on |
| **Types** | `with_structured_output(Schema)` (production), `PydanticOutputParser` (fallback for no-function-calling models) |
| **Production gotcha** | Use `temperature=0`; keep schemas focused (min fields); add `Field(description=...)` to every field; treat schemas as API contracts |

## ➡️ Next Steps

- **Example file:** `app/schemas.py` — RetailOps `RAGResponse`, `RouteDecision`, `JudgeResult` definitions
- **Next doc:** `09_document_loaders.md` — how external documents enter a RAG system
- **Official docs:** https://python.langchain.com/docs/concepts/structured_outputs/
