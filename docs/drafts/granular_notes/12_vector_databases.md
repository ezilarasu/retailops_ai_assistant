# 12 - Vector Databases

# Learning Objectives

After completing this document, you should understand:

* What a Vector Database is
* Why Vector Databases exist
* Why not store embeddings in normal databases
* How Vector Search works
* Approximate Nearest Neighbor (ANN)
* Chroma
* FAISS
* Pinecone
* Qdrant
* Weaviate
* Metadata Filtering
* Vector Database Tradeoffs
* Production Best Practices
* RetailOps Implementation

---

# 1. What is a Vector Database?

## Definition

A Vector Database stores embeddings and allows efficient similarity search.

Think of it as:

```text id="vdb1"
Text
 ↓
Embedding
 ↓
Vector Database
 ↓
Similarity Search
```

---

# Why Do We Need It?

Suppose:

```text id="vdb2"
1 million document chunks
```

---

Each chunk has:

```text id="vdb3"
Embedding Vector
```

---

Question:

```text id="vdb4"
What does P1 mean?
```

---

We need to find:

```text id="vdb5"
Most Similar Chunks
```

---

Doing this manually:

```text id="vdb6"
Too Slow
```

---

Vector databases solve this.

---

# 2. Traditional Database vs Vector Database

## Traditional Database

Stores:

```text id="vdb7"
Name
Price
Date
Status
```

---

Example:

```sql id="vdb8"
SELECT *
FROM employees
WHERE id = 123
```

---

Best for:

```text id="vdb9"
Exact Lookup
```

---

# Vector Database

Stores:

```text id="vdb10"
Embedding Vectors
```

---

Example:

```text id="vdb11"
Find documents
similar to this query.
```

---

Best for:

```text id="vdb12"
Similarity Search
```

---

# 3. Why Not Use PostgreSQL?

Technically possible.

---

Question:

```text id="vdb13"
Compare query vector
against 1 million vectors.
```

---

Brute Force:

```text id="vdb14"
1 million comparisons
```

---

Too slow.

---

Vector databases use:

```text id="vdb15"
Indexes
ANN Search
```

to make retrieval fast.

---

# 4. Vector Database Architecture

```text id="vdb16"
Document
 ↓
Embedding
 ↓
Vector Database
```

---

Question:

```text id="vdb17"
Question
 ↓
Embedding
 ↓
Vector Search
 ↓
Top K Chunks
```

---

# 5. How Similarity Search Works

Suppose:

Question:

```text id="vdb18"
What does P1 mean?
```

---

Embedding:

```text id="vdb19"
Vector Q
```

---

Database:

```text id="vdb20"
Vector A
Vector B
Vector C
...
```

---

Search:

```text id="vdb21"
Find nearest vectors
```

---

Output:

```text id="vdb22"
Top K documents
```

---

# 6. Why Scale Becomes Hard

Example:

```text id="vdb23"
1,000,000 chunks
```

---

Brute Force:

```text id="vdb24"
Compare every vector
```

---

Too expensive.

---

Need:

```text id="vdb25"
ANN
```

---

# 7. What is ANN?

ANN =

```text id="vdb26"
Approximate Nearest Neighbor
```

---

Idea:

```text id="vdb27"
Find very good matches
without checking everything.
```

---

Example

Google Maps:

```text id="vdb28"
Nearby restaurants
```

---

Does not check:

```text id="vdb29"
Every location on Earth
```

---

ANN works similarly.

---

# Why ANN Matters

Without ANN:

```text id="vdb30"
Slow Retrieval
```

---

With ANN:

```text id="vdb31"
Milliseconds
```

---

# 8. Chroma

Current RetailOps database.

---

Example:

```python id="vdb32"
from langchain_chroma import Chroma
```

---

Why Chroma?

Pros:

```text id="vdb33"
Free
Local
Easy Setup
```

---

Cons:

```text id="vdb34"
Not ideal for massive scale
```

---

RetailOps:

```text id="vdb35"
Uses Chroma
```

---

# 9. FAISS

Facebook AI Similarity Search.

---

Example:

```text id="vdb36"
FAISS
```

---

Pros:

```text id="vdb37"
Very Fast
Local
Mature
```

---

Cons:

```text id="vdb38"
Less convenient persistence
```

---

Used in:

```text id="vdb39"
Research
Local Search
```

---

# 10. Pinecone

Managed vector database.

---

Pros:

```text id="vdb40"
Cloud Native
Scalable
Managed
```

---

Cons:

```text id="vdb41"
Paid
```

---

Used in:

```text id="vdb42"
Production SaaS
```

---

# 11. Qdrant

Modern open-source vector database.

---

Pros:

```text id="vdb43"
Metadata Filtering
Performance
Open Source
```

---

Cons:

```text id="vdb44"
More Infrastructure
```

---

Popular for:

```text id="vdb45"
Enterprise RAG
```

---

# 12. Weaviate

Another enterprise vector database.

---

Pros:

```text id="vdb46"
Strong Filtering
Enterprise Features
```

---

Cons:

```text id="vdb47"
More Complex
```

---

# 13. Metadata

One of the most important features.

---

Example:

```python id="vdb48"
metadata={
    "source":"hr_policy.txt",
    "department":"HR"
}
```

---

Why?

Supports:

```text id="vdb49"
Filtering
Security
Access Control
```

---

# Example

User:

```text id="vdb50"
Store Associate
```

---

Filter:

```text id="vdb51"
department != HR
```

---

HR docs excluded.

---

# This Is Enterprise RAG

Metadata filtering is foundational.

---

# 14. Metadata Filtering

Example:

```python id="vdb52"
filter={
    "department":"HR"
}
```

---

Search only:

```text id="vdb53"
HR documents
```

---

RetailOps:

```text id="vdb54"
Future Enterprise Upgrade
```

---

# 15. Persistence

Without persistence:

```text id="vdb55"
Restart App
 ↓
Index Lost
```

---

With persistence:

```text id="vdb56"
Index Reused
```

---

RetailOps:

```python id="vdb57"
persist_directory=
vectorstore/chroma
```

---

# 16. Vector Database vs Retriever

Common confusion.

---

Vector Database:

```text id="vdb58"
Stores Vectors
```

---

Retriever:

```text id="vdb59"
Uses Database
```

---

Example:

```text id="vdb60"
Question
 ↓
Retriever
 ↓
Chroma
 ↓
Results
```

---

# Difference

Database:

```text id="vdb61"
Storage Layer
```

---

Retriever:

```text id="vdb62"
Access Layer
```

---

# 17. Production Best Practices

## Use Persistence

Avoid rebuilding indexes.

---

## Store Metadata

Always include:

```text id="vdb63"
Source
Version
Department
```

---

## Evaluate Retrieval

Never assume:

```text id="vdb64"
Top K
```

is correct.

---

## Use Hybrid Search

Combine:

```text id="vdb65"
Embeddings
+
BM25
```

---

## Add Reranking

Use:

```text id="vdb66"
Cross Encoder
```

---

# 18. RetailOps Implementation

Current:

```text id="vdb67"
Chroma
```

---

Files:

```text id="vdb68"
app/vectorstore.py
```

---

Pipeline:

```text id="vdb69"
Documents
 ↓
Embeddings
 ↓
Chroma
 ↓
Retriever
```

---

# 19. Common Mistakes

## Mistake 1

Confusing retrievers and vector databases.

---

## Mistake 2

No metadata.

---

## Mistake 3

No persistence.

---

## Mistake 4

Using vector search for exact IDs only.

---

## Mistake 5

Ignoring retrieval evaluation.

---

# 20. Interview Questions

### What is a Vector Database?

A database optimized for storing and searching embeddings.

---

### Why use a Vector Database?

Efficient similarity search.

---

### Why not use PostgreSQL?

Brute-force similarity search does not scale well.

---

### What is ANN?

Approximate Nearest Neighbor search.

---

### Chroma vs Pinecone?

Chroma:

```text id="vdb70"
Local
```

Pinecone:

```text id="vdb71"
Managed Cloud
```

---

### Database vs Retriever?

Database:

```text id="vdb72"
Storage
```

Retriever:

```text id="vdb73"
Access
```

---

### Why is metadata important?

Filtering, security, source attribution.

---

# Summary

Vector Databases store embeddings and make semantic retrieval efficient.

RetailOps currently uses:

```text id="vdb74"
Chroma
```

to support:

```text id="vdb75"
Semantic Search
Hybrid Search
RAG
```

and later can evolve toward:

```text id="vdb76"
Qdrant
Pinecone
Weaviate
```

for enterprise-scale deployments.

The next document:

```text id="vdb77"
13_retrievers.md
```

explains how LangChain retrieves relevant chunks from vector databases and why retrieval quality is the heart of a RAG system.
