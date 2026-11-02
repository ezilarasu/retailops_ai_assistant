# 08 - Structured Output

# Learning Objectives

After completing this document, you should understand:

* What Structured Output is
* Why Structured Output exists
* Structured Output vs Text Output
* Structured Output vs Output Parsers
* Pydantic Models
* Schema Design
* Validation
* Function Calling Relationship
* Production Use Cases
* RetailOps Implementation
* Best Practices

---

# 1. What is Structured Output?

## Definition

Structured Output is a technique that forces an LLM to return data in a predefined schema rather than free-form text.

---

Without Structured Output:

```text id="so1"
The answer is 18 vacation days.
```

---

With Structured Output:

```json id="so2"
{
  "answer": "18 vacation days",
  "confidence": "high"
}
```

---

# Why Does Structured Output Exist?

Applications need:

```text id="so3"
Reliable
Predictable
Machine-readable
```

data.

---

LLMs naturally produce:

```text id="so4"
Text
```

Applications usually need:

```text id="so5"
Objects
```

---

# 2. Problem Without Structured Output

Question:

```text id="so6"
How many vacation days do employees receive?
```

---

Model A:

```text id="so7"
Employees receive 18 vacation days.
```

---

Model B:

```text id="so8"
The policy provides eighteen vacation days.
```

---

Model C:

```text id="so9"
18 days.
```

---

All correct.

But difficult for applications.

---

# Example Problem

Suppose:

```python id="so10"
if answer == "18":
```

This fails.

---

Because responses vary.

---

# 3. Structured Output Solution

Define a schema:

```python id="so11"
class VacationPolicy(BaseModel):
    days: int
```

---

Output:

```python id="so12"
VacationPolicy(
    days=18
)
```

Always consistent.

---

# 4. Structured Output vs Text Output

## Text Output

Output:

```text id="so13"
Employees receive 18 vacation days.
```

---

Pros:

```text id="so14"
Flexible
Natural
```

---

Cons:

```text id="so15"
Unpredictable
```

---

## Structured Output

Output:

```python id="so16"
{
  "days": 18
}
```

---

Pros:

```text id="so17"
Predictable
Reliable
```

---

Cons:

```text id="so18"
More setup
```

---

# 5. Structured Output vs Output Parsers

Very common interview question.

---

# Output Parser

Flow:

```text id="so19"
LLM
 ↓
Text
 ↓
Parser
 ↓
Object
```

---

Example:

```text id="so20"
JSON text
```

↓

```python id="so21"
dict
```

---

# Structured Output

Flow:

```text id="so22"
LLM
 ↓
Schema
```

---

Output:

```python id="so23"
Object
```

directly.

---

# Difference

Parser:

```text id="so24"
Convert output
```

---

Structured Output:

```text id="so25"
Constrain output
```

---

# Which Is Better?

Production:

```text id="so26"
Structured Output
```

usually wins.

---

# 6. Pydantic Models

Structured Output relies heavily on:

```python id="so27"
Pydantic
```

---

Example

```python id="so28"
from pydantic import BaseModel

class EmployeePolicy(BaseModel):
    vacation_days: int
    source: str
```

---

Why Pydantic?

Provides:

```text id="so29"
Validation
Typing
Serialization
```

---

# 7. LangChain Structured Output

Example:

```python id="so30"
structured_llm = (
    llm.with_structured_output(
        EmployeePolicy
    )
)
```

---

Invocation:

```python id="so31"
result = structured_llm.invoke(
    "How many vacation days?"
)
```

---

Output:

```python id="so32"
EmployeePolicy(
    vacation_days=18,
    source="hr_policy.txt"
)
```

---

# 8. Validation

Pydantic validates results.

---

Schema:

```python id="so33"
vacation_days: int
```

---

Model returns:

```text id="so34"
eighteen
```

---

Validation:

```text id="so35"
Fails
```

---

This is good.

---

Because:

```text id="so36"
Bad data is detected.
```

---

# 9. Schema Design Principles

Good schema:

```python id="so37"
class RAGResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: str
```

---

Bad schema:

```python id="so38"
class Everything(BaseModel):
    field1
    field2
    ...
    field50
```

---

Rule:

```text id="so39"
Keep schemas focused.
```

---

# 10. RetailOps RAGResponse

Current:

```python id="so40"
class RAGResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: str
```

---

Why?

Application needs:

```text id="so41"
Answer
Source
Confidence
```

---

Nothing more.

---

# 11. RetailOps RouteDecision

Current:

```python id="so42"
class RouteDecision(BaseModel):
    route: str
    reason: str
```

---

Output:

```python id="so43"
route="rag"
```

---

Router can act immediately.

---

# 12. RetailOps JudgeResult

Current:

```python id="so44"
class JudgeResult(BaseModel):
    correct: bool
    grounded: bool
    complete: bool
    explanation: str
```

---

Used in:

```text id="so45"
Evaluation
```

---

# Why Structured Output Is Powerful

Without:

```text id="so46"
Text
```

↓

Manual interpretation.

---

With:

```text id="so47"
Typed Object
```

↓

Application logic.

---

# Example

Without:

```python id="so48"
if "high" in response:
```

---

With:

```python id="so49"
if result.confidence == "high":
```

---

Much safer.

---

# 13. Relationship to Function Calling

Modern structured output often uses:

```text id="so50"
Tool Calling
Function Calling
```

under the hood.

---

Model generates:

```json id="so51"
{
  "answer":"...",
  "confidence":"high"
}
```

---

LangChain converts into:

```python id="so52"
RAGResponse(...)
```

---

# Important

Structured Output:

```text id="so53"
Not always function calling
```

but many providers implement it that way.

---

# 14. Production Use Cases

## Routing

```python id="so54"
RouteDecision
```

---

## RAG

```python id="so55"
RAGResponse
```

---

## Evaluation

```python id="so56"
JudgeResult
```

---

## Classification

```python id="so57"
SentimentResult
```

---

## Extraction

```python id="so58"
InvoiceData
```

---

# 15. Production Best Practices

## Use Structured Output for Logic

Good:

```text id="so59"
Routing
Evaluation
Classification
```

---

## Use Text for Conversation

Good:

```text id="so60"
Chat
Explanation
Writing
```

---

## Keep Schemas Small

Avoid:

```text id="so61"
Huge Schemas
```

---

## Validate Results

Use Pydantic.

---

## Version Schemas

Treat schemas as contracts.

---

# 16. Common Mistakes

## Mistake 1

Using text output for routing.

---

## Mistake 2

Huge schemas.

---

## Mistake 3

Not validating.

---

## Mistake 4

Mixing unrelated fields.

---

## Mistake 5

Using structured output for creative writing.

---

# 17. Structured Output vs JSON Prompting

JSON Prompting:

```text id="so62"
Please return JSON...
```

---

Problem:

```text id="so63"
Model may ignore instructions.
```

---

Structured Output:

```python id="so64"
with_structured_output()
```

---

Much more reliable.

---

# 18. Interview Questions

### What is Structured Output?

Schema-constrained model output.

---

### Why use Structured Output?

Predictable machine-readable responses.

---

### Structured Output vs Parser?

Parser:

```text id="so65"
Convert output
```

Structured Output:

```text id="so66"
Constrain output
```

---

### Why use Pydantic?

Validation and typing.

---

### When should Structured Output be used?

When application logic depends on the result.

---

### When should it NOT be used?

General conversation and creative writing.

---

# Summary

Structured Output is one of the most important production patterns in modern AI systems.

It allows:

```text id="so67"
Routing
Evaluation
RAG
Extraction
Classification
```

to operate on:

```text id="so68"
Reliable Typed Data
```

instead of:

```text id="so69"
Unpredictable Text
```

RetailOps relies heavily on structured output through:

```text id="so70"
RAGResponse
RouteDecision
JudgeResult
```

making the application more reliable and maintainable.

The next document:

```text id="so71"
09_document_loaders.md
```

begins the RAG section by explaining how external documents enter a LangChain application.
