# 31 - Memory

# Learning Objectives

After completing this document, you should understand:

* What Memory is
* Why Memory exists
* Memory vs RAG
* Memory vs History-Aware Retrieval
* Short-Term Memory
* Long-Term Memory
* Session Memory
* Persistent Memory
* Memory Tradeoffs
* Production Best Practices
* RetailOps Implementation

---

# 1. What is Memory?

## Definition

Memory allows an AI system to remember information from previous interactions.

---

Without memory:

```text id="mem1"
Question
↓
Answer
```

---

Each request is independent.

---

With memory:

```text id="mem2"
Question
↓
History
↓
Answer
```

---

The system can use:

```text id="mem3"
Previous Messages
```

---

# Why Does Memory Exist?

Humans naturally assume:

```text id="mem4"
Conversation Continuity
```

---

Example

User:

```text id="mem5"
What does P1 mean?
```

---

Assistant:

```text id="mem6"
P1 means full store outage.
```

---

User:

```text id="mem7"
What should managers do?
```

---

Without memory:

```text id="mem8"
Managers for what?
```

---

With memory:

```text id="mem9"
Managers during a P1 incident.
```

---

# 2. What Memory Solves

Memory enables:

```text id="mem10"
Context
Personalization
Conversation Flow
```

---

Without memory:

```text id="mem11"
Repeated Questions
Repeated Context
```

---

# 3. Memory Architecture

```text id="mem12"
Question
+
History
 ↓
Prompt
 ↓
LLM
```

---

History becomes:

```text id="mem13"
Additional Context
```

---

# 4. Memory vs RAG

Very common interview question.

---

# Memory

Stores:

```text id="mem14"
Conversation History
```

---

Example:

```text id="mem15"
Previous Questions
Previous Answers
```

---

# RAG

Stores:

```text id="mem16"
Knowledge Base
```

---

Example:

```text id="mem17"
Policies
Manuals
Documents
```

---

# Difference

Memory:

```text id="mem18"
Conversation
```

---

RAG:

```text id="mem19"
Knowledge
```

---

# 5. Example

Memory:

```text id="mem20"
User:
What does P1 mean?

Assistant:
P1 means full store outage.
```

---

RAG:

```text id="mem21"
Incident Policy Document
```

---

Different purposes.

---

# 6. Memory vs History-Aware Retrieval

Another common confusion.

---

# Memory

Goal:

```text id="mem22"
Maintain Conversation
```

---

# History-Aware Retrieval

Goal:

```text id="mem23"
Improve Search Query
```

---

Example

Question:

```text id="mem24"
What about part-time employees?
```

---

Memory:

```text id="mem25"
Conversation Context
```

---

History-Aware Retrieval:

```text id="mem26"
Rewrite Question
```

---

# Difference

Memory:

```text id="mem27"
Conversation
```

---

History-Aware Retrieval:

```text id="mem28"
Retrieval Optimization
```

---

# 7. Short-Term Memory

Stores:

```text id="mem29"
Current Session
```

---

Example:

```text id="mem30"
Last 10 Messages
```

---

Pros:

```text id="mem31"
Simple
Fast
```

---

Cons:

```text id="mem32"
Lost On Restart
```

---

# RetailOps

Current memory:

```text id="mem33"
Short-Term
```

---

# 8. Long-Term Memory

Stores:

```text id="mem34"
Information Across Sessions
```

---

Example:

```text id="mem35"
User Preferences
Recurring Topics
```

---

Persists.

---

Examples:

```text id="mem36"
Database
Redis
Vector Store
```

---

# 9. Session Memory

Memory exists only during:

```text id="mem37"
One Conversation
```

---

Example:

```text id="mem38"
Browser Session
```

---

When session ends:

```text id="mem39"
Memory Gone
```

---

# 10. Persistent Memory

Memory survives:

```text id="mem40"
Restart
Logout
Deployment
```

---

Example:

```text id="mem41"
Redis
Postgres
LangGraph Checkpoints
```

---

Enterprise systems often require this.

---

# 11. Why Memory Can Be Dangerous

More memory:

```text id="mem42"
More Context
```

---

Also:

```text id="mem43"
More Tokens
More Cost
```

---

Large memory can introduce:

```text id="mem44"
Noise
```

---

# Example

Conversation:

```text id="mem45"
100 Messages
```

---

Most are irrelevant.

---

Injecting all history:

```text id="mem46"
Poor Prompt Quality
```

---

# 12. Memory Window

Common solution.

---

Keep:

```text id="mem47"
Recent Messages
```

---

Example:

```text id="mem48"
Last 10 Messages
```

---

Discard:

```text id="mem49"
Old Messages
```

---

# Why?

Control:

```text id="mem50"
Cost
Latency
```

---

# 13. Memory Summarization

Alternative approach.

---

Instead of:

```text id="mem51"
100 Messages
```

---

Store:

```text id="mem52"
Conversation Summary
```

---

Example:

```text id="mem53"
User discussed PTO policies.
```

---

Much smaller.

---

# 14. RetailOps Memory

Current:

```text id="mem54"
Conversation Buffer
```

---

Purpose:

```text id="mem55"
Question Rewriting
Conversation Continuity
```

---

Files:

```text id="mem56"
app/memory.py
```

---

# Current Limitation

Memory is:

```text id="mem57"
In-Memory
```

---

Restart app:

```text id="mem58"
Lost
```

---

# Enterprise Upgrade

Future:

```text id="mem59"
Redis
Postgres
LangGraph Memory
```

---

# 15. Memory vs Context Window

Memory:

```text id="mem60"
Stored Information
```

---

Context Window:

```text id="mem61"
Information Sent To Model
```

---

Not the same thing.

---

Example:

```text id="mem62"
Memory Store
```

contains:

```text id="mem63"
1000 Messages
```

---

Prompt may contain:

```text id="mem64"
10 Messages
```

---

# 16. Production Best Practices

## Keep Memory Small

Avoid:

```text id="mem65"
Unlimited History
```

---

## Summarize History

Useful for long conversations.

---

## Separate Memory and RAG

Different responsibilities.

---

## Use Persistent Storage

For enterprise systems.

---

## Track Memory Size

Monitor:

```text id="mem66"
Tokens
Latency
```

---

# 17. Common Mistakes

## Mistake 1

Confusing memory and RAG.

---

## Mistake 2

Injecting entire conversation history.

---

## Mistake 3

No memory limits.

---

## Mistake 4

Assuming memory survives restarts.

---

## Mistake 5

Using memory instead of retrieval.

---

# 18. Interview Questions

### What is Memory?

A mechanism for remembering previous interactions.

---

### Memory vs RAG?

Memory:

```text id="mem67"
Conversation
```

RAG:

```text id="mem68"
Knowledge
```

---

### Memory vs History-Aware Retrieval?

Memory:

```text id="mem69"
Conversation Context
```

History-Aware Retrieval:

```text id="mem70"
Query Rewriting
```

---

### Why is unlimited memory bad?

Higher token usage and more noise.

---

### Why does RetailOps use memory?

To support conversation continuity and question rewriting.

---

### Why isn't RetailOps memory enterprise-grade yet?

Because it is not persistent.

---

# Summary

Memory allows AI systems to maintain:

```text id="mem71"
Conversation Continuity
```

across interactions.

RetailOps currently uses:

```text id="mem72"
Short-Term Session Memory
```

for:

```text id="mem73"
Question Rewriting
Conversation Flow
```

while future enterprise upgrades may include:

```text id="mem74"
Persistent Memory
Redis
LangGraph Checkpoints
```

The next document:

```text id="mem75"
32_fastapi_integration.md
```

begins the Production section and explains how LangChain systems are exposed as production APIs.
