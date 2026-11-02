# 28 - Agents

# Learning Objectives

After completing this document, you should understand:

* What an Agent is
* Why Agents exist
* Agents vs Chains
* Agents vs RAG
* Agents vs Tools
* Agent Architecture
* Tool Selection
* Reasoning and Acting
* ReAct Pattern
* Agent Loops
* Production Best Practices
* RetailOps Implementation

---

# 1. What is an Agent?

## Definition

An Agent is an LLM-powered system that can:

```text id="ag1"
Reason
Decide
Act
```

to achieve a goal.

---

Unlike a simple chain:

```text id="ag2"
Input
↓
Output
```

---

An agent can:

```text id="ag3"
Choose Tools
Call Tools
Analyze Results
Call More Tools
Generate Answer
```

---

# Simple Explanation

Chain:

```text id="ag4"
Follow Instructions
```

---

Agent:

```text id="ag5"
Decide What To Do
```

---

# 2. Why Do Agents Exist?

Many tasks cannot be solved using:

```text id="ag6"
One Prompt
```

---

Example:

```text id="ag7"
Which stores have low stock
and how much revenue did they generate?
```

---

Need:

```text id="ag8"
Inventory Tool
+
Sales Tool
```

---

Agent decides:

```text id="ag9"
Which Tool
Which Order
```

---

# 3. Agent vs Chain

Most important distinction.

---

# Chain

Flow:

```text id="ag10"
Input
↓
Prompt
↓
LLM
↓
Output
```

---

Behavior:

```text id="ag11"
Fixed
```

---

# Agent

Flow:

```text id="ag12"
Input
↓
Reason
↓
Tool
↓
Reason
↓
Tool
↓
Answer
```

---

Behavior:

```text id="ag13"
Dynamic
```

---

# Difference

Chain:

```text id="ag14"
Predefined Path
```

---

Agent:

```text id="ag15"
Chooses Path
```

---

# 4. Agent vs RAG

Another common interview question.

---

# RAG

Goal:

```text id="ag16"
Retrieve Knowledge
```

---

Question:

```text id="ag17"
What is the return policy?
```

---

RAG is perfect.

---

# Agent

Goal:

```text id="ag18"
Perform Actions
```

---

Question:

```text id="ag19"
Show low stock items.
```

---

Need:

```text id="ag20"
Tool Calls
```

---

# Difference

RAG:

```text id="ag21"
Knowledge
```

---

Agent:

```text id="ag22"
Actions
```

---

# 5. Agent vs Tools

Tools:

```text id="ag23"
Capabilities
```

---

Agent:

```text id="ag24"
Decision Maker
```

---

Example

Tool:

```python id="ag25"
get_store_sales()
```

---

Agent decides:

```text id="ag26"
Use get_store_sales()
```

---

# Relationship

```text id="ag27"
Agent
↓
Uses Tools
```

---

# 6. Agent Architecture

```text id="ag28"
Question
 ↓
Agent
 ↓
Reason
 ↓
Tool Selection
 ↓
Tool Execution
 ↓
Observation
 ↓
Answer
```

---

# Why This Matters

Agent can adapt.

---

Unlike chains:

```text id="ag29"
One Fixed Flow
```

---

# 7. Agent Loop

Core idea:

```text id="ag30"
Think
Act
Observe
Repeat
```

---

Example

Question:

```text id="ag31"
Show low stock items.
```

---

Agent:

```text id="ag32"
Need inventory tool.
```

---

Tool:

```text id="ag33"
Returns inventory.
```

---

Agent:

```text id="ag34"
Now I can answer.
```

---

# This Loop

is what makes agents powerful.

---

# 8. ReAct Pattern

ReAct =

```text id="ag35"
Reason
+
Act
```

---

Architecture:

```text id="ag36"
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

Example

Thought:

```text id="ag37"
Need inventory data.
```

---

Action:

```text id="ag38"
Call Tool
```

---

Observation:

```text id="ag39"
Inventory Result
```

---

Answer:

```text id="ag40"
Low stock items are...
```

---

Most modern agents follow this pattern.

---

# 9. RetailOps Agent

Current:

```python id="ag41"
tool_agent
```

---

Tools:

```text id="ag42"
Inventory
Sales
Incidents
```

---

Agent receives:

```text id="ag43"
Question
```

---

Decides:

```text id="ag44"
Which Tool To Use
```

---

# 10. Why Agents Are Useful

Question:

```text id="ag45"
Which stores have low inventory?
```

---

Need:

```text id="ag46"
Inventory Tool
```

---

Question:

```text id="ag47"
What are open incidents?
```

---

Need:

```text id="ag48"
Incident Tool
```

---

Question:

```text id="ag49"
Show sales data.
```

---

Need:

```text id="ag50"
Sales Tool
```

---

Agent handles this dynamically.

---

# 11. Why Not Use Agents Everywhere?

Very important.

---

Agents introduce:

```text id="ag51"
Complexity
Latency
Cost
```

---

Simple task:

```text id="ag52"
Translate Text
```

---

Agent:

```text id="ag53"
Overkill
```

---

Chain:

```text id="ag54"
Better
```

---

# Rule

Use agents only when:

```text id="ag55"
Decision Making
```

is required.

---

# 12. Agent Tradeoffs

## Pros

```text id="ag56"
Flexible
Powerful
Adaptive
```

---

## Cons

```text id="ag57"
More Expensive
More Complex
Harder To Test
```

---

# 13. Agent vs Router

RetailOps uses both.

---

# Router

Purpose:

```text id="ag58"
Choose Workflow
```

---

Example:

```text id="ag59"
RAG
Tools
General Chat
```

---

# Agent

Purpose:

```text id="ag60"
Choose Tool
```

---

Different responsibilities.

---

# Architecture

```text id="ag61"
Router
 ↓
Agent
```

possible.

---

# 14. RetailOps Architecture

Current:

```text id="ag62"
Question
 ↓
Router
 ├── General
 ├── RAG
 └── Agent
```

---

Agent handles:

```text id="ag63"
Tool Questions
```

---

# 15. Production Best Practices

## Keep Tools Small

One responsibility.

---

## Add Tool Descriptions

Critical.

---

## Add Logging

Track:

```text id="ag64"
Tool Usage
Latency
Failures
```

---

## Add Evaluation

Agents must be tested.

---

## Avoid Unnecessary Agents

Prefer:

```text id="ag65"
Chains
```

when possible.

---

# 16. Common Mistakes

## Mistake 1

Using agents for everything.

---

## Mistake 2

Huge tools.

---

## Mistake 3

No observability.

---

## Mistake 4

No evaluation.

---

## Mistake 5

Confusing agents and tools.

---

# 17. Interview Questions

### What is an Agent?

An LLM system that can reason, select tools, and act.

---

### Agent vs Chain?

Chain:

```text id="ag66"
Fixed Workflow
```

Agent:

```text id="ag67"
Dynamic Workflow
```

---

### Agent vs Tool?

Tool:

```text id="ag68"
Capability
```

Agent:

```text id="ag69"
Decision Maker
```

---

### Why use Agents?

To solve tasks requiring dynamic decisions.

---

### What is ReAct?

Reason + Act pattern used by modern agents.

---

### Why doesn't RetailOps use agents for everything?

Chains are simpler, faster, and cheaper when decisions are not required.

---

# Summary

Agents are dynamic AI systems capable of:

```text id="ag70"
Reasoning
Tool Selection
Action Execution
```

They are most useful when workflows cannot be predefined.

RetailOps uses agents selectively for:

```text id="ag71"
Inventory
Sales
Incident Data
```

while continuing to use:

```text id="ag72"
Chains
RAG
Routers
```

for simpler tasks.

The next document:

```text id="ag73"
29_react_pattern.md
```

explains the ReAct architecture in depth, including reasoning loops, observations, and multi-step tool usage.
