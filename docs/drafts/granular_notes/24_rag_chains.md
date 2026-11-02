# 24 - RAG Chains

# Learning Objectives

After completing this document, you should understand:

* What a RAG Chain is
* Why RAG Chains exist
* End-to-End RAG Architecture
* Retrieval Pipeline
* Context Injection
* Grounded Generation
* History-Aware RAG
* Multi-Query RAG
* Hybrid RAG
* Structured RAG Responses
* Production RAG Architecture
* RetailOps Implementation

---

# 1. What is a RAG Chain?

RAG stands for:

```text id="rag1"
Retrieval Augmented Generation
```

---

## Definition

A RAG Chain combines:

```text id="rag2"
Retrieval
+
Generation
```

to answer questions using external knowledge.

---

Instead of:

```text id="rag3"
Question
↓
LLM
↓
Answer
```

---

We do:

```text id="rag4"
Question
↓
Retrieve Documents
↓
Inject Context
↓
LLM
↓
Answer
```

---

# Why Does RAG Exist?

LLMs have limitations.

---

# Problem 1

Training data becomes stale.

---

Question:

```text id="rag5"
What is our current HR policy?
```

---

LLM:

```text id="rag6"
Does not know.
```

---

# Problem 2

Enterprise data is private.

---

Examples:

```text id="rag7"
HR Policies
Store SOPs
Vendor Contracts
Internal Runbooks
```

---

LLM was never trained on these.

---

# Solution

Retrieve documents dynamically.

---

# 2. RAG Architecture

Basic architecture:

```text id="rag8"
Question
 ↓
Retriever
 ↓
Documents
 ↓
Prompt
 ↓
LLM
 ↓
Answer
```

---

RetailOps architecture:

```text id="rag9"
Question
 ↓
Question Rewriter
 ↓
Multi Query
 ↓
Hybrid Search
 ↓
Cross Encoder
 ↓
Top K Chunks
 ↓
RAG Prompt
 ↓
Structured LLM
 ↓
RAGResponse
```

---

# 3. Retrieval Phase

Goal:

```text id="rag10"
Find Relevant Context
```

---

Question:

```text id="rag11"
How many vacation days do employees receive?
```

---

Retriever finds:

```text id="rag12"
Vacation Policy
```

---

Output:

```python id="rag13"
list[Document]
```

---

# Important

Retriever does NOT answer.

---

Retriever only finds:

```text id="rag14"
Evidence
```

---

# 4. Generation Phase

Goal:

```text id="rag15"
Generate Answer
```

---

Input:

```text id="rag16"
Question
+
Retrieved Context
```

---

Prompt:

```text id="rag17"
Use only provided context.
```

---

LLM:

```text id="rag18"
Answer
```

---

# Why This Matters

Answer becomes:

```text id="rag19"
Grounded
```

instead of:

```text id="rag20"
Hallucinated
```

---

# 5. Context Injection

Retrieved documents become:

```text id="rag21"
Prompt Context
```

---

Example

Question:

```text id="rag22"
What does P1 mean?
```

---

Retrieved:

```text id="rag23"
P1 means full store outage.
```

---

Prompt:

```text id="rag24"
Context:
P1 means full store outage.

Question:
What does P1 mean?
```

---

LLM now has evidence.

---

# 6. Grounded Generation

One of the most important concepts.

---

Without RAG:

```text id="rag25"
Answer From Model Memory
```

---

With RAG:

```text id="rag26"
Answer From Retrieved Evidence
```

---

Goal:

```text id="rag27"
Reduce Hallucinations
```

---

# RetailOps Prompt Rule

Current:

```text id="rag28"
Use only provided context.
```

---

If answer not found:

```text id="rag29"
I don't know.
```

---

Very important production pattern.

---

# 7. History-Aware RAG

RetailOps:

```text id="rag30"
Question Rewriter
```

before retrieval.

---

Conversation:

```text id="rag31"
Vacation Policy?
```

---

Follow-up:

```text id="rag32"
What about part-time employees?
```

---

Rewrite:

```text id="rag33"
What is PTO policy for part-time employees?
```

---

Then retrieve.

---

# Why?

Better retrieval quality.

---

# 8. Multi-Query RAG

RetailOps:

```text id="rag34"
Generate Alternate Queries
```

---

Example:

```text id="rag35"
PTO
```

becomes:

```text id="rag36"
Vacation Policy
Leave Benefits
Paid Time Off
```

---

Retrieval improves.

---

# 9. Hybrid RAG

RetailOps:

```text id="rag37"
Vector Search
+
BM25
```

---

Why?

Need:

```text id="rag38"
Meaning
+
Exact Terms
```

---

Examples:

```text id="rag39"
PTO
Vacation

P1
SKU
INC-1001
```

---

# 10. Reranked RAG

RetailOps:

```text id="rag40"
Cross Encoder
```

---

Purpose:

```text id="rag41"
Select Best Chunks
```

---

Pipeline:

```text id="rag42"
Candidates
 ↓
Cross Encoder
 ↓
Top K
```

---

# Why?

Better context.

---

# 11. Structured RAG Responses

RetailOps:

```python id="rag43"
RAGResponse
```

---

Fields:

```text id="rag44"
answer
sources
confidence
```

---

Output:

```python id="rag45"
RAGResponse(...)
```

---

Instead of:

```text id="rag46"
Plain Text
```

---

# Why?

Applications need:

```text id="rag47"
Predictable Output
```

---

# 12. RetailOps RAGResponse

Example:

```python id="rag48"
{
  "answer":"18 vacation days",
  "sources":[
      "hr_policy.txt"
  ],
  "confidence":"high"
}
```

---

# Benefits

Supports:

```text id="rag49"
UI
APIs
Evaluation
```

---

# 13. Source Attribution

RetailOps always returns:

```text id="rag50"
Sources
```

---

Why?

Users need:

```text id="rag51"
Trust
```

---

Example:

```text id="rag52"
Source:
hr_policy.txt
```

---

# Production Rule

Never hide sources.

---

# 14. Confidence Scores

RetailOps returns:

```text id="rag53"
high
medium
low
```

---

Purpose:

```text id="rag54"
Communicate Uncertainty
```

---

Not all answers are equal.

---

# 15. RAG Chain in LCEL

RetailOps:

```python id="rag55"
retrieve_context
|
rag_prompt
|
structured_llm
```

---

Flow:

```text id="rag56"
Retrieve
 ↓
Prompt
 ↓
Generate
```

---

Simple and powerful.

---

# 16. Why RAG Chains Matter

Without RAG:

```text id="rag57"
General Knowledge
```

---

With RAG:

```text id="rag58"
Enterprise Knowledge
```

---

This is the foundation of:

```text id="rag59"
Internal Assistants
Knowledge Search
Support Bots
```

---

# 17. Production Best Practices

## Always Return Sources

Required.

---

## Add Retrieval Evaluation

Measure:

```text id="rag60"
Source Accuracy
```

---

## Add Reranking

Use:

```text id="rag61"
Cross Encoder
```

---

## Use Hybrid Retrieval

Use:

```text id="rag62"
BM25
+
Embeddings
```

---

## Use Structured Output

Prefer:

```python id="rag63"
RAGResponse
```

---

# 18. Common Mistakes

## Mistake 1

No source attribution.

---

## Mistake 2

No retrieval evaluation.

---

## Mistake 3

Using vector search only.

---

## Mistake 4

No reranking.

---

## Mistake 5

Trusting the LLM more than retrieval.

---

# 19. Interview Questions

### What is RAG?

Retrieval Augmented Generation.

---

### Why use RAG?

To answer using external knowledge.

---

### What are the two phases?

```text id="rag64"
Retrieval
Generation
```

---

### Why return sources?

Trust and verification.

---

### Why use structured output?

Predictable responses.

---

### Why does RetailOps use question rewriting?

To improve conversational retrieval.

---

### Why does RetailOps use hybrid retrieval?

To combine semantic and exact-match search.

---

# Summary

RAG Chains combine:

```text id="rag65"
Retrieval
+
Generation
```

to answer questions using external documents.

RetailOps implements a modern production-style RAG pipeline with:

```text id="rag66"
History-Aware Retrieval
Multi Query
Hybrid Search
Cross Encoder
Structured Output
Source Attribution
```

making it significantly stronger than basic tutorial RAG systems.

The next document:

```text id="rag67"
25_rag_evaluation.md
```

covers evaluation, LLM-as-judge, retrieval metrics, groundedness, and how to measure RAG quality scientifically.
