# 16 - Semantic Chunking

# Learning Objectives

After completing this document, you should understand:

* What Semantic Chunking is
* Why Semantic Chunking exists
* Semantic Chunking vs Recursive Chunking
* How Semantic Chunking works
* Topic Boundaries
* Embedding-Based Splitting
* Chunk Quality
* Semantic Chunking Tradeoffs
* Production Best Practices
* RetailOps Implementation

---

# 1. What is Semantic Chunking?

## Definition

Semantic Chunking splits documents based on:

```text id="sc1"
Meaning
```

instead of:

```text id="sc2"
Character Count
```

or:

```text id="sc3"
Fixed Size Rules
```

---

# Why Does It Exist?

Traditional chunking asks:

```text id="sc4"
Where should 300 characters end?
```

---

Semantic chunking asks:

```text id="sc5"
Where does the topic change?
```

---

This is a fundamentally different approach.

---

# 2. Why Chunk Quality Matters

Most people focus on:

```text id="sc6"
LLMs
Embeddings
Retrievers
```

---

But retrieval quality depends heavily on:

```text id="sc7"
Chunk Quality
```

---

Rule:

```text id="sc8"
Bad Chunks
↓
Bad Retrieval
↓
Bad Answers
```

---

Even with:

```text id="sc9"
Excellent Models
```

---

# 3. Example Problem

Document:

```text id="sc10"
Vacation Policy

Employees receive 18 vacation days.

Managers approve requests.

--------------------------------

Incident Management

P1 means full store outage.

Managers notify IT immediately.
```

---

Recursive splitter may create:

```text id="sc11"
Chunk A

Employees receive 18 vacation days.

Managers approve requests.

Incident Management
```

---

Topics mixed.

---

# Problem

Retriever now sees:

```text id="sc12"
Vacation
+
Incident
```

inside the same chunk.

---

Semantic meaning becomes noisy.

---

# 4. Semantic Chunking Solution

Semantic chunker detects:

```text id="sc13"
Topic Boundary
```

between:

```text id="sc14"
Vacation Policy
```

and

```text id="sc15"
Incident Management
```

---

Output:

```text id="sc16"
Chunk A
Vacation Policy
```

---

```text id="sc17"
Chunk B
Incident Management
```

---

Much cleaner.

---

# 5. How Semantic Chunking Works

High-level process:

```text id="sc18"
Sentence
 ↓
Embedding
 ↓
Similarity Comparison
 ↓
Topic Shift Detection
 ↓
Chunk Creation
```

---

Example

Sentence A:

```text id="sc19"
Employees receive vacation days.
```

---

Sentence B:

```text id="sc20"
Managers approve vacation requests.
```

---

Similarity:

```text id="sc21"
0.92
```

Same topic.

---

Sentence C:

```text id="sc22"
P1 means full store outage.
```

---

Similarity:

```text id="sc23"
0.18
```

Topic changed.

---

Create new chunk.

---

# 6. Visual Representation

Document:

```text id="sc24"
Vacation
Vacation
Vacation
Incident
Incident
Incident
```

---

Semantic Chunking:

```text id="sc25"
Chunk A
Vacation
Vacation
Vacation
```

---

```text id="sc26"
Chunk B
Incident
Incident
Incident
```

---

# Why This Matters

Chunks become:

```text id="sc27"
Single Topic
```

instead of:

```text id="sc28"
Mixed Topics
```

---

# 7. Recursive vs Semantic Chunking

## Recursive Chunking

Uses:

```text id="sc29"
Characters
Paragraphs
Separators
```

---

Question:

```text id="sc30"
How large should chunk be?
```

---

# Pros

```text id="sc31"
Fast
Simple
Stable
```

---

# Cons

```text id="sc32"
Not Meaning Aware
```

---

## Semantic Chunking

Uses:

```text id="sc33"
Embeddings
Similarity
Topic Boundaries
```

---

Question:

```text id="sc34"
Where does meaning change?
```

---

# Pros

```text id="sc35"
Cleaner Chunks
Better Retrieval
```

---

# Cons

```text id="sc36"
Slower
More Complex
```

---

# 8. Why Semantic Chunking Improves Retrieval

Question:

```text id="sc37"
What does P1 mean?
```

---

Semantic chunk:

```text id="sc38"
Incident Management Section
```

---

High relevance.

---

Mixed chunk:

```text id="sc39"
Vacation Policy
+
Incident Management
```

---

Lower relevance.

---

Therefore:

```text id="sc40"
Better Chunks
↓
Better Embeddings
↓
Better Retrieval
```

---

# 9. Semantic Chunking in LangChain

Example:

```python id="sc41"
from langchain_experimental.text_splitter import (
    SemanticChunker
)
```

---

Example:

```python id="sc42"
splitter = SemanticChunker(
    embeddings
)
```

---

Then:

```python id="sc43"
chunks = splitter.split_documents(
    docs
)
```

---

# RetailOps

Added as:

```text id="sc44"
Production Option
```

---

# 10. Semantic Chunking vs Parent-Child

Common confusion.

---

# Semantic Chunking

Goal:

```text id="sc45"
Better Search Chunks
```

---

# Parent-Child

Goal:

```text id="sc46"
Better Answer Context
```

---

# Difference

Semantic Chunking:

```text id="sc47"
Improve Retrieval Precision
```

---

Parent-Child:

```text id="sc48"
Improve Context Completeness
```

---

# Which Comes First?

Usually:

```text id="sc49"
Semantic Chunking
```

---

Because:

```text id="sc50"
Retrieval Quality
```

is more important.

---

# 11. Semantic Chunking vs Multi Query

Semantic Chunking:

```text id="sc51"
Improve Chunks
```

---

Multi Query:

```text id="sc52"
Improve Questions
```

---

Together:

```text id="sc53"
Better Questions
+
Better Chunks
```

---

# 12. Semantic Chunking vs Reranking

Semantic Chunking:

```text id="sc54"
Before Retrieval
```

---

Reranking:

```text id="sc55"
After Retrieval
```

---

Both improve:

```text id="sc56"
Retrieval Quality
```

---

Different stages.

---

# 13. RetailOps Evolution

Initial:

```text id="sc57"
RecursiveCharacterTextSplitter
```

---

Later:

```text id="sc58"
Semantic Chunking
```

---

Reason:

```text id="sc59"
Higher Retrieval Quality
```

---

# 14. Production Best Practices

## Start Simple

Begin with:

```text id="sc60"
Recursive Splitter
```

---

## Measure Improvements

Compare:

```text id="sc61"
Recursive
vs
Semantic
```

using evaluation.

---

## Keep Metadata

Store:

```text id="sc62"
Source
Section
Parent ID
```

---

## Track Chunk Counts

Watch for:

```text id="sc63"
Too Many Tiny Chunks
```

---

## Reindex After Changes

New chunking strategy:

```text id="sc64"
Requires Reindexing
```

---

# 15. Common Mistakes

## Mistake 1

Assuming semantic chunking is always better.

---

## Mistake 2

Never evaluating retrieval quality.

---

## Mistake 3

Using semantic chunking on tiny datasets.

---

## Mistake 4

Ignoring indexing costs.

---

## Mistake 5

Changing chunking without rebuilding vectors.

---

# 16. Interview Questions

### What is Semantic Chunking?

Chunking based on meaning rather than fixed size.

---

### Why use Semantic Chunking?

To improve retrieval quality.

---

### Recursive vs Semantic Chunking?

Recursive:

```text id="sc65"
Structure-Based
```

Semantic:

```text id="sc66"
Meaning-Based
```

---

### Why can Semantic Chunking improve RAG?

Because chunk quality strongly affects retrieval quality.

---

### Semantic Chunking vs Parent-Child?

Semantic:

```text id="sc67"
Better Search Units
```

Parent-Child:

```text id="sc68"
Better Context Units
```

---

### What must happen after changing chunking?

Rebuild embeddings and reindex.

---

# Summary

Semantic Chunking is a major retrieval-quality improvement.

Instead of splitting based on:

```text id="sc69"
Characters
```

it splits based on:

```text id="sc70"
Meaning
```

leading to:

```text id="sc71"
Cleaner Chunks
Better Retrieval
Better RAG Answers
```

RetailOps evolved from:

```text id="sc72"
Recursive Chunking
```

to:

```text id="sc73"
Semantic Chunking
```

to improve retrieval quality before introducing more advanced techniques such as parent-child retrieval and contextual compression.

The next document:

```text id="sc74"
17_hybrid_search.md
```

covers one of the most important production RAG patterns: combining vector search and BM25 retrieval.
