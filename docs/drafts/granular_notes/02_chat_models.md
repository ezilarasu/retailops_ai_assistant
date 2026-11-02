# 02 - Chat Models

# Learning Objectives

After completing this document, you should understand:

* What a Chat Model is
* Why Chat Models exist
* Chat Model Architecture
* Chat Models vs Base LLMs
* LangChain Chat Models
* ChatGroq
* ChatOpenAI
* ChatAnthropic
* ChatOllama
* Model Parameters
* Temperature
* Max Tokens
* Streaming
* Structured Output
* Model Selection
* Production Best Practices

---

# 1. What is a Chat Model?

## Definition

A Chat Model is a LangChain wrapper around a Large Language Model provider.

Examples:

```text id="ow7t5h"
ChatGroq
ChatOpenAI
ChatAnthropic
ChatGoogleGenerativeAI
ChatOllama
```

---

## Simple Explanation

A Chat Model is the interface between:

```text id="tdvgj4"
Your Application
```

and

```text id="jlwmcm"
The LLM Provider
```

---

Architecture:

```text id="jlwmcn"
Application
 ↓
LangChain Chat Model
 ↓
Provider API
 ↓
LLM
```

---

# 2. Why Do Chat Models Exist?

Without LangChain:

OpenAI:

```python id="jlwmco"
client.chat.completions.create(...)
```

---

Anthropic:

```python id="jlwmcp"
client.messages.create(...)
```

---

Groq:

```python id="jlwmcq"
client.chat.completions.create(...)
```

Different APIs.

Different response formats.

Different parameters.

---

LangChain provides:

```python id="jlwmcr"
llm.invoke(...)
```

for all providers.

---

# 3. Chat Models vs Base Models

This is frequently misunderstood.

---

# Base Model

Input:

```text id="jlwmcs"
Raw Text
```

---

Example:

```text id="jlwmct"
Explain Python
```

---

Output:

```text id="jlwmcu"
Generated Text
```

---

# Chat Model

Input:

```text id="jlwmcv"
Messages
```

---

Example:

```python id="jlwmcw"
[
  {"role":"system",...},
  {"role":"user",...}
]
```

---

Output:

```text id="jlwmcx"
AI Message
```

---

# Why Chat Models Won

Modern LLMs are optimized for:

```text id="jlwmcy"
Conversations
Instructions
Tool Calling
```

rather than plain text completion.

---

# 4. Chat Model Architecture

Modern chat model flow:

```text id="jlwmcz"
System Message
 ↓
User Message
 ↓
Assistant Message
 ↓
LLM
 ↓
Response
```

---

# System Message

Controls behavior.

Example:

```text id="jlwmd0"
You are a senior Python instructor.
```

---

# User Message

Current request.

Example:

```text id="jlwmd1"
Explain decorators.
```

---

# Assistant Message

Previous response.

Used for:

```text id="jlwmd2"
Conversation Memory
```

---

# 5. LangChain Chat Model Interface

Every chat model supports:

```python id="jlwmd3"
invoke()
stream()
batch()
```

---

# invoke()

Run once.

Example:

```python id="jlwmd4"
response = llm.invoke(
    "Explain Python."
)
```

---

# stream()

Token streaming.

Example:

```python id="jlwmd5"
for chunk in llm.stream(
    "Explain Python."
):
    print(chunk.content)
```

---

# batch()

Multiple requests.

Example:

```python id="jlwmd6"
responses = llm.batch([
    "Explain Python",
    "Explain Java"
])
```

---

# 6. ChatGroq

Used in RetailOps.

---

## Why Groq?

Pros:

```text id="jlwmd7"
Very Fast
Low Cost
Good Open Models
```

---

## Example

```python id="jlwmd8"
from langchain_groq import ChatGroq

llm = ChatGroq(
    model="llama-3.3-70b-versatile"
)
```

---

## RetailOps

File:

```text id="jlwmd9"
app/llm.py
```

---

# 7. ChatOpenAI

Most popular.

---

Example:

```python id="jlwmda"
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o"
)
```

---

Pros:

```text id="jlwmdb"
High Quality
Strong Tool Calling
Strong Structured Output
```

---

Cons:

```text id="jlwmdc"
More Expensive
```

---

# 8. ChatAnthropic

Claude models.

---

Example:

```python id="jlwmdd"
from langchain_anthropic import ChatAnthropic
```

---

Pros:

```text id="jlwmde"
Long Context
Strong Reasoning
```

---

# 9. ChatOllama

Local models.

---

Example:

```python id="jlwmdf"
from langchain_ollama import ChatOllama
```

---

Pros:

```text id="jlwmdg"
Private
Offline
No API Cost
```

---

Cons:

```text id="jlwmdh"
Hardware Requirements
```

---

# 10. Temperature

## Definition

Controls randomness.

---

# Temperature = 0

Deterministic.

Use for:

```text id="jlwmdi"
RAG
Classification
Extraction
```

---

# Temperature = 0.7

Balanced.

Use for:

```text id="jlwmdj"
Assistants
General Chat
```

---

# Temperature = 1+

Creative.

Use for:

```text id="jlwmdk"
Stories
Marketing
```

---

# RetailOps

Current:

```python id="jlwmdl"
temperature=0
```

---

Why?

```text id="jlwmdm"
Consistent RAG Answers
```

---

# 11. Max Tokens

## Definition

Maximum generated output.

---

Example:

```python id="jlwmdn"
max_tokens=500
```

---

Why?

```text id="jlwmdo"
Control Cost
Control Latency
```

---

# 12. Structured Output

One of the most important production features.

---

Without Structured Output:

```text id="jlwmdp"
Text
```

---

With Structured Output:

```python id="jlwmdq"
RAGResponse
```

---

Example:

```python id="jlwmdr"
llm.with_structured_output(
    RAGResponse
)
```

---

Output:

```python id="jlwmds"
result.answer
result.sources
result.confidence
```

---

# Why Use It?

Applications need:

```text id="jlwmdt"
Predictable Data
```

not random text.

---

# 13. Streaming

## Definition

Return tokens as they are generated.

---

Without Streaming:

```text id="jlwmdu"
Wait
 ↓
Answer
```

---

With Streaming:

```text id="jlwmdv"
Answer Appears Gradually
```

---

Used in:

```text id="jlwmdw"
ChatGPT
Claude
Gemini
```

---

# 14. Model Selection Strategy

Choose based on use case.

---

# RAG

Prefer:

```text id="jlwmdx"
Fast
Cheap
Reliable
```

Example:

```text id="jlwmdy"
Groq
GPT-4o-mini
```

---

# Complex Reasoning

Prefer:

```text id="jlwmdz"
Claude
GPT-4o
```

---

# Local Privacy

Prefer:

```text id="jlwme0"
Ollama
```

---

# Production Strategy

Common:

```text id="jlwme1"
Fast Model
↓
Most Requests

Premium Model
↓
Complex Requests
```

---

# 15. Production Best Practices

## Separate Model Initialization

Good:

```text id="jlwme2"
app/llm.py
```

---

Bad:

```text id="jlwme3"
Create models everywhere
```

---

## Use Structured Output

Prefer:

```python id="jlwme4"
with_structured_output()
```

---

## Keep Temperature Low for RAG

Prefer:

```python id="jlwme5"
temperature=0
```

---

## Monitor Costs

Track:

```text id="jlwme6"
Tokens
Latency
Usage
```

---

## Use LangSmith

Trace:

```text id="jlwme7"
Prompts
Model Calls
Errors
```

---

# 16. RetailOps Implementation

Current model:

```text id="jlwme8"
ChatGroq
```

---

File:

```text id="jlwme9"
app/llm.py
```

---

Used by:

```text id="jlwmea"
RAG
Router
Agent
Evaluation
```

---

# 17. Common Mistakes

## Mistake 1

High temperature in RAG.

---

## Mistake 2

No output schema.

---

## Mistake 3

Recreating model objects repeatedly.

---

## Mistake 4

Using the most expensive model for everything.

---

## Mistake 5

Ignoring latency.

---

# 18. Interview Questions

### What is a Chat Model?

A LangChain wrapper around an LLM provider.

---

### Why use Chat Models?

Provider-independent interface.

---

### Difference between Chat Model and Base Model?

Chat Models operate on messages.

Base models operate on raw text.

---

### Why use temperature=0 for RAG?

To reduce randomness and improve consistency.

---

### What is structured output?

Schema-constrained model output.

---

### Why use streaming?

Improves user experience and perceived latency.

---

### How would you choose a model?

Based on:

```text id="jlwmeb"
Quality
Cost
Latency
Context Window
Tool Calling
```

---

# Summary

Chat Models are the gateway between LangChain and LLM providers.

They provide:

```text id="jlwmec"
Provider Abstraction
Structured Output
Streaming
Tool Calling
Consistent APIs
```

and are the foundation for every chain, retriever, agent, and evaluation workflow in the RetailOps project.

The next document:

```text id="jlwmed"
03_prompt_templates.md
```

covers prompt templates, message structures, dynamic variables, and prompt composition in depth.
