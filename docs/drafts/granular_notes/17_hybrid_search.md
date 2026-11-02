# 17 - Hybrid Search

# Learning Objectives

After completing this document, you should understand:

* What Hybrid Search is
* Why Hybrid Search exists
* Semantic Search vs Keyword Search
* Vector Search
* BM25 Search
* Hybrid Search Architecture
* Query Flow
* Hybrid Search Tradeoffs
* When to Use Hybrid Search
* Production Best Practices
* RetailOps Implementation

---

# 1. What is Hybrid Search?

## Definition

Hybrid Search combines:

```text id="hy1"
Semantic Search
+
Keyword Search
```

to improve retrieval quality.

---

In RetailOps:

```text id="hy2"
Vector Search
+
BM25
```

---

# Why Does Hybrid Search Exist?

Because:

```text id="hy3"
Semantic Search
```

and

```text id="hy4"
Keyword Search
```

have different strengths.

---

Neither is perfect alone.

---

# 2. Problem with Semantic Search

Question:

```text id="hy5"
What does P1 mean?
```

---

Document:

```text id="hy6"
P1 means full store outage.
```

---

Problem:

```text id="hy7"
P1
```

has weak semantic meaning.

---

Embedding models often struggle with:

```text id="hy8"
IDs
Codes
Dates
SKUs
```

---

Examples:

```text id="hy9"
P1
INC-1001
DENIM-4421
Store 102
```

---

Similarity Search may miss them.

---

# 3. Problem with Keyword Search

Question:

```text id="hy10"
How much PTO do employees receive?
```

---

Document:

```text id="hy11"
Employees receive 18 vacation days.
```

---

Keyword Search:

```text id="hy12"
PTO
```

not found.

---

Result:

```text id="hy13"
Missed Document
```

---

Humans know:

```text id="hy14"
PTO
≈
Vacation
```

---

Keyword search does not.

---

# 4. Hybrid Search Solution

Use both.

---

Architecture:

```text id="hy15"
Question
 ↓
Vector Search
 ↓
Candidates

Question
 ↓
BM25
 ↓
Candidates

Merge
 ↓
Final Candidates
```

---

Now:

```text id="hy16"
Meaning
+
Exact Match
```

both work.

---

# 5. Semantic Search Component

Question:

```text id="hy17"
How much PTO do employees receive?
```

---

Vector Search understands:

```text id="hy18"
PTO
≈
Vacation
```

---

Finds:

```text id="hy19"
Vacation Policy
```

---

Strength:

```text id="hy20"
Meaning
```

---

# 6. BM25 Component

Question:

```text id="hy21"
What does P1 mean?
```

---

BM25 finds:

```text id="hy22"
P1
```

exactly.

---

Strength:

```text id="hy23"
Exact Terms
```

---

# 7. Why Hybrid Search Works

Question:

```text id="hy24"
Find vendor for SKU DENIM-4421
```

---

Semantic Search:

```text id="hy25"
Vendor
Product
```

---

BM25:

```text id="hy26"
DENIM-4421
```

---

Combined:

```text id="hy27"
Best Retrieval
```

---

# 8. Hybrid Search Architecture

RetailOps:

```text id="hy28"
Question
 ↓
Vector Search
 ↓
Candidates

Question
 ↓
BM25
 ↓
Candidates

Merge
 ↓
Cross Encoder
 ↓
Top K
 ↓
LLM
```

---

Notice:

```text id="hy29"
Hybrid Search
≠
Reranking
```

---

Different stages.

---

# 9. Merge Step

After retrieval:

```text id="hy30"
Vector Results
```

---

and:

```text id="hy31"
BM25 Results
```

---

must be merged.

---

Example:

Vector:

```text id="hy32"
A
B
C
```

---

BM25:

```text id="hy33"
B
D
E
```

---

Merged:

```text id="hy34"
A
B
C
D
E
```

---

Duplicates removed.

---

# 10. Why We Need Reranking

Merged results contain:

```text id="hy35"
Good Chunks
Average Chunks
Noise
```

---

Need:

```text id="hy36"
Cross Encoder
```

to rank them.

---

Architecture:

```text id="hy37"
Hybrid Search
 ↓
Candidates
 ↓
Cross Encoder
 ↓
Top K
```

---

# Difference

Hybrid Search:

```text id="hy38"
Candidate Retrieval
```

---

Cross Encoder:

```text id="hy39"
Candidate Ranking
```

---

# 11. Hybrid Search vs Similarity Search

Similarity Search:

```text id="hy40"
Meaning Only
```

---

Hybrid Search:

```text id="hy41"
Meaning
+
Exact Match
```

---

Hybrid is usually stronger.

---

# 12. Hybrid Search vs BM25

BM25:

```text id="hy42"
Exact Terms Only
```

---

Hybrid:

```text id="hy43"
Meaning
+
Exact Terms
```

---

Again:

```text id="hy44"
Stronger
```

---

# 13. Hybrid Search vs Multi Query

Different concepts.

---

Hybrid Search:

```text id="hy45"
Improve Retrieval
```

---

Multi Query:

```text id="hy46"
Improve Queries
```

---

Together:

```text id="hy47"
Better Questions
+
Better Retrieval
```

---

# 14. RetailOps Hybrid Retriever

Current implementation:

```python id="hy48"
HybridRetriever
```

---

Combines:

```text id="hy49"
Vector Search
BM25
```

---

Files:

```text id="hy50"
app/hybrid_retriever.py
app/bm25_retriever.py
```

---

# 15. Production Best Practices

## Always Evaluate

Do not assume:

```text id="hy51"
Hybrid
```

is automatically better.

---

Use:

```text id="hy52"
Evaluation Reports
```

---

## Add Reranking

Use:

```text id="hy53"
Cross Encoder
```

after hybrid retrieval.

---

## Keep Candidate Set Reasonable

Avoid:

```text id="hy54"
Huge Candidate Lists
```

---

## Track Retrieval Sources

Monitor:

```text id="hy55"
Source Accuracy
```

---

# 16. Common Mistakes

## Mistake 1

Thinking Hybrid Search replaces reranking.

---

## Mistake 2

Thinking Hybrid Search solves chunking problems.

---

## Mistake 3

No evaluation.

---

## Mistake 4

Ignoring BM25.

---

## Mistake 5

Retrieving too many chunks.

---

# 17. Interview Questions

### What is Hybrid Search?

Combining semantic search and keyword search.

---

### Why use Hybrid Search?

To get both:

```text id="hy56"
Meaning
+
Exact Matching
```

---

### Hybrid Search vs Similarity Search?

Similarity:

```text id="hy57"
Meaning Only
```

Hybrid:

```text id="hy58"
Meaning + Exact Terms
```

---

### Hybrid Search vs BM25?

BM25:

```text id="hy59"
Exact Terms
```

Hybrid:

```text id="hy60"
Exact Terms + Meaning
```

---

### Why does RetailOps use Hybrid Search?

To handle:

```text id="hy61"
PTO
Vacation
P1
SKU
Incident IDs
```

effectively.

---

# Summary

Hybrid Search is one of the most important production RAG patterns.

It combines:

```text id="hy62"
Vector Search
+
BM25
```

to improve retrieval quality.

RetailOps uses Hybrid Search because it handles:

```text id="hy63"
Semantic Questions
+
Exact Identifiers
```

much better than either retrieval strategy alone.

The next document:

```text id="hy64"
18_bm25.md
```

dives deep into BM25, lexical retrieval, ranking scores, and why BM25 remains one of the most important retrieval algorithms even in modern AI systems.
