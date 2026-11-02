# 11 - Embeddings

# Learning Objectives

After completing this document, you should understand:

* What Embeddings are
* Why Embeddings exist
* How Embeddings work
* Embeddings vs Keywords
* Semantic Similarity
* Vector Representation
* Embedding Models
* Embedding Quality
* Similarity Search
* Embedding Tradeoffs
* Production Best Practices
* RetailOps Implementation

---

# 1. What is an Embedding?

## Definition

An embedding is a numerical representation of meaning.

It converts:

```text id="emb1"
Text
```

into:

```text id="emb2"
Vector
```

---

Example:

Text:

```text id="emb3"
Vacation Policy
```

Embedding:

```text id="emb4"
[0.22, -0.18, 0.93, ...]
```

---

# Why Does This Exist?

Computers understand:

```text id="emb5"
Numbers
```

better than:

```text id="emb6"
Meaning
```

---

Embeddings convert:

```text id="emb7"
Meaning
↓
Numbers
```

---

# 2. Why Not Use Keywords?

Suppose user asks:

```text id="emb8"
How much PTO do employees receive?
```

Document:

```text id="emb9"
Employees receive 18 vacation days.
```

---

Keyword Search:

```text id="emb10"
PTO
```

does not exist.

---

Result:

```text id="emb11"
No Match
```

---

But humans know:

```text id="emb12"
PTO
≈
Vacation
```

---

Embeddings capture that relationship.

---

# 3. How Embeddings Work

Input:

```text id="emb13"
Vacation Policy
```

---

Embedding Model:

```text id="emb14"
all-MiniLM-L6-v2
```

---

Output:

```text id="emb15"
[0.14, 0.72, -0.51, ...]
```

---

These numbers represent semantic meaning.

---

# Important

Embeddings do NOT store facts.

---

Many beginners think:

```text id="emb16"
Embedding
=
Knowledge
```

Wrong.

---

Embedding:

```text id="emb17"
Represents Meaning
```

---

# 4. Semantic Similarity

Question:

```text id="emb18"
How much PTO do employees receive?
```

---

Document:

```text id="emb19"
Employees receive 18 vacation days.
```

---

Embedding Model understands:

```text id="emb20"
PTO
≈
Vacation
```

---

Therefore vectors become close.

---

# Visual

```text id="emb21"
Question ●

Document ●
```

---

Close vectors:

```text id="emb22"
Similar Meaning
```

---

Far vectors:

```text id="emb23"
Different Meaning
```

---

# 5. Embedding Space

Imagine a huge mathematical space.

---

Example:

```text id="emb24"
Vacation Policy
PTO
Leave Policy
```

cluster together.

---

Meanwhile:

```text id="emb25"
Inventory
SKU
Stock
```

cluster elsewhere.

---

Visualization:

```text id="emb26"
PTO
Vacation
Leave
   ● ● ●

Inventory
Stock
SKU
   ● ● ●
```

---

# Why This Matters

Retrieval becomes:

```text id="emb27"
Meaning Search
```

instead of:

```text id="emb28"
Word Search
```

---

# 6. Similarity Search

Question:

```text id="emb29"
How much PTO do employees receive?
```

---

Embedding:

```text id="emb30"
Vector Q
```

---

Documents:

```text id="emb31"
Vector A
Vector B
Vector C
```

---

Retriever finds:

```text id="emb32"
Nearest Vectors
```

---

This is called:

```text id="emb33"
Similarity Search
```

---

# 7. Cosine Similarity

Most common similarity metric.

---

Formula:

\cos(\theta)=\frac{A\cdot B}{||A||||B||}

---

Interpretation:

```text id="emb34"
1.0
=
Very Similar

0.0
=
Unrelated

-1.0
=
Opposite
```

---

# Why Use It?

Measures direction rather than magnitude.

---

Most vector databases use:

```text id="emb35"
Cosine Similarity
```

or related metrics.

---

# 8. Embedding Models

Examples:

```text id="emb36"
all-MiniLM-L6-v2
bge-small-en
bge-large-en
nomic-embed-text
text-embedding-3-small
```

---

# OpenAI

Example:

```text id="emb37"
text-embedding-3-small
```

---

Pros:

```text id="emb38"
High Quality
```

---

Cons:

```text id="emb39"
API Cost
```

---

# Hugging Face

Example:

```text id="emb40"
all-MiniLM-L6-v2
```

---

Pros:

```text id="emb41"
Free
Local
Fast
```

---

Cons:

```text id="emb42"
Smaller Model
```

---

# RetailOps

Current model:

```text id="emb43"
all-MiniLM-L6-v2
```

---

Why?

```text id="emb44"
Free
Fast
Good Learning Model
```

---

# 9. Embedding Quality

Not all embeddings are equal.

---

Weak model:

```text id="emb45"
Lower Retrieval Quality
```

---

Strong model:

```text id="emb46"
Higher Retrieval Quality
```

---

# Important Insight

Changing embedding models often improves RAG more than changing prompts.

---

# 10. Embeddings in RAG

Pipeline:

```text id="emb47"
Document
 ↓
Embedding
 ↓
Vector Store
```

---

Question:

```text id="emb48"
Question
 ↓
Embedding
 ↓
Similarity Search
```

---

Output:

```text id="emb49"
Relevant Chunks
```

---

# RetailOps

Used for:

```text id="emb50"
Semantic Retrieval
Semantic Chunking
Hybrid Search
```

---

# 11. Embeddings vs BM25

Very common interview question.

---

# BM25

Searches:

```text id="emb51"
Words
```

---

Example:

```text id="emb52"
P1
DENIM-4421
```

---

Strength:

```text id="emb53"
Exact Matches
```

---

# Embeddings

Search:

```text id="emb54"
Meaning
```

---

Example:

```text id="emb55"
PTO
Vacation
```

---

Strength:

```text id="emb56"
Semantic Similarity
```

---

# Production Pattern

Use:

```text id="emb57"
Embeddings
+
BM25
```

---

RetailOps:

```text id="emb58"
Hybrid Search
```

---

# 12. Embeddings vs Cross Encoder

Another common interview topic.

---

# Embeddings

Question:

```text id="emb59"
Vector
```

---

Document:

```text id="emb60"
Vector
```

---

Compare:

```text id="emb61"
Similarity
```

---

# Cross Encoder

Input:

```text id="emb62"
Question
+
Document
```

---

Output:

```text id="emb63"
Relevance Score
```

---

# Difference

Embeddings:

```text id="emb64"
Fast
```

---

Cross Encoder:

```text id="emb65"
More Accurate
```

---

# Production Pattern

```text id="emb66"
Embeddings
↓
Candidate Retrieval

Cross Encoder
↓
Reranking
```

---

# 13. Production Best Practices

## Evaluate Embedding Models

Do not assume:

```text id="emb67"
Default
=
Best
```

---

## Use Hybrid Retrieval

Combine:

```text id="emb68"
Embeddings
+
BM25
```

---

## Rerank Results

Use:

```text id="emb69"
Cross Encoder
```

after retrieval.

---

## Reindex When Embeddings Change

New model:

```text id="emb70"
Requires Reindexing
```

---

# 14. Common Mistakes

## Mistake 1

Embeddings store knowledge.

---

## Mistake 2

Using embeddings without evaluation.

---

## Mistake 3

Ignoring BM25.

---

## Mistake 4

Using embeddings for exact IDs only.

---

## Mistake 5

Changing models without rebuilding indexes.

---

# 15. RetailOps Implementation

Current:

```python id="emb71"
HuggingFaceEmbeddings(
    model_name=
    "sentence-transformers/all-MiniLM-L6-v2"
)
```

---

Used in:

```text id="emb72"
Retrieval
Semantic Chunking
Vector Store
```

---

Files:

```text id="emb73"
app/vectorstore.py
app/rag.py
```

---

# 16. Interview Questions

### What is an embedding?

A numerical representation of semantic meaning.

---

### Why use embeddings?

To perform semantic search.

---

### Do embeddings store facts?

No.

They represent meaning.

---

### Embeddings vs BM25?

Embeddings:

```text id="emb74"
Meaning
```

BM25:

```text id="emb75"
Exact Terms
```

---

### Embeddings vs Cross Encoder?

Embeddings:

```text id="emb76"
Fast Retrieval
```

Cross Encoder:

```text id="emb77"
Accurate Ranking
```

---

### Why use embeddings in RAG?

To find semantically similar chunks.

---

# Summary

Embeddings are the foundation of semantic retrieval.

They convert:

```text id="emb78"
Meaning
```

into:

```text id="emb79"
Vectors
```

which allow systems like RetailOps to perform:

```text id="emb80"
Semantic Search
Hybrid Search
Semantic Chunking
```

efficiently.

The next document:

```text id="emb81"
12_vector_databases.md
```

explains how embeddings are stored, indexed, and searched efficiently at scale.
