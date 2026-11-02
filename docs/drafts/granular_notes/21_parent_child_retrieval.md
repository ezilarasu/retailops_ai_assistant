# 21 - Parent-Child Retrieval

# Learning Objectives

After completing this document, you should understand:

* What Parent-Child Retrieval is
* Why Parent-Child Retrieval exists
* Child Chunks vs Parent Chunks
* Retrieval Precision vs Context Completeness
* Parent Lookup
* Parent-Child Architecture
* Parent-Child vs Semantic Chunking
* Parent-Child vs Multi-Query Retrieval
* Parent-Child Tradeoffs
* When to Use It
* When NOT to Use It
* RetailOps Learnings

---

# 1. What is Parent-Child Retrieval?

## Definition

Parent-Child Retrieval is a retrieval strategy where:

```text id="pc1"
Small Chunks
```

are used for:

```text id="pc2"
Retrieval
```

and

```text id="pc3"
Larger Chunks
```

are used for:

```text id="pc4"
Answer Generation
```

---

# Why Does It Exist?

Search prefers:

```text id="pc5"
Small Chunks
```

---

LLMs prefer:

```text id="pc6"
More Context
```

---

Parent-child retrieval attempts to satisfy both.

---

# 2. Core Idea

Instead of:

```text id="pc7"
Retrieve Chunk
↓
Send Same Chunk To LLM
```

---

We do:

```text id="pc8"
Retrieve Child Chunk
↓
Find Parent Chunk
↓
Send Parent To LLM
```

---

# 3. Example

Document:

```text id="pc9"
Incident Priority Definitions

P1 means full store outage.

P2 means partial outage.

P3 means single-device issue.

Managers must notify IT immediately.

Incident tickets must include:
Store ID
Device ID
Timestamp
```

---

# Child Chunks

Child A:

```text id="pc10"
P1 means full store outage.
```

---

Child B:

```text id="pc11"
Managers must notify IT immediately.
```

---

Child C:

```text id="pc12"
Incident tickets must include...
```

---

# Parent Chunk

Parent:

```text id="pc13"
Entire Incident Priority Section
```

---

# Retrieval Flow

Question:

```text id="pc14"
Tell me everything about P1 incidents.
```

---

Retriever finds:

```text id="pc15"
Child A
```

---

Then:

```text id="pc16"
Parent Lookup
```

---

LLM receives:

```text id="pc17"
Entire Incident Section
```

---

Much richer context.

---

# 4. Why Not Use Large Chunks Directly?

Good question.

---

Suppose:

```text id="pc18"
Chunk Size = 2000
```

---

Question:

```text id="pc19"
What does P1 mean?
```

---

Retriever compares:

```text id="pc20"
Huge Document
```

against:

```text id="pc21"
Question
```

---

Retrieval precision drops.

---

# Small Chunks

Pros:

```text id="pc22"
Precise Retrieval
```

---

Cons:

```text id="pc23"
Limited Context
```

---

# Large Chunks

Pros:

```text id="pc24"
Rich Context
```

---

Cons:

```text id="pc25"
Lower Retrieval Precision
```

---

# Parent-Child Goal

```text id="pc26"
Small Retrieval Units
+
Large Context Units
```

---

# 5. Parent-Child Architecture

```text id="pc27"
Document
 ↓
Parent Chunk
 ↓
Child Chunks
```

---

Example:

```text id="pc28"
Parent A
```

contains:

```text id="pc29"
Child 1
Child 2
Child 3
```

---

Each child stores:

```text id="pc30"
parent_id
```

---

Retriever finds:

```text id="pc31"
Child
```

---

System loads:

```text id="pc32"
Parent
```

---

# 6. Why Parent Retrieval Improves Answers

Question:

```text id="pc33"
Explain vacation policy.
```

---

Child:

```text id="pc34"
Employees receive 18 vacation days.
```

---

Answer:

```text id="pc35"
18 vacation days.
```

---

Incomplete.

---

Parent:

```text id="pc36"
Vacation Days
PTO Rules
Approval Process
Carry-over Rules
```

---

Answer becomes:

```text id="pc37"
Complete Policy Explanation
```

---

# 7. Parent-Child vs Semantic Chunking

Very important distinction.

---

# Semantic Chunking

Goal:

```text id="pc38"
Better Search Chunks
```

---

# Parent-Child

Goal:

```text id="pc39"
Better Answer Context
```

---

Difference:

Semantic Chunking:

```text id="pc40"
Retrieval Precision
```

---

Parent-Child:

```text id="pc41"
Context Completeness
```

---

# Which Comes First?

Usually:

```text id="pc42"
Semantic Chunking
```

---

because:

```text id="pc43"
Better Retrieval
```

has larger impact.

---

# 8. Parent-Child vs Multi Query

Multi Query:

```text id="pc44"
Improve Questions
```

---

Parent-Child:

```text id="pc45"
Improve Context
```

---

Different stages.

---

# 9. Parent-Child vs Reranking

Reranking:

```text id="pc46"
Choose Best Chunks
```

---

Parent-Child:

```text id="pc47"
Expand Chunks Into Context
```

---

Again:

```text id="pc48"
Different Problem
```

---

# 10. Token Cost Problem

One major drawback.

---

Child:

```text id="pc49"
100 tokens
```

---

Parent:

```text id="pc50"
1000 tokens
```

---

Sending parent:

```text id="pc51"
More Cost
More Latency
```

---

# This Is Important

Parent-child often increases:

```text id="pc52"
Token Usage
```

---

# Production Solution

Use:

```text id="pc53"
Contextual Compression
```

after parent lookup.

---

Architecture:

```text id="pc54"
Child
↓
Parent
↓
Compression
↓
LLM
```

---

# 11. When Parent-Child Helps

Useful for:

```text id="pc55"
Employee Handbooks
Legal Documents
Runbooks
Large Policies
Large Manuals
```

---

Reason:

```text id="pc56"
Context Matters
```

---

# Example

Finding:

```text id="pc57"
Vacation Rule
```

---

But answer requires:

```text id="pc58"
Approval
Escalation
Exceptions
```

---

Parent-child helps.

---

# 12. When Parent-Child Does NOT Help

Small datasets.

---

Example:

```text id="pc59"
RetailOps
```

current documents.

---

Already retrieving:

```text id="pc60"
MMR
Multi Query
Cross Encoder
```

---

Benefit:

```text id="pc61"
Limited
```

---

Cost:

```text id="pc62"
Higher
```

---

# RetailOps Decision

We implemented it as:

```text id="pc63"
Learning Pattern
```

---

Not:

```text id="pc64"
Default Retrieval Path
```

---

# 13. RetailOps Learning

Key observation:

Current architecture already has:

```text id="pc65"
MMR
Hybrid Search
Cross Encoder
Multi Query
```

---

Therefore:

```text id="pc66"
Parent Child
```

adds less value.

---

This is a realistic production tradeoff.

---

# 14. Production Best Practices

## Use Only When Needed

Do not enable blindly.

---

## Combine with Compression

Avoid sending:

```text id="pc67"
Huge Parents
```

---

## Evaluate

Compare:

```text id="pc68"
Standard Retrieval
vs
Parent Child
```

---

## Keep Parent Size Reasonable

Avoid:

```text id="pc69"
Massive Context
```

---

# 15. Common Mistakes

## Mistake 1

Using Parent-Child before fixing chunking.

---

## Mistake 2

Sending huge parent chunks.

---

## Mistake 3

Skipping evaluation.

---

## Mistake 4

Thinking Parent-Child improves retrieval.

---

It improves:

```text id="pc70"
Context
```

not retrieval.

---

# 16. Interview Questions

### What is Parent-Child Retrieval?

Use small chunks for retrieval and larger chunks for answering.

---

### Why use Parent-Child Retrieval?

To balance retrieval precision and answer completeness.

---

### Why not use large chunks directly?

Retrieval precision decreases.

---

### Parent-Child vs Semantic Chunking?

Semantic Chunking:

```text id="pc71"
Better Retrieval
```

Parent-Child:

```text id="pc72"
Better Context
```

---

### Biggest drawback?

Higher token usage.

---

### How do production systems address this?

Contextual Compression.

---

# Summary

Parent-Child Retrieval attempts to solve:

```text id="pc73"
Precision
vs
Context
```

by separating:

```text id="pc74"
Search Chunks
```

from:

```text id="pc75"
Answer Chunks
```

It is most useful for:

```text id="pc76"
Large Policies
Large Manuals
Enterprise Documents
```

and is often combined with:

```text id="pc77"
Contextual Compression
```

to control token costs.

The next document:

```text id="pc78"
22_contextual_compression.md
```

explains how production systems reduce context size while preserving answer quality.
