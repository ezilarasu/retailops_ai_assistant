# 05 - Project Implementation (RetailOps AI Assistant)

# Learning Objectives

After completing this document, you should understand:

* The complete RetailOps AI Assistant architecture
* Why each folder exists
* How all LangChain concepts fit together
* The flow of a user request
* How RAG works in the project
* How Tools work in the project
* How Routing works
* How Memory works
* How Testing works
* How the API layer works
* How to extend the project

---

# 1. Project Goal

The RetailOps AI Assistant is a production-style AI assistant built to teach:

```text id="i3o1hp"
LLM Fundamentals
Prompt Engineering
LangChain
RAG
Tools
Agents
Memory
FastAPI
Testing
LangSmith
```

through one realistic enterprise use case.

---

# 2. Business Use Case

Imagine a retail company.

Employees need answers about:

```text id="j7lzwq"
HR Policies
Store Operations
Returns Policy
IT Support
Inventory
Vendors
Incidents
```

Instead of searching documents manually:

```text id="24x2eo"
User
 ↓
RetailOps AI Assistant
 ↓
Answer
```

---

# 3. Project Structure

```text id="d5z3vv"
retailops_ai_assistant/
│
├── app/
├── data/
├── docs/
├── examples/
├── tests/
├── vectorstore/
│
├── .env
├── requirements.txt
└── README.md
```

---

# 4. Folder Responsibilities

---

# app/

Contains application code.

```text id="8p8h4e"
Prompts
Chains
RAG Logic
Tools
Router
Memory
API
```

---

# data/

Contains business data.

---

## Unstructured Data

```text id="a4v2v4"
hr_policy.txt
store_operations_sop.txt
returns_refunds_policy.txt
it_support_kb.txt
```

Used for:

```text id="4f3ns8"
RAG
```

---

## Structured Data

```text id="h7yr5m"
inventory.csv
vendors.csv
incidents.json
```

Used for:

```text id="7r65t6"
Tools
```

---

# docs/

Contains learning material.

Examples:

```text id="4b8px4"
LLM Fundamentals
Prompt Engineering
LangChain
RAG
```

---

# examples/

Preserves every concept example.

Examples:

```text id="dd2z4q"
RunnableLambda
RAG
Tools
Router
Memory
```

---

# tests/

Contains automated tests.

---

# vectorstore/

Stores Chroma vector database.

---

# 5. Configuration Layer

File:

```text id="rkf92z"
app/config.py
```

---

## Purpose

Centralized settings.

---

Example:

```python id="fjf21t"
settings.llm_model
settings.chunk_size
settings.retrieval_k
```

---

## Why?

Avoid:

```python id="3o9eec"
hardcoded values
```

throughout the application.

---

# 6. Prompt Layer

File:

```text id="5w3ahj"
app/prompts.py
```

---

Contains:

```text id="zcvpgj"
general_chat_prompt
rag_prompt
router_prompt
question_rewrite_prompt
```

---

## Why Separate Prompts?

Prompts are business logic.

Treat them like code.

---

# 7. LLM Layer

File:

```text id="e16rph"
app/chains.py
```

---

## Current Provider

```text id="e7c4u8"
Groq
```

---

## Model Wrapper

```python id="qyw9i7"
ChatGroq(...)
```

---

## Why Use LangChain Models?

Provider-independent interface.

---

# 8. General Chat Chain

Architecture:

```text id="f6wksg"
Question
 ↓
general_chat_prompt
 ↓
Groq LLM
 ↓
StrOutputParser
 ↓
Answer
```

---

## Use Cases

```text id="t7af5l"
Greetings
General Explanations
Small Talk
```

---

## Example

```text id="4zjlwm"
Who are you?
```

---

# 9. RAG Pipeline

The most important workflow.

---

Architecture:

```text id="y6sk8m"
Documents
 ↓
Loader
 ↓
Chunking
 ↓
Embeddings
 ↓
Chroma
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

# Document Loading

Files:

```text id="j5qffv"
HR Policy
Returns Policy
Store SOP
IT KB
```

Loaded using:

```python id="2o3st6"
TextLoader
```

---

# Chunking

Purpose:

```text id="s5ps40"
Improve Retrieval Quality
```

Settings:

```python id="3knw9f"
chunk_size=300
chunk_overlap=50
```

---

# Embeddings

Current Model:

```text id="30p0qm"
all-MiniLM-L6-v2
```

---

Purpose:

```text id="8x8jui"
Semantic Search
```

---

# Chroma

Purpose:

```text id="0o5j0h"
Store Embeddings
```

---

# Retriever

Current Configuration:

```python id="y2h40w"
search_type="mmr"
```

---

Why?

```text id="kw0fdw"
Relevant + Diverse Results
```

---

# Structured Output

Returns:

```python id="4du91m"
RAGResponse
```

Fields:

```text id="nq2icm"
answer
sources
confidence
```

---

# Example Question

```text id="eclsyj"
How many vacation days do employees receive?
```

---

Flow:

```text id="s01sgc"
Retriever
 ↓
HR Policy
 ↓
Prompt
 ↓
LLM
 ↓
Answer
```

---

# 10. Tool Layer

File:

```text id="w9y6kc"
app/tools.py
```

---

Current Tools:

```text id="msj70n"
get_low_stock_items
get_vendor_for_sku
get_open_incidents
```

---

## Why Tools?

Structured data should not use RAG.

---

## Inventory Example

Question:

```text id="5zzl5w"
Which items are low stock in store 102?
```

---

Tool:

```python id="d4s0pk"
get_low_stock_items()
```

---

# Vendor Example

Question:

```text id="m1z77m"
Who owns SKU DENIM-4421?
```

---

Tool:

```python id="c0p7s4"
get_vendor_for_sku()
```

---

# Incident Example

Question:

```text id="7j0q0q"
Are there open incidents for store 102?
```

---

Tool:

```python id="74u5dg"
get_open_incidents()
```

---

# 11. Agent Layer

Purpose:

```text id="2j4q2e"
Dynamic Tool Selection
```

---

Architecture:

```text id="b8h2lh"
Question
 ↓
Agent
 ↓
Choose Tool
 ↓
Tool Result
 ↓
Answer
```

---

## Why Use Agent?

The user should not choose tools.

The model decides.

---

# Example

Question:

```text id="a7n9x4"
Who is the vendor for SKU DENIM-4421?
```

---

Agent decides:

```text id="7j4sdy"
Vendor Tool
```

---

# 12. Router Layer

File:

```text id="t2uwpn"
app/router.py
```

---

Purpose:

```text id="y33fnw"
Choose Correct Workflow
```

---

Routes:

```text id="tv8avm"
general
rag
tools
```

---

Architecture:

```text id="2mx1wq"
Question
 ↓
Router
 ├── General Chat
 ├── RAG
 └── Tools
```

---

# Example

Question:

```text id="odfey2"
How many vacation days do employees receive?
```

Route:

```text id="6vf8bg"
rag
```

---

Question:

```text id="tqqvpg"
Which items are low stock?
```

Route:

```text id="zv0ohv"
tools
```

---

# 13. Memory Layer

File:

```text id="jlwm0z"
app/memory.py
```

---

Purpose:

```text id="7dq00y"
Conversation History
```

---

Example

User:

```text id="0l98s0"
How many vacation days do employees receive?
```

Assistant answers.

User:

```text id="qqb8zk"
What about part-time employees?
```

Memory provides context.

---

# 14. History-Aware Retrieval

Purpose:

```text id="2m7w9q"
Rewrite Follow-Up Questions
```

---

Example

Input:

```text id="rj9e67"
What about part-time employees?
```

---

Rewritten:

```text id="xw0r71"
What is the PTO policy for part-time employees?
```

---

Then retrieval occurs.

---

# 15. FastAPI Layer

File:

```text id="wukmko"
app/api.py
```

---

Purpose:

```text id="ry78v7"
Expose Assistant as API
```

---

Endpoints:

```text id="bjlwm7"
/health
/chat
/memory/clear
```

---

# Example

```http id="b8fh4j"
POST /chat
```

Request:

```json id="t2r3lk"
{
  "question": "How many vacation days do employees receive?"
}
```

---

Response:

```json id="k7k9r6"
{
  "route": "rag",
  "answer": "...",
  "sources": [...],
  "confidence": "high"
}
```

---

# 16. Testing Layer

Files:

```text id="h0m6o2"
test_tools.py
test_rag.py
test_router.py
```

---

Purpose:

```text id="cr0hy6"
Prevent Regressions
```

---

Examples:

```text id="3j7jzw"
Tool Output Validation
Retriever Validation
Routing Validation
```

---

# 17. LangSmith Layer

Purpose:

```text id="rknz8q"
Observability
```

---

Tracks:

```text id="q9e7c4"
Prompts
Tool Calls
Retriever Calls
LLM Calls
Latency
Errors
```

---

# 18. End-to-End Request Flow

Example:

```text id="g5xw1j"
How many vacation days do employees receive?
```

---

Flow:

```text id="ll1m5n"
User
 ↓
Router
 ↓
RAG
 ↓
Question Rewriter
 ↓
Retriever
 ↓
Prompt
 ↓
Groq
 ↓
Structured Output
 ↓
Response
```

---

# 19. Extension Opportunities

Future Features:

```text id="n6mx41"
Authentication
Persistent Memory
User Profiles
Cloud Vector Database
LangGraph
Human Approval
Multi-Agent Workflows
Evaluation Framework
```

---

# 20. Production Recommendations

Use:

```text id="4mg0mh"
Prompt Templates
Structured Output
Source Attribution
Testing
Tracing
```

Avoid:

```text id="8nrmcl"
Hardcoded Prompts
No Testing
No Monitoring
No Grounding
```

---

# Interview Questions

### Why use RAG for policies?

Policies are knowledge.

RAG retrieves knowledge dynamically.

---

### Why use tools for inventory?

Inventory is structured data.

Tools are more accurate.

---

### Why have a router?

Different questions require different workflows.

---

### Why use structured output?

Predictable application behavior.

---

### Why keep prompts separate?

Prompts are business logic and should be maintainable.

---

# Summary

The RetailOps AI Assistant combines:

```text id="5ct5kl"
LangChain
RAG
Tools
Agents
Memory
Routing
FastAPI
Testing
LangSmith
```

into a realistic enterprise architecture.

This project serves as the foundation for the next phase:

```text id="yjlwm9"
LangGraph
Human-in-the-Loop
Persistence
Multi-Agent Systems
Production AI Architecture
```
