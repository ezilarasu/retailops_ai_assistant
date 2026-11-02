# 43 - LangChain, RAG, and AI Engineering Interview Questions

# Purpose

This document consolidates the most important interview questions from the RetailOps learning journey.

The goal is not memorization.

The goal is understanding:

```text id="iq1"
Why
When
How
Tradeoffs
```

---

# Section 1 — LLM Fundamentals

## What is an LLM?

A Large Language Model is a neural network trained on massive amounts of text data to predict the next token in a sequence.

---

## What is the difference between an LLM and a Chat Model?

LLM:

```text id="iq2"
Raw text completion
```

Chat Model:

```text id="iq3"
Message-based interface
```

---

## What is temperature?

Controls randomness.

---

Low:

```text id="iq4"
Predictable
```

---

High:

```text id="iq5"
Creative
```

---

## Why use temperature=0 for RAG?

To improve consistency and reduce hallucinations.

---

# Section 2 — Prompt Engineering

## What is a Prompt Template?

A reusable prompt with variables.

---

## PromptTemplate vs ChatPromptTemplate?

PromptTemplate:

```text id="iq6"
Text
```

ChatPromptTemplate:

```text id="iq7"
Messages
```

---

## What is Few-Shot Prompting?

Providing examples before the actual task.

---

## Why use role prompting?

To influence behavior and expertise.

---

Example:

```text id="iq8"
You are a Retail Operations Assistant.
```

---

# Section 3 — LCEL

## What is LCEL?

LangChain Expression Language.

Used to compose runnables.

---

Example:

```python id="iq9"
prompt | llm | parser
```

---

## Why use LCEL?

Cleaner composition and reusable pipelines.

---

## What is a Runnable?

A component supporting:

```python id="iq10"
invoke()
batch()
stream()
```

---

# Section 4 — Structured Output

## What is Structured Output?

Schema-constrained model output.

---

## Why is Structured Output important?

Applications require predictable responses.

---

## Structured Output vs Output Parsing?

Output Parsing:

```text id="iq11"
Convert Output
```

Structured Output:

```text id="iq12"
Constrain Output
```

---

# Section 5 — RAG Fundamentals

## What is RAG?

Retrieval Augmented Generation.

---

Architecture:

```text id="iq13"
Retrieve
+
Generate
```

---

## Why use RAG?

To answer using external knowledge.

---

## What are the two phases of RAG?

```text id="iq14"
Retrieval
Generation
```

---

## Why return sources?

Trust and verification.

---

# Section 6 — Chunking

## Why chunk documents?

To improve retrieval precision.

---

## What is chunk overlap?

Shared content between chunks.

---

## Recursive vs Semantic Chunking?

Recursive:

```text id="iq15"
Structure-Based
```

Semantic:

```text id="iq16"
Meaning-Based
```

---

## Why can semantic chunking improve RAG?

Better chunk quality leads to better retrieval.

---

# Section 7 — Embeddings

## What is an embedding?

A vector representation of meaning.

---

## Do embeddings store facts?

No.

They represent semantic relationships.

---

## Why use embeddings?

Semantic search.

---

## Embeddings vs BM25?

Embeddings:

```text id="iq17"
Meaning
```

BM25:

```text id="iq18"
Words
```

---

# Section 8 — Vector Databases

## What is a vector database?

A database optimized for storing and searching embeddings.

---

## Why not use PostgreSQL?

Vector search requires specialized indexing.

---

## What is ANN?

Approximate Nearest Neighbor search.

---

## Chroma vs Pinecone?

Chroma:

```text id="iq19"
Local
```

Pinecone:

```text id="iq20"
Managed Cloud
```

---

# Section 9 — Retrieval

## What is a retriever?

A component that finds relevant documents.

---

## Loader vs Retriever?

Loader:

```text id="iq21"
Read Data
```

Retriever:

```text id="iq22"
Find Data
```

---

## Retriever vs Vector Database?

Retriever:

```text id="iq23"
Access Layer
```

Database:

```text id="iq24"
Storage Layer
```

---

# Section 10 — MMR

## What is MMR?

Maximum Marginal Relevance.

---

## Why use MMR?

Balance:

```text id="iq25"
Relevance
+
Diversity
```

---

## Similarity Search vs MMR?

Similarity:

```text id="iq26"
Most Similar
```

MMR:

```text id="iq27"
Relevant + Diverse
```

---

# Section 11 — Hybrid Search

## What is Hybrid Search?

Combining:

```text id="iq28"
Vector Search
+
BM25
```

---

## Why use Hybrid Search?

To support:

```text id="iq29"
Meaning
+
Exact Matching
```

---

## Why is BM25 still important?

Enterprise data contains:

```text id="iq30"
IDs
Codes
Dates
```

---

# Section 12 — Cross Encoder

## What is a Cross Encoder?

A model that scores query-document pairs.

---

## Why use Cross Encoders?

Improve retrieval precision.

---

## Embeddings vs Cross Encoder?

Embeddings:

```text id="iq31"
Fast Retrieval
```

Cross Encoder:

```text id="iq32"
Accurate Ranking
```

---

## Why not use Cross Encoder for retrieval?

Does not scale to large corpora.

---

# Section 13 — Multi Query Retrieval

## What is Multi Query Retrieval?

Generating multiple search queries from one question.

---

## Why use it?

Improve recall.

---

## Multi Query vs Hybrid Search?

Hybrid:

```text id="iq33"
Better Search Engine
```

Multi Query:

```text id="iq34"
Better Search Queries
```

---

# Section 14 — Parent Child Retrieval

## What is Parent Child Retrieval?

Small chunks for retrieval.

Large chunks for answering.

---

## Why use it?

Balance:

```text id="iq35"
Precision
+
Context
```

---

## Biggest drawback?

More tokens.

---

# Section 15 — Tools

## What is a Tool?

A function an LLM can call.

---

## Tools vs RAG?

RAG:

```text id="iq36"
Knowledge
```

Tools:

```text id="iq37"
Actions
Dynamic Data
```

---

## When should tools be used?

For:

```text id="iq38"
Inventory
Orders
Incidents
```

---

# Section 16 — Function Calling

## What is Function Calling?

A model capability for selecting tools and arguments.

---

## Tool vs Function Calling?

Tool:

```text id="iq39"
Code
```

Function Calling:

```text id="iq40"
Selection Mechanism
```

---

# Section 17 — Agents

## What is an Agent?

A system that can reason and use tools dynamically.

---

## Agent vs Chain?

Chain:

```text id="iq41"
Fixed Workflow
```

Agent:

```text id="iq42"
Dynamic Workflow
```

---

## Agent vs Tool?

Agent:

```text id="iq43"
Decision Maker
```

Tool:

```text id="iq44"
Capability
```

---

# Section 18 — ReAct

## What is ReAct?

Reason + Act.

---

Architecture:

```text id="iq45"
Thought
Action
Observation
```

---

## Why use ReAct?

To solve multi-step tasks.

---

# Section 19 — Routers

## What is a Router?

A workflow selection mechanism.

---

## Router vs Agent?

Router:

```text id="iq46"
Choose Workflow
```

Agent:

```text id="iq47"
Choose Tool
```

---

# Section 20 — Memory

## Memory vs RAG?

Memory:

```text id="iq48"
Conversation
```

RAG:

```text id="iq49"
Knowledge
```

---

## Why is unlimited memory dangerous?

Cost and noise.

---

# Section 21 — Evaluation

## Why evaluate RAG?

Because:

```text id="iq50"
Looks Good
```

is not a metric.

---

## What is Groundedness?

Whether answers are supported by evidence.

---

## What is Completeness?

Whether important information is missing.

---

## What is LLM-as-Judge?

Using an LLM to evaluate another model.

---

# Section 22 — Production

## What makes a RAG system production-ready?

```text id="iq51"
Evaluation
Observability
Security
Maintainability
```

---

## What makes a RAG system enterprise-grade?

```text id="iq52"
Authorization
Metadata Filtering
Persistent State
Governance
Compliance
```

---

# Section 23 — LangChain vs LangGraph

## Why was LangGraph created?

To solve:

```text id="iq53"
State
Persistence
Workflow Orchestration
```

---

## LangChain vs LangGraph?

LangChain:

```text id="iq54"
Pipelines
```

LangGraph:

```text id="iq55"
Stateful Workflows
```

---

## When is LangChain enough?

```text id="iq56"
RAG
Tools
Simple Agents
```

---

## When use LangGraph?

```text id="iq57"
Approvals
Long Workflows
Multi-Agent Systems
```

---

# Final Interview Advice

Always answer in this order:

```text id="iq58"
Definition
Why
How
Tradeoffs
Production Example
```

Example:

```text id="iq59"
What is Hybrid Search?
```

Bad:

```text id="iq60"
Vector + BM25
```

---

Good:

```text id="iq61"
Hybrid Search combines semantic retrieval and keyword retrieval.

It exists because semantic search struggles with IDs and codes while BM25 struggles with synonyms.

In production systems, Hybrid Search improves recall and is often followed by Cross Encoder reranking.
```

That style demonstrates:

```text id="iq62"
Understanding
```

rather than:

````text id="iq63"
Memorization
```.
````
