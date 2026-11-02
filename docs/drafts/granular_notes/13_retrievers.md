# 13 - Retrievers

# Learning Objectives

After completing this document, you should understand:

* What a Retriever is
* Why Retrievers exist
* Retriever Architecture
* Retriever vs Vector Database
* Retriever vs Loader
* Similarity Search
* MMR Retrieval
* Hybrid Retrieval
* Custom Retrievers
* Retrieval Quality
* Production Best Practices
* RetailOps Implementation

---

# 1. What is a Retriever?

## Definition

A Retriever is a component responsible for finding the most relevant documents for a query.

Think of it as:

```text id="ret1"
Question
 ↓
Retriever
 ↓
Relevant Documents
```

---

# Why Do Retrievers Exist?

Suppose:

```text id="ret2"
100,000 document chunks
```

stored in Chroma.

---

Question:

```text id="ret3"
How many vacation days do employees receive?
```

---

We need:

```text id="ret4"
Only relevant chunks
```

---

Retriever finds them.

---

# Simple Explanation

Retriever answers:

```text id="ret5"
Which chunks should the LLM see?
```

---

This is one of the most important decisions in a RAG system.

---

# 2. Retriever Architecture

```text id="ret6"
Question
 ↓
Embedding
 ↓
Retriever
 ↓
Top K Chunks
```

---

Those chunks become:

```text id="ret7"
Context
```

for the LLM.

---

# Why Retrieval Matters

Bad retrieval:

```text id="ret8"
Bad Answer
```

---

Good retrieval:

```text id="ret9"
Good Answer
```

---

Even with:

```text id="ret10"
Excellent LLM
```

---

# Rule

Retrieval quality often matters more than model quality.

---

# 3. Retriever vs Loader

Very common interview question.

---

# Loader

Purpose:

```text id="ret11"
Read Documents
```

---

Example:

```text id="ret12"
PDF
 ↓
Loader
 ↓
Document
```

---

# Retriever

Purpose:

```text id="ret13"
Find Documents
```

---

Example:

```text id="ret14"
Question
 ↓
Retriever
 ↓
Relevant Chunks
```

---

# Difference

Loader:

```text id="ret15"
Ingestion Time
```

---

Retriever:

```text id="ret16"
Query Time
```

---

# 4. Retriever vs Vector Database

Another common confusion.

---

Vector Database:

```text id="ret17"
Stores Embeddings
```

---

Retriever:

```text id="ret18"
Uses Database
```

---

Architecture:

```text id="ret19"
Retriever
 ↓
Chroma
 ↓
Results
```

---

Database:

```text id="ret20"
Storage Layer
```

---

Retriever:

```text id="ret21"
Access Layer
```

---

# 5. LangChain Retriever Interface

Most retrievers support:

```python id="ret22"
invoke()
```

---

Example:

```python id="ret23"
docs = retriever.invoke(
    "What does P1 mean?"
)
```

---

Output:

```python id="ret24"
list[Document]
```

---

# Why This Matters

Every retriever has a common interface.

---

Examples:

```text id="ret25"
Chroma Retriever
FAISS Retriever
Custom Retriever
```

---

All support:

```python id="ret26"
invoke()
```

---

# 6. Similarity Search

Default retrieval strategy.

---

Question:

```text id="ret27"
How much PTO do employees receive?
```

---

Embedding:

```text id="ret28"
Vector Q
```

---

Retriever:

```text id="ret29"
Find nearest vectors
```

---

Output:

```text id="ret30"
Top K Similar Chunks
```

---

# Pros

```text id="ret31"
Simple
Fast
```

---

# Cons

May return:

```text id="ret32"
Near Duplicates
```

---

# Example

Results:

```text id="ret33"
Vacation Policy Chunk A
Vacation Policy Chunk B
Vacation Policy Chunk C
```

---

Very similar.

---

# 7. MMR Retrieval

MMR =

```text id="ret34"
Maximum Marginal Relevance
```

---

Purpose:

```text id="ret35"
Relevance
+
Diversity
```

---

# Example

Question:

```text id="ret36"
Tell me about vacation policy.
```

---

Similarity Search:

```text id="ret37"
Vacation Chunk A
Vacation Chunk B
Vacation Chunk C
```

---

MMR:

```text id="ret38"
Vacation Chunk A
Approval Process Chunk
PTO Rules Chunk
```

---

More useful.

---

# Why RetailOps Uses MMR

Current:

```python id="ret39"
search_type="mmr"
```

---

Reason:

```text id="ret40"
Better Context Diversity
```

---

# 8. Hybrid Retrieval

One of the most important production concepts.

---

Combines:

```text id="ret41"
Semantic Search
+
Keyword Search
```

---

Question:

```text id="ret42"
What does P1 mean?
```

---

Semantic Search:

```text id="ret43"
Meaning
```

---

Keyword Search:

```text id="ret44"
Exact Term
```

---

Hybrid:

```text id="ret45"
Best of Both
```

---

RetailOps:

```text id="ret46"
Vector Search
+
BM25
```

---

# Why Hybrid Retrieval?

Semantic search struggles with:

```text id="ret47"
SKU
IDs
Dates
Codes
```

---

Examples:

```text id="ret48"
DENIM-4421
INC-1001
P1
```

---

Keyword search handles these well.

---

# 9. BM25 Retrieval

Industry-standard keyword retrieval.

---

Example:

```text id="ret49"
P1
```

---

BM25 finds:

```text id="ret50"
P1 Documents
```

---

Better than:

```text id="ret51"
term in content
```

matching.

---

RetailOps:

```text id="ret52"
BM25Retriever
```

---

# 10. Multi-Query Retrieval

Generate multiple search queries.

---

Question:

```text id="ret53"
How much PTO do employees get?
```

---

Generated:

```text id="ret54"
Vacation Policy
Paid Time Off Policy
Employee Leave Policy
```

---

Retrieve for each.

---

Merge results.

---

Why?

```text id="ret55"
Improve Recall
```

---

# RetailOps

Current:

```text id="ret56"
Multi Query Retrieval
```

supported.

---

# 11. Candidate Retrieval vs Reranking

Important concept.

---

# Retriever

Find candidates.

---

Example:

```text id="ret57"
Top 20 Chunks
```

---

# Reranker

Sort candidates.

---

Example:

```text id="ret58"
Top 5 Chunks
```

---

Architecture:

```text id="ret59"
Retriever
 ↓
Candidates
 ↓
Cross Encoder
 ↓
Final Chunks
```

---

# Difference

Retriever:

```text id="ret60"
Recall
```

---

Reranker:

```text id="ret61"
Precision
```

---

# 12. Retrieval Quality

Question:

```text id="ret62"
What determines RAG quality?
```

---

Most important factors:

```text id="ret63"
Chunking
Embeddings
Retriever
Reranker
```

---

Not:

```text id="ret64"
Prompt
```

alone.

---

# Retrieval Rule

```text id="ret65"
Bad Retrieval
=
Bad Answer
```

---

# 13. Custom Retrievers

Sometimes built manually.

---

RetailOps:

```python id="ret66"
HybridRetriever
```

---

Combines:

```text id="ret67"
Vector Search
BM25
Reranking
```

---

This is a custom retriever.

---

# 14. Production Retrieval Architecture

Strong production pattern:

```text id="ret68"
Question
 ↓
Multi Query
 ↓
Vector Search
 ↓
BM25
 ↓
Merge
 ↓
Cross Encoder
 ↓
Top K
 ↓
LLM
```

---

RetailOps is approaching this architecture.

---

# 15. Production Best Practices

## Evaluate Retrieval

Use:

```text id="ret69"
Golden Dataset
```

---

## Use Hybrid Search

Prefer:

```text id="ret70"
Vector + BM25
```

---

## Add Reranking

Use:

```text id="ret71"
Cross Encoder
```

---

## Track Sources

Always.

---

## Log Retrieval

Track:

```text id="ret72"
Source
Score
Latency
```

---

# 16. RetailOps Implementation

Current:

```text id="ret73"
Hybrid Retriever
```

---

Components:

```text id="ret74"
Vector Search
BM25
Cross Encoder
Multi Query
```

---

Files:

```text id="ret75"
app/hybrid_retriever.py
app/bm25_retriever.py
app/multi_query.py
app/reranker.py
```

---

# 17. Common Mistakes

## Mistake 1

Using vector search only.

---

## Mistake 2

Ignoring retrieval evaluation.

---

## Mistake 3

Too many retrieved chunks.

---

## Mistake 4

No reranking.

---

## Mistake 5

Blaming the LLM for retrieval failures.

---

# 18. Interview Questions

### What is a Retriever?

A component that finds relevant documents for a query.

---

### Retriever vs Loader?

Loader:

```text id="ret76"
Read Documents
```

Retriever:

```text id="ret77"
Find Documents
```

---

### Retriever vs Vector Database?

Database:

```text id="ret78"
Stores Vectors
```

Retriever:

```text id="ret79"
Uses Vectors
```

---

### Why use MMR?

To balance relevance and diversity.

---

### Why use Hybrid Retrieval?

To combine semantic and exact-match search.

---

### Retriever vs Reranker?

Retriever:

```text id="ret80"
Recall
```

Reranker:

```text id="ret81"
Precision
```

---

# Summary

Retrievers are the heart of a RAG system.

They determine:

```text id="ret82"
What Context
The LLM Sees
```

RetailOps evolved from:

```text id="ret83"
Simple Retrieval
```

to:

```text id="ret84"
Hybrid Retrieval
BM25
Cross Encoder
Multi Query
```

to improve retrieval quality systematically.

The next document:

```text id="ret85"
14_similarity_search.md
```

will dive deeper into similarity search, vector distance metrics, cosine similarity, and retrieval scoring.
