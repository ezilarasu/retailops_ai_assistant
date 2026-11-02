# 20 - Multi-Query Retrieval

# Learning Objectives

After completing this document, you should understand:

* What Multi-Query Retrieval is
* Why Multi-Query Retrieval exists
* Query Expansion
* Recall vs Precision
* How Multi-Query Retrieval works
* Multi-Query vs Hybrid Search
* Multi-Query vs Semantic Chunking
* Multi-Query vs Reranking
* Production Tradeoffs
* RetailOps Implementation

---

# 1. What is Multi-Query Retrieval?

## Definition

Multi-Query Retrieval generates multiple search queries from a single user question and retrieves documents for each query.

---

Instead of:

```text id="mq1"
1 Question
↓
1 Search
```

---

We do:

```text id="mq2"
1 Question
↓
Multiple Searches
```

---

# Why?

Users often ask questions differently than documents are written.

---

# 2. Example Problem

User asks:

```text id="mq3"
How much PTO do employees get?
```

---

Document contains:

```text id="mq4"
Employees receive 18 vacation days.
```

---

Problem:

```text id="mq5"
PTO
```

and

```text id="mq6"
Vacation Days
```

are different phrases.

---

Even good retrieval may miss some relevant chunks.

---

# Multi-Query Solution

Generate:

```text id="mq7"
How much PTO do employees get?

What is the paid time off policy?

How many vacation days do employees receive?

What employee leave benefits are available?
```

---

Now retrieval has more chances to find useful documents.

---

# 3. Why Multi-Query Exists

A single query represents:

```text id="mq8"
One Perspective
```

---

Documents may use:

```text id="mq9"
Different Vocabulary
Different Terminology
Different Wording
```

---

Multi-query increases:

```text id="mq10"
Recall
```

---

# What is Recall?

Recall answers:

```text id="mq11"
Did we retrieve all relevant documents?
```

---

Higher recall:

```text id="mq12"
More Relevant Documents Found
```

---

# 4. Multi-Query Architecture

```text id="mq13"
Question
 ↓
Generate Queries
 ↓
Query A
Query B
Query C
 ↓
Retrieve Documents
 ↓
Merge Results
 ↓
Rerank
 ↓
Top K
```

---

# RetailOps

Current:

```text id="mq14"
Question
 ↓
Multi Query
 ↓
Hybrid Search
 ↓
Cross Encoder
```

---

# 5. Query Generation

Question:

```text id="mq15"
What does P1 mean?
```

---

Generated:

```text id="mq16"
What is P1?

Define P1 incident priority.

What does P1 represent in incident management?

Explain P1 outage classification.
```

---

Each query retrieves different candidates.

---

# 6. Why Retrieval Improves

Different chunks may respond better to:

```text id="mq17"
Different Query Wording
```

---

Example

Document:

```text id="mq18"
Incident priority definitions.
```

---

Query:

```text id="mq19"
What does P1 mean?
```

---

Alternative:

```text id="mq20"
Explain incident priority levels.
```

---

May retrieve better context.

---

# 7. Query Expansion

Multi-query retrieval is a form of:

```text id="mq21"
Query Expansion
```

---

Original:

```text id="mq22"
PTO
```

---

Expanded:

```text id="mq23"
Paid Time Off

Vacation Days

Leave Benefits
```

---

Why?

Improves search coverage.

---

# 8. Merge Step

Results:

Query A:

```text id="mq24"
Chunk A
Chunk B
```

---

Query B:

```text id="mq25"
Chunk B
Chunk C
```

---

Query C:

```text id="mq26"
Chunk D
Chunk A
```

---

Merged:

```text id="mq27"
A
B
C
D
```

---

Duplicates removed.

---

# 9. Why We Need Reranking

Merged results often contain:

```text id="mq28"
Useful Chunks
Average Chunks
Noise
```

---

Need:

```text id="mq29"
Cross Encoder
```

to select:

```text id="mq30"
Best Chunks
```

---

Architecture:

```text id="mq31"
Multi Query
 ↓
Merge
 ↓
Cross Encoder
 ↓
Top K
```

---

# 10. Multi-Query vs Hybrid Search

Very common confusion.

---

# Hybrid Search

Improves:

```text id="mq32"
Retrieval Mechanism
```

---

Example:

```text id="mq33"
Vector
+
BM25
```

---

# Multi Query

Improves:

```text id="mq34"
Search Queries
```

---

Example:

```text id="mq35"
PTO
Vacation
Leave
```

---

# Difference

Hybrid Search:

```text id="mq36"
Better Search Engine
```

---

Multi Query:

```text id="mq37"
Better Search Terms
```

---

# 11. Multi-Query vs Semantic Chunking

Semantic Chunking:

```text id="mq38"
Improve Chunks
```

---

Multi Query:

```text id="mq39"
Improve Queries
```

---

Different stages.

---

# 12. Multi-Query vs Reranking

Multi Query:

```text id="mq40"
Increase Recall
```

---

Reranking:

```text id="mq41"
Increase Precision
```

---

# Difference

Recall:

```text id="mq42"
Find More Good Documents
```

---

Precision:

```text id="mq43"
Keep Best Documents
```

---

Both are important.

---

# 13. Why Multi-Query Can Improve RAG

Question:

```text id="mq44"
How much PTO do employees get?
```

---

Single query may retrieve:

```text id="mq45"
Vacation Policy
```

---

Multi-query may retrieve:

```text id="mq46"
Vacation Policy
Benefits Policy
Leave Policy
```

---

More complete context.

---

# 14. Tradeoffs

## Pros

```text id="mq47"
Higher Recall
Better Retrieval
More Coverage
```

---

## Cons

```text id="mq48"
More LLM Calls
More Retrieval Calls
More Latency
```

---

Nothing is free.

---

# 15. RetailOps Implementation

Current:

```python id="mq49"
generate_queries()
```

---

Produces:

```text id="mq50"
Multiple Retrieval Queries
```

---

Files:

```text id="mq51"
app/multi_query.py
```

---

Pipeline:

```text id="mq52"
Question
 ↓
Query Expansion
 ↓
Hybrid Search
 ↓
Cross Encoder
```

---

# 16. Production Best Practices

## Use for Difficult Queries

Good:

```text id="mq53"
Knowledge Search
Policies
Documentation
```

---

## Avoid for Everything

Not every query needs expansion.

---

## Add Evaluation

Measure:

```text id="mq54"
Recall Improvement
```

---

## Add Final Reranking

Always.

---

## Make It Configurable

RetailOps:

```text id="mq55"
ENABLE_MULTI_QUERY
```

---

# 17. Common Mistakes

## Mistake 1

Using Multi Query without reranking.

---

## Mistake 2

Generating too many queries.

---

## Mistake 3

Never evaluating impact.

---

## Mistake 4

Using it for exact lookups.

---

Example:

```text id="mq56"
SKU Search
```

does not need expansion.

---

# 18. Interview Questions

### What is Multi-Query Retrieval?

Generating multiple search queries from a single question.

---

### Why use Multi-Query Retrieval?

To improve retrieval recall.

---

### Multi-Query vs Hybrid Search?

Hybrid:

```text id="mq57"
Better Search Engine
```

Multi Query:

```text id="mq58"
Better Search Queries
```

---

### Multi-Query vs Reranking?

Multi Query:

```text id="mq59"
Recall
```

Reranking:

```text id="mq60"
Precision
```

---

### What is Query Expansion?

Generating alternate ways to express the same question.

---

### Why make Multi Query optional?

Because it increases cost and latency.

---

# Summary

Multi-Query Retrieval improves:

```text id="mq61"
Recall
```

by searching for multiple interpretations of a question.

RetailOps uses:

```text id="mq62"
Query Expansion
+
Hybrid Search
+
Cross Encoder
```

to maximize retrieval quality before generation.

The next document:

```text id="mq63"
21_parent_child_retrieval.md
```

explains parent-child retrieval, context completeness, and why some enterprise systems separate search chunks from answer chunks.
