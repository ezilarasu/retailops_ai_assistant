# 06 - Tools and Agents

# Learning Objectives

After completing this document, you should understand:

* What a Tool is
* Why Tools exist
* Function Calling
* Tool Calling Lifecycle
* Tool Design Best Practices
* LangChain Tools
* Agents
* Agent Execution Loop
* ReAct Pattern
* Tool Selection
* Multi-Tool Agents
* Router Chains
* Memory in Agent Systems
* Agent vs Chain
* Agent vs RAG
* RetailOps Agent Architecture
* Production Agent Design

---

# 1. What is a Tool?

## Definition

A Tool is a function that can be called by an LLM.

Example:

```python id="1vgh4x"
@tool
def get_weather(city: str):
    ...
```

---

## Why Do Tools Exist?

LLMs cannot:

```text id="j1c4lm"
Query Databases
Call APIs
Read CSV Files
Check Inventory
Send Emails
Create Tickets
```

directly.

Tools extend LLM capabilities.

---

# Traditional LLM

```text id="v3h7o9"
Question
 ↓
LLM
 ↓
Answer
```

---

# Tool-Enabled LLM

```text id="8p6k7v"
Question
 ↓
LLM
 ↓
Tool
 ↓
Answer
```

---

# RetailOps Example

Question:

```text id="4z7kqs"
Which items are low stock in store 102?
```

The LLM does not know.

Tool provides the answer.

---

# 2. Function Calling

## Definition

Function Calling allows the model to decide:

```text id="h7g3mw"
I need external information.
```

and request a tool invocation.

---

# Example

User:

```text id="w3u9pf"
Who owns SKU DENIM-4421?
```

Model decides:

```text id="h7n1qj"
Use vendor lookup tool.
```

---

# Important Concept

The model does NOT execute code.

---

The model generates:

```json id="vx1pyt"
{
  "tool": "get_vendor_for_sku",
  "args": {
    "sku": "DENIM-4421"
  }
}
```

Your application executes:

```python id="twv9ci"
get_vendor_for_sku(
    "DENIM-4421"
)
```

---

# Why This Matters

Security.

The model never directly:

```text id="3ydbf5"
Deletes Data
Sends Money
Calls APIs
```

without your code.

---

# 3. Tool Calling Lifecycle

Full lifecycle:

```text id="91uvjc"
User Question
 ↓
LLM
 ↓
Choose Tool
 ↓
Generate Arguments
 ↓
Tool Execution
 ↓
Tool Result
 ↓
LLM
 ↓
Final Answer
```

---

# RetailOps Example

Question:

```text id="o4c4na"
Are there open incidents for store 102?
```

Flow:

```text id="m8y7kc"
Question
 ↓
Agent
 ↓
get_open_incidents()
 ↓
JSON Result
 ↓
Agent
 ↓
Answer
```

---

# 4. Tool Anatomy

A good tool contains:

```python id="vkp4u4"
@tool
def tool_name(...):
    """
    Description
    """
```

---

# Tool Name

Example:

```python id="k5l1vb"
get_vendor_for_sku
```

---

# Why Tool Names Matter

Bad:

```python id="3ew3x5"
helper()
```

---

Good:

```python id="3jlm0q"
get_vendor_for_sku()
```

---

The model uses names to infer intent.

---

# Tool Description

Example:

```python id="ew5y72"
"""
Get vendor details for a product SKU.
"""
```

---

# Why Descriptions Matter

The model reads descriptions to decide:

```text id="l7j13w"
When to use a tool.
```

---

# Tool Arguments

Example:

```python id="rq4txz"
sku: str
```

---

The model uses these to construct inputs.

---

# 5. Tool Design Best Practices

---

# Small Focused Tools

Good:

```python id="p0v2jh"
get_vendor_for_sku()

get_open_incidents()

get_low_stock_items()
```

---

Bad:

```python id="2l08uk"
super_tool()
```

that does everything.

---

# Descriptive Names

Good:

```python id="jlwmto"
get_vendor_for_sku()
```

Bad:

```python id="jlwmtp"
lookup()
```

---

# Descriptive Docstrings

Good:

```python id="jlwmtq"
Get vendor contact information.
```

Bad:

```python id="jlwmtr"
Utility function.
```

---

# Return Strings

For LLM compatibility:

```python id="jlwmts"
return json.dumps(...)
```

---

Avoid:

```python id="jlwmtt"
return dict
return list
```

when tool calling providers expect strings.

---

# 6. LangChain Tools

## Definition

LangChain wraps functions using:

```python id="jlwmtu"
@tool
```

---

## Example

```python id="jlwmtv"
from langchain_core.tools import tool

@tool
def multiply(a: int, b: int):
    return str(a * b)
```

---

## Benefits

```text id="jlwmtw"
Schema Generation
Validation
Agent Integration
```

---

# 7. What is an Agent?

## Definition

An Agent is an LLM that can decide what actions to take.

---

# Traditional Chain

```text id="jlwmtx"
Prompt
 ↓
LLM
 ↓
Answer
```

Fixed workflow.

---

# Agent

```text id="jlwmty"
Question
 ↓
Decision
 ↓
Tool
 ↓
Observation
 ↓
Answer
```

Dynamic workflow.

---

# 8. Agent Execution Loop

The heart of every agent.

```text id="jlwmtz"
Question
 ↓
Reason
 ↓
Choose Tool
 ↓
Execute Tool
 ↓
Observe Result
 ↓
Continue Reasoning
 ↓
Final Answer
```

---

# Why It Matters

Agents can:

```text id="jlwmu0"
Search
Calculate
Retrieve Data
Combine Information
```

without hardcoded workflows.

---

# 9. ReAct Pattern

ReAct =

```text id="jlwmu1"
Reason
+
Act
```

---

# Example

Question:

```text id="jlwmu2"
Who owns SKU DENIM-4421?
```

---

Reason:

```text id="jlwmu3"
Need vendor lookup.
```

---

Act:

```text id="jlwmu4"
Call get_vendor_for_sku().
```

---

Observe:

```text id="jlwmu5"
Vendor found.
```

---

Answer:

```text id="jlwmu6"
BlueRiver Denim Supply.
```

---

# Why ReAct Works

Combines:

```text id="jlwmu7"
Reasoning
Tool Use
```

into a loop.

---

# 10. Agent vs Chain

Very common interview question.

---

# Chain

Fixed sequence.

Example:

```text id="jlwmu8"
Prompt
 ↓
LLM
 ↓
Parser
```

---

# Agent

Dynamic sequence.

Example:

```text id="jlwmu9"
Question
 ↓
Choose Tool
 ↓
Execute Tool
 ↓
Answer
```

---

# When to Use Chains

Use when:

```text id="jlwmua"
Workflow is predictable.
```

Examples:

```text id="jlwmub"
Summarization
Classification
Extraction
```

---

# When to Use Agents

Use when:

```text id="jlwmuc"
Decision making is required.
```

Examples:

```text id="jlwmud"
Inventory Lookup
Research Assistant
Customer Support
```

---

# 11. Agent vs RAG

Another important distinction.

---

# RAG

Purpose:

```text id="jlwmue"
Retrieve Knowledge
```

---

Examples:

```text id="jlwmuf"
Policies
FAQs
Documentation
```

---

# Tools

Purpose:

```text id="jlwmug"
Perform Actions
Retrieve Structured Data
```

---

Examples:

```text id="jlwmuh"
Inventory
Incidents
Vendors
```

---

# RetailOps Examples

RAG:

```text id="jlwmui"
Vacation Policy
Returns Policy
Store SOP
```

---

Tools:

```text id="jlwmuj"
Vendor Lookup
Inventory Lookup
Incident Lookup
```

---

# 12. Multi-Tool Agents

Agents can use multiple tools.

---

Example:

Available:

```text id="jlwmuk"
Inventory Tool
Vendor Tool
Incident Tool
```

---

Question:

```text id="jlwmul"
Who owns SKU DENIM-4421 and are there open incidents in store 102?
```

---

Possible Flow:

```text id="jlwmum"
Vendor Tool
 ↓
Incident Tool
 ↓
Combined Answer
```

---

# 13. RetailOps Tools

Current Tools:

```text id="jlwmun"
get_low_stock_items()
get_vendor_for_sku()
get_open_incidents()
```

---

# Inventory Tool

Purpose:

```text id="jlwmuo"
CSV Lookup
```

---

# Vendor Tool

Purpose:

```text id="jlwmup"
Vendor Identification
```

---

# Incident Tool

Purpose:

```text id="jlwmuq"
Incident Search
```

---

# 14. RetailOps Agent Architecture

Current Architecture:

```text id="jlwmur"
Question
 ↓
Router
 ↓
Tools Route
 ↓
Agent
 ↓
Tool Selection
 ↓
Tool Execution
 ↓
Answer
```

---

# Why Use a Router?

Not every question needs an agent.

---

Examples:

```text id="jlwmus"
Vacation Policy
```

↓

```text id="jlwmut"
RAG
```

---

Example:

```text id="jlwmuu"
Low Stock Inventory
```

↓

```text id="jlwmuv"
Agent
```

---

# 15. Memory in Agent Systems

Memory enables:

```text id="jlwmuw"
Follow-Up Questions
Conversation Context
```

---

Example:

```text id="jlwmux"
Who owns SKU DENIM-4421?
```

Later:

```text id="jlwmuy"
What is their SLA?
```

Memory helps resolve:

```text id="jlwmuz"
their
```

---

# 16. Common Agent Problems

---

# Tool Hallucination

Model tries:

```text id="jlwmv0"
tool_that_does_not_exist()
```

---

Solution:

```text id="jlwmv1"
Clear Tool Descriptions
```

---

# Poor Tool Selection

Cause:

```text id="jlwmv2"
Ambiguous Tool Names
```

---

# Overusing Agents

Many workflows should remain:

```text id="jlwmv3"
Chains
```

not agents.

---

# Tool Failures

Always handle:

```text id="jlwmv4"
Missing Data
Errors
Timeouts
```

---

# 17. Production Recommendations

Use:

```text id="jlwmv5"
Small Tools
Descriptive Names
Clear Docstrings
String Outputs
Testing
Tracing
```

Avoid:

```text id="jlwmv6"
Huge Tools
Hidden Side Effects
Ambiguous Names
```

---

# 18. Interview Questions

### What is a Tool?

A function callable by an LLM.

---

### What is Function Calling?

The model generating a tool request.

---

### Does the model execute code?

No.

Your application executes tools.

---

### What is an Agent?

An LLM capable of choosing actions.

---

### Difference between Agent and Chain?

Chain:

```text id="jlwmv7"
Fixed Workflow
```

Agent:

```text id="jlwmv8"
Dynamic Workflow
```

---

### What is ReAct?

Reason + Act.

---

### Difference between RAG and Tools?

RAG retrieves knowledge.

Tools retrieve structured data or perform actions.

---

### Why use a Router?

Different questions require different workflows.

---

# Summary

Tools and Agents transform an LLM from:

```text id="jlwmv9"
Text Generator
```

into:

```text id="jlwmva"
Action-Oriented Assistant
```

The RetailOps project demonstrates:

```text id="jlwmvb"
Tool Design
Function Calling
Agent Loops
Router-Based Architecture
Memory
Multi-Workflow Systems
```

These concepts form the foundation for the next phase:

```text id="jlwmvc"
LangGraph
Multi-Agent Systems
Human-in-the-Loop Workflows
Production Agent Architecture
```
