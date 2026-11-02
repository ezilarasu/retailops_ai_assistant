# 19 - Cross Encoder Reranking

# Learning Objectives

After completing this document, you should understand:

* What a Cross Encoder is
* Why Reranking exists
* Retriever vs Reranker
* Embedding Similarity vs Cross Encoder
* Cross Encoder Architecture
* Cross Encoder Models
* Candidate Retrieval vs Candidate Ranking
* Production Retrieval Pipelines
* RetailOps Implementation
* Best Practices

---

# 1. What is Reranking?

## Definition

Reranking is the process of reordering retrieved documents based on relevance before sending them to the LLM.

---

Question:

```text id="ce1"
What does P1 mean?
```

---

Retriever returns:

```text id="ce2"
Chunk A
Chunk B
Chunk C
Chunk D
```

---

Reranker decides:

```text id="ce3"
Which chunks are actually best?
```

---

# Why Does Reranking Exist?

Retrievers are optimized for:

```text id="ce4"
Speed
```

---

Not necessarily:

```text id="ce5"
Perfect Ranking
```

---

Retrievers find:

```text id="ce6"
Candidates
```

---

Rerankers find:

```text id="ce7"
Best Candidates
```

---

# 2. Retrieval Pipeline

Modern architecture:

```text id="ce8"
Question
 ↓
Retriever
 ↓
Top 20

Reranker
 ↓
Top 5

LLM
```

---

RetailOps:

```text id="ce9"
Hybrid Search
 ↓
Candidates
 ↓
Cross Encoder
 ↓
Top K
 ↓
LLM
```

---

# 3. What is a Cross Encoder?

## Definition

A Cross Encoder is a model that receives:

```text id="ce10"
Query
+
Document
```

together and produces:

```text id="ce11"
Relevance Score
```

---

Example

Input:

```text id="ce12"
Question:
What does P1 mean?

Document:
P1 means full store outage.
```

---

Output:

```text id="ce13"
0.99
```

---

Meaning:

```text id="ce14"
Highly Relevant
```

---

# 4. Why Is It Called Cross Encoder?

Because attention crosses between:

```text id="ce15"
Question Tokens
```

and

```text id="ce16"
Document Tokens
```

inside the model.

---

Unlike embeddings:

```text id="ce17"
Question
```

and

```text id="ce18"
Document
```

are processed together.

---

# 5. Embedding Similarity vs Cross Encoder

This is one of the most important concepts.

---

# Embedding Similarity

Question:

```text id="ce19"
What does P1 mean?
```

---

Question:

```text id="ce20"
Embedding Q
```

---

Document:

```text id="ce21"
Embedding D
```

---

Compare:

```text id="ce22"
Cosine Similarity
```

---

Result:

```text id="ce23"
Approximate Relevance
```

---

# Cross Encoder

Input:

```text id="ce24"
Question
+
Document
```

---

Model:

```text id="ce25"
Understands Relationship
```

---

Output:

```text id="ce26"
Precise Relevance Score
```

---

# Difference

Embeddings:

```text id="ce27"
Semantic Similarity
```

---

Cross Encoder:

```text id="ce28"
Question-Answer Relevance
```

---

# 6. Example

Question:

```text id="ce29"
What does P1 mean?
```

---

Document A:

```text id="ce30"
P1 means full store outage.
```

---

Document B:

```text id="ce31"
P1 incidents require manager approval.
```

---

Embedding Similarity:

```text id="ce32"
A = 0.91
B = 0.88
```

Very close.

---

Cross Encoder:

```text id="ce33"
A = 0.99
B = 0.42
```

Much better.

---

Because:

```text id="ce34"
A answers the question.
```

---

# 7. Why Not Use Cross Encoder for Retrieval?

Very common interview question.

---

Imagine:

```text id="ce35"
1,000,000 chunks
```

---

Cross Encoder must evaluate:

```text id="ce36"
Question + Chunk1

Question + Chunk2

Question + Chunk3

...
```

---

One million times.

---

Impossible.

---

Too slow.

---

# Embeddings Scale

Question:

```text id="ce37"
Embedding
```

---

Vector Database:

```text id="ce38"
ANN Search
```

---

Finds:

```text id="ce39"
Top 20
```

quickly.

---

Then:

```text id="ce40"
Cross Encoder
```

reranks only those.

---

# Production Pattern

```text id="ce41"
Embeddings
 ↓
Candidates

Cross Encoder
 ↓
Ranking
```

---

# 8. Popular Cross Encoder Models

Examples:

```text id="ce42"
cross-encoder/ms-marco-MiniLM-L-6-v2

cross-encoder/ms-marco-MiniLM-L-12-v2

bge-reranker-base

bge-reranker-large
```

---

# RetailOps

Current:

```text id="ce43"
cross-encoder/ms-marco-MiniLM-L-6-v2
```

---

Why?

```text id="ce44"
Free
Local
Lightweight
```

---

# 9. Cross Encoder Workflow

Question:

```text id="ce45"
How much PTO do employees receive?
```

---

Candidates:

```text id="ce46"
Vacation Policy

Remote Work Policy

Incident Policy

Benefits Policy
```

---

Cross Encoder Scores:

```text id="ce47"
Vacation Policy = 0.98

Benefits Policy = 0.73

Remote Work = 0.15

Incident = 0.02
```

---

Keep:

```text id="ce48"
Top Chunks
```

---

# Why This Helps

LLM sees:

```text id="ce49"
Best Context
```

instead of:

```text id="ce50"
Average Context
```

---

# 10. Reranking vs Retrieval

Retriever:

```text id="ce51"
Find Candidates
```

---

Cross Encoder:

```text id="ce52"
Rank Candidates
```

---

Retriever Optimizes:

```text id="ce53"
Recall
```

---

Cross Encoder Optimizes:

```text id="ce54"
Precision
```

---

# 11. RetailOps Pipeline

Current:

```text id="ce55"
Question
 ↓
Hybrid Search
 ↓
Candidates
 ↓
Cross Encoder
 ↓
Top K
 ↓
LLM
```

---

This is close to modern production RAG.

---

# 12. Cross Encoder Tradeoffs

## Pros

```text id="ce56"
Better Ranking
Better Context
Better Answers
```

---

## Cons

```text id="ce57"
Extra Latency
Extra Compute
```

---

# Why Worth It?

LLM costs are usually higher than reranking costs.

---

Good reranking:

```text id="ce58"
Reduces Noise
```

---

Better answers.

---

# 13. Cross Encoder vs LLM Reranking

Cross Encoder:

```text id="ce59"
Specialized Ranking Model
```

---

LLM Reranking:

```text id="ce60"
General Purpose LLM
```

---

Cross Encoder:

```text id="ce61"
Faster
Cheaper
```

---

LLM:

```text id="ce62"
More Flexible
```

---

Most production systems prefer:

```text id="ce63"
Cross Encoder
```

---

# 14. Production Best Practices

## Retrieve Broadly

Example:

```text id="ce64"
Top 20
```

---

## Rerank Aggressively

Example:

```text id="ce65"
Top 4
```

---

## Evaluate

Measure:

```text id="ce66"
Answer Quality
Source Accuracy
```

---

## Combine with Hybrid Search

Best pattern:

```text id="ce67"
Hybrid Search
+
Cross Encoder
```

---

# 15. Common Mistakes

## Mistake 1

Using Cross Encoder for full retrieval.

---

## Mistake 2

Skipping reranking.

---

## Mistake 3

Reranking too many candidates.

---

## Mistake 4

No evaluation.

---

## Mistake 5

Confusing reranking with retrieval.

---

# 16. Interview Questions

### What is a Cross Encoder?

A model that scores query-document pairs.

---

### Why use Cross Encoders?

To improve retrieval precision.

---

### Why not use Cross Encoders for retrieval?

They do not scale to large document collections.

---

### Embeddings vs Cross Encoder?

Embeddings:

```text id="ce68"
Fast Retrieval
```

Cross Encoder:

```text id="ce69"
Accurate Ranking
```

---

### Retriever vs Reranker?

Retriever:

```text id="ce70"
Find Candidates
```

Reranker:

```text id="ce71"
Sort Candidates
```

---

### Why does RetailOps use a Cross Encoder?

To improve retrieval quality before sending context to Groq.

---

# Summary

Cross Encoders are one of the highest-impact retrieval improvements in modern RAG systems.

They transform:

```text id="ce72"
Good Retrieval
```

into:

```text id="ce73"
Great Retrieval
```

by selecting the most useful chunks before generation.

RetailOps uses:

```text id="ce74"
Hybrid Search
+
Cross Encoder
```

which closely mirrors production retrieval architectures used in enterprise AI systems.

The next document:

```text id="ce75"
20_multi_query_retrieval.md
```

covers query expansion, alternate search strategies, and how multiple retrieval queries can dramatically improve recall.
