# 40 - LangChain Limitations

# Learning Objectives

After completing this document, you should understand:

* What LangChain is good at
* Where LangChain struggles
* Chain-Based Architecture Limitations
* State Management Problems
* Long-Running Workflow Problems
* Human-in-the-Loop Limitations
* Multi-Agent Limitations
* Persistence Limitations
* Why LangGraph Was Created
* When LangChain Is Enough
* When LangGraph Is Better
* RetailOps Lessons

---

# 1. Why Discuss Limitations?

Every technology has strengths and weaknesses.

---

Many developers ask:

```text id="lim1"
Why was LangGraph created if LangChain already exists?
```

---

Answer:

```text id="lim2"
LangChain solves one set of problems.

LangGraph solves another.
```

---

Understanding limitations is essential for architecture decisions.

---

# 2. What LangChain Does Well

LangChain is excellent for:

```text id="lim3"
RAG
Tools
Agents
Prompt Pipelines
Evaluation
Observability
```

---

Examples:

```text id="lim4"
Knowledge Assistants
Support Bots
Internal Search
RetailOps
```

---

These fit naturally into:

```text id="lim5"
Chain Architecture
```

---

# 3. What Is a Chain?

Most LangChain applications follow:

```text id="lim6"
Input
 ↓
Step A
 ↓
Step B
 ↓
Step C
 ↓
Output
```

---

Example:

```text id="lim7"
Question
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

This works extremely well.

---

# Problem

Not all workflows are linear.

---

# 4. State Management Problem

Suppose:

```text id="lim8"
Question
 ↓
Research
 ↓
Review
 ↓
Approval
 ↓
Execution
```

---

Need:

```text id="lim9"
State
```

between steps.

---

Example:

```text id="lim10"
Current Stage
Approval Status
Progress
```

---

Chains do not naturally manage state.

---

# RetailOps

Current:

```text id="lim11"
Stateless Request Processing
```

---

Works well.

---

But complex workflows become harder.

---

# 5. Long-Running Workflow Problem

Example:

```text id="lim12"
Generate Vendor Report
```

---

Steps:

```text id="lim13"
Research
Analysis
Manager Approval
Final Report
```

---

May take:

```text id="lim14"
Hours
```

---

Chain model assumes:

```text id="lim15"
Single Request
Single Response
```

---

Not ideal.

---

# 6. Human-in-the-Loop Problem

Enterprise example:

```text id="lim16"
Refund Request
```

---

Need:

```text id="lim17"
AI Recommendation
 ↓
Manager Approval
 ↓
Execution
```

---

Approval may occur:

```text id="lim18"
Tomorrow
```

---

Chains struggle because:

```text id="lim19"
Execution Ends
```

---

No persistent workflow.

---

# 7. Retry Problem

Suppose:

```text id="lim20"
Tool Call Failed
```

---

Need:

```text id="lim21"
Retry
```

---

Maybe:

```text id="lim22"
Retry 3 Times
```

---

Chain architecture:

```text id="lim23"
Not Natural
```

---

Must implement manually.

---

# 8. Branching Complexity

Simple routing:

```text id="lim24"
General
RAG
Tools
```

---

Easy.

---

Complex branching:

```text id="lim25"
Research
Approval
Escalation
Review
Execution
```

---

Chains become difficult to maintain.

---

# 9. Multi-Agent Problem

Example:

```text id="lim26"
Research Agent
Reviewer Agent
Planner Agent
```

---

Need:

```text id="lim27"
Shared State
Communication
```

---

Chain architecture becomes messy.

---

# 10. Memory Persistence Problem

Current RetailOps:

```text id="lim28"
In-Memory History
```

---

Restart:

```text id="lim29"
Lost
```

---

Enterprise workflows require:

```text id="lim30"
Persistent State
```

---

Across:

```text id="lim31"
Days
Weeks
```

---

# 11. Checkpointing Problem

Question:

```text id="lim32"
Workflow crashes halfway through.
```

---

Need:

```text id="lim33"
Resume From Last Step
```

---

Chains generally restart.

---

Not ideal.

---

# 12. Auditability Problem

Enterprise systems often require:

```text id="lim34"
Who Approved?
Who Rejected?
What Happened?
```

---

Need:

```text id="lim35"
Workflow State
```

---

Chains do not naturally track this.

---

# 13. Visualization Problem

Small chains:

```text id="lim36"
Easy
```

---

Large workflows:

```text id="lim37"
Hard To Understand
```

---

Need:

```text id="lim38"
Graph View
```

---

Which LangGraph provides.

---

# 14. LangChain vs Workflow Engines

Traditional workflow systems:

```text id="lim39"
Airflow
Temporal
Step Functions
```

---

Support:

```text id="lim40"
State
Retries
Persistence
```

---

LangChain was not originally designed for this.

---

# 15. Why LangGraph Was Created

LangGraph solves:

```text id="lim41"
State
Loops
Persistence
Retries
Human Approval
Multi-Agent Workflows
```

---

Instead of:

```text id="lim42"
Chain
```

---

Use:

```text id="lim43"
Graph
```

---

Architecture:

```text id="lim44"
Nodes
Edges
State
```

---

# 16. When LangChain Is Enough

Use LangChain when:

```text id="lim45"
RAG
Tools
Simple Agents
Prompt Pipelines
```

---

RetailOps:

```text id="lim46"
Current Architecture
```

---

Fits very well.

---

# 17. When LangGraph Is Better

Use LangGraph when:

```text id="lim47"
Long Running Workflows
Human Approval
Persistent State
Multi-Agent Systems
Complex Branching
```

---

Examples:

```text id="lim48"
Research Assistants
Enterprise Workflows
Business Process Automation
```

---

# 18. RetailOps Assessment

Current system:

```text id="lim49"
General Chat
RAG
Tools
Router
```

---

LangChain is sufficient.

---

Future enterprise version:

```text id="lim50"
Approval
Escalation
Persistent State
```

---

Likely requires:

```text id="lim51"
LangGraph
```

---

# 19. Production Best Practices

## Do Not Use LangGraph Prematurely

Start simple.

---

## Use LangChain First

When possible.

---

## Introduce LangGraph Only When Needed

Based on workflow complexity.

---

## Separate RAG From Workflow

Good architecture.

---

# 20. Common Mistakes

## Mistake 1

Using LangGraph for simple RAG.

---

## Mistake 2

Using chains for long-running workflows.

---

## Mistake 3

Building manual state management.

---

## Mistake 4

Ignoring workflow complexity.

---

## Mistake 5

Assuming LangChain and LangGraph compete.

---

# 21. Interview Questions

### What are LangChain's biggest limitations?

State management, persistence, and workflow orchestration.

---

### Why was LangGraph created?

To support stateful AI workflows.

---

### LangChain vs LangGraph?

LangChain:

```text id="lim52"
Chains
```

LangGraph:

```text id="lim53"
Workflows
```

---

### When is LangChain sufficient?

RAG, tools, and simple agents.

---

### When should LangGraph be used?

Long-running, stateful, multi-step workflows.

---

### Why is RetailOps currently using LangChain?

Because current requirements fit chain-based architecture well.

---

# Summary

LangChain is excellent for:

```text id="lim54"
RAG
Tools
Agents
Prompt Pipelines
```

but becomes less natural when workflows require:

```text id="lim55"
State
Persistence
Retries
Approvals
Multi-Agent Coordination
```

These limitations led to the creation of:

```text id="lim56"
LangGraph
```

which extends LangChain into a workflow orchestration framework.

The next document:

```text id="lim57"
41_langgraph_transition.md
```

explains how to decide when to move from LangChain to LangGraph and how RetailOps could evolve into a graph-based architecture.
