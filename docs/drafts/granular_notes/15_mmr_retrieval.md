# 15 - MMR Retrieval (Maximum Marginal Relevance)

# Learning Objectives

After completing this document, you should understand:

* What MMR is
* Why MMR exists
* MMR vs Similarity Search
* Relevance vs Diversity
* How MMR Works
* MMR Scoring Concept
* MMR Tradeoffs
* When to Use MMR
* When NOT to Use MMR
* Production Best Practices
* RetailOps Implementation

---

# 1. What is MMR?

MMR stands for:

```text id="mmr1"
Maximum Marginal Relevance
```

---

## Definition

MMR is a retrieval strategy that balances:

```text id="mmr2"
Relevance
+
Diversity
```

when selecting documents.

---

Instead of asking:

```text id="mmr3"
What are the most similar chunks?
```

MMR asks:

```text id="mmr4"
What are the most useful chunks?
```

---

# 2. Why Does MMR Exist?

Suppose we have:

```text id="mmr5"
Vacation Policy
```

document.

---

Question:

```text id="mmr6"
Tell me about employee vacation policy.
```

---

Similarity Search may return:

```text id="mmr7"
Chunk A
Employees receive 18 vacation days.

Chunk B
Employees receive 18 vacation days.

Chunk C
Employees receive 18 vacation days.
```

---

All highly similar.

---

Problem:

```text id="mmr8"
Duplicate Context
```

---

LLM sees:

```text id="mmr9"
Same Information Repeated
```

---

Wasted tokens.

---

# 3. MMR Solution

MMR tries to retrieve:

```text id="mmr10"
Relevant
AND
Different
```

chunks.

---

Example:

```text id="mmr11"
Chunk A
Vacation Days

Chunk B
Approval Process

Chunk C
Part-Time PTO Rules

Chunk D
Carry-Over Rules
```

---

Now the LLM gets:

```text id="mmr12"
Broader Context
```

---

# 4. Similarity Search vs MMR

## Similarity Search

Goal:

```text id="mmr13"
Most Similar
```

---

Output:

```text id="mmr14"
A
A
A
A
```

---

## MMR

Goal:

```text id="mmr15"
Relevant
+
Different
```

---

Output:

```text id="mmr16"
A
B
C
D
```

---

# Visual

Similarity Search:

```text id="mmr17"
Question
 ↓
Chunk A
Chunk A
Chunk A
Chunk A
```

---

MMR:

```text id="mmr18"
Question
 ↓
Chunk A
Chunk B
Chunk C
Chunk D
```

---

# 5. Relevance vs Diversity

This is the core concept.

---

# Relevance

How closely a chunk matches the query.

---

Example:

```text id="mmr19"
Vacation Policy
```

---

Very relevant.

---

# Diversity

How different chunks are from each other.

---

Example:

```text id="mmr20"
Approval Process
```

adds new information.

---

# MMR Goal

Maximize:

```text id="mmr21"
Relevance
```

while avoiding:

```text id="mmr22"
Redundancy
```

---

# 6. Conceptual MMR Formula

MMR balances:

```text id="mmr23"
Query Similarity
```

and

```text id="mmr24"
Document Diversity
```

---

Conceptually:

```text id="mmr25"
Score
=
Relevant
-
Redundant
```

---

You do not need to memorize the full formula for interviews.

---

Understand:

```text id="mmr26"
More Relevant
Less Duplicate
```

---

# 7. Example

Question:

```text id="mmr27"
Tell me about P1 incidents.
```

---

Similarity Search:

```text id="mmr28"
P1 definition

P1 definition

P1 definition
```

---

MMR:

```text id="mmr29"
P1 definition

Escalation process

Manager notification

Ticket requirements
```

---

Much more useful.

---

# 8. Why MMR Helps RAG

RAG systems have:

```text id="mmr30"
Limited Context Window
```

---

Every chunk matters.

---

Would you rather send:

```text id="mmr31"
Same information 4 times?
```

or:

```text id="mmr32"
4 different useful chunks?
```

---

MMR chooses:

```text id="mmr33"
Useful Diversity
```

---

# 9. MMR in LangChain

Example:

```python id="mmr34"
retriever = db.as_retriever(
    search_type="mmr"
)
```

---

RetailOps:

```python id="mmr35"
search_type="mmr"
```

---

Current default.

---

# 10. MMR Parameters

Common parameter:

```python id="mmr36"
k=4
```

---

Meaning:

```text id="mmr37"
Return 4 chunks
```

---

Some vector stores expose:

```text id="mmr38"
fetch_k
lambda_mult
```

---

Advanced tuning.

---

# 11. MMR vs Reranking

Very important distinction.

---

# MMR

During:

```text id="mmr39"
Retrieval
```

---

Goal:

```text id="mmr40"
Diverse Candidates
```

---

# Reranking

After retrieval.

---

Goal:

```text id="mmr41"
Best Ordering
```

---

Architecture:

```text id="mmr42"
MMR
 ↓
Candidates
 ↓
Cross Encoder
 ↓
Final Ranking
```

---

# Difference

MMR:

```text id="mmr43"
Candidate Selection
```

---

Cross Encoder:

```text id="mmr44"
Candidate Ranking
```

---

# 12. MMR vs Hybrid Search

Different concepts.

---

# MMR

```text id="mmr45"
Selection Strategy
```

---

# Hybrid Search

```text id="mmr46"
Retrieval Strategy
```

---

Hybrid Search:

```text id="mmr47"
Vector
+
BM25
```

---

MMR:

```text id="mmr48"
Choose diverse results
```

---

Can use both together.

---

RetailOps:

```text id="mmr49"
Hybrid Search
+
MMR
```

---

# 13. When To Use MMR

Use when:

```text id="mmr50"
Policies
Manuals
Knowledge Bases
Documentation
```

---

Reason:

Documents often contain:

```text id="mmr51"
Related Sections
```

---

Need diversity.

---

# 14. When NOT To Use MMR

Sometimes exact retrieval is better.

---

Example:

```text id="mmr52"
SKU Lookup
```

---

Question:

```text id="mmr53"
Who owns SKU DENIM-4421?
```

---

Need:

```text id="mmr54"
Exact Match
```

not diversity.

---

Tools are better.

---

# 15. RetailOps Implementation

Current:

```python id="mmr55"
search_type="mmr"
```

---

Why?

Our documents:

```text id="mmr56"
Policies
Procedures
Knowledge Base
```

benefit from diverse context.

---

# 16. Production Best Practices

## Use MMR for RAG

Good default.

---

## Add Reranking

Use:

```text id="mmr57"
Cross Encoder
```

after MMR.

---

## Evaluate

Do not assume:

```text id="mmr58"
MMR
```

is always better.

---

Compare:

```text id="mmr59"
Similarity
vs
MMR
```

using evaluation reports.

---

## Tune K

Avoid:

```text id="mmr60"
Too many chunks
```

---

# 17. Common Mistakes

## Mistake 1

Thinking MMR replaces reranking.

---

## Mistake 2

Thinking MMR improves exact lookup.

---

## Mistake 3

Using huge K values.

---

## Mistake 4

Never evaluating retrieval quality.

---

# 18. Interview Questions

### What is MMR?

Maximum Marginal Relevance.

---

### Why use MMR?

To balance relevance and diversity.

---

### Similarity Search vs MMR?

Similarity:

```text id="mmr61"
Most Similar
```

MMR:

```text id="mmr62"
Relevant + Diverse
```

---

### MMR vs Reranking?

MMR:

```text id="mmr63"
Candidate Selection
```

Reranking:

```text id="mmr64"
Candidate Ordering
```

---

### Why does RetailOps use MMR?

To avoid redundant chunks and improve context diversity.

---

# Summary

MMR is a retrieval strategy that helps RAG systems avoid:

```text id="mmr65"
Duplicate Context
```

and instead retrieve:

```text id="mmr66"
Relevant
+
Diverse
```

chunks.

RetailOps uses MMR because:

```text id="mmr67"
Policies
Procedures
Knowledge Bases
```

benefit greatly from diverse context.

The next document:

```text id="mmr68"
16_semantic_chunking.md
```

dives deeper into semantic chunking, topic boundaries, chunk quality, and why chunking often has a bigger impact on RAG quality than retriever tuning.
