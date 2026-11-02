# 26 - Tools

# Learning Objectives

After completing this document, you should understand:

* What Tools are
* Why Tools exist
* Tools vs RAG
* Tools vs Functions
* Tool Architecture
* Tool Calling
* Tool Design
* Tool Inputs and Outputs
* Structured Data Access
* Production Best Practices
* RetailOps Implementation

---

# 1. What is a Tool?

## Definition

A Tool is a function that an LLM can call to perform an action or retrieve information.

---

Without tools:

```text id="tool1"
LLM
↓
Text Generation
```

---

With tools:

```text id="tool2"
LLM
↓
Tool
↓
Real Data
```

---

# Why Do Tools Exist?

LLMs are limited to:

```text id="tool3"
Training Data
Retrieved Documents
```

---

They cannot directly:

```text id="tool4"
Read Databases
Call APIs
Run Business Logic
```

---

Tools solve this.

---

# 2. Example Problem

Question:

```text id="tool5"
Which items are low in stock?
```

---

RAG:

```text id="tool6"
Not Ideal
```

---

Inventory changes constantly.

---

Document:

```text id="tool7"
May Be Outdated
```

---

Need:

```text id="tool8"
Live Data
```

---

Tool:

```text id="tool9"
Reads inventory.csv
```

---

Returns:

```text id="tool10"
Current Inventory
```

---

# 3. Tools vs RAG

This is extremely important.

---

# RAG

Best for:

```text id="tool11"
Policies
Manuals
Knowledge Bases
Documentation
```

---

Examples:

```text id="tool12"
HR Policy
Returns Policy
Store SOP
```

---

# Tools

Best for:

```text id="tool13"
Live Data
Structured Data
Actions
```

---

Examples:

```text id="tool14"
Inventory
Orders
Incidents
Reports
```

---

# Rule

Static Knowledge:

```text id="tool15"
RAG
```

---

Dynamic Data:

```text id="tool16"
Tools
```

---

# 4. Tool Architecture

```text id="tool17"
Question
 ↓
LLM
 ↓
Tool Selection
 ↓
Tool Execution
 ↓
Tool Result
 ↓
Final Answer
```

---

# Example

Question:

```text id="tool18"
Show low stock items.
```

---

LLM:

```text id="tool19"
Needs Inventory Tool
```

---

Tool:

```text id="tool20"
get_low_stock_items()
```

---

Result:

```text id="tool21"
Inventory Data
```

---

LLM:

```text id="tool22"
Formats Response
```

---

# 5. LangChain Tool

Example:

```python id="tool23"
from langchain_core.tools import tool
```

---

```python id="tool24"
@tool
def get_store_sales():
    ...
```

---

Now the LLM can use:

```text id="tool25"
get_store_sales
```

---

# 6. Tool Inputs

Example:

```python id="tool26"
@tool
def get_store_sales(
    store_id: str
):
    ...
```

---

Input:

```text id="tool27"
store_id=101
```

---

Output:

```text id="tool28"
Store Sales Data
```

---

# Why Inputs Matter

Tools are essentially:

```text id="tool29"
Functions
```

with:

```text id="tool30"
Parameters
```

---

# 7. Tool Outputs

Tool output becomes:

```text id="tool31"
Context
```

for the LLM.

---

Example:

```json id="tool32"
{
  "store_id":101,
  "sales":50000
}
```

---

LLM converts:

```text id="tool33"
Data
```

into:

```text id="tool34"
Human Explanation
```

---

# 8. RetailOps Tools

Current:

```text id="tool35"
get_low_stock_items

get_store_sales

get_open_incidents
```

---

Files:

```text id="tool36"
app/tools.py
```

---

Purpose:

```text id="tool37"
Operational Data
```

---

# 9. Why Tools Are Better Than RAG for Operational Data

Example:

Question:

```text id="tool38"
How many incidents are open?
```

---

RAG:

```text id="tool39"
Needs Reindexing
```

---

Tool:

```text id="tool40"
Reads Current Data
```

---

Much better.

---

# Rule

Current State:

```text id="tool41"
Tools
```

---

Historical Knowledge:

```text id="tool42"
RAG
```

---

# 10. Tool Design Principles

Good Tool:

```text id="tool43"
Single Responsibility
```

---

Example:

```python id="tool44"
get_open_incidents()
```

---

Bad Tool:

```python id="tool45"
do_everything()
```

---

Keep tools focused.

---

# 11. Tool Descriptions

Very important.

---

Example:

```python id="tool46"
@tool
def get_store_sales():
    """
    Get sales information for a store.
    """
```

---

The description teaches the LLM:

```text id="tool47"
When To Use Tool
```

---

Poor descriptions:

```text id="tool48"
Bad Tool Selection
```

---

# 12. Tool Error Handling

Production systems must handle:

```text id="tool49"
File Errors
API Errors
Database Errors
```

---

RetailOps:

```text id="tool50"
Returns Safe Messages
```

---

instead of crashing.

---

# Example

Bad:

```text id="tool51"
Traceback
```

---

Good:

```text id="tool52"
Unable to retrieve inventory.
```

---

# 13. Tools vs Function Calling

Often confused.

---

# Tool

Actual executable code.

---

Example:

```python id="tool53"
get_store_sales()
```

---

# Function Calling

Model capability.

---

Purpose:

```text id="tool54"
Select Tool
```

---

Relationship:

```text id="tool55"
Function Calling
↓
Tool Execution
```

---

# Difference

Tool:

```text id="tool56"
Code
```

---

Function Calling:

```text id="tool57"
Decision Mechanism
```

---

# 14. Tool Selection

Question:

```text id="tool58"
Show low stock items.
```

---

Agent decides:

```text id="tool59"
get_low_stock_items()
```

---

Question:

```text id="tool60"
Show store sales.
```

---

Agent decides:

```text id="tool61"
get_store_sales()
```

---

# Why?

LLM reads:

```text id="tool62"
Tool Name
Description
Schema
```

---

# 15. Production Best Practices

## Use Tools for Dynamic Data

Examples:

```text id="tool63"
Inventory
Orders
Incidents
```

---

## Use RAG for Static Knowledge

Examples:

```text id="tool64"
Policies
Manuals
Procedures
```

---

## Keep Tools Small

Single responsibility.

---

## Add Error Handling

Always.

---

## Add Logging

Track:

```text id="tool65"
Tool Usage
Latency
Failures
```

---

# 16. RetailOps Implementation

Current:

```text id="tool66"
Inventory Tool
Sales Tool
Incident Tool
```

---

Purpose:

```text id="tool67"
Structured Operational Data
```

---

Router decides:

```text id="tool68"
RAG
or
Tools
```

---

# 17. Common Mistakes

## Mistake 1

Using RAG for live data.

---

## Mistake 2

Using tools for documentation.

---

## Mistake 3

Huge tools.

---

## Mistake 4

Poor descriptions.

---

## Mistake 5

No error handling.

---

# 18. Interview Questions

### What is a Tool?

A function an LLM can call.

---

### Why use Tools?

To access live or structured data.

---

### Tools vs RAG?

RAG:

```text id="tool69"
Knowledge
```

Tools:

```text id="tool70"
Actions
Data
```

---

### Tools vs Function Calling?

Tool:

```text id="tool71"
Code
```

Function Calling:

```text id="tool72"
Selection Mechanism
```

---

### Why are tool descriptions important?

They guide tool selection.

---

### Why does RetailOps use tools?

To access inventory, sales, and incident data.

---

# Summary

Tools extend LLM capabilities beyond text generation.

They allow access to:

```text id="tool73"
Databases
Files
APIs
Business Logic
```

and are the preferred solution for:

```text id="tool74"
Dynamic Structured Data
```

RetailOps uses tools to provide:

```text id="tool75"
Inventory
Sales
Incident Information
```

without relying on RAG.

The next document:

```text id="tool76"
27_function_calling.md
```

explains how LLMs decide which tool to use and how modern tool-calling systems work internally.
