# 05 - LCEL (LangChain Expression Language)

# Learning Objectives

After completing this document, you should understand:

* What LCEL is
* Why LCEL was created
* How LCEL works
* The Pipe Operator (`|`)
* Runnable Composition
* Sequential Pipelines
* Parallel Pipelines
* Branching
* Data Flow
* LCEL vs Traditional Python
* LCEL Best Practices
* RetailOps Implementation

---

# 1. What is LCEL?

LCEL stands for:

```text id="lcel1"
LangChain Expression Language
```

It is the modern way to connect LangChain components together.

---

## Definition

LCEL is a declarative syntax for composing:

```text id="lcel2"
Prompts
Models
Parsers
Retrievers
Chains
Tools
```

into pipelines.

---

## Simple Example

```python id="lcel3"
chain = (
    prompt
    | llm
    | parser
)
```

---

Meaning:

```text id="lcel4"
Prompt
 ↓
LLM
 ↓
Parser
```

---

# 2. Why Was LCEL Created?

Before LCEL:

```python id="lcel5"
formatted_prompt = prompt.invoke(data)

response = llm.invoke(formatted_prompt)

result = parser.invoke(response)
```

---

Problems:

```text id="lcel6"
Verbose
Hard to read
Hard to compose
```

---

LCEL:

```python id="lcel7"
chain = prompt | llm | parser
```

Much cleaner.

---

# 3. Core Idea

Every LangChain component is a:

```text id="lcel8"
Runnable
```

If it is a Runnable, it can be connected using:

```python id="lcel9"
|
```

---

# Visual

```text id="lcel10"
Prompt
 ↓
LLM
 ↓
Parser
```

becomes:

```python id="lcel11"
prompt | llm | parser
```

---

# 4. The Pipe Operator

## Definition

The pipe operator passes output from one Runnable into the next Runnable.

---

Example:

```python id="lcel12"
prompt | llm
```

---

Equivalent to:

```python id="lcel13"
formatted = prompt.invoke(data)

result = llm.invoke(formatted)
```

---

# Data Flow

```text id="lcel14"
Input
 ↓
Prompt
 ↓
Messages
 ↓
LLM
 ↓
AIMessage
```

---

# 5. Simple LCEL Chain

Example:

```python id="lcel15"
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

Flow:

```text id="lcel16"
Question
 ↓
Prompt
 ↓
LLM
 ↓
String
```

---

RetailOps:

```text id="lcel17"
General Chat Chain
```

uses this pattern.

---

# 6. invoke()

Every LCEL chain supports:

```python id="lcel18"
invoke()
```

---

Example:

```python id="lcel19"
result = chain.invoke({
    "question": "What is Python?"
})
```

---

# Why?

Runs the entire pipeline.

---

# 7. batch()

Process multiple inputs.

---

Example:

```python id="lcel20"
results = chain.batch([
    {"question": "Python"},
    {"question": "Java"}
])
```

---

Use when:

```text id="lcel21"
Bulk processing
Evaluation
```

---

# 8. stream()

Stream results.

---

Example:

```python id="lcel22"
for chunk in chain.stream(
    {"question":"Python"}
):
    print(chunk)
```

---

Used for:

```text id="lcel23"
Chat Interfaces
Real-Time Responses
```

---

# 9. LCEL Data Transformation

Chains can include custom transformations.

---

Example:

```python id="lcel24"
from langchain_core.runnables import (
    RunnableLambda
)
```

---

```python id="lcel25"
clean_question = RunnableLambda(
    lambda x: x.strip()
)
```

---

Chain:

```python id="lcel26"
clean_question
|
prompt
|
llm
```

---

# Why?

Allows business logic inside pipelines.

---

# 10. LCEL With Retrievers

Example:

```python id="lcel27"
Retriever
 ↓
Prompt
 ↓
LLM
```

---

RetailOps:

```text id="lcel28"
Question
 ↓
Retriever
 ↓
Context
 ↓
RAG Prompt
 ↓
LLM
```

---

Implemented using LCEL.

---

# 11. LCEL With Structured Output

Example:

```python id="lcel29"
structured_llm = (
    llm.with_structured_output(
        RAGResponse
    )
)
```

---

Chain:

```python id="lcel30"
prompt
|
structured_llm
```

---

Output:

```python id="lcel31"
RAGResponse
```

---

Instead of:

```python id="lcel32"
str
```

---

# 12. LCEL With Memory

Example:

```text id="lcel33"
Question
 ↓
History
 ↓
Prompt
 ↓
LLM
```

---

RetailOps:

```text id="lcel34"
Question Rewriter
```

uses memory.

---

# 13. LCEL vs Traditional Python

Traditional:

```python id="lcel35"
a = prompt.invoke(...)

b = llm.invoke(a)

c = parser.invoke(b)
```

---

LCEL:

```python id="lcel36"
prompt | llm | parser
```

---

# Pros

```text id="lcel37"
Readable
Composable
Reusable
```

---

# Cons

```text id="lcel38"
Less explicit for beginners
```

---

# 14. RunnableParallel

Run multiple tasks simultaneously.

---

Example:

```python id="lcel39"
RunnableParallel({
    "summary": summary_chain,
    "keywords": keyword_chain,
})
```

---

Input:

```text id="lcel40"
Document
```

---

Output:

```python id="lcel41"
{
  "summary": "...",
  "keywords": [...]
}
```

---

# When To Use

```text id="lcel42"
Independent Computations
```

---

# RetailOps Future Use

```text id="lcel43"
Retrieval
+
Metadata Analysis
```

in parallel.

---

# 15. RunnableBranch

Conditional execution.

---

Example:

```python id="lcel44"
RunnableBranch(
    (
        condition,
        chain_a,
    ),
    chain_b,
)
```

---

Flow:

```text id="lcel45"
Question
 ↓
Condition
 ├── Chain A
 └── Chain B
```

---

# When To Use

```text id="lcel46"
Routing
Workflow Selection
```

---

# 16. LCEL vs LangGraph

Important distinction.

---

LCEL:

```text id="lcel47"
Pipeline
```

---

LangGraph:

```text id="lcel48"
Workflow
```

---

LCEL:

```text id="lcel49"
Prompt
 ↓
LLM
 ↓
Answer
```

---

LangGraph:

```text id="lcel50"
State
 ↓
Node
 ↓
Conditional Node
 ↓
Retry
 ↓
Approval
```

---

# Rule

Use LCEL first.

Use LangGraph when workflows become complex.

---

# 17. RetailOps LCEL Examples

General Chat:

```python id="lcel51"
prompt
|
llm
|
StrOutputParser()
```

---

Question Rewriter:

```python id="lcel52"
rewrite_prompt
|
llm
|
StrOutputParser()
```

---

RAG:

```python id="lcel53"
retrieve_context
|
rag_prompt
|
structured_llm
```

---

Judge:

```python id="lcel54"
judge_prompt
|
judge_llm
```

---

# 18. Production Best Practices

## Small Chains

Good:

```text id="lcel55"
One Responsibility
```

---

Bad:

```text id="lcel56"
Huge Chains
```

---

## Reuse Components

Prompts:

```text id="lcel57"
Reusable
```

Models:

```text id="lcel58"
Reusable
```

---

## Use Structured Output

Prefer:

```python id="lcel59"
with_structured_output()
```

---

## Keep Business Logic Outside Chains

Good:

```text id="lcel60"
Services
```

---

Bad:

```text id="lcel61"
Complex Logic In Prompts
```

---

# 19. Common Mistakes

## Mistake 1

Using LCEL for everything.

---

## Mistake 2

Massive pipelines.

---

## Mistake 3

No structured output.

---

## Mistake 4

Mixing retrieval and business logic.

---

# 20. Interview Questions

### What is LCEL?

LangChain Expression Language.

---

### Why use LCEL?

To compose LangChain components into pipelines.

---

### What does the pipe operator do?

Passes output from one Runnable to the next Runnable.

---

### Difference between LCEL and Python code?

LCEL is declarative and composable.

---

### When use RunnableParallel?

Independent computations.

---

### When use RunnableBranch?

Conditional execution.

---

### LCEL vs LangGraph?

LCEL:

```text id="lcel62"
Pipelines
```

LangGraph:

```text id="lcel63"
Stateful Workflows
```

---

# Summary

LCEL is the programming model behind modern LangChain applications.

It allows us to compose:

```text id="lcel64"
Prompts
Models
Retrievers
Parsers
Tools
```

into clean reusable pipelines.

RetailOps heavily relies on LCEL for:

```text id="lcel65"
General Chat
RAG
Question Rewriting
Evaluation
```

The next document:

```text id="lcel66"
06_runnables.md
```

dives deeper into the Runnable system that powers every LCEL pipeline.
