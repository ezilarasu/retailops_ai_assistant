# 14 - Similarity Search

# Learning Objectives

After completing this document, you should understand:

* What Similarity Search is
* Why Similarity Search exists
* How Similarity Search works
* Query Embeddings
* Document Embeddings
* Vector Distance Metrics
* Cosine Similarity
* Euclidean Distance
* Dot Product
* Similarity Search Limitations
* Similarity Search vs BM25
* Similarity Search vs Reranking
* Production Best Practices

---

# 1. What is Similarity Search?

## Definition

Similarity Search finds documents whose embeddings are most similar to a query embedding.

---

Example:

Question:

```text id="sim1"
How much PTO do employees receive?
```

---

Document:

```text id="sim2"
Employees receive 18 vacation days.
```

---

Even though:

```text id="sim3"
PTO
≠
Vacation
```

Similarity search understands:

```text id="sim4"
PTO
≈
Vacation
```

---

# Why It Exists

Traditional search relies on:

```text id="sim5"
Words
```

---

Similarity search relies on:

```text id="sim6"
Meaning
```

---

# 2. Similarity Search Architecture

```text id="sim7"
Question
 ↓
Embedding
 ↓
Vector Database
 ↓
Nearest Vectors
 ↓
Documents
```

---

Example:

```text id="sim8"
Question
 ↓
Vector Q
```

---

Database:

```text id="sim9"
Vector A
Vector B
Vector C
```

---

Find:

```text id="sim10"
Most Similar
```

vectors.

---

# 3. Query Embeddings

Question:

```text id="sim11"
How much PTO do employees receive?
```

---

Embedding Model:

```text id="sim12"
all-MiniLM-L6-v2
```

---

Output:

```text id="sim13"
Vector Q
```

---

The retriever searches using:

```text id="sim14"
Vector Q
```

not the text itself.

---

# 4. Document Embeddings

Each chunk is embedded.

---

Example:

Chunk:

```text id="sim15"
Employees receive 18 vacation days.
```

---

Embedding:

```text id="sim16"
Vector D
```

---

Stored in:

```text id="sim17"
Vector Database
```

---

# 5. Similarity Search Process

Step 1:

```text id="sim18"
Embed Question
```

---

Step 2:

```text id="sim19"
Compare Against Stored Vectors
```

---

Step 3:

```text id="sim20"
Rank Similarity Scores
```

---

Step 4:

```text id="sim21"
Return Top K Documents
```

---

# Visual

```text id="sim22"
Question
 ↓
Embedding

Document A
Document B
Document C

Compare Similarity

Top K
```

---

# 6. Cosine Similarity

Most common metric.

---

Formula:

\cos(\theta)=\frac{A\cdot B}{||A||||B||}

---

# Interpretation

```text id="sim23"
1.0
=
Identical Direction

0.0
=
Unrelated

-1.0
=
Opposite
```

---

# Why Cosine Similarity?

It measures:

```text id="sim24"
Direction
```

rather than:

```text id="sim25"
Magnitude
```

---

This works well for embeddings.

---

# Example

Question:

```text id="sim26"
PTO
```

---

Document:

```text id="sim27"
Vacation Policy
```

---

Similarity:

```text id="sim28"
0.93
```

---

Document:

```text id="sim29"
Inventory Report
```

---

Similarity:

```text id="sim30"
0.08
```

---

Retriever selects:

```text id="sim31"
Vacation Policy
```

---

# 7. Euclidean Distance

Measures physical distance.

---

Formula:

d(A,B)=\sqrt{\sum_{i=1}^{n}(A_i-B_i)^2}

---

Interpretation:

```text id="sim32"
Smaller Distance
=
More Similar
```

---

Pros:

```text id="sim33"
Easy to Understand
```

---

Cons:

```text id="sim34"
Less Common for Embeddings
```

---

# 8. Dot Product

Another common metric.

---

Formula:

A\cdot B=\sum_{i=1}^{n}A_iB_i

---

Measures:

```text id="sim35"
Vector Alignment
```

---

Used by:

```text id="sim36"
Many Embedding Models
```

---

# Difference

Cosine:

```text id="sim37"
Direction Only
```

---

Dot Product:

```text id="sim38"
Direction + Magnitude
```

---

# 9. Why Similarity Search Works

Embedding Models learn:

```text id="sim39"
Semantic Relationships
```

---

Example:

```text id="sim40"
PTO
Vacation
Leave
```

become nearby vectors.

---

Example:

```text id="sim41"
Inventory
Stock
SKU
```

become another cluster.

---

Retriever uses this structure.

---

# 10. Similarity Search Limitations

Very important.

---

# Problem 1

Exact IDs.

---

Question:

```text id="sim42"
DENIM-4421
```

---

Similarity Search:

```text id="sim43"
Weak
```

---

Why?

IDs have little semantic meaning.

---

# Problem 2

Dates

Example:

```text id="sim44"
October 31
```

---

Similarity Search often struggles.

---

# Problem 3

Codes

Example:

```text id="sim45"
P1
INC-1001
```

---

Again:

```text id="sim46"
Weak Semantic Meaning
```

---

# Solution

Use:

```text id="sim47"
BM25
```

too.

---

# 11. Similarity Search vs BM25

Very common interview topic.

---

# Similarity Search

Searches:

```text id="sim48"
Meaning
```

---

Example:

```text id="sim49"
PTO
```

finds:

```text id="sim50"
Vacation
```

---

# BM25

Searches:

```text id="sim51"
Exact Terms
```

---

Example:

```text id="sim52"
P1
```

finds:

```text id="sim53"
P1
```

---

# Production Pattern

```text id="sim54"
Similarity Search
+
BM25
```

---

RetailOps:

```text id="sim55"
Hybrid Search
```

---

# 12. Similarity Search vs Reranking

Another critical distinction.

---

# Similarity Search

Goal:

```text id="sim56"
Find Candidates
```

---

Example:

```text id="sim57"
Top 20 Chunks
```

---

# Reranking

Goal:

```text id="sim58"
Sort Candidates
```

---

Example:

```text id="sim59"
Top 5 Chunks
```

---

Architecture:

```text id="sim60"
Similarity Search
 ↓
Candidates
 ↓
Cross Encoder
 ↓
Best Candidates
```

---

# Difference

Similarity Search:

```text id="sim61"
Recall
```

---

Reranker:

```text id="sim62"
Precision
```

---

# 13. RetailOps Similarity Search

Current:

```text id="sim63"
Embeddings
 ↓
Chroma
 ↓
Retriever
```

---

Used in:

```text id="sim64"
Semantic Retrieval
Hybrid Search
Multi Query
```

---

Files:

```text id="sim65"
app/vectorstore.py
app/hybrid_retriever.py
```

---

# 14. Production Best Practices

## Never Use Similarity Search Alone

Combine:

```text id="sim66"
BM25
```

---

## Evaluate Retrieval

Use:

```text id="sim67"
Golden Dataset
```

---

## Add Reranking

Use:

```text id="sim68"
Cross Encoder
```

---

## Tune Top K

Avoid:

```text id="sim69"
Too Many Chunks
```

---

## Monitor Retrieval Quality

Track:

```text id="sim70"
Source Accuracy
Recall
Latency
```

---

# 15. Common Mistakes

## Mistake 1

Thinking similarity search understands facts.

---

## Mistake 2

Using it for exact IDs only.

---

## Mistake 3

No evaluation.

---

## Mistake 4

Retrieving too many chunks.

---

## Mistake 5

Using similarity search without reranking.

---

# 16. Interview Questions

### What is Similarity Search?

Finding documents whose embeddings are most similar to a query embedding.

---

### Why use embeddings?

To search by meaning rather than keywords.

---

### What is Cosine Similarity?

A measure of vector direction similarity.

---

### Similarity Search vs BM25?

Similarity:

```text id="sim71"
Meaning
```

BM25:

```text id="sim72"
Exact Terms
```

---

### Similarity Search vs Reranking?

Similarity Search:

```text id="sim73"
Candidate Retrieval
```

Reranking:

```text id="sim74"
Candidate Ranking
```

---

### Why not use Similarity Search alone?

Because it struggles with IDs, codes, dates, and exact matches.

---

# Summary

Similarity Search is the foundation of semantic retrieval.

It allows systems like RetailOps to retrieve:

```text id="sim75"
Meaning-Based Context
```

rather than:

```text id="sim76"
Keyword Matches
```

but it works best when combined with:

```text id="sim77"
BM25
Cross Encoder Reranking
Evaluation
```

The next document:

```text id="sim78"
15_mmr_retrieval.md
```

explains Maximum Marginal Relevance (MMR), diversity-based retrieval, and why RetailOps uses MMR instead of plain similarity search.
