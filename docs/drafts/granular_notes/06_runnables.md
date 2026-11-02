# 06 - Runnables

# Learning Objectives

After completing this document, you should understand:

* What a Runnable is
* Why Runnables exist
* Runnable Interface
* invoke()
* batch()
* stream()
* RunnableLambda
* RunnableParallel
* RunnableBranch
* RunnablePassthrough
* RunnableAssign
* Data Flow
* Runnable Composition
* Production Best Practices

---

# 1. What is a Runnable?

## Definition

A Runnable is the fundamental building block of LangChain.

A Runnable is anything that:

```text id="run1"
Accepts Input
↓
Produces Output
```

---

Examples:

```text id="run2"
Prompt Templates
Chat Models
Output Parsers
Retrievers
Chains
Tools
```

All are Runnables.

---

# Why is this Important?

Because every Runnable supports:

```python id="run3"
invoke()
batch()
stream()
```

This creates a consistent programming model.

---

# 2. Runnable Architecture

Without Runnables:

```text id="run4"
Prompt API
Model API
Retriever API
Parser API
```

All different.

---

With Runnables:

```text id="run5"
invoke()
```

works everywhere.

---

Example:

```python id="run6"
prompt.invoke(...)
llm.invoke(...)
retriever.invoke(...)
chain.invoke(...)
```

Same interface.

---

# 3. Runnable Lifecycle

```text id="run7"
Input
 ↓
Runnable
 ↓
Output
```

---

Example

Question:

```text id="run8"
What is Python?
```

---

Prompt Runnable:

```text id="run9"
Messages
```

---

LLM Runnable:

```text id="run10"
AIMessage
```

---

Parser Runnable:

```text id="run11"
String
```

---

# 4. invoke()

## Definition

Execute one request.

---

Example

```python id="run12"
response = llm.invoke(
    "Explain Python."
)
```

---

Used in:

```text id="run13"
Chat
RAG
Agents
Evaluation
```

---

RetailOps:

```python id="run14"
chain.invoke(...)
```

everywhere.

---

# 5. batch()

## Definition

Process multiple inputs.

---

Example

```python id="run15"
results = llm.batch([
    "Python",
    "Java",
    "Go"
])
```

---

Why Use It?

```text id="run16"
Bulk Processing
Evaluation
Dataset Generation
```

---

Pros:

```text id="run17"
Faster Throughput
```

---

Cons:

```text id="run18"
Higher Memory Usage
```

---

# 6. stream()

## Definition

Return output incrementally.

---

Without Streaming

```text id="run19"
Wait
↓
Full Response
```

---

With Streaming

```text id="run20"
Token
Token
Token
```

---

Example

```python id="run21"
for chunk in llm.stream(
    "Explain Python"
):
    print(chunk.content)
```

---

Used for:

```text id="run22"
Chat Interfaces
```

---

# 7. RunnableLambda

## Definition

Wrap a Python function as a Runnable.

---

Why?

Allows custom logic inside LCEL.

---

Example

```python id="run23"
from langchain_core.runnables import (
    RunnableLambda
)

clean_text = RunnableLambda(
    lambda text: text.strip()
)
```

---

Input:

```text id="run24"
"  hello  "
```

---

Output:

```text id="run25"
hello
```

---

RetailOps Use Cases

```text id="run26"
Formatting
Validation
Transformations
```

---

# 8. RunnableParallel

## Definition

Run multiple Runnables simultaneously.

---

Example

```python id="run27"
RunnableParallel({
    "summary": summary_chain,
    "keywords": keyword_chain,
})
```

---

Input:

```text id="run28"
Document
```

---

Output:

```python id="run29"
{
  "summary": "...",
  "keywords": [...]
}
```

---

Architecture

```text id="run30"
Input
 ↓
 ├── Runnable A
 ├── Runnable B
 └── Runnable C
 ↓
Combined Result
```

---

When To Use

```text id="run31"
Independent Computations
```

---

Pros

```text id="run32"
Faster
Efficient
```

---

Cons

```text id="run33"
More Complex Debugging
```

---

# 9. RunnableBranch

## Definition

Conditional execution.

---

Example

```python id="run34"
RunnableBranch(
    (
        lambda x: "python" in x,
        python_chain,
    ),
    default_chain,
)
```

---

Flow

```text id="run35"
Input
 ↓
Condition
 ├── Chain A
 └── Chain B
```

---

When To Use

```text id="run36"
Routing
Intent Detection
Workflow Selection
```

---

RetailOps Equivalent

```text id="run37"
Router Chain
```

---

# 10. RunnablePassthrough

## Definition

Pass data through unchanged.

---

Example

```python id="run38"
from langchain_core.runnables import (
    RunnablePassthrough
)
```

---

```python id="run39"
RunnablePassthrough()
```

---

Input:

```python id="run40"
{"question":"What is Python?"}
```

---

Output:

```python id="run41"
{"question":"What is Python?"}
```

---

Why Useful?

Keep original input available.

---

# Example

```python id="run42"
{
    "question": RunnablePassthrough(),
    "context": retriever
}
```

---

Output:

```python id="run43"
{
    "question": "...",
    "context": "..."
}
```

---

# 11. RunnableAssign

## Definition

Add fields to existing data.

---

Example

Input:

```python id="run44"
{
  "question": "Python"
}
```

---

Assign:

```python id="run45"
{
  "length": 6
}
```

---

Output:

```python id="run46"
{
  "question": "Python",
  "length": 6
}
```

---

Why Useful?

Enrich data during pipelines.

---

# 12. Runnable Composition

Multiple Runnables can be combined.

---

Example

```python id="run47"
clean_text
|
prompt
|
llm
|
parser
```

---

Flow

```text id="run48"
Input
 ↓
Clean
 ↓
Prompt
 ↓
LLM
 ↓
Parser
```

---

# 13. Data Flow

Understanding data flow is critical.

---

Example

Prompt:

```python id="run49"
ChatPromptTemplate
```

Output:

```text id="run50"
Messages
```

---

LLM:

Output:

```text id="run51"
AIMessage
```

---

Parser:

Output:

```text id="run52"
String
```

---

Every Runnable changes data.

---

# 14. Runnables in RetailOps

General Chat:

```python id="run53"
prompt
|
llm
|
parser
```

---

Question Rewrite:

```python id="run54"
rewrite_prompt
|
llm
|
parser
```

---

Judge:

```python id="run55"
judge_prompt
|
judge_llm
```

---

Multi Query:

```python id="run56"
multi_query_prompt
|
llm
|
parser
```

---

# 15. Why LangChain Uses Runnables

Because every component becomes:

```text id="run57"
Composable
Reusable
Testable
```

---

Without Runnables:

```text id="run58"
Different APIs
Different Interfaces
```

---

With Runnables:

```text id="run59"
One Programming Model
```

---

# 16. Production Best Practices

## Keep Runnables Small

Good:

```text id="run60"
Single Responsibility
```

---

Bad:

```text id="run61"
Huge Transformation Logic
```

---

## Reuse Runnables

Example:

```text id="run62"
Shared LLM
Shared Prompt
```

---

## Log Important Stages

Track:

```text id="run63"
Input
Output
Latency
```

---

## Use Structured Output

Prefer:

```python id="run64"
with_structured_output()
```

when possible.

---

# 17. Common Mistakes

## Mistake 1

Treating chains and runnables as different concepts.

---

Reality:

```text id="run65"
Chains
=
Composed Runnables
```

---

## Mistake 2

Not understanding data flow.

---

## Mistake 3

Overusing RunnableLambda.

---

## Mistake 4

Putting business logic inside prompts instead of runnables.

---

# 18. Interview Questions

### What is a Runnable?

A component that accepts input and produces output.

---

### Why do Runnables exist?

To provide a consistent interface across LangChain.

---

### What methods do Runnables support?

```python id="run66"
invoke()
batch()
stream()
```

---

### What is RunnableLambda?

Wraps a Python function as a Runnable.

---

### What is RunnableParallel?

Runs multiple Runnables simultaneously.

---

### What is RunnableBranch?

Conditional execution.

---

### What is RunnablePassthrough?

Returns input unchanged.

---

### Why are Runnables important?

They are the foundation of LCEL.

---

# Summary

Runnables are the core abstraction of LangChain.

Everything:

```text id="run67"
Prompts
Models
Retrievers
Parsers
Chains
```

is ultimately a Runnable.

Understanding Runnables is essential because:

```text id="run68"
LCEL
RAG
Agents
LangGraph
```

all build on top of them.

The next document:

```text id="run69"
07_output_parsers.md
```

covers how model outputs are transformed into strings, dictionaries, and structured objects.
