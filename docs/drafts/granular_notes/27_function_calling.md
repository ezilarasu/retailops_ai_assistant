# 27 - Function Calling

# Learning Objectives

After completing this document, you should understand:

* What Function Calling is
* Why Function Calling exists
* Function Calling vs Tools
* How Function Calling works
* Tool Selection Process
* Function Schemas
* Structured Arguments
* Function Calling Architecture
* Multi-Step Tool Usage
* Production Best Practices
* RetailOps Implementation

---

# 1. What is Function Calling?

## Definition

Function Calling is a model capability that allows an LLM to decide:

```text id="fc1"
Which Tool To Use
```

and

```text id="fc2"
What Arguments To Pass
```

---

Important:

Function Calling does NOT execute tools.

---

It only decides:

```text id="fc3"
Tool Name
Arguments
```

---

# Example

Question:

```text id="fc4"
Show low stock items for store 101.
```

---

LLM decides:

```json id="fc5"
{
  "tool": "get_low_stock_items",
  "arguments": {
    "store_id": "101"
  }
}
```

---

Then:

```text id="fc6"
Application Executes Tool
```

---

# 2. Why Does Function Calling Exist?

Without function calling:

```text id="fc7"
LLM
↓
Text
```

---

Problem:

LLM cannot reliably invoke code.

---

Example:

```text id="fc8"
Call get_store_sales(101)
```

---

Could appear as:

```text id="fc9"
Text
```

not an actual function call.

---

Function Calling solves this.

---

# 3. Tools vs Function Calling

This is one of the most common interview questions.

---

# Tool

Actual code.

---

Example:

```python id="fc10"
@tool
def get_store_sales():
    ...
```

---

# Function Calling

Model capability.

---

Purpose:

```text id="fc11"
Choose Tool
```

---

# Relationship

```text id="fc12"
Function Calling
↓
Tool Selection
↓
Tool Execution
```

---

# Difference

Tool:

```text id="fc13"
Code
```

---

Function Calling:

```text id="fc14"
Decision Logic
```

---

# 4. Function Calling Architecture

```text id="fc15"
Question
 ↓
LLM
 ↓
Function Call
 ↓
Tool Execution
 ↓
Tool Result
 ↓
LLM
 ↓
Answer
```

---

This is the foundation of modern agents.

---

# 5. Tool Schema

Function Calling requires schemas.

---

Example:

```python id="fc16"
@tool
def get_store_sales(
    store_id: str
):
    ...
```

---

Schema:

```json id="fc17"
{
  "name":"get_store_sales",
  "parameters":{
     "store_id":"string"
  }
}
```

---

LLM sees:

```text id="fc18"
Name
Description
Parameters
```

---

and decides when to use it.

---

# 6. Tool Description Importance

Question:

```text id="fc19"
How much revenue did store 101 generate?
```

---

Tool:

```python id="fc20"
"""
Get sales information for a store.
"""
```

---

LLM understands:

```text id="fc21"
This Tool Is Relevant
```

---

Bad descriptions:

```text id="fc22"
Bad Tool Selection
```

---

# 7. Argument Generation

Question:

```text id="fc23"
Show sales for store 101.
```

---

Function Call:

```json id="fc24"
{
  "store_id":"101"
}
```

---

Model extracts:

```text id="fc25"
Arguments
```

from user input.

---

# Why This Matters

Without function calling:

```text id="fc26"
Manual Parsing
```

---

With function calling:

```text id="fc27"
Automatic Parsing
```

---

# 8. Function Calling Flow

Question:

```text id="fc28"
Show open incidents.
```

---

Model:

```text id="fc29"
Select Tool
```

---

Tool:

```text id="fc30"
Returns Incident Data
```

---

Model:

```text id="fc31"
Explains Results
```

---

Final Answer:

```text id="fc32"
Human Friendly
```

---

# 9. Multi-Step Function Calling

More advanced systems may call:

```text id="fc33"
Tool A
```

then:

```text id="fc34"
Tool B
```

---

Example:

```text id="fc35"
Find Store
↓
Find Sales
↓
Generate Report
```

---

This is where agents become powerful.

---

# 10. Function Calling vs Structured Output

Very important.

---

# Structured Output

Purpose:

```text id="fc36"
Generate Schema
```

---

Example:

```python id="fc37"
RAGResponse
```

---

# Function Calling

Purpose:

```text id="fc38"
Execute Tool
```

---

# Difference

Structured Output:

```text id="fc39"
Output Contract
```

---

Function Calling:

```text id="fc40"
Action Selection
```

---

# 11. Function Calling vs RAG

RAG:

```text id="fc41"
Retrieve Documents
```

---

Function Calling:

```text id="fc42"
Call Code
```

---

Example

Question:

```text id="fc43"
What is the return policy?
```

---

RAG.

---

Question:

```text id="fc44"
How many incidents are open?
```

---

Function Calling.

---

# 12. Modern LLM Function Calling

Supported by:

```text id="fc45"
OpenAI
Anthropic
Groq
Gemini
```

---

LangChain abstracts this.

---

Example:

```python id="fc46"
create_tool_calling_agent(...)
```

---

RetailOps uses this pattern.

---

# 13. RetailOps Function Calling

Current:

```text id="fc47"
Inventory Tool
Sales Tool
Incident Tool
```

---

Agent receives:

```text id="fc48"
Question
```

---

Function Calling decides:

```text id="fc49"
Tool
Arguments
```

---

Tool executes.

---

Answer generated.

---

# 14. Why Function Calling Is Better Than Prompt Tricks

Old approach:

```text id="fc50"
Return:
CALL_TOOL(...)
```

---

Problem:

```text id="fc51"
Unreliable
```

---

Modern approach:

```text id="fc52"
Native Function Calling
```

---

More reliable.

---

# 15. Production Best Practices

## Small Focused Tools

One responsibility.

---

## Good Descriptions

Very important.

---

## Validate Arguments

Never trust raw inputs.

---

## Add Error Handling

Always.

---

## Log Tool Calls

Track:

```text id="fc53"
Tool Name
Arguments
Latency
Failures
```

---

# 16. Common Mistakes

## Mistake 1

Confusing tools and function calling.

---

## Mistake 2

Huge tools.

---

## Mistake 3

Bad descriptions.

---

## Mistake 4

No argument validation.

---

## Mistake 5

Using RAG for dynamic data.

---

# 17. Interview Questions

### What is Function Calling?

A model capability that selects tools and generates arguments.

---

### Function Calling vs Tools?

Tool:

```text id="fc54"
Code
```

Function Calling:

```text id="fc55"
Selection Mechanism
```

---

### Why use Function Calling?

To allow LLMs to interact with external systems reliably.

---

### Function Calling vs Structured Output?

Function Calling:

```text id="fc56"
Execute Actions
```

Structured Output:

```text id="fc57"
Generate Schema
```

---

### Why are tool descriptions important?

They guide tool selection.

---

### Why does RetailOps use Function Calling?

To access operational data through tools.

---

# Summary

Function Calling is the bridge between:

```text id="fc58"
Language Models
```

and

```text id="fc59"
Executable Code
```

It enables LLMs to:

```text id="fc60"
Choose Tools
Generate Arguments
Execute Workflows
```

and forms the foundation of modern AI agents.

The next document:

```text id="fc61"
28_agents.md
```

explains how tools, function calling, reasoning, and decision-making combine to create intelligent AI agents.
