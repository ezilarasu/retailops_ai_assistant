# 09 - Document Loaders

# Learning Objectives

After completing this document, you should understand:

* What Document Loaders are
* Why Document Loaders exist
* Document Loader Architecture
* LangChain Document Object
* TextLoader
* PDF Loaders
* Web Loaders
* Directory Loaders
* Metadata
* Production Ingestion Patterns
* RetailOps Implementation

---

# 1. What is a Document Loader?

## Definition

A Document Loader is responsible for loading data from external sources and converting it into LangChain Documents.

Think of it as:

```text id="dl1"
External Data
 ↓
Document Loader
 ↓
LangChain Document
```

---

# Why Do We Need Document Loaders?

LLMs cannot directly understand:

```text id="dl2"
PDF Files
Word Documents
HTML Pages
SharePoint
Confluence
Google Drive
```

---

They need:

```text id="dl3"
Text
```

---

Document Loaders extract:

```text id="dl4"
Content
Metadata
```

from source systems.

---

# 2. Loader Architecture

Input:

```text id="dl5"
PDF
TXT
DOCX
HTML
```

---

Output:

```python id="dl6"
Document(
    page_content="...",
    metadata={}
)
```

---

This standardization is extremely important.

---

# Why?

Because:

```text id="dl7"
Chunking
Embeddings
Retrievers
```

all expect:

```python id="dl8"
Document
```

objects.

---

# 3. The LangChain Document Object

## Definition

The standard container for knowledge.

---

Structure:

```python id="dl9"
Document(
    page_content="...",
    metadata={}
)
```

---

# page_content

Contains:

```text id="dl10"
Actual Text
```

---

Example:

```python id="dl11"
Document(
    page_content="Employees receive 18 vacation days."
)
```

---

# metadata

Contains:

```text id="dl12"
Source Information
```

---

Example:

```python id="dl13"
Document(
    metadata={
        "source":"hr_policy.txt"
    }
)
```

---

# Why Metadata Matters

Metadata enables:

```text id="dl14"
Source Attribution
Filtering
Auditing
Access Control
```

---

# 4. TextLoader

The simplest loader.

---

Example:

```python id="dl15"
from langchain_community.document_loaders import (
    TextLoader
)

loader = TextLoader(
    "data/hr_policy.txt"
)

docs = loader.load()
```

---

Output:

```python id="dl16"
[
    Document(...)
]
```

---

# RetailOps

Current documents:

```text id="dl17"
hr_policy.txt
returns_refunds_policy.txt
store_operations_sop.txt
it_support_kb.txt
```

---

Loaded using:

```python id="dl18"
TextLoader
```

---

# 5. DirectoryLoader

Load multiple files.

---

Example:

```python id="dl19"
from langchain_community.document_loaders import (
    DirectoryLoader
)

loader = DirectoryLoader(
    "data/"
)
```

---

Why Useful?

Avoid:

```python id="dl20"
Load File A
Load File B
Load File C
```

manually.

---

# 6. PDF Loaders

One of the most common production loaders.

---

Example:

```python id="dl21"
from langchain_community.document_loaders import (
    PyPDFLoader
)

loader = PyPDFLoader(
    "employee_handbook.pdf"
)
```

---

Output:

```text id="dl22"
Document Per Page
```

usually.

---

# Use Cases

```text id="dl23"
Policies
Contracts
Manuals
Reports
```

---

# 7. Web Loaders

Load web pages.

---

Example:

```python id="dl24"
from langchain_community.document_loaders import (
    WebBaseLoader
)

loader = WebBaseLoader(
    "https://..."
)
```

---

Use Cases:

```text id="dl25"
Documentation
Knowledge Bases
Blogs
```

---

# 8. CSV Loaders

Load tabular data.

---

Example:

```python id="dl26"
CSVLoader
```

---

Use Cases:

```text id="dl27"
Reports
Exports
Structured Documents
```

---

# Important

For operational data:

```text id="dl28"
Tools
```

are often better.

---

Example:

```text id="dl29"
Inventory
Orders
Incidents
```

---

RetailOps uses:

```text id="dl30"
Tools
```

instead of RAG.

---

# 9. Metadata

One of the most important concepts.

---

Example:

```python id="dl31"
Document(
    page_content="...",
    metadata={
        "source":"hr_policy.txt",
        "department":"HR",
        "version":"v2"
    }
)
```

---

# Why Metadata Matters

Without metadata:

```text id="dl32"
No Source Tracking
```

---

With metadata:

```text id="dl33"
Source Attribution
Filtering
Auditing
```

---

# Future Enterprise Use

Metadata enables:

```text id="dl34"
Role Filtering
Region Filtering
Access Control
```

---

# Example

```python id="dl35"
metadata={
    "department":"HR"
}
```

---

User:

```text id="dl36"
Store Associate
```

---

Retriever:

```text id="dl37"
Exclude HR Docs
```

---

# 10. Loader Strategies

---

# Single File

Example:

```text id="dl38"
employee_handbook.pdf
```

---

# Directory

Example:

```text id="dl39"
Policies Folder
```

---

# Website

Example:

```text id="dl40"
Confluence
Documentation
```

---

# Database

Example:

```text id="dl41"
Knowledge Tables
```

---

# Cloud Storage

Example:

```text id="dl42"
SharePoint
Google Drive
S3
```

---

# 11. Production Ingestion Pipeline

Enterprise Architecture:

```text id="dl43"
Source
 ↓
Loader
 ↓
Document
 ↓
Chunking
 ↓
Embeddings
 ↓
Vector Store
```

---

RetailOps:

```text id="dl44"
TXT Files
 ↓
TextLoader
 ↓
Documents
 ↓
Chunking
 ↓
Embeddings
 ↓
Chroma
```

---

# 12. Loader vs Retriever

Very common confusion.

---

Loader:

```text id="dl45"
Read Data
```

---

Retriever:

```text id="dl46"
Find Data
```

---

Example:

```text id="dl47"
PDF
 ↓
Loader
 ↓
Document
```

---

Later:

```text id="dl48"
Question
 ↓
Retriever
 ↓
Relevant Documents
```

---

# Difference

Loader:

```text id="dl49"
Ingestion Time
```

---

Retriever:

```text id="dl50"
Query Time
```

---

# 13. Production Best Practices

## Store Metadata

Always include:

```text id="dl51"
Source
Version
Department
```

---

## Separate Ingestion

Good:

```text id="dl52"
Load Once
Index Once
```

---

Bad:

```text id="dl53"
Reload Everything Every Request
```

---

## Track Document Versions

Important for:

```text id="dl54"
Reindexing
```

---

## Validate Input Files

Avoid:

```text id="dl55"
Corrupt PDFs
```

breaking ingestion.

---

# 14. RetailOps Implementation

Current:

```python id="dl56"
load_documents()
```

---

Loads:

```text id="dl57"
hr_policy.txt
returns_refunds_policy.txt
store_operations_sop.txt
it_support_kb.txt
```

---

Returns:

```python id="dl58"
list[Document]
```

---

Used by:

```text id="dl59"
Chunking
Embeddings
Retrieval
```

---

# 15. Common Mistakes

## Mistake 1

Ignoring metadata.

---

## Mistake 2

Using tools when documents are better.

---

## Mistake 3

Using documents when tools are better.

---

Example:

```text id="dl60"
Inventory Data
```

should be:

```text id="dl61"
Tool
```

---

not:

```text id="dl62"
RAG
```

---

## Mistake 4

Reloading documents every request.

---

# 16. Interview Questions

### What is a Document Loader?

A component that converts external data into LangChain Documents.

---

### Why do Document Loaders exist?

To standardize data ingestion.

---

### What is a LangChain Document?

A container with:

```text id="dl63"
page_content
metadata
```

---

### Why is metadata important?

Source attribution, filtering, auditing, and access control.

---

### Loader vs Retriever?

Loader:

```text id="dl64"
Read Data
```

Retriever:

```text id="dl65"
Find Data
```

---

### When should tools be used instead of loaders?

For operational structured data.

---

# Summary

Document Loaders are the entry point into RAG systems.

They convert:

```text id="dl66"
Files
Pages
Documents
```

into:

```python id="dl67"
Document
```

objects that can be:

```text id="dl68"
Chunked
Embedded
Indexed
Retrieved
```

RetailOps currently uses:

```text id="dl69"
TextLoader
```

but the same architecture can later support:

```text id="dl70"
PDF
Confluence
SharePoint
Google Drive
```

without changing the retrieval layer.

The next document:

```text id="dl71"
10_text_splitters.md
```

covers chunking, semantic chunking, parent-child retrieval, and how chunk quality directly affects RAG quality.
