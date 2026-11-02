# 01 - LangChain Overview

# Learning Objectives

After completing this document, you should understand:

* What LangChain is
* Why LangChain was created
* Problems LangChain solves
* LangChain Architecture
* LangChain Core Components
* LangChain vs Raw LLM SDKs
* LangChain vs LangGraph
* When to use LangChain
* When NOT to use LangChain
* Production Best Practices
* How LangChain is used in RetailOps

---

# 1. What is LangChain?

## Definition

LangChain is an application framework for building software powered by Large Language Models (LLMs).

Think of:

```text
Python
=
Programming Language

FastAPI
=
Web Framework

LangChain
=
LLM Application Framework
```

---

## Simple Explanation

Without LangChain:

```text
Prompt
↓
LLM
↓
Response
```

With LangChain:

```text
Prompt
↓
LLM
↓
Retriever
↓
Tools
↓
Memory
↓
Evaluation
↓
Observability
```

LangChain provides building blocks to connect all of these pieces.

---

# 2. Why Does LangChain Exist?

## Problem

Using an LLM directly looks simple:

```python
client.chat.completions.create(...)
```

Initially this works.

But real applications quickly need:

```text
Prompt Templates
Memory
RAG
Tools
Agents
Structured Output
Tracing
Evaluation
```

Without a framework:

```text
Lots of custom code
Lots of duplication
Hard maintenance
```

---

## Example

Simple chatbot:

```python
question
↓
LLM
↓
answer
```

Easy.

---

Production assistant:

```text
Question
↓
Retrieve Documents
↓
Call Tools
↓
Track Sources
↓
Evaluate Output
↓
Log Metrics
↓
Return Answer
```

Much harder.

LangChain solves this.

---

# 3. Core Idea Behind LangChain

LangChain is based on:

```text
Composable Components
```

Everything becomes a reusable building block.

Examples:

```text
Prompt
Model
Retriever
Parser
Tool
Agent
Memory
```

---

These components can be combined.

Example:

```python
prompt | llm | parser
```

---

# 4. Problems LangChain Solves

## Prompt Management

Without LangChain:

```python
prompt = f"""
Explain {topic}
"""
```

Prompts become scattered.

---

LangChain:

```python
ChatPromptTemplate
```

Centralized.

Reusable.

---

## Provider Abstraction

Without LangChain:

```python
OpenAI SDK
Groq SDK
Anthropic SDK
Gemini SDK
```

Different APIs.

---

LangChain:

```python
llm.invoke(...)
```

Same interface.

---

## Retrieval

Without LangChain:

```text
Custom Chunking
Custom Embeddings
Custom Retrieval
```

---

LangChain:

```text
Document Loaders
Text Splitters
Retrievers
Vector Stores
```

built-in.

---

## Agents

Without LangChain:

```text
Manual Tool Selection
Manual Execution
```

---

LangChain:

```text
Agents
Tools
Function Calling
```

---

# 5. LangChain Architecture

High-level architecture:

```text
User
 ↓
Prompt
 ↓
Model
 ↓
Parser
 ↓
Response
```

---

More advanced:

```text
User
 ↓
Router
 ↓
Retriever
 ↓
Tools
 ↓
Model
 ↓
Response
```

---

RetailOps:

```text
User
 ↓
Router
 ├── General Chat
 ├── RAG
 └── Tool Agent
 ↓
Answer
```

---

# 6. LangChain Core Components

## Chat Models

Examples:

```text
ChatGroq
ChatOpenAI
ChatAnthropic
ChatOllama
```

Purpose:

```text
LLM access
```

---

## Prompt Templates

Purpose:

```text
Reusable prompts
```

Example:

```python
ChatPromptTemplate
```

---

## Output Parsers

Purpose:

```text
Convert model output
```

Examples:

```python
StrOutputParser
PydanticOutputParser
```

---

## Retrievers

Purpose:

```text
Find relevant documents
```

---

## Tools

Purpose:

```text
Execute external functions
```

---

## Agents

Purpose:

```text
Choose tools dynamically
```

---

## Memory

Purpose:

```text
Conversation context
```

---

# 7. LangChain vs Raw SDK

## Raw SDK

Example:

```python
client.chat.completions.create(...)
```

---

Pros:

```text
Simple
Minimal
Fast
```

---

Cons:

```text
No abstraction
No RAG framework
No tools framework
No observability
```

---

## LangChain

Pros:

```text
Reusable
Extensible
Provider-independent
```

---

Cons:

```text
More abstraction
Learning curve
Additional dependencies
```

---

# 8. LangChain vs LangGraph

This is one of the most important distinctions.

---

## LangChain

Best for:

```text
Chains
RAG
Tools
Agents
```

---

Architecture:

```text
Question
↓
Answer
```

---

## LangGraph

Best for:

```text
State
Loops
Retries
Approvals
Persistence
Multi-Agent Systems
```

---

Architecture:

```text
Question
↓
Workflow
↓
State Machine
↓
Answer
```

---

## Relationship

Wrong:

```text
LangGraph replaces LangChain
```

---

Correct:

```text
LangGraph uses LangChain
```

---

# 9. When Should You Use LangChain?

Use LangChain when:

```text
Building RAG
Building Tools
Building Agents
Building AI APIs
Building Assistants
```

---

Examples:

```text
Customer Support
Knowledge Assistants
Internal Search
RetailOps
```

---

# 10. When Should You NOT Use LangChain?

Do NOT use LangChain when:

```text
One simple LLM call
Tiny script
No retrieval
No tools
No workflow
```

---

Example:

```python
Translate text
```

Raw SDK is enough.

---

# 11. Pros

## Rapid Development

Built-in components.

---

## Reusability

Components can be reused.

---

## Provider Independence

Switch models easily.

---

## Strong Ecosystem

Supports:

```text
RAG
Agents
LangSmith
LangGraph
```

---

# 12. Cons

## Abstraction

Sometimes hides complexity.

---

## Breaking Changes

LangChain evolves quickly.

---

## Performance Overhead

Extra abstraction layers.

---

## Can Encourage Overengineering

Not every application needs LangChain.

---

# 13. Production Best Practices

## Keep Prompts Separate

Good:

```text
app/prompts.py
```

Bad:

```text
Prompts everywhere
```

---

## Use Structured Output

Prefer:

```python
with_structured_output()
```

for machine-readable results.

---

## Add Evaluation

Never rely only on:

```text
"It looks good"
```

---

## Add Observability

Use:

```text
LangSmith
Logging
Metrics
```

---

## Keep Chains Small

Small focused chains are easier to maintain.

---

# 14. RetailOps Implementation

Current project uses:

```text
Prompt Templates
LCEL
RAG
Hybrid Search
BM25
Cross Encoder
Tools
Agents
Router
Memory
LangSmith
Evaluation
```

---

Files:

```text
app/chains.py
app/prompts.py
app/router.py
app/tools.py
app/reranker.py
```

---

# 15. Common Mistakes

## Mistake 1

Using LangChain for everything.

---

## Mistake 2

Skipping evaluation.

---

## Mistake 3

Putting prompts inside business logic.

---

## Mistake 4

Building giant chains.

---

## Mistake 5

Using agents when a chain is sufficient.

---

# 16. Interview Questions

### What is LangChain?

A framework for building LLM-powered applications.

---

### Why does LangChain exist?

To provide reusable abstractions for prompts, models, retrieval, tools, agents, and observability.

---

### LangChain vs Raw SDK?

Raw SDK:

```text
Lower abstraction
```

LangChain:

```text
Higher abstraction
Reusable architecture
```

---

### LangChain vs LangGraph?

LangChain:

```text
Chains and agents
```

LangGraph:

```text
Stateful workflows
```

---

### Biggest benefit of LangChain?

Composable reusable components.

---

### Biggest drawback?

Additional abstraction and complexity.

---

# Summary

LangChain is an application framework for LLM systems.

It provides:

```text
Models
Prompts
RAG
Tools
Agents
Memory
Evaluation
Observability
```

and serves as the foundation for the RetailOps AI Assistant.

The next document:

```text
02_chat_models.md
```

dives into how LangChain communicates with Groq, OpenAI, Anthropic, Ollama, and other model providers.
