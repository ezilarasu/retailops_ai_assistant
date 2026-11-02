# 29 - ReAct Pattern (Reason + Act)

# Learning Objectives

After completing this document, you should understand:

* What ReAct is
* Why ReAct exists
* Reasoning vs Acting
* ReAct Architecture
* Thought → Action → Observation Loop
* ReAct vs Chains
* ReAct vs RAG
* ReAct vs Tool Calling
* Multi-Step Tool Usage
* Production Tradeoffs
* RetailOps Implementation

---

# 1. What is ReAct?

ReAct stands for:

```text id="react1"
Reason
+
Act
```

---

## Definition

ReAct is an agent pattern where the model alternates between:

```text id="react2"
Thinking
↓
Taking Action
↓
Observing Results
```

until it can answer the question.

---

# Why Was ReAct Created?

Traditional chains:

```text id="react3"
Question
↓
Answer
```

---

Problem:

Some tasks require:

```text id="react4"
Reasoning
Tool Usage
Multiple Steps
```

---

Example:

```text id="react5"
Which stores have low inventory and what are their sales?
```

---

Need:

```text id="react6"
Inventory Tool
+
Sales Tool
```

---

A single prompt is not enough.

---

# 2. Core ReAct Loop

```text id="react7"
Thought
↓
Action
↓
Observation
↓
Thought
↓
Action
↓
Observation
↓
Answer
```

---

This loop is the heart of ReAct.

---

# 3. Example

Question:

```text id="react8"
Which stores have low inventory?
```

---

Thought:

```text id="react9"
I need inventory data.
```

---

Action:

```text id="react10"
Call get_low_stock_items()
```

---

Observation:

```text id="react11"
Inventory data returned.
```

---

Thought:

```text id="react12"
I now have enough information.
```

---

Answer:

```text id="react13"
Stores 101 and 102 have low inventory.
```

---

# Why This Is Powerful

The model can adapt based on:

```text id="react14"
Tool Results
```

---

# 4. Thought

Thought represents:

```text id="react15"
Reasoning
```

---

Example:

```text id="react16"
Need sales data.
```

---

Not shown to end users.

---

Purpose:

```text id="react17"
Plan Next Step
```

---

# 5. Action

Action represents:

```text id="react18"
Tool Usage
```

---

Example:

```text id="react19"
get_store_sales()
```

---

Action produces:

```text id="react20"
Observation
```

---

# 6. Observation

Observation is:

```text id="react21"
Tool Result
```

---

Example:

```json id="react22"
{
  "store":101,
  "sales":50000
}
```

---

The model can now reason using:

```text id="react23"
Real Data
```

---

# 7. Why Observation Matters

Without observation:

```text id="react24"
No Feedback Loop
```

---

ReAct becomes:

```text id="react25"
Blind
```

---

Observation enables:

```text id="react26"
Adaptive Decision Making
```

---

# 8. ReAct Architecture

```text id="react27"
Question
 ↓
Thought
 ↓
Action
 ↓
Observation
 ↓
Thought
 ↓
Answer
```

---

RetailOps agent follows this pattern internally.

---

# 9. ReAct vs Chains

## Chain

```text id="react28"
Input
↓
Output
```

---

Fixed path.

---

Example:

```text id="react29"
RAG Chain
```

---

# ReAct

```text id="react30"
Input
↓
Reason
↓
Tool
↓
Reason
↓
Answer
```

---

Dynamic path.

---

# Difference

Chain:

```text id="react31"
Predefined Workflow
```

---

ReAct:

```text id="react32"
Adaptive Workflow
```

---

# 10. ReAct vs Tool Calling

Very important.

---

# Tool Calling

Ability to:

```text id="react33"
Call Tool
```

---

# ReAct

Strategy for:

```text id="react34"
Reasoning About Tool Calls
```

---

Difference:

Tool Calling:

```text id="react35"
Capability
```

---

ReAct:

```text id="react36"
Workflow Pattern
```

---

# 11. ReAct vs RAG

RAG:

```text id="react37"
Retrieve Knowledge
```

---

ReAct:

```text id="react38"
Take Actions
```

---

Question:

```text id="react39"
What is the return policy?
```

---

RAG.

---

Question:

```text id="react40"
Show current store sales.
```

---

ReAct + Tools.

---

# 12. Multi-Step ReAct Example

Question:

```text id="react41"
Which stores have low inventory and what are their sales?
```

---

Thought:

```text id="react42"
Need inventory.
```

---

Action:

```text id="react43"
Inventory Tool
```

---

Observation:

```text id="react44"
Stores 101 and 102.
```

---

Thought:

```text id="react45"
Need sales for those stores.
```

---

Action:

```text id="react46"
Sales Tool
```

---

Observation:

```text id="react47"
Sales Data
```

---

Answer:

```text id="react48"
Combined Report
```

---

This is impossible with a simple chain.

---

# 13. Why ReAct Became Popular

Before ReAct:

```text id="react49"
One Prompt
```

---

After ReAct:

```text id="react50"
Reason
Act
Observe
Repeat
```

---

Much more powerful.

---

Most modern agents are ReAct-inspired.

---

# 14. RetailOps Agent

Current:

```text id="react51"
Tool Agent
```

---

Tools:

```text id="react52"
Inventory
Sales
Incidents
```

---

Agent:

```text id="react53"
Reasons
Selects Tool
Uses Tool
Answers
```

---

# 15. Production Tradeoffs

## Pros

```text id="react54"
Flexible
Adaptive
Powerful
```

---

## Cons

```text id="react55"
More Cost
More Latency
More Complexity
```

---

# Why?

Each step may require:

```text id="react56"
Additional Model Calls
```

---

# 16. ReAct and LangGraph

Interesting relationship.

---

LangChain ReAct:

```text id="react57"
Short-Term Reasoning Loop
```

---

LangGraph:

```text id="react58"
Persistent Workflow Loop
```

---

LangGraph is often used when:

```text id="react59"
ReAct Workflows
Become Complex
```

---

# 17. Production Best Practices

## Keep Tools Focused

Avoid giant tools.

---

## Log Observations

Track:

```text id="react60"
Tool Calls
Results
Latency
```

---

## Limit Iterations

Avoid:

```text id="react61"
Infinite Loops
```

---

## Evaluate Agent Behavior

Measure:

```text id="react62"
Correct Tool Selection
```

---

## Use ReAct Only When Needed

Do not replace:

```text id="react63"
Simple Chains
```

with agents.

---

# 18. Common Mistakes

## Mistake 1

Using ReAct for everything.

---

## Mistake 2

No tool descriptions.

---

## Mistake 3

No iteration limits.

---

## Mistake 4

No logging.

---

## Mistake 5

Confusing tool calling with ReAct.

---

# 19. Interview Questions

### What is ReAct?

A reasoning and acting framework where the model alternates between thought, action, and observation.

---

### Why use ReAct?

To solve multi-step tasks requiring tools.

---

### ReAct vs Chains?

Chains:

```text id="react64"
Fixed Workflow
```

ReAct:

```text id="react65"
Dynamic Workflow
```

---

### ReAct vs Tool Calling?

Tool Calling:

```text id="react66"
Capability
```

ReAct:

```text id="react67"
Reasoning Pattern
```

---

### What is Observation?

The result returned by a tool.

---

### Why does RetailOps use ReAct?

To dynamically retrieve inventory, sales, and incident data.

---

# Summary

ReAct is one of the most influential agent architectures.

It enables:

```text id="react68"
Reasoning
Tool Usage
Multi-Step Workflows
```

through a continuous:

```text id="react69"
Thought
Action
Observation
```

loop.

RetailOps uses ReAct principles through its tool agent to interact with operational data dynamically.

The next document:

```text id="react70"
30_router_pattern.md
```

covers routing architectures, intent classification, workflow selection, and how RetailOps decides between General Chat, RAG, and Agent workflows.
