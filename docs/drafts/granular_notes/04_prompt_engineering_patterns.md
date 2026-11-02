# 04 - Prompt Engineering Patterns

# Learning Objectives

After completing this document, you should understand:

* What Prompt Engineering is
* Why Prompt Engineering matters
* Prompt Design Patterns
* Zero-Shot Prompting
* Few-Shot Prompting
* Role Prompting
* Constraint Prompting
* Structured Prompting
* Chain of Thought Prompting
* Routing Prompts
* RAG Prompts
* Evaluation Prompts
* Prompt Tradeoffs
* Production Prompt Engineering

---

# 1. What is Prompt Engineering?

## Definition

Prompt Engineering is the process of designing prompts that reliably guide an LLM toward the desired behavior and output.

Think of a prompt as:

```text id="jjlwm1"
A Program Written in Natural Language
```

---

## Why Does Prompt Engineering Matter?

LLMs are probabilistic.

Small prompt changes can produce:

```text id="jjlwm2"
Different Answers
Different Formats
Different Behavior
```

---

Example:

Prompt:

```text id="jjlwm3"
Explain Python.
```

Output:

```text id="jjlwm4"
Generic answer
```

---

Prompt:

```text id="jjlwm5"
Explain Python to a beginner.

Include:
- Definition
- Example
- Common use cases

Limit to 150 words.
```

Output:

```text id="jjlwm6"
Much more useful answer
```

---

# 2. Prompt Structure

A production prompt typically contains:

```text id="jjlwm7"
Role
Task
Context
Constraints
Output Format
```

---

Example:

```text id="jjlwm8"
Role:
HR Assistant

Task:
Answer policy questions

Context:
Provided policy documents

Constraints:
Use only provided context

Output:
Answer + Sources
```

---

# 3. Zero-Shot Prompting

## Definition

Ask the model to perform a task without providing examples.

---

Example:

```text id="jjlwm9"
Classify sentiment:

I love this product.
```

---

Output:

```text id="jjlwm10"
Positive
```

---

## Why Use It?

Simple tasks often do not need examples.

---

## When To Use

```text id="jjlwm11"
Classification
Summarization
General Questions
```

---

## Pros

```text id="jjlwm12"
Simple
Cheap
Fast
```

---

## Cons

```text id="jjlwm13"
Less reliable for complex tasks
```

---

# 4. Few-Shot Prompting

## Definition

Provide examples before asking the model to perform a task.

---

Example:

```text id="jjlwm14"
Input: Cat
Output: Animal

Input: Apple
Output: Fruit

Input: Car
Output:
```

---

Model:

```text id="j’wini15"
Vehicle
```

---

## Why It Works

LLMs are pattern completion systems.

Examples teach patterns better than instructions alone.

---

## When To Use

```text id="j’wini16"
Extraction
Classification
Formatting
Complex Rules
```

---

## Pros

```text id="j’wini17"
Higher Accuracy
More Consistent
```

---

## Cons

```text id="j’wini18"
Uses More Tokens
```

---

# 5. Role Prompting

## Definition

Assign a role to the model.

---

Example:

```text id="j’wini19"
You are a senior Python instructor.
```

---

Why?

The role influences:

```text id="j’wini20"
Tone
Vocabulary
Depth
Behavior
```

---

RetailOps Example:

```text id="j’wini21"
You are RetailOps AI Assistant.
```

---

# 6. Constraint Prompting

## Definition

Explicitly define limitations.

---

Example:

```text id="j’wini22"
Answer in less than 100 words.
```

---

Example:

```text id="j’wini23"
Use only provided context.
```

---

## Why?

Without constraints:

```text id="j’wini24"
Answers become unpredictable.
```

---

# 7. Structured Prompting

## Definition

Request structured outputs.

---

Bad:

```text id="j’wini25"
Summarize this document.
```

---

Good:

```text id="j’wini26"
Return:

Summary:
Risks:
Recommendations:
```

---

## Why?

Applications need predictable outputs.

---

## RetailOps

Combined with:

```python id="j’wini27"
with_structured_output()
```

---

# 8. Chain of Thought Prompting

## Definition

Encourage reasoning before answering.

---

Example:

```text id="j’wini28"
Think step by step.
```

---

Question:

```text id="j’wini29"
A store has 10 laptops and sells 3. How many remain?
```

---

Reasoning:

```text id="j’wini30"
10 - 3 = 7
```

---

Answer:

```text id="j’wini31"
7
```

---

## Why Use It?

Improves reasoning quality.

---

## Pros

```text id="j’wini32"
Better Logic
Higher Accuracy
```

---

## Cons

```text id="j’wini33"
More Tokens
More Latency
```

---

# 9. Routing Prompts

## Definition

Prompts that classify requests.

---

RetailOps Example:

Routes:

```text id="j’wini34"
general
rag
tools
```

---

Prompt:

```text id="j’wini35"
Choose exactly one route.
```

---

Output:

```text id="j’wini36"
rag
```

---

## Why?

Allows dynamic workflow selection.

---

# 10. RAG Prompts

## Definition

Prompts designed for retrieval-based answering.

---

RetailOps Example:

```text id="j’wini37"
Use only provided context.

If answer is not found:
"I don't know."
```

---

## Why?

Reduces hallucinations.

---

## Production Rule

Never allow:

```text id="j’wini38"
Use your own knowledge
```

for enterprise documents.

---

# 11. Evaluation Prompts

## Definition

Prompts used to evaluate answers.

---

RetailOps Example:

Judge:

```text id="j’wini39"
Correct?
Grounded?
Complete?
```

---

Output:

```python id="j’wini40"
JudgeResult
```

---

## Why?

Measure quality systematically.

---

# 12. Multi-Query Prompts

## Definition

Generate alternative search queries.

---

Example:

Question:

```text id="j’wini41"
How much PTO do employees get?
```

---

Generated:

```text id="j’wini42"
What is the paid time off policy?
How many vacation days do employees receive?
What employee leave benefits exist?
```

---

## Why?

Improve retrieval recall.

---

# 13. History-Aware Rewrite Prompts

## Definition

Rewrite follow-up questions into standalone questions.

---

Example:

User:

```text id="j’wini43"
How many vacation days do employees receive?
```

---

Follow-up:

```text id="j’wini44"
What about part-time employees?
```

---

Rewrite:

```text id="j’wini45"
What is the PTO policy for part-time employees?
```

---

## Why?

Retrievers need complete queries.

---

# 14. Prompt Patterns Used in RetailOps

Current prompts:

```text id="j’wini46"
general_chat_prompt
rag_prompt
router_prompt
question_rewrite_prompt
multi_query_prompt
judge_prompt
```

---

Each solves a different problem.

---

# 15. Prompt Tradeoffs

## More Instructions

Pros:

```text id="j’wini47"
More Control
```

Cons:

```text id="j’wini48"
More Tokens
```

---

## Few-Shot Examples

Pros:

```text id="j’wini49"
Higher Accuracy
```

Cons:

```text id="j’wini50"
Higher Cost
```

---

## Long Prompts

Pros:

```text id="j’wini51"
More Context
```

Cons:

```text id="j’wini52"
Higher Latency
```

---

# 16. Production Best Practices

## Use Roles

Always define:

```text id="j’wini53"
Who the model is
```

---

## Add Constraints

Examples:

```text id="j’wini54"
Use only context.
Return JSON.
Maximum 100 words.
```

---

## Keep Prompts Focused

One purpose per prompt.

---

## Evaluate Prompt Changes

Never assume:

```text id="j’wini55"
Prompt v2
```

is better than:

```text id="j’wini56"
Prompt v1
```

---

## Version Prompts

Treat prompts as code.

---

# 17. Common Mistakes

## Mistake 1

Vague instructions.

---

## Mistake 2

No output format.

---

## Mistake 3

No constraints.

---

## Mistake 4

Using giant prompts for multiple tasks.

---

## Mistake 5

Not evaluating prompt changes.

---

# 18. Interview Questions

### What is Prompt Engineering?

Designing prompts that guide model behavior.

---

### Why use role prompting?

To influence model behavior and expertise.

---

### Difference between Zero-Shot and Few-Shot?

Zero-Shot:

```text id="j’wini57"
No examples
```

Few-Shot:

```text id="j’wini58"
Examples provided
```

---

### Why use RAG prompts?

To ground answers and reduce hallucinations.

---

### What is a routing prompt?

A prompt that classifies requests and selects workflows.

---

### Why rewrite follow-up questions?

Retrievers need complete standalone queries.

---

# Summary

Prompt Engineering is the highest-leverage skill in LangChain.

It determines:

```text id="j’wini59"
Behavior
Accuracy
Formatting
Routing
Retrieval Quality
Evaluation Quality
```

The RetailOps project uses multiple prompt engineering patterns simultaneously:

```text id="j’wini60"
Role Prompting
Constraint Prompting
Routing Prompts
RAG Prompts
Evaluation Prompts
History-Aware Prompts
Multi-Query Prompts
```

These patterns form the foundation of production AI systems.

The next document:

```text id="j’wini61"
05_lcel.md
```

covers LangChain Expression Language (LCEL), the most important programming model in modern LangChain applications.
