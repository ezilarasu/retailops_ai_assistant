# 00 - LangChain Learning Roadmap

# Purpose

This handbook teaches LangChain from beginner level to production-grade AI architecture using the RetailOps AI Assistant project.

The goal is not only to learn APIs.

The goal is to understand:

* Why concepts exist
* When to use them
* When NOT to use them
* Tradeoffs
* Production patterns
* Enterprise architecture

---

# Learning Path

## Phase 1 — Foundation

Learn:

```text
LLMs
Chat Models
Prompt Engineering
LCEL
Runnables
Output Parsers
Structured Output
```

Goal:

```text
Build simple LangChain applications.
```

Documents:

```text
01 → 08
```

---

## Phase 2 — RAG

Learn:

```text
Document Loaders
Chunking
Embeddings
Vector Databases
Retrievers
Hybrid Search
Reranking
RAG Evaluation
```

Goal:

```text
Build production-quality retrieval systems.
```

Documents:

```text
09 → 25
```

---

## Phase 3 — Agents

Learn:

```text
Tools
Function Calling
Agents
ReAct
Routing
Memory
```

Goal:

```text
Build action-oriented assistants.
```

Documents:

```text
26 → 31
```

---

## Phase 4 — Production

Learn:

```text
FastAPI
LangSmith
Logging
Caching
Security
Evaluation
Indexing
```

Goal:

```text
Build production-ready LangChain applications.
```

Documents:

```text
32 → 39
```

---

## Phase 5 — Architecture

Learn:

```text
LangChain Limitations
LangGraph
Enterprise RAG
```

Goal:

```text
Build enterprise AI systems.
```

Documents:

```text
40 → 44
```

---

# RetailOps Mapping

Every concept is implemented in the RetailOps project.

Examples:

```text
Prompt Templates
→ app/prompts.py

RAG
→ app/chains.py

Hybrid Search
→ app/hybrid_retriever.py

Cross Encoder
→ app/reranker.py

Evaluation
→ evals/
```

This handbook should be read alongside the project source code.

---

# Expected Outcome

After completing this handbook, you should be able to:

* Build LangChain applications
* Build production-quality RAG systems
* Build agents and tools
* Design retrieval architectures
* Evaluate AI systems
* Explain tradeoffs in interviews
* Transition to LangGraph
* Design enterprise-grade AI systems
