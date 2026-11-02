# 05 - LangChain RAG Implementation

# Learning Objectives

After completing this document, you should understand:

* How RAG is implemented in LangChain
* Document Loaders
* Text Splitters
* Embedding Models
* Vector Stores
* Chroma Integration
* Retrievers
* Similarity Search
* MMR Search
* History-Aware Retrieval
* RAG Chains
* Structured RAG Output
* Source Attribution
* RAG Evaluation
* RetailOps RAG Architecture
* Production RAG Design Patterns

---

# 1. From RAG Theory to RAG Implementation

In the previous document:

```text id="e72i49"
04_rag_fundamentals.md
```

we learned:

```text id="ndcikv"
What RAG is
Why RAG exists
Embeddings
Vector Databases
Retrieval
```

Now we implement those concepts using LangChain.

---

# High-Level Architecture

```text id="70j6fu"
Documents
 ↓
Loader
 ↓
Splitter
 ↓
Embeddings
 ↓
Vector Store
 ↓
Retriever
 ↓
Prompt
 ↓
LLM
 ↓
Answer
```

---

# RetailOps Architecture

```text id="9nws8l"
HR Policy
Store SOP
Returns Policy
IT KB
        ↓
Document Loader
        ↓
Text Splitter
        ↓
Embeddings
        ↓
Chroma
        ↓
Retriever
        ↓
RAG Prompt
        ↓
Groq
        ↓
Structured Output
```

---

# 2. Document Loaders

## Definition

Document Loaders convert files into LangChain Documents.

---

## Input

```text id="r76zv2"
TXT
PDF
HTML
DOCX
CSV
```

---

## Output

```python id="7njlzh"
Document(
    page_content="...",
    metadata={}
)
```

---

## Why Use Document Loaders?

LLMs cannot directly read files.

They require text.

---

## Example

```python id="q2nyu9"
from langchain_community.document_loaders import (
    TextLoader
)

loader = TextLoader(
    "data/hr_policy.txt"
)

docs = loader.load()
```

---

## RetailOps Implementation

File:

```text id="uyjybd"
app/rag.py
```

Function:

```python id="r84z1k"
load_documents()
```

---

## Supported Future Formats

We can later add:

```text id="3av62t"
PDF
Confluence
Jira
SharePoint
GitHub
```

---

# 3. LangChain Documents

## Definition

A Document is LangChain's standard knowledge container.

---

## Structure

```python id="zjlwmv"
Document(
    page_content="...",
    metadata={
        "source":"..."
    }
)
```

---

## Why Metadata Matters

Metadata enables:

```text id="lvg04r"
Source Attribution
Filtering
Citations
Auditing
```

---

## Example

```python id="67sp0m"
doc.metadata["source"]
```

Output:

```text id="d8n6mk"
hr_policy.txt
```

---

# 4. Text Splitters

## Definition

Break large documents into smaller chunks.

---

## Why?

Embedding an entire document:

```text id="sdw43l"
Poor Retrieval
```

---

Instead:

```text id="v8r7or"
Document
 ↓
Chunk 1
Chunk 2
Chunk 3
```

---

## RetailOps Splitter

```python id="fj7pj4"
RecursiveCharacterTextSplitter
```

---

## Example

```python id="0t5o4h"
splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50
)
```

---

# Chunk Size

## Definition

Maximum chunk length.

---

## Small Chunks

Pros:

```text id="st3e6f"
More Precise
```

Cons:

```text id="h9qkmb"
Less Context
```

---

## Large Chunks

Pros:

```text id="y7jtm6"
More Context
```

Cons:

```text id="1w8x2o"
Less Precise
```

---

## Production Recommendation

```python id="x0bgsq"
300-1000
```

depending on document type.

---

# Chunk Overlap

## Definition

Shared text between chunks.

---

Example:

```python id="03q64v"
chunk_overlap=50
```

---

## Why?

Preserves context across chunk boundaries.

---

## Benefits

```text id="e5lsr3"
Better Retrieval
Reduced Context Loss
```

---

# 5. Embedding Models

## Definition

Convert text into vectors.

---

## RetailOps Model

```text id="b6fcpk"
all-MiniLM-L6-v2
```

---

## Why This Model?

Pros:

```text id="3lcx6z"
Free
Fast
Local
Good Semantic Quality
```

---

Cons:

```text id="g7wq1m"
Smaller than enterprise embedding models
```

---

## Example

```python id="x1zgl4"
embeddings.embed_query(
    "vacation policy"
)
```

Output:

```text id="jlwm4k"
[0.22, -0.14, ...]
```

---

# 6. Vector Stores

## Definition

Store embeddings and perform similarity search.

---

## RetailOps Choice

```text id="kg08kx"
Chroma
```

---

## Why Chroma?

Pros:

```text id="pjlwm2"
Free
Local
Easy Setup
```

---

Cons:

```text id="jlwm2z"
Not ideal for massive scale
```

---

## Example

```python id="jlwm8o"
db = Chroma.from_documents(
    chunks,
    embeddings
)
```

---

# Persistence

## Why Persist?

Without persistence:

```text id="jlwm1p"
Rebuild embeddings every startup
```

---

With persistence:

```text id="jlwm6c"
Reuse vector database
```

---

## RetailOps

```text id="jlwm6m"
vectorstore/
```

stores Chroma data.

---

# 7. Retrievers

## Definition

Components that retrieve relevant documents.

---

## Why Use Retrievers?

Abstraction.

Instead of:

```python id="jlwmx1"
db.similarity_search(...)
```

Use:

```python id="jlwmx2"
retriever.invoke(...)
```

---

## Benefits

```text id="jlwmx3"
Reusable
Database Independent
```

---

# RetailOps Retriever

```python id="jlwmx4"
db.as_retriever(...)
```

---

# 8. Similarity Search

## Definition

Retrieve most similar chunks.

---

Example:

Query:

```text id="jlwmx5"
vacation days
```

---

Returns:

```text id="jlwmx6"
HR Policy Chunks
```

---

## Pros

```text id="jlwmx7"
Simple
Fast
```

---

## Cons

May return duplicate information.

---

# 9. MMR Retrieval

Maximum Marginal Relevance

---

## Definition

Balances:

```text id="jlwmx8"
Relevance
+
Diversity
```

---

## Similarity Search

May return:

```text id="jlwmx9"
Chunk A
Chunk B
Chunk C
```

all nearly identical.

---

## MMR

May return:

```text id="jlwmxa"
Chunk A
Chunk X
Chunk Z
```

More useful context.

---

## RetailOps

```python id="jlwmxb"
search_type="mmr"
```

---

## Why We Use It

Better answers.

Less duplicate context.

---

# 10. Context Formatting

After retrieval:

```text id="jlwmxc"
Documents
```

must become:

```text id="jlwmxd"
Prompt Context
```

---

## RetailOps Function

```python id="jlwmxe"
format_docs()
```

---

## Example

```text id="jlwmxf"
Source: hr_policy.txt

Employees receive 18 paid vacation days...
```

---

# Why Include Sources?

Enables:

```text id="jlwmxg"
Source Attribution
Transparency
```

---

# 11. RAG Prompt

## Purpose

Guide the model to use retrieved context.

---

## RetailOps Prompt

```text id="jlwmxh"
Answer using only the provided context.

If answer not found:
"I don't know."
```

---

## Why?

Reduce hallucinations.

---

# Prompt Structure

```text id="jlwmxi"
Context
Question
Instructions
```

---

# 12. Basic RAG Chain

Architecture:

```text id="jlwmxj"
Question
 ↓
Retriever
 ↓
Context
 ↓
Prompt
 ↓
LLM
 ↓
Answer
```

---

## LangChain Implementation

```python id="jlwmxk"
retrieve_context
|
rag_prompt
|
llm
|
StrOutputParser()
```

---

## Example File

```text id="jlwmxl"
examples/06_basic_rag_with_parser.py
```

---

# 13. Structured RAG Output

Instead of:

```text id="jlwmxm"
Plain Text
```

Return:

```python id="jlwmxn"
RAGResponse
```

---

## Schema

```python id="jlwmxo"
answer
sources
confidence
```

---

## Benefits

```text id="jlwmxp"
Machine Readable
Predictable
Production Friendly
```

---

## RetailOps Example

```python id="jlwmxq"
structured_llm = llm.with_structured_output(
    RAGResponse
)
```

---

# 14. History-Aware Retrieval

## Problem

User:

```text id="jlwmxr"
How many vacation days?
```

Later:

```text id="jlwmxs"
What about part-time employees?
```

Retriever receives:

```text id="jlwmxt"
What about part-time employees?
```

Weak query.

---

## Solution

Rewrite:

```text id="jlwmxu"
What is the PTO policy for part-time employees?
```

before retrieval.

---

## RetailOps Component

```text id="jlwmxv"
question_rewrite_prompt
```

---

# Architecture

```text id="jlwmxw"
Question
 ↓
Rewrite
 ↓
Retriever
 ↓
Answer
```

---

# 15. Source Attribution

## Why Important?

Without sources:

```text id="jlwmxx"
Trust is low
```

---

With sources:

```text id="jlwmxy"
Source:
hr_policy.txt
```

Users can verify answers.

---

## RetailOps

Returned in:

```python id="jlwmxz"
RAGResponse.sources
```

---

# 16. RAG Evaluation

## Question

How do we know retrieval is working?

---

## Basic Evaluation

Ask:

```text id="jlwmya"
How many vacation days?
```

Expected:

```text id="jlwmyb"
18 paid vacation days
```

---

## Metrics

Production systems often measure:

```text id="jlwmyc"
Retrieval Accuracy
Answer Accuracy
Groundedness
Latency
```

---

# 17. Common RAG Problems

---

## Poor Chunk Size

Too small:

```text id="jlwmyd"
Loss of context
```

Too large:

```text id="jlwmye"
Poor retrieval precision
```

---

## Too Many Retrieved Chunks

Problem:

```text id="jlwmyf"
Token explosion
```

---

## Missing Source Metadata

Problem:

```text id="jlwmyg"
No citations
```

---

## Weak Retrieval Queries

Problem:

```text id="jlwmyh"
Poor search quality
```

Solution:

```text id="jlwmyi"
History-Aware Retrieval
```

---

# 18. Production RAG Recommendations

Use:

```text id="jlwmyj"
Chunking
MMR
Source Attribution
Structured Output
History-Aware Retrieval
Evaluation
```

Avoid:

```text id="jlwmyk"
Entire Document Retrieval
Huge Context Dumps
No Grounding
```

---

# 19. RetailOps RAG Flow

Current Architecture:

```text id="jlwmyl"
User Question
 ↓
Question Rewriter
 ↓
Retriever
 ↓
Chroma
 ↓
Relevant Chunks
 ↓
RAG Prompt
 ↓
Groq
 ↓
RAGResponse
```

---

# Interview Questions

### What is a Retriever?

A component that retrieves relevant documents.

---

### Why chunk documents?

Improve retrieval quality.

---

### Why use embeddings?

Represent semantic meaning numerically.

---

### Why use MMR?

Retrieve relevant and diverse chunks.

---

### Why use source attribution?

Improve trust and transparency.

---

### What is History-Aware Retrieval?

Rewriting follow-up questions into standalone retrieval queries.

---

### Why use structured output in RAG?

Predictable application responses.

---

### What is the difference between Similarity Search and MMR?

Similarity:

```text id="jlwmym"
Most Similar
```

MMR:

```text id="jlwmyn"
Relevant + Diverse
```

---

# Summary

LangChain RAG consists of:

```text id="jlwmyo"
Loaders
Splitters
Embeddings
Vector Stores
Retrievers
MMR
Prompts
Structured Output
History-Aware Retrieval
```

The RetailOps project implements a production-style RAG pipeline that serves as the foundation for advanced agent and LangGraph workflows.
