# 04 - RAG Fundamentals

# Learning Objectives

After completing this document, you should understand:

* What RAG is
* Why RAG exists
* Why LLMs cannot answer company-specific questions
* Fine-Tuning vs RAG
* Embeddings
* Semantic Search
* Vector Databases
* Document Chunking
* Chunk Overlap
* Document Loaders
* Retrievers
* Similarity Search
* MMR Retrieval
* History-Aware Retrieval
* Memory vs RAG
* RAG Architecture
* Production RAG Design
* Common RAG Mistakes
* RAG in the RetailOps Project

---

# 1. What is RAG?

RAG stands for:

```text id="f2sw0y"
Retrieval Augmented Generation
```

---

## Definition

RAG is a technique that combines:

```text id="z3k4m9"
Information Retrieval
+
LLM Generation
```

to answer questions using external knowledge.

---

## Traditional LLM

```text id="qpt3dn"
Question
 ↓
LLM
 ↓
Answer
```

---

## RAG

```text id="mdm4g8"
Question
 ↓
Retriever
 ↓
Relevant Documents
 ↓
LLM
 ↓
Answer
```

---

# 2. Why Does RAG Exist?

## Problem

LLMs do not know:

```text id="jzml7r"
Company Policies
Private Documents
Latest Information
Internal Wikis
Current Databases
```

---

## Example

Question:

```text id="0zmx9g"
What is RetailOps vacation policy?
```

The model was never trained on:

```text id="6emwq7"
RetailOps HR Policy
```

Therefore:

```text id="swtv8u"
The answer is unavailable
```

---

## Without RAG

The model may hallucinate.

---

## With RAG

The model retrieves:

```text id="v14kj2"
Employees receive 18 paid vacation days...
```

and answers correctly.

---

# 3. Why Not Just Fine-Tune?

This is one of the most important concepts in AI engineering.

---

# Fine-Tuning

## Definition

Additional training performed on a base model.

---

## Goal

Modify:

```text id="zkn5ji"
Behavior
Style
Format
Tone
```

---

## Example

Train a model to:

```text id="cyyr8l"
Write legal documents
Respond like customer support
Use company writing style
```

---

## Pros

```text id="rq4gjt"
Behavior Customization
Domain Adaptation
```

---

## Cons

```text id="y9i98d"
Expensive
Slow
Hard to Update
```

---

# RAG

## Goal

Provide knowledge dynamically.

---

## Example

Store:

```text id="7n48nk"
Policies
FAQs
Manuals
```

outside the model.

Retrieve when needed.

---

## Pros

```text id="49mwq4"
Cheap
Easy Updates
Fresh Knowledge
```

---

## Cons

```text id="m6tzj2"
Requires Retrieval Infrastructure
```

---

# Production Rule

Use:

```text id="lajp9j"
Fine-Tuning
```

for:

```text id="6zgxpi"
Behavior
Style
Tone
```

Use:

```text id="tf0hfh"
RAG
```

for:

```text id="a7jmlm"
Knowledge
Policies
Documents
```

---

# 4. Embeddings

## Definition

A numerical representation of semantic meaning.

---

## Example

Text:

```text id="4up9xb"
Vacation Policy
```

Embedding:

```text id="1yx9w7"
[0.12, -0.45, 0.88, ...]
```

---

## Why Do Embeddings Exist?

Computers compare numbers.

Not meaning.

Embeddings convert:

```text id="9x2nso"
Meaning
 ↓
Numbers
```

---

# Semantic Search

Query:

```text id="tvw1d4"
PTO policy
```

Document:

```text id="5o18ol"
Vacation policy
```

Embeddings recognize similarity.

Keyword search may not.

---

## Benefits

```text id="gs2x0q"
Meaning-Based Search
Synonym Handling
Better Retrieval
```

---

# 5. Semantic Search

## Definition

Searching by meaning rather than exact words.

---

## Keyword Search

Query:

```text id="v8n1h4"
automobile
```

Document:

```text id="r2vq9s"
car
```

No match.

---

## Semantic Search

Recognizes:

```text id="i7ng9o"
car ≈ automobile
```

Match found.

---

## Why It Matters

Most users do not use exact document wording.

---

# 6. Document Loaders

## Definition

Convert files into LangChain Documents.

---

## Example

Input:

```text id="f3x17e"
PDF
TXT
DOCX
HTML
```

Output:

```python id="m5k6r9"
Document(
    page_content="...",
    metadata={}
)
```

---

## Why Use Them?

LLMs only understand text.

Loaders extract text from files.

---

## Used In RetailOps

```text id="ibxkwg"
hr_policy.txt
returns_refunds_policy.txt
store_operations_sop.txt
it_support_kb.txt
```

---

# 7. Chunking

## Definition

Breaking large documents into smaller pieces.

---

## Why?

Bad:

```text id="vqiv5j"
Entire 100-page handbook
 ↓
One Embedding
```

Poor retrieval.

---

Good:

```text id="j5gk0o"
Handbook
 ↓
Chunk 1
Chunk 2
Chunk 3
```

Better retrieval.

---

## Benefits

```text id="g31h1v"
Focused Meaning
Better Search Quality
```

---

# Chunk Size

Example:

```python id="mttxwv"
chunk_size=300
```

---

## Tradeoff

Small:

```text id="9j3xvq"
More Precise
Less Context
```

Large:

```text id="zv2v7g"
More Context
Less Precise
```

---

# Chunk Overlap

## Definition

Shared text between chunks.

---

Example:

```python id="bbxknv"
chunk_overlap=50
```

---

## Why Use It?

Without overlap:

```text id="18qzq6"
Sentence may be split
```

and meaning lost.

---

## Benefits

```text id="mt1rls"
Context Preservation
```

---

# 8. Vector Databases

## Definition

Databases optimized for storing embeddings.

---

## Traditional Database

```text id="7x91qt"
id
name
price
```

---

## Vector Database

```text id="gwk39s"
id
embedding
```

---

## Purpose

Efficient similarity search.

---

## Popular Options

```text id="q1xt6v"
Chroma
FAISS
Pinecone
Qdrant
Weaviate
```

---

# Chroma

Used in RetailOps.

---

## Pros

```text id="7dn8xt"
Free
Local
Simple
```

---

## Cons

```text id="t0xqyz"
Limited Scalability
```

---

# 9. Retrievers

## Definition

Components that retrieve relevant documents.

---

## Why Use Retrievers?

Instead of:

```python id="syw75x"
db.similarity_search(...)
```

use:

```python id="rpsfxj"
retriever.invoke(...)
```

Standardized interface.

---

## Benefits

```text id="10iv6r"
Reusable
Provider Independent
```

---

# 10. Similarity Search

## Definition

Retrieve documents most similar to the query.

---

Example:

```text id="x39m6u"
Vacation policy question
 ↓
Top matching chunks
```

---

## Pros

```text id="hr02rn"
Fast
Simple
```

---

## Cons

May retrieve:

```text id="a5m7tu"
Near-duplicate chunks
```

---

# 11. MMR Retrieval

Maximum Marginal Relevance

---

## Definition

Balances:

```text id="4h0f0p"
Relevance
+
Diversity
```

---

## Similarity Search

May return:

```text id="c4gz4m"
Chunk A
Chunk B
Chunk C
```

all very similar.

---

## MMR

May return:

```text id="uv3gb8"
Chunk A
Chunk X
Chunk Z
```

More diverse.

---

## Why Use It?

Provides broader context.

---

## Used In RetailOps

```python id="cbzj5k"
search_type="mmr"
```

---

# 12. RAG Prompting

## Definition

Prompt design for retrieval-based answering.

---

## Example

```text id="k4gw87"
Answer using only the provided context.

If the answer is not found:
"I don't know based on available documents."
```

---

## Why?

Reduces hallucinations.

---

# 13. Source Attribution

## Definition

Showing where information came from.

---

## Example

```text id="9vpxci"
Source:
hr_policy.txt
```

---

## Benefits

```text id="cgk27j"
Trust
Auditability
Transparency
```

---

# 14. Memory vs RAG

This is commonly misunderstood.

---

# Memory

Stores:

```text id="2eh4xt"
Conversation History
```

---

Example:

```text id="vw8du8"
My name is John.
```

Later:

```text id="wdmjx0"
What is my name?
```

---

# RAG

Stores:

```text id="zpc7vt"
Documents
Knowledge
Policies
```

---

## Comparison

| Feature              | Memory | RAG     |
| -------------------- | ------ | ------- |
| Stores Conversations | Yes    | No      |
| Stores Documents     | No     | Yes     |
| Personalization      | Yes    | Limited |
| Knowledge Retrieval  | No     | Yes     |

---

# 15. History-Aware Retrieval

## Problem

User:

```text id="gmgdx8"
How many vacation days do employees receive?
```

Assistant answers.

User:

```text id="y7fqg4"
What about part-time employees?
```

Retriever sees:

```text id="6ok7bi"
What about part-time employees?
```

Weak query.

---

## Solution

Rewrite into:

```text id="xikrxr"
What is the PTO policy for part-time employees?
```

before retrieval.

---

## Benefits

```text id="lpchdy"
Better Search
Better Follow-Up Handling
```

---

## Used In RetailOps

```text id="r4iwlw"
question_rewrite_prompt
```

---

# 16. Complete RAG Pipeline

Production Architecture:

```text id="w6p0mk"
Documents
 ↓
Loaders
 ↓
Chunking
 ↓
Embeddings
 ↓
Vector Database
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

```text id="a14nsx"
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
Groq LLM
        ↓
Structured Response
```

---

# 17. Common RAG Mistakes

---

## Mistake 1

Huge chunks.

Result:

```text id="fl7spu"
Poor Retrieval
```

---

## Mistake 2

Tiny chunks.

Result:

```text id="o4uqr3"
Lost Context
```

---

## Mistake 3

Too many retrieved chunks.

Result:

```text id="5c78eo"
Token Explosion
```

---

## Mistake 4

No source attribution.

---

## Mistake 5

Using RAG for structured data.

Use tools instead.

---

# 18. RAG vs Tools

---

# RAG

Use for:

```text id="ghjk4o"
Policies
Knowledge Base
Documentation
FAQs
```

---

# Tools

Use for:

```text id="8l72xj"
CSV
Databases
APIs
Calculations
Inventory
Incidents
```

---

## RetailOps Examples

RAG:

```text id="55mb7w"
Vacation Policy
Return Policy
Store SOP
```

Tools:

```text id="abv9je"
Inventory Lookup
Vendor Lookup
Incident Lookup
```

---

# 19. Production Recommendations

Use:

```text id="72x5ta"
Chunking
MMR
Source Attribution
History-Aware Retrieval
Evaluation
```

Avoid:

```text id="qz9tif"
Huge Context Dumps
Retrieving Entire Documents
No Grounding
```

---

# Interview Questions

### What is RAG?

Retrieval Augmented Generation.

---

### Why use RAG?

To answer questions using external knowledge.

---

### RAG vs Fine-Tuning?

RAG retrieves knowledge.

Fine-tuning changes behavior.

---

### What is an embedding?

A numerical representation of semantic meaning.

---

### What is semantic search?

Search based on meaning rather than keywords.

---

### Why use chunk overlap?

Preserve context between chunks.

---

### Why use a vector database?

Efficient similarity search.

---

### Difference between Similarity Search and MMR?

Similarity:

```text id="mg6l7k"
Most similar
```

MMR:

```text id="5x0yml"
Relevant + Diverse
```

---

### Difference between Memory and RAG?

Memory stores conversation.

RAG stores knowledge.

---

### When should tools be used instead of RAG?

For structured data and actions.

---

# Summary

RAG enables LLMs to answer questions using external knowledge.

Core Concepts:

```text id="wukz6s"
Document Loaders
Chunking
Embeddings
Semantic Search
Vector Databases
Retrievers
MMR
History-Aware Retrieval
```

These concepts form the foundation of most production AI assistants, including the RetailOps project.

The next document, `05_project_implementation.md`, will connect all concepts together and explain how every component of the RetailOps AI Assistant works end-to-end.
