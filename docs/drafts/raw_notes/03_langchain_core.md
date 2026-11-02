# 03 - LangChain Core

# Learning Objectives

After completing this document, you should understand:

* What LangChain is
* Why LangChain exists
* Chat Models
* Prompt Templates
* LCEL (LangChain Expression Language)
* Runnables
* Runnable Interface
* invoke()
* batch()
* stream()
* Output Parsers
* Structured Output
* Pydantic Integration
* RunnableLambda
* RunnableParallel
* RunnableBranch
* LangChain Architecture
* How LangChain is used in the RetailOps project

---

# 1. What is LangChain?

## Definition

LangChain is a framework for building applications powered by Large Language Models (LLMs).

Think of:

```text
Python     → Programming Language
FastAPI    → Web Framework
LangChain  → LLM Application Framework
```

---

## Why Does LangChain Exist?

A real AI application needs:

```text
Prompts
Models
Tools
RAG
Memory
Structured Output
Streaming
Agents
Tracing
```

Without LangChain:

```text
Lots of custom code
Lots of API-specific logic
Difficult maintenance
```

LangChain provides reusable abstractions.

---

## What Problem Does It Solve?

Without LangChain:

```python
prompt = build_prompt()
response = provider_specific_api(prompt)
parsed = parse_response(response)
```

Every provider is different.

---

With LangChain:

```python
prompt | llm | parser
```

Consistent.

Reusable.

Provider-independent.

---

## Pros

```text
Reusable Components
Provider Abstraction
Fast Development
Agent Support
RAG Support
LangGraph Integration
```

---

## Cons

```text
Additional Abstraction Layer
Learning Curve
Rapidly Evolving APIs
```

---

# 2. LangChain Architecture

Most LangChain applications follow:

```text
Input
 ↓
Prompt
 ↓
Model
 ↓
Parser
 ↓
Output
```

More advanced:

```text
Input
 ↓
Retriever
 ↓
Prompt
 ↓
LLM
 ↓
Parser
 ↓
Application Logic
```

---

# 3. Chat Models

## Definition

A Chat Model is a LangChain wrapper around an LLM provider.

Examples:

```text
ChatGroq
ChatOpenAI
ChatAnthropic
ChatGoogleGenerativeAI
ChatOllama
```

---

## Why Use Chat Models?

Every provider has a different API.

Without LangChain:

```text
OpenAI API
Claude API
Gemini API
Groq API
```

all differ.

---

With LangChain:

```python
llm.invoke(...)
```

works everywhere.

---

## Example

```python
from langchain_groq import ChatGroq

llm = ChatGroq(
    model="llama-3.3-70b-versatile"
)
```

---

## Used In RetailOps

```python
def get_llm():
    return ChatGroq(...)
```

---

# 4. Prompt Templates

## Definition

Reusable prompts with variables.

---

## Why Use Them?

Bad:

```python
prompt = f"""
Explain {topic}
"""
```

Problems:

```text
Hard to maintain
Hard to test
Hard to reuse
```

---

## LangChain Solution

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_template(
    """
    Explain {topic}
    """
)
```

---

## Example

```python
prompt.invoke({
    "topic": "Decorators"
})
```

---

## Used In RetailOps

```text
general_chat_prompt
rag_prompt
router_prompt
question_rewrite_prompt
```

---

# 5. ChatPromptTemplate

Most production systems use:

```python
ChatPromptTemplate.from_messages()
```

---

## Example

```python
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a Python instructor."
    ),
    (
        "human",
        "{question}"
    )
])
```

---

## Why?

Chat models operate on:

```text
System Messages
User Messages
Assistant Messages
```

not plain text.

---

# 6. Runnables

## Definition

A Runnable is any LangChain component that:

```text
Receives Input
Produces Output
```

---

## Examples

```text
Prompt Templates
Models
Parsers
Retrievers
Chains
```

All are Runnables.

---

## Why Do Runnables Exist?

Without them:

```python
prompt.run()
model.call()
parser.execute()
```

Different APIs.

---

With Runnables:

```python
invoke()
batch()
stream()
```

Everywhere.

---

# 7. Runnable Interface

Every Runnable supports:

```python
invoke()
batch()
stream()
```

---

# invoke()

## Definition

Runs once.

---

## Example

```python
response = llm.invoke(
    "Explain Python."
)
```

---

## Used In RetailOps

```python
chain.invoke(...)
retriever.invoke(...)
agent.invoke(...)
```

---

# batch()

## Definition

Runs multiple inputs together.

---

## Example

```python
results = llm.batch([
    "Explain Python",
    "Explain Java"
])
```

---

## Why Use It?

```text
Improved Throughput
Bulk Processing
```

---

# stream()

## Definition

Returns output incrementally.

---

## Example

```python
for chunk in llm.stream(
    "Explain Python"
):
    print(chunk.content)
```

---

## Why Use It?

ChatGPT-style streaming.

---

# 8. LCEL

LangChain Expression Language

---

## Definition

A way to connect Runnables together.

---

## Example

```python
prompt | llm
```

means:

```text
Prompt Output
 ↓
LLM Input
```

---

## More Complex Example

```python
prompt | llm | parser
```

---

## Why Use LCEL?

Without LCEL:

```python
formatted = prompt.invoke(data)

response = llm.invoke(formatted)

parsed = parser.invoke(response)
```

---

With LCEL:

```python
chain = prompt | llm | parser
```

Cleaner.

---

## Used In RetailOps

```python
general_chat_prompt
|
llm
|
StrOutputParser()
```

---

# 9. Output Parsers

## Definition

Convert model outputs into desired formats.

---

## Problem

LLMs return:

```python
AIMessage(...)
```

Applications often need:

```python
str
```

or

```python
dict
```

---

## Example

```python
from langchain_core.output_parsers import (
    StrOutputParser
)

chain = prompt | llm | StrOutputParser()
```

---

## Output

```python
"plain text"
```

instead of:

```python
AIMessage(...)
```

---

## Used In RetailOps

```python
general_chat_chain
question_rewriter_chain
```

---

# 10. Structured Output

## Definition

Force the model to return a predefined schema.

---

## Why?

Applications need predictable data.

---

## Example

Bad:

```text
The answer is positive.
```

---

Good:

```json
{
  "sentiment": "positive"
}
```

---

# Pydantic Integration

## Example

```python
from pydantic import BaseModel

class SentimentResult(BaseModel):
    sentiment: str
```

---

Use:

```python
structured_llm = llm.with_structured_output(
    SentimentResult
)
```

---

Output:

```python
SentimentResult(
    sentiment="positive"
)
```

---

## Used In RetailOps

```python
RAGResponse
RouteDecision
```

---

# 11. RunnableLambda

## Definition

Wraps a normal Python function as a Runnable.

---

## Example

```python
from langchain_core.runnables import (
    RunnableLambda
)

def clean_text(text):
    return text.strip()

cleaner = RunnableLambda(clean_text)
```

---

## Why Use It?

Insert custom logic into LCEL pipelines.

---

## Use Cases

```text
Validation
Formatting
Transformations
Business Logic
```

---

# 12. RunnableParallel

## Definition

Runs multiple operations simultaneously.

---

## Example

```python
RunnableParallel({
    "summary": summary_chain,
    "keywords": keyword_chain
})
```

---

## Why Use It?

Improves performance.

---

## Use Cases

```text
Parallel Analysis
Multi-Output Processing
Combined Pipelines
```

---

# 13. RunnableBranch

## Definition

Routes inputs based on conditions.

---

## Example

```python
RunnableBranch(
    (
        lambda x: "python" in x,
        coding_chain
    ),
    general_chain
)
```

---

## Why Use It?

Conditional routing.

---

## Use Cases

```text
Intent Routing
Workflow Selection
Prompt Selection
Retriever Selection
```

---

# 14. Chains

## Definition

A sequence of Runnables.

---

## Example

```python
Prompt
 ↓
LLM
 ↓
Parser
```

---

## Chain Example

```python
chain = (
    prompt
    | llm
    | parser
)
```

---

## Used In RetailOps

```text
General Chat Chain
RAG Chain
Question Rewriter Chain
Router Chain
```

---

# 15. LangChain vs Raw Provider SDK

Without LangChain:

```python
groq_client.chat.completions.create(...)
```

---

With LangChain:

```python
llm.invoke(...)
```

---

## Benefits

```text
Cleaner Code
Provider Independence
Reusable Components
```

---

# 16. LangChain in RetailOps

Current Architecture:

```text
User
 ↓
Router Chain
 ├── General Chat Chain
 ├── RAG Chain
 └── Tool Agent
 ↓
Response
```

---

## General Chat Chain

```python
Prompt
|
ChatGroq
|
StrOutputParser
```

---

## Question Rewriter Chain

```python
Prompt
|
ChatGroq
|
StrOutputParser
```

---

## RAG Chain

```python
Retriever
|
Prompt
|
Structured LLM
```

---

## Router Chain

```python
Prompt
|
Structured LLM
```

---

# 17. Common Mistakes

---

## Mistake 1

Hardcoding prompts everywhere.

Use Prompt Templates.

---

## Mistake 2

Parsing model output manually.

Use:

```python
StrOutputParser
```

or

```python
with_structured_output()
```

---

## Mistake 3

Ignoring LCEL.

LCEL is the preferred modern LangChain pattern.

---

## Mistake 4

Using Structured Output when plain text is enough.

---

## Mistake 5

Using RunnableBranch when a simple if statement is sufficient.

---

# 18. Production Recommendations

Use:

```text
Prompt Templates
LCEL
Structured Output
Small Focused Chains
Reusable Runnables
```

Avoid:

```text
Hardcoded Prompts
Massive Chains
Provider-Specific Logic Everywhere
```

---

# Interview Questions

### What is LangChain?

A framework for building LLM-powered applications.

---

### What is a Runnable?

Any component that accepts input and produces output.

---

### What is LCEL?

LangChain Expression Language for composing pipelines.

---

### Why use Prompt Templates?

Reusable and maintainable prompts.

---

### Why use Output Parsers?

Convert model outputs into usable formats.

---

### What is Structured Output?

Schema-constrained model output.

---

### Difference between RunnableLambda and a normal function?

RunnableLambda allows the function to participate in LangChain pipelines.

---

### Difference between RunnableParallel and RunnableBranch?

RunnableParallel:

```text
Run multiple operations simultaneously
```

RunnableBranch:

```text
Choose one path conditionally
```

---

# Summary

LangChain provides:

```text
Chat Models
Prompt Templates
Runnables
LCEL
Parsers
Structured Output
Chains
```

These abstractions allow us to build:

```text
RAG Systems
Agents
Routers
Memory Systems
LangGraph Workflows
```

The RetailOps project uses nearly every LangChain Core concept covered in this document and serves as the foundation for the upcoming LangGraph and LangSmith sections.
