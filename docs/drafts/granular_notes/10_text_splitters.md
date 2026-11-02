# 10 - Text Splitters (Chunking)

# Learning Objectives

After completing this document, you should understand:

* What Chunking is
* Why Chunking exists
* Why not embed entire documents
* Chunk Size
* Chunk Overlap
* RecursiveCharacterTextSplitter
* Semantic Chunking
* Parent-Child Retrieval
* Chunking Tradeoffs
* Chunking Strategies
* Production Best Practices
* RetailOps Implementation

---

# 1. What is Chunking?

## Definition

Chunking is the process of breaking large documents into smaller pieces before generating embeddings.

---

# Why Does Chunking Exist?

LLMs and embedding models work better with:

```text id="ts1"
Small Focused Context
```

than:

```text id="ts2"
Huge Documents
```

---

Example

Document:

```text id="ts3"
100-page employee handbook
```

---

Without chunking:

```text id="ts4"
Entire handbook
 ↓
One embedding
```

---

Problem:

```text id="ts5"
Poor retrieval quality
```

---

With chunking:

```text id="ts6"
Handbook
 ↓
Chunk 1
Chunk 2
Chunk 3
...
```

---

Now retrieval becomes much more precise.

---

# 2. Why Not Embed Entire Documents?

Suppose:

```text id="ts7"
HR Policy
```

contains:

```text id="ts8"
Vacation Policy
Remote Work Policy
Dress Code
Benefits
```

---

Question:

```text id="ts9"
How many vacation days do employees receive?
```

---

Entire-document embedding contains:

```text id="ts10"
Everything
```

---

Retriever sees:

```text id="ts11"
Mixed meaning
```

---

Chunking creates:

```text id="ts12"
Vacation Chunk
```

which is much more relevant.

---

# 3. Chunking Architecture

```text id="ts13"
Document
 ↓
Chunking
 ↓
Chunks
 ↓
Embeddings
 ↓
Vector Store
```

---

Important:

```text id="ts14"
Chunk Quality
=
Retrieval Quality
```

---

# 4. Chunk Size

## Definition

Maximum size of each chunk.

---

Example:

```python id="ts15"
chunk_size=300
```

---

# Small Chunks

Example:

```text id="ts16"
100 tokens
```

---

Pros:

```text id="ts17"
High Precision
```

---

Cons:

```text id="ts18"
Less Context
```

---

# Large Chunks

Example:

```text id="ts19"
1000 tokens
```

---

Pros:

```text id="ts20"
More Context
```

---

Cons:

```text id="ts21"
Lower Precision
```

---

# Tradeoff

```text id="ts22"
Small
=
Precision

Large
=
Context
```

---

# 5. Chunk Overlap

## Definition

Shared content between adjacent chunks.

---

Example:

```python id="ts23"
chunk_overlap=50
```

---

Without Overlap

Chunk 1:

```text id="ts24"
Employees receive 18 vacation
```

---

Chunk 2:

```text id="ts25"
days after 90 days employment
```

---

Meaning split.

---

With Overlap

Chunk 1:

```text id="ts26"
Employees receive 18 vacation days
```

---

Chunk 2:

```text id="ts27"
18 vacation days after 90 days
```

---

Meaning preserved.

---

# Why Use Overlap?

```text id="ts28"
Context Preservation
```

---

# Cons

Too much overlap:

```text id="ts29"
More Storage
More Duplicate Context
```

---

# 6. RecursiveCharacterTextSplitter

The most common starter splitter.

---

RetailOps started with:

```python id="ts30"
RecursiveCharacterTextSplitter
```

---

# How It Works

Splits using:

```text id="ts31"
Paragraphs
Sentences
Words
Characters
```

---

Example:

```python id="ts32"
RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50
)
```

---

# Why It's Popular

Pros:

```text id="ts33"
Simple
Fast
Stable
```

---

Cons:

```text id="ts34"
Not Meaning Aware
```

---

# Example Problem

Document:

```text id="ts35"
Vacation Policy

Employees receive 18 days.

Incident Policy

P1 means full outage.
```

---

Recursive splitting may create:

```text id="ts36"
Chunk:
Employees receive 18 days.
Incident Policy
```

---

Two topics mixed.

---

# 7. Semantic Chunking

## Definition

Chunking based on meaning instead of characters.

---

Question:

```text id="ts37"
Where does the topic change?
```

---

instead of:

```text id="ts38"
Where do 300 characters end?
```

---

# Example

Document:

```text id="ts39"
Vacation Policy

Employees receive 18 days.

Managers approve requests.

--------------------------------

Incident Policy

P1 means full outage.
```

---

Semantic Chunker creates:

```text id="ts40"
Chunk A
Vacation Policy
```

---

```text id="ts41"
Chunk B
Incident Policy
```

---

Much cleaner.

---

# How It Works

```text id="ts42"
Sentence
 ↓
Embedding
 ↓
Compare Similarity
 ↓
Detect Topic Shift
 ↓
Create Chunk
```

---

# Pros

```text id="ts43"
Better Retrieval
Cleaner Context
```

---

# Cons

```text id="ts44"
Slower Indexing
More Complex
```

---

# RetailOps Upgrade

We later added:

```text id="ts45"
Semantic Chunking
```

as a production option.

---

# 8. Parent-Child Retrieval

## Definition

Use:

```text id="ts46"
Small Child Chunks
```

for retrieval and:

```text id="ts47"
Larger Parent Chunks
```

for answering.

---

# Why?

Search prefers:

```text id="ts48"
Small Chunks
```

---

Answering prefers:

```text id="ts49"
More Context
```

---

# Example

Child:

```text id="ts50"
P1 means full store outage.
```

---

Parent:

```text id="ts51"
Entire Incident Priority Section
```

---

Retriever finds:

```text id="ts52"
Child
```

---

LLM receives:

```text id="ts53"
Parent
```

---

# Pros

```text id="ts54"
Better Context
```

---

# Cons

```text id="ts55"
More Tokens
```

---

# RetailOps

Implemented as:

```text id="ts56"
Learning Pattern
```

not default path.

---

# 9. Chunking Strategies

## Fixed Size

Example:

```text id="ts57"
300 characters
```

---

Pros:

```text id="ts58"
Simple
```

---

Cons:

```text id="ts59"
Breaks Meaning
```

---

# Recursive

Example:

```text id="ts60"
RecursiveCharacterTextSplitter
```

---

Pros:

```text id="ts61"
Balanced
```

---

Cons:

```text id="ts62"
Not Semantic
```

---

# Semantic

Example:

```text id="ts63"
SemanticChunker
```

---

Pros:

```text id="ts64"
Meaning Aware
```

---

Cons:

```text id="ts65"
More Expensive
```

---

# Parent-Child

Example:

```text id="ts66"
Search Small
Answer Large
```

---

Pros:

```text id="ts67"
Best of Both
```

---

Cons:

```text id="ts68"
More Complexity
```

---

# 10. Chunking vs Retrieval

Very important.

---

Chunking:

```text id="ts69"
Create Search Units
```

---

Retriever:

```text id="ts70"
Find Search Units
```

---

Bad chunking:

```text id="ts71"
Bad Retrieval
```

---

Good chunking:

```text id="ts72"
Good Retrieval
```

---

# Rule

Retriever quality cannot fully compensate for poor chunking.

---

# 11. Production Best Practices

## Start Simple

Use:

```text id="ts73"
RecursiveCharacterTextSplitter
```

first.

---

## Evaluate

Compare:

```text id="ts74"
Recursive
vs
Semantic
```

---

## Keep Chunks Focused

One topic per chunk.

---

## Use Metadata

Store:

```text id="ts75"
Source
Section
Parent ID
```

---

## Track Chunking Strategy

Include in evaluation reports.

---

# 12. RetailOps Implementation

Current Options:

```text id="ts76"
Recursive Chunking
Semantic Chunking
```

---

Future:

```text id="ts77"
Parent Child
Compression
```

---

Files:

```text id="ts78"
app/rag.py
app/parent_child.py
```

---

# 13. Common Mistakes

## Mistake 1

Huge chunks.

---

## Mistake 2

Tiny chunks.

---

## Mistake 3

No overlap.

---

## Mistake 4

Ignoring chunk evaluation.

---

## Mistake 5

Assuming retrievers fix bad chunking.

---

# 14. Interview Questions

### What is chunking?

Breaking documents into smaller pieces before embedding.

---

### Why chunk documents?

Improve retrieval precision.

---

### What is chunk overlap?

Shared content between adjacent chunks.

---

### Why use chunk overlap?

Preserve context.

---

### Recursive vs Semantic Chunking?

Recursive:

```text id="ts79"
Structure Based
```

Semantic:

```text id="ts80"
Meaning Based
```

---

### What is Parent-Child Retrieval?

Small chunks for retrieval, larger chunks for answering.

---

### Why is chunking important?

Retrieval quality depends heavily on chunk quality.

---

# Summary

Chunking is one of the most important parts of a RAG system.

It determines:

```text id="ts81"
Retrieval Quality
Context Quality
Answer Quality
```

RetailOps evolved from:

```text id="ts82"
Recursive Chunking
```

to:

```text id="ts83"
Semantic Chunking
```

and explored:

```text id="ts84"
Parent-Child Retrieval
```

to understand production retrieval strategies.

The next document:

```text id="ts85"
11_embeddings.md
```

covers embeddings, vector representations, similarity search, and how semantic retrieval actually works.
