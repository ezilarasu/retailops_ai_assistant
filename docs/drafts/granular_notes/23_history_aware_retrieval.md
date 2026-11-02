# 23 - History-Aware Retrieval

# Learning Objectives

After completing this document, you should understand:

* What History-Aware Retrieval is
* Why History-Aware Retrieval exists
* Conversational RAG
* Follow-Up Questions
* Question Rewriting
* Standalone Questions
* History-Aware Retrieval vs Memory
* Query Rewriting Architecture
* Production Best Practices
* RetailOps Implementation

---

# 1. What is History-Aware Retrieval?

## Definition

History-Aware Retrieval rewrites follow-up questions into standalone questions before retrieval.

---

Instead of retrieving using:

```text id="har1"
What about part-time employees?
```

---

It retrieves using:

```text id="har2"
What is the PTO policy for part-time employees?
```

---

# Why Does This Exist?

Retrievers work best with:

```text id="har3"
Complete Questions
```

---

Humans often ask:

```text id="har4"
Incomplete Questions
```

---

Example:

```text id="har5"
What about them?
```

---

Retriever has no idea:

```text id="har6"
Who "them" is.
```

---

# 2. The Core Problem

Conversation:

User:

```text id="har7"
How many vacation days do employees receive?
```

---

Assistant:

```text id="har8"
18 vacation days.
```

---

User:

```text id="har9"
What about part-time employees?
```

---

Question:

```text id="har10"
Can retrieval understand this?
```

---

Usually:

```text id="har11"
No
```

---

Because:

```text id="har12"
Part-time employees
```

has no connection to:

```text id="har13"
Vacation policy
```

unless history is considered.

---

# 3. Solution

Rewrite:

```text id="har14"
What about part-time employees?
```

into:

```text id="har15"
What is the PTO policy for part-time employees?
```

---

Now retrieval becomes much stronger.

---

# 4. Architecture

Without history awareness:

```text id="har16"
Question
 ↓
Retriever
 ↓
Documents
```

---

With history awareness:

```text id="har17"
Question
+
History
 ↓
Question Rewriter
 ↓
Standalone Question
 ↓
Retriever
 ↓
Documents
```

---

# 5. Why Not Send Chat History Directly?

Common beginner idea.

---

Question:

```text id="har18"
What about part-time employees?
```

---

History:

```text id="har19"
Vacation Policy Discussion
```

---

Send all history:

```text id="har20"
Possible
```

---

Problems:

```text id="har21"
More Tokens
More Noise
More Cost
```

---

Question rewriting is usually cleaner.

---

# 6. What is a Standalone Question?

A question that contains all required context.

---

Example

Not standalone:

```text id="har22"
What about them?
```

---

Standalone:

```text id="har23"
What is the PTO policy for part-time employees?
```

---

Retriever can understand it.

---

# 7. RetailOps Question Rewriter

Current:

```python id="har24"
question_rewrite_prompt
```

---

Purpose:

```text id="har25"
Convert Follow-Up Questions
↓
Standalone Questions
```

---

Output:

```text id="har26"
Retrieval-Friendly Query
```

---

# 8. Example

Conversation:

User:

```text id="har27"
What does P1 mean?
```

---

Assistant:

```text id="har28"
P1 means full store outage.
```

---

User:

```text id="har29"
What should managers do?
```

---

Rewritten:

```text id="har30"
What should managers do during a P1 incident?
```

---

Much stronger retrieval.

---

# 9. Why Rewriting Improves Retrieval

Retriever understands:

```text id="har31"
Explicit Context
```

better than:

```text id="har32"
Implicit Context
```

---

Question:

```text id="har33"
What should managers do?
```

---

Could refer to:

```text id="har34"
Vacation Policy
Incident Policy
Returns Policy
```

---

Rewritten question removes ambiguity.

---

# 10. History-Aware Retrieval vs Memory

Very important distinction.

---

# Memory

Purpose:

```text id="har35"
Conversation Continuity
```

---

Example:

```text id="har36"
Remember Previous Messages
```

---

# History-Aware Retrieval

Purpose:

```text id="har37"
Improve Retrieval Query
```

---

Example:

```text id="har38"
Rewrite Question
```

---

# Difference

Memory:

```text id="har39"
Conversation
```

---

History-Aware Retrieval:

```text id="har40"
Search Optimization
```

---

# 11. History-Aware Retrieval vs Multi Query

History-Aware:

```text id="har41"
Fix Question
```

---

Multi Query:

```text id="har42"
Expand Question
```

---

Different goals.

---

Example:

Question:

```text id="har43"
What about part-time employees?
```

---

History-Aware:

```text id="har44"
What is PTO policy for part-time employees?
```

---

Multi Query:

```text id="har45"
Part-time PTO

Part-time leave

Part-time vacation benefits
```

---

# 12. History-Aware Retrieval vs RAG

RAG:

```text id="har46"
Find Documents
```

---

History-Aware Retrieval:

```text id="har47"
Improve Question
```

---

Before RAG.

---

Architecture:

```text id="har48"
Question
 ↓
Rewrite
 ↓
RAG
```

---

# 13. Why Rewriting Is Usually Better Than History Injection

Alternative:

```text id="har49"
Question
+
Entire History
```

---

Problems:

```text id="har50"
Token Cost
Noise
Long Context
```

---

Question rewriting:

```text id="har51"
Compact
Focused
Efficient
```

---

# 14. RetailOps Implementation

Current:

```python id="har52"
build_question_rewriter_chain()
```

---

Files:

```text id="har53"
app/prompts.py
app/chains.py
```

---

Pipeline:

```text id="har54"
Question
 ↓
History
 ↓
Rewrite
 ↓
Retrieval
```

---

# 15. Production Best Practices

## Rewrite Before Retrieval

Always.

---

## Keep Rewritten Questions Short

Avoid:

```text id="har55"
Long Essays
```

---

## Evaluate Rewrites

Bad rewrites:

```text id="har56"
Bad Retrieval
```

---

## Log Rewritten Queries

RetailOps:

```text id="har57"
Logs Original
Logs Rewritten
```

---

Useful for debugging.

---

# 16. Common Mistakes

## Mistake 1

Using follow-up questions directly.

---

## Mistake 2

Injecting entire chat history.

---

## Mistake 3

Skipping evaluation.

---

## Mistake 4

Treating memory and rewriting as the same thing.

---

## Mistake 5

Not logging rewritten queries.

---

# 17. Interview Questions

### What is History-Aware Retrieval?

Rewriting follow-up questions into standalone questions before retrieval.

---

### Why use History-Aware Retrieval?

To improve retrieval quality.

---

### History-Aware Retrieval vs Memory?

Memory:

```text id="har58"
Conversation
```

History-Aware:

```text id="har59"
Retrieval
```

---

### Why not pass chat history directly?

More tokens, more noise, higher cost.

---

### What is a standalone question?

A question that contains all required context.

---

### Why does RetailOps use question rewriting?

To improve retrieval accuracy for follow-up questions.

---

# Summary

History-Aware Retrieval is one of the most effective conversational RAG techniques.

It transforms:

```text id="har60"
Incomplete Questions
```

into:

```text id="har61"
Standalone Questions
```

which significantly improves retrieval quality.

RetailOps uses:

```text id="har62"
Question Rewriting
+
Multi Query
+
Hybrid Search
+
Cross Encoder
```

to maximize retrieval performance before generation.

The next document:

```text id="har63"
24_rag_chains.md
```

brings together all retrieval concepts into a complete end-to-end RAG pipeline.
