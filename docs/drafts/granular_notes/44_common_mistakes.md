# 44 - Common Mistakes in LangChain, RAG, and AI Systems

# Purpose

This document captures the most common mistakes engineers make when building:

```text id="cm1"
LLM Applications
RAG Systems
Agents
Production AI Platforms
```

Most failures are not caused by:

```text id="cm2"
Models
```

They are caused by:

```text id="cm3"
Architecture
Evaluation
Retrieval
Operations
```

---

# Section 1 — Prompt Engineering Mistakes

## Mistake 1

Treating prompts as text instead of code.

---

Bad:

```text id="cm4"
Prompts scattered everywhere.
```

---

Good:

```text id="cm5"
Centralized prompt management.
```

---

RetailOps:

```text id="cm6"
app/prompts.py
```

---

## Mistake 2

No output format.

---

Bad:

```text id="cm7"
Return whatever you want.
```

---

Good:

```text id="cm8"
Structured Output
```

---

## Mistake 3

One giant prompt doing everything.

---

Problem:

```text id="cm9"
Hard To Maintain
```

---

Solution:

```text id="cm10"
Small Focused Prompts
```

---

# Section 2 — Chunking Mistakes

## Mistake 4

Huge chunks.

---

Example:

```text id="cm11"
2000+
tokens
```

---

Problem:

```text id="cm12"
Poor Retrieval Precision
```

---

## Mistake 5

Tiny chunks.

---

Example:

```text id="cm13"
20 tokens
```

---

Problem:

```text id="cm14"
No Context
```

---

## Mistake 6

No overlap.

---

Problem:

```text id="cm15"
Broken Meaning
```

---

## Mistake 7

Never evaluating chunk quality.

---

Reality:

```text id="cm16"
Chunk Quality
=
Retrieval Quality
```

---

# Section 3 — Embedding Mistakes

## Mistake 8

Thinking embeddings store knowledge.

---

Wrong:

```text id="cm17"
Embedding
=
Knowledge
```

---

Correct:

```text id="cm18"
Embedding
=
Meaning Representation
```

---

## Mistake 9

Changing embedding models without rebuilding indexes.

---

Problem:

```text id="cm19"
Embedding Mismatch
```

---

Solution:

```text id="cm20"
Reindex
```

---

# Section 4 — Retrieval Mistakes

## Mistake 10

Using vector search only.

---

Problem:

```text id="cm21"
Poor Exact Match Retrieval
```

---

Examples:

```text id="cm22"
P1
SKU
Incident IDs
```

---

Solution:

```text id="cm23"
Hybrid Search
```

---

## Mistake 11

No reranking.

---

Problem:

```text id="cm24"
Average Context
```

---

Solution:

```text id="cm25"
Cross Encoder
```

---

## Mistake 12

Retrieving too many chunks.

---

Problem:

```text id="cm26"
Context Noise
```

---

Solution:

```text id="cm27"
Top K Optimization
```

---

## Mistake 13

Blaming the LLM for retrieval failures.

---

Reality:

```text id="cm28"
Most RAG Failures
=
Retrieval Failures
```

---

# Section 5 — RAG Mistakes

## Mistake 14

No source attribution.

---

Problem:

```text id="cm29"
No Trust
```

---

Solution:

```text id="cm30"
Return Sources
```

---

## Mistake 15

Allowing answers outside context.

---

Bad:

```text id="cm31"
Use your own knowledge.
```

---

Good:

```text id="cm32"
Use only provided context.
```

---

## Mistake 16

No confidence score.

---

Users cannot distinguish:

```text id="cm33"
Strong
Weak
```

answers.

---

# Section 6 — Multi Query Mistakes

## Mistake 17

Generating too many queries.

---

Problem:

```text id="cm34"
Latency
Cost
```

---

## Mistake 18

Using Multi Query without reranking.

---

Problem:

```text id="cm35"
Noise
```

---

Solution:

```text id="cm36"
Final Cross Encoder
```

---

# Section 7 — Tool Mistakes

## Mistake 19

Using RAG for dynamic data.

---

Bad:

```text id="cm37"
Inventory
Orders
Incidents
```

---

Good:

```text id="cm38"
Tools
```

---

## Mistake 20

Using tools for static documentation.

---

Bad:

```text id="cm39"
Return Policy Tool
```

---

Good:

```text id="cm40"
RAG
```

---

## Mistake 21

Huge tools.

---

Bad:

```text id="cm41"
do_everything()
```

---

Good:

```text id="cm42"
Single Responsibility
```

---

# Section 8 — Agent Mistakes

## Mistake 22

Using agents for everything.

---

Bad:

```text id="cm43"
Simple Question
↓
Agent
```

---

Good:

```text id="cm44"
Simple Chain
```

---

## Mistake 23

No tool descriptions.

---

Problem:

```text id="cm45"
Wrong Tool Selection
```

---

## Mistake 24

No iteration limits.

---

Problem:

```text id="cm46"
Infinite Loops
```

---

# Section 9 — Router Mistakes

## Mistake 25

No router.

---

Everything:

```text id="cm47"
RAG
```

---

Wasteful.

---

## Mistake 26

Too many routes.

---

Problem:

```text id="cm48"
Ambiguity
```

---

## Mistake 27

No routing evaluation.

---

Problem:

```text id="cm49"
Wrong Workflow
```

---

# Section 10 — Evaluation Mistakes

## Mistake 28

Manual testing only.

---

Problem:

```text id="cm50"
No Measurement
```

---

## Mistake 29

No golden dataset.

---

Problem:

```text id="cm51"
No Regression Testing
```

---

## Mistake 30

Only measuring answer correctness.

---

Need:

```text id="cm52"
Source Accuracy
Groundedness
Completeness
```

---

## Mistake 31

No evaluation reports.

---

Problem:

```text id="cm53"
No Historical Tracking
```

---

# Section 11 — Observability Mistakes

## Mistake 32

Using print statements.

---

Use:

```text id="cm54"
Structured Logging
```

---

## Mistake 33

No request IDs.

---

Problem:

```text id="cm55"
Hard Debugging
```

---

## Mistake 34

No retrieval logs.

---

Problem:

```text id="cm56"
Cannot Diagnose RAG
```

---

## Mistake 35

No LangSmith.

---

Problem:

```text id="cm57"
Blind Debugging
```

---

# Section 12 — Security Mistakes

## Mistake 36

Authentication without authorization.

---

Problem:

```text id="cm58"
Everyone Sees Everything
```

---

## Mistake 37

Filtering after retrieval.

---

Bad:

```text id="cm59"
Retrieve
↓
Filter
```

---

Good:

```text id="cm60"
Filter
↓
Retrieve
```

---

## Mistake 38

Logging sensitive information.

---

Never log:

```text id="cm61"
Passwords
Tokens
PII
```

---

# Section 13 — Memory Mistakes

## Mistake 39

Confusing memory and RAG.

---

Memory:

```text id="cm62"
Conversation
```

---

RAG:

```text id="cm63"
Knowledge
```

---

## Mistake 40

Unlimited history.

---

Problem:

```text id="cm64"
Cost
Noise
```

---

Solution:

```text id="cm65"
Windowing
Summarization
```

---

# Section 14 — Architecture Mistakes

## Mistake 41

Premature LangGraph.

---

Use LangChain first.

---

## Mistake 42

Building workflow state manually.

---

LangGraph exists for this.

---

## Mistake 43

Calling production baselines enterprise-grade.

---

Enterprise requires:

```text id="cm66"
Identity
Authorization
Governance
Persistent State
```

---

# Section 15 — RetailOps Lessons Learned

Highest ROI improvements:

```text id="cm67"
Hybrid Search
Cross Encoder
Evaluation
Observability
```

---

Not:

```text id="cm68"
Prompt Tweaks
```

alone.

---

Key realization:

```text id="cm69"
Retrieval Quality
>
Prompt Quality
```

for RAG systems.

---

Second realization:

```text id="cm70"
Evaluation
>
Opinion
```

---

Third realization:

```text id="cm71"
Enterprise Problems
≠
RAG Problems
```

---

# Final Advice

When debugging AI systems, ask:

```text id="cm72"
Was the right route selected?

Was the right tool selected?

Was the right document retrieved?

Was the answer grounded?

Was the answer complete?
```

before blaming:

```text id="cm73"
The Model
```

---

# Final Handbook Outcome

After completing this handbook, you should be able to:

```text id="cm74"
Build LangChain Applications

Build Production RAG Systems

Build Tool-Using Agents

Evaluate AI Systems

Design Retrieval Architectures

Explain Tradeoffs

Prepare For Interviews

Transition To LangGraph

Understand Enterprise AI Architecture
```

---

# RetailOps Final Assessment

Current status:

```text id="cm75"
Tutorial
❌

Production Baseline
✅

Enterprise Ready Foundation
✅

Enterprise Grade
❌
```

Missing:

```text id="cm76"
Authorization
Metadata Filtering
Persistent State
Workflow Orchestration
Compliance
```

These are primarily:

```text id="cm77"
Enterprise Architecture Problems
```

rather than:

```text id="cm78"
LangChain Problems
```

which is exactly where the next stage of learning begins.
