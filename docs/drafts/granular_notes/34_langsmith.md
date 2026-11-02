# 34 - LangSmith

# Learning Objectives

After completing this document, you should understand:

* What LangSmith is
* Why LangSmith exists
* LangSmith vs Traditional Logging
* Traces
* Runs
* Projects
* Datasets
* Evaluations
* Prompt Debugging
* Retrieval Debugging
* Production Monitoring
* RetailOps Implementation

---

# 1. What is LangSmith?

## Definition

LangSmith is LangChain's observability, evaluation, and debugging platform for AI applications.

Think of it as:

```text id="ls1"
Datadog
+
Grafana
+
Testing
+
Tracing

for AI Systems
```

---

# Why Does LangSmith Exist?

Traditional logs tell us:

```text id="ls2"
What Happened
```

---

AI systems require:

```text id="ls3"
Prompts
Retrieved Documents
Tool Calls
Model Outputs
Evaluations
```

---

Traditional logging is often insufficient.

---

LangSmith solves this.

---

# 2. Why AI Systems Need Special Observability

Traditional application:

```text id="ls4"
Request
↓
Response
```

---

AI application:

```text id="ls5"
Request
↓
Router
↓
Retriever
↓
Tool
↓
Model
↓
Parser
↓
Response
```

---

Need visibility into:

```text id="ls6"
Every Step
```

---

# 3. Core LangSmith Concepts

LangSmith revolves around:

```text id="ls7"
Projects
Runs
Traces
Datasets
Evaluations
```

---

# 4. Project

## Definition

A project groups related traces.

---

Example:

```text id="ls8"
RetailOps AI Assistant
```

---

All traces stored together.

---

Purpose:

```text id="ls9"
Organization
```

---

# 5. Run

## Definition

One execution of a component.

---

Example:

```text id="ls10"
Router Execution
```

---

Example:

```text id="ls11"
Retriever Execution
```

---

Example:

```text id="ls12"
LLM Call
```

---

Every execution becomes a:

```text id="ls13"
Run
```

---

# 6. Trace

## Definition

A complete execution path.

---

Example:

```text id="ls14"
Question
 ↓
Router
 ↓
Retriever
 ↓
Cross Encoder
 ↓
LLM
 ↓
Answer
```

---

This entire flow becomes:

```text id="ls15"
One Trace
```

---

# Why Useful?

Allows debugging of:

```text id="ls16"
Entire Request Lifecycle
```

---

# 7. Trace Visualization

Without LangSmith:

```text id="ls17"
Logs Everywhere
```

---

With LangSmith:

```text id="ls18"
Visual Execution Tree
```

---

Example:

```text id="ls19"
Root
 ├── Router
 ├── Retriever
 ├── LLM
 └── Output
```

---

Very easy to inspect.

---

# 8. Prompt Debugging

Question:

```text id="ls20"
Why did the model answer incorrectly?
```

---

LangSmith shows:

```text id="ls21"
Exact Prompt
```

---

Example:

```text id="ls22"
System Message
User Message
Context
```

---

No guessing.

---

# 9. Retrieval Debugging

Question:

```text id="ls23"
Why did RAG fail?
```

---

LangSmith shows:

```text id="ls24"
Retrieved Chunks
```

---

Example:

```text id="ls25"
Source
Score
Content
```

---

Often reveals:

```text id="ls26"
Wrong Retrieval
```

---

instead of:

```text id="ls27"
Wrong LLM
```

---

# 10. Tool Debugging

Question:

```text id="ls28"
Why did the agent fail?
```

---

LangSmith shows:

```text id="ls29"
Tool Selected
Arguments
Tool Output
```

---

Useful for:

```text id="ls30"
Agent Development
```

---

# 11. Metadata

RetailOps sends:

```text id="ls31"
Route
Version
Environment
```

---

Example:

```text id="ls32"
route=rag
env=local
version=0.2.0
```

---

Why?

Filter traces.

---

Example:

```text id="ls33"
Show all RAG traces.
```

---

# 12. LangSmith Datasets

## Definition

A collection of evaluation examples.

---

Example:

```text id="ls34"
Questions
Expected Answers
Expected Sources
```

---

Purpose:

```text id="ls35"
Repeatable Evaluation
```

---

# Example Dataset

```json id="ls36"
{
  "question":"What does P1 mean?",
  "answer":"P1 means full store outage."
}
```

---

# 13. LangSmith Evaluations

Evaluations measure:

```text id="ls37"
Quality
```

---

Examples:

```text id="ls38"
Correctness
Groundedness
Completeness
```

---

Can be:

```text id="ls39"
Human
LLM
Programmatic
```

---

# 14. LangSmith vs Local Evaluation

RetailOps currently uses:

```text id="ls40"
Local Evaluation Runner
```

---

LangSmith provides:

```text id="ls41"
Centralized Evaluation
```

---

Benefits:

```text id="ls42"
History
Visualization
Comparison
```

---

# 15. LangSmith vs Logging

Very common interview question.

---

# Logging

Purpose:

```text id="ls43"
Events
```

---

Example:

```text id="ls44"
route=rag
```

---

# LangSmith

Purpose:

```text id="ls45"
AI Workflow Visibility
```

---

Shows:

```text id="ls46"
Prompts
Documents
Tool Calls
Outputs
```

---

# Difference

Logs:

```text id="ls47"
System Events
```

---

LangSmith:

```text id="ls48"
AI Events
```

---

# 16. RetailOps LangSmith Setup

Current:

```env id="ls49"
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=...
LANGCHAIN_PROJECT=RetailOps
```

---

Purpose:

```text id="ls50"
Trace Collection
```

---

# 17. Production Monitoring

LangSmith helps answer:

```text id="ls51"
Why did this fail?
```

---

Examples:

```text id="ls52"
Bad Prompt

Bad Retrieval

Wrong Tool

Bad Route
```

---

Root causes become visible.

---

# 18. RetailOps Use Cases

Current:

```text id="ls53"
Prompt Debugging
Retrieval Debugging
Evaluation
Latency Analysis
```

---

Future:

```text id="ls54"
Production Monitoring
```

---

# 19. Production Best Practices

## Tag Traces

Include:

```text id="ls55"
Version
Route
Environment
```

---

## Track Retrieval

Always.

---

## Track Prompt Versions

Very important.

---

## Evaluate Regularly

Do not rely on:

```text id="ls56"
Manual Testing
```

---

## Use Datasets

Create:

```text id="ls57"
Golden Sets
```

---

# 20. Common Mistakes

## Mistake 1

Thinking LangSmith replaces logs.

---

## Mistake 2

Not tagging traces.

---

## Mistake 3

No evaluation datasets.

---

## Mistake 4

Ignoring retrieval traces.

---

## Mistake 5

Using LangSmith only after production.

---

# 21. Interview Questions

### What is LangSmith?

An observability and evaluation platform for AI applications.

---

### Why use LangSmith?

To debug prompts, retrieval, tools, and model behavior.

---

### What is a Trace?

A complete execution path of a request.

---

### What is a Run?

A single component execution.

---

### LangSmith vs Logging?

Logging:

```text id="ls58"
System Events
```

LangSmith:

```text id="ls59"
AI Workflow Visibility
```

---

### Why does RetailOps use LangSmith?

To trace routing, retrieval, evaluation, and answer generation.

---

# Summary

LangSmith provides:

```text id="ls60"
Tracing
Evaluation
Observability
Debugging
```

for AI systems.

RetailOps uses LangSmith to understand:

```text id="ls61"
Why Answers Succeed
Why Answers Fail
```

and to measure improvements across:

```text id="ls62"
Prompts
Retrieval
Reranking
Evaluation
```

making it a key component of a production-style AI system.

The next document:

```text id="ls63"
35_testing.md
```

covers unit testing, integration testing, RAG testing, evaluation testing, and how AI systems should be tested differently from traditional software.
