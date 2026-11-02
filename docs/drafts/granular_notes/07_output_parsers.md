# 07 - Output Parsers

# Learning Objectives

After completing this document, you should understand:

* What Output Parsers are
* Why Output Parsers exist
* Output Parsers vs Raw LLM Output
* StrOutputParser
* Structured Output
* Pydantic Output Parsing
* JSON Parsing
* Parser Patterns
* Parser Tradeoffs
* Production Best Practices
* RetailOps Implementation

---

# 1. What is an Output Parser?

## Definition

An Output Parser converts the output of an LLM into a format that an application can use.

Think of it as:

```text id="parser1"
LLM Output
 ↓
Parser
 ↓
Application Data
```

---

# Why Do We Need Parsers?

LLMs naturally return:

```text id="parser2"
Text
```

Applications usually need:

```text id="parser3"
String
JSON
Object
Schema
```

---

# Example

Question:

```text id="parser4"
How many vacation days do employees receive?
```

---

Raw Model Output:

```text id="parser5"
Employees receive 18 paid vacation days.
```

---

Application Wants:

```python id="parser6"
{
    "answer": "...",
    "source": "...",
}
```

---

Parser helps bridge this gap.

---

# 2. Without Output Parsers

Example:

```python id="parser7"
response = llm.invoke(question)
```

Output:

```python id="parser8"
AIMessage(
    content="..."
)
```

---

To access content:

```python id="parser9"
response.content
```

---

Works.

But becomes messy at scale.

---

# 3. With Output Parsers

Example:

```python id="parser10"
chain = (
    prompt
    | llm
    | StrOutputParser()
)
```

---

Output:

```python id="parser11"
"Employees receive 18 paid vacation days."
```

---

Much cleaner.

---

# 4. StrOutputParser

## Definition

The simplest parser.

Converts:

```python id="parser12"
AIMessage
```

into:

```python id="parser13"
str
```

---

Example

```python id="parser14"
from langchain_core.output_parsers import (
    StrOutputParser
)

chain = (
    prompt
    | llm
    | StrOutputParser()
)
```

---

Output:

```python id="parser15"
"Python is a programming language."
```

---

# Why Use It?

Avoids:

```python id="parser16"
response.content
```

everywhere.

---

# RetailOps

Used in:

```text id="parser17"
General Chat
Question Rewriter
Multi Query Generation
```

---

# 5. Data Flow Example

Without parser:

```text id="parser18"
Question
 ↓
Prompt
 ↓
LLM
 ↓
AIMessage
```

---

With parser:

```text id="parser19"
Question
 ↓
Prompt
 ↓
LLM
 ↓
String
```

---

# 6. Structured Output

Most production systems need:

```text id="parser20"
Objects
```

not text.

---

Example

Bad:

```text id="parser21"
The answer is 18 vacation days.
```

---

Application must parse manually.

---

Better:

```python id="parser22"
RAGResponse(
    answer="18 vacation days",
    sources=["hr_policy.txt"],
    confidence="high"
)
```

---

# 7. Pydantic Models

LangChain uses:

```python id="parser23"
Pydantic
```

for structured output.

---

Example

```python id="parser24"
from pydantic import BaseModel

class RAGResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: str
```

---

# Why?

Defines a contract.

---

# 8. with_structured_output()

## Definition

Force the model to return a schema.

---

Example

```python id="parser25"
structured_llm = (
    llm.with_structured_output(
        RAGResponse
    )
)
```

---

Output:

```python id="parser26"
RAGResponse(...)
```

---

instead of:

```python id="parser27"
str
```

---

# RetailOps

Used for:

```text id="parser28"
RAGResponse
JudgeResult
RouteDecision
```

---

# 9. Why Structured Output Is Better

Without:

```text id="parser29"
Unpredictable Text
```

---

With:

```text id="parser30"
Predictable Object
```

---

Example

Without:

```text id="parser31"
The answer is probably...
```

---

With:

```json id="parser32"
{
  "answer": "...",
  "confidence": "high"
}
```

---

# 10. Parser Categories

## String Parser

Output:

```python id="parser33"
str
```

---

## JSON Parser

Output:

```python id="parser34"
dict
```

---

## Structured Output

Output:

```python id="parser35"
Pydantic Model
```

---

# 11. Output Parsing vs Structured Output

This is important.

---

# Output Parsing

Model:

```text id="parser36"
Produces Text
```

---

Parser:

```text id="parser37"
Attempts Conversion
```

---

Example

```text id="parser38"
JSON Text
```

↓

```python id="parser39"
dict
```

---

# Structured Output

Model:

```text id="parser40"
Directly Produces Schema
```

---

Example

```python id="parser41"
RAGResponse
```

directly.

---

# Which Is Better?

For production:

```text id="parser42"
Structured Output
```

usually wins.

---

# 12. Evaluation Example

RetailOps Judge:

```python id="parser43"
JudgeResult
```

Fields:

```text id="parser44"
correct
grounded
complete
explanation
```

---

Output:

```python id="parser45"
JudgeResult(...)
```

---

No manual parsing required.

---

# 13. Router Example

Router Output:

```python id="parser46"
RouteDecision
```

---

Fields:

```text id="parser47"
route
reason
```

---

Application can route immediately.

---

# 14. Parser Tradeoffs

## String Parser

Pros:

```text id="parser48"
Simple
Fast
```

---

Cons:

```text id="parser49"
No Structure
```

---

## Structured Output

Pros:

```text id="parser50"
Reliable
Typed
Predictable
```

---

Cons:

```text id="parser51"
More Setup
```

---

# 15. Production Best Practices

## Use Structured Output

Whenever:

```text id="parser52"
Application Logic
```

depends on results.

---

## Use String Parser

For:

```text id="parser53"
General Chat
Simple Text Generation
```

---

## Avoid Manual Parsing

Bad:

```python id="parser54"
if "high" in response:
```

---

Good:

```python id="parser55"
result.confidence
```

---

## Version Schemas

Treat schemas as API contracts.

---

# 16. Common Mistakes

## Mistake 1

Using plain text for machine logic.

---

## Mistake 2

Manually parsing JSON strings.

---

## Mistake 3

No validation.

---

## Mistake 4

Not using Pydantic.

---

# 17. RetailOps Implementation

Current Schemas:

```text id="parser56"
RAGResponse
RouteDecision
JudgeResult
ChatRequest
ChatResponse
```

---

Used in:

```text id="parser57"
RAG
Routing
Evaluation
API Layer
```

---

# 18. Interview Questions

### What is an Output Parser?

A component that converts model output into usable application data.

---

### Why use StrOutputParser?

Converts AIMessage into a string.

---

### What is structured output?

Schema-constrained model output.

---

### Why use Pydantic?

Validation and type safety.

---

### Output Parsing vs Structured Output?

Output Parsing:

```text id="parser58"
Convert model output
```

Structured Output:

```text id="parser59"
Generate schema directly
```

---

### Which is better for production?

Structured Output.

---

# Summary

Output Parsers transform:

```text id="parser60"
LLM Output
```

into:

```text id="parser61"
Strings
Objects
Schemas
```

and are essential for:

```text id="parser62"
Routing
RAG
Evaluation
APIs
Agents
```

RetailOps uses both:

```text id="parser63"
StrOutputParser
```

and

```text id="parser64"
Structured Output
```

depending on the use case.

The next document:

```text id="parser65"
08_structured_output.md
```

will dive deeper into schema-driven AI applications and why structured output is one of the most important production patterns in modern LangChain systems.
