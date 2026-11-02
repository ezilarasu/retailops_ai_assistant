# 30 - Router Pattern

# Learning Objectives

After completing this document, you should understand:

* What a Router Pattern is
* Why Routers exist
* Intent Classification
* Workflow Selection
* Router vs Agent
* Router vs ReAct
* Router Architecture
* Structured Routing
* Production Routing Strategies
* RetailOps Implementation

---

# 1. What is a Router?

## Definition

A Router is a component that decides:

```text id="router1"
Which Workflow
Should Handle
The Request
```

---

Instead of:

```text id="router2"
Everything
↓
One Chain
```

---

We do:

```text id="router3"
Question
↓
Router
├── Workflow A
├── Workflow B
└── Workflow C
```

---

# Why Does This Exist?

Different questions need different systems.

---

Example:

Question:

```text id="router4"
What is the return policy?
```

Needs:

```text id="router5"
RAG
```

---

Question:

```text id="router6"
Show low stock items.
```

Needs:

```text id="router7"
Tools
```

---

Question:

```text id="router8"
Who are you?
```

Needs:

```text id="router9"
General Chat
```

---

One workflow cannot handle everything efficiently.

---

# 2. Router Architecture

```text id="router10"
Question
 ↓
Router
 ↓
Route Decision
 ↓
Workflow
 ↓
Answer
```

---

RetailOps:

```text id="router11"
Question
 ↓
Router
 ├── General Chat
 ├── RAG
 └── Tool Agent
```

---

# 3. What Problem Does Routing Solve?

Without routing:

```text id="router12"
Everything
↓
RAG
```

---

Problems:

```text id="router13"
Wasted Retrieval
Higher Cost
Lower Accuracy
```

---

Example:

Question:

```text id="router14"
Who are you?
```

---

RAG:

```text id="router15"
Unnecessary
```

---

Routing avoids this.

---

# 4. Intent Classification

Routers are often:

```text id="router16"
Intent Classifiers
```

---

Question:

```text id="router17"
Show store sales.
```

---

Intent:

```text id="router18"
Tool Usage
```

---

Question:

```text id="router19"
What is the vacation policy?
```

---

Intent:

```text id="router20"
Knowledge Retrieval
```

---

Question:

```text id="router21"
Hello
```

---

Intent:

```text id="router22"
Conversation
```

---

# Router decides.

---

# 5. RetailOps Routes

Current:

```text id="router23"
general
rag
tools
```

---

# General

Examples:

```text id="router24"
Hello

Who are you?

Explain Python
```

---

# RAG

Examples:

```text id="router25"
What is the return policy?

What does P1 mean?
```

---

# Tools

Examples:

```text id="router26"
Show low stock items.

Show sales data.
```

---

# 6. Router Prompt

RetailOps uses:

```text id="router27"
router_prompt
```

---

Purpose:

```text id="router28"
Choose Route
```

---

Output:

```python id="router29"
RouteDecision
```

---

Fields:

```text id="router30"
route
reason
```

---

# Example

Question:

```text id="router31"
Show low stock items.
```

---

Output:

```json id="router32"
{
  "route":"tools",
  "reason":"Inventory requires tool access."
}
```

---

# 7. Structured Routing

One of the best production patterns.

---

Without:

```text id="router33"
Text Parsing
```

---

With:

```python id="router34"
RouteDecision
```

---

Reliable.

---

Example:

```python id="router35"
if decision.route == "rag":
```

---

No string matching required.

---

# 8. Router vs Agent

Very common interview question.

---

# Router

Purpose:

```text id="router36"
Choose Workflow
```

---

Example:

```text id="router37"
General
RAG
Tools
```

---

# Agent

Purpose:

```text id="router38"
Choose Tool
```

---

Example:

```text id="router39"
Inventory Tool
Sales Tool
Incident Tool
```

---

# Difference

Router:

```text id="router40"
Workflow Selection
```

---

Agent:

```text id="router41"
Action Selection
```

---

# 9. Router vs ReAct

ReAct:

```text id="router42"
Reasoning Loop
```

---

Router:

```text id="router43"
Initial Decision
```

---

Architecture:

```text id="router44"
Question
 ↓
Router
 ↓
Agent
 ↓
ReAct
```

---

Possible combination.

---

# 10. Router vs Classifier

Traditional classifier:

```text id="router45"
Label
```

---

Router:

```text id="router46"
Label
+
Workflow Selection
```

---

More useful for AI systems.

---

# 11. Why Routers Improve Performance

Question:

```text id="router47"
Hello
```

---

Without router:

```text id="router48"
RAG
Retrieval
Cross Encoder
```

---

Wasteful.

---

With router:

```text id="router49"
General Chat
```

---

Much cheaper.

---

# Benefits

```text id="router50"
Lower Cost
Lower Latency
```

---

# 12. RetailOps Router Flow

Current:

```text id="router51"
Question
 ↓
Router
 ↓
RouteDecision
 ↓
Workflow
 ↓
Answer
```

---

Workflow:

```text id="router52"
General Chat Chain

RAG Chain

Tool Agent
```

---

# 13. Production Routing Patterns

## Pattern 1

Rule-Based

---

Example:

```text id="router53"
contains "sales"
```

---

Pros:

```text id="router54"
Fast
```

---

Cons:

```text id="router55"
Rigid
```

---

# Pattern 2

LLM Router

---

RetailOps.

---

Pros:

```text id="router56"
Flexible
```

---

Cons:

```text id="router57"
Model Cost
```

---

# Pattern 3

Hybrid Router

---

Rules first.

---

LLM second.

---

Most enterprise systems eventually use this.

---

# 14. Production Best Practices

## Use Structured Output

Always.

---

## Log Routing Decisions

Track:

```text id="router58"
Question
Route
Reason
```

---

## Evaluate Routing

Incorrect routes:

```text id="router59"
Wrong Workflow
```

---

## Keep Routes Clear

Avoid:

```text id="router60"
Overlapping Routes
```

---

# 15. Common Mistakes

## Mistake 1

No router.

---

## Mistake 2

Too many routes.

---

## Mistake 3

No structured output.

---

## Mistake 4

No routing evaluation.

---

## Mistake 5

Confusing routers and agents.

---

# 16. Interview Questions

### What is a Router?

A component that selects the appropriate workflow for a request.

---

### Why use Routers?

To improve accuracy, cost, and latency.

---

### Router vs Agent?

Router:

```text id="router61"
Workflow Selection
```

Agent:

```text id="router62"
Tool Selection
```

---

### Router vs ReAct?

Router:

```text id="router63"
Initial Decision
```

ReAct:

```text id="router64"
Reasoning Loop
```

---

### Why does RetailOps use a Router?

To choose between:

```text id="router65"
General Chat
RAG
Tools
```

---

# Summary

The Router Pattern is one of the most important AI architecture patterns.

It enables:

```text id="router66"
Workflow Selection
Cost Optimization
Latency Reduction
```

and prevents forcing every request through the same processing pipeline.

RetailOps uses:

```text id="router67"
Structured Routing
+
RouteDecision
```

to dynamically choose between:

```text id="router68"
General Chat
RAG
Tool Agent
```

making the application more efficient and scalable.

The next document:

```text id="router69"
31_memory.md
```

covers memory systems, conversation history, short-term memory, long-term memory, and how memory differs from retrieval.
