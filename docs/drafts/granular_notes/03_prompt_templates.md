# 03 - Prompt Templates

# Learning Objectives

After completing this document, you should understand:

* What Prompt Templates are
* Why Prompt Templates exist
* Prompt Templates vs Raw Strings
* ChatPromptTemplate
* Prompt Variables
* Message-Based Prompting
* System Messages
* User Messages
* Prompt Composition
* Dynamic Prompts
* Prompt Reusability
* Prompt Versioning
* Production Best Practices

---

# 1. What is a Prompt Template?

## Definition

A Prompt Template is a reusable prompt with placeholders (variables) that are filled at runtime.

Think of it as:

```text id="1d4m2h"
Template
+
Data
=
Prompt
```

---

## Example

Template:

```text id="jlwmf1"
Explain {topic}
```

---

Input:

```python id="jlwmf2"
{
  "topic": "Python"
}
```

---

Final Prompt:

```text id="jlwmf3"
Explain Python
```

---

# 2. Why Do Prompt Templates Exist?

Without templates:

```python id="jlwmf4"
topic = "Python"

prompt = f"""
Explain {topic}
"""
```

Works initially.

---

But in real systems:

```text id="jlwmf5"
100+ prompts
Multiple variables
Multiple models
```

become difficult to manage.

---

Prompt Templates solve:

```text id="jlwmf6"
Reusability
Maintainability
Consistency
```

---

# 3. Prompt Template vs Raw String

## Raw String

```python id="jlwmf7"
prompt = f"""
Explain {topic}
"""
```

---

Pros:

```text id="jlwmf8"
Simple
```

---

Cons:

```text id="jlwmf9"
Hard to reuse
Hard to test
Hard to version
```

---

## Prompt Template

```python id="jlwmfa"
from langchain_core.prompts import PromptTemplate

prompt = PromptTemplate.from_template(
    "Explain {topic}"
)
```

---

Pros:

```text id="jlwmfb"
Reusable
Composable
Maintainable
```

---

# 4. Types of Prompt Templates

LangChain provides:

```text id="jlwmfc"
PromptTemplate
ChatPromptTemplate
FewShotPromptTemplate
```

---

# PromptTemplate

Simple text prompt.

---

Example:

```python id="jlwmfd"
PromptTemplate.from_template(
    "Explain {topic}"
)
```

---

# ChatPromptTemplate

Most important.

Used with chat models.

---

Example:

```python id="jlwmfe"
ChatPromptTemplate.from_messages(...)
```

---

# FewShotPromptTemplate

Used when examples are needed.

---

Example:

```text id="jlwmff"
Input
Output

Input
Output
```

---

# 5. ChatPromptTemplate

## Definition

A prompt composed of messages.

---

Modern LLMs work with:

```text id="jlwmfg"
System
User
Assistant
```

messages.

---

Example:

```python id="jlwmfh"
from langchain_core.prompts import (
    ChatPromptTemplate
)

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a Python instructor."
    ),
    (
        "human",
        "{question}"
    )
])
```

---

# Why Use It?

Matches how modern chat models operate.

---

# 6. System Messages

## Definition

High-priority instructions controlling behavior.

---

Example:

```text id="jlwmfi"
You are a senior Python instructor.
```

---

Purpose:

```text id="จ๊กเกอร์fj"
Role
Behavior
Constraints
```

---

RetailOps Example:

```text id="jlwmfk"
You are RetailOps AI Assistant.
```

---

# 7. Human Messages

## Definition

Current user request.

---

Example:

```text id="jlwmfl"
How many vacation days do employees receive?
```

---

Usually contains:

```text id="jlwmfm"
Question
Input Data
Context
```

---

# 8. Assistant Messages

## Definition

Previous AI responses.

---

Used for:

```text id="jlwmfn"
Conversation Continuity
```

---

Example:

```text id="jlwmfo"
User:
What is Python?

Assistant:
Python is a language.

User:
Why is it popular?
```

---

The model understands:

```text id="jlwmfp"
Python
```

from previous messages.

---

# 9. Prompt Variables

Variables make prompts dynamic.

---

Example:

```python id="jlwmfq"
prompt = ChatPromptTemplate.from_template(
    """
    Explain {topic}
    for a {level} developer.
    """
)
```

---

Input:

```python id="jlwmfr"
{
    "topic": "Decorators",
    "level": "Beginner"
}
```

---

Output:

```text id="jlwmfs"
Explain Decorators
for a Beginner developer.
```

---

# 10. Prompt Invocation

Templates become prompts using:

```python id="jlwmft"
prompt.invoke(...)
```

---

Example:

```python id="jlwmfu"
messages = prompt.invoke({
    "question": "Explain Python."
})
```

---

Result:

```text id="jlwmfv"
System Message
Human Message
```

---

# 11. Prompt Composition

Prompts can be combined with:

```text id="jlwmfw"
LCEL
```

---

Example:

```python id="jlwmfx"
prompt
|
llm
|
parser
```

---

This is how most LangChain applications work.

---

# 12. Prompt Design Pattern

A strong prompt usually contains:

```text id="jlwmfy"
Role
Task
Context
Constraints
Output Format
```

---

Example:

```text id="jlwmfz"
Role:
HR Assistant

Task:
Answer employee questions

Context:
Provided policy documents

Constraint:
Use only provided context

Output:
Answer + Source
```

---

# 13. RetailOps Prompts

Current prompts:

```text id="jlwmg0"
general_chat_prompt
rag_prompt
router_prompt
question_rewrite_prompt
multi_query_prompt
judge_prompt
```

---

Each has a specific purpose.

---

# General Chat Prompt

Used for:

```text id="jlwmg1"
General conversation
```

---

# RAG Prompt

Used for:

```text id="jlwmg2"
Document-grounded answers
```

---

# Router Prompt

Used for:

```text id="jlwmg3"
Route selection
```

---

# Question Rewrite Prompt

Used for:

```text id="jlwmg4"
History-aware retrieval
```

---

# Multi Query Prompt

Used for:

```text id="jlwmg5"
Generate alternate retrieval queries
```

---

# Judge Prompt

Used for:

```text id="jlwmg6"
Evaluation
```

---

# 14. Why Separate Prompts?

Bad:

```python id="jlwmg7"
Prompts inside chains
```

---

Good:

```text id="jlwmg8"
app/prompts.py
```

---

Benefits:

```text id="jlwmg9"
Versioning
Testing
Maintenance
```

---

# 15. Prompt Versioning

Prompts are application logic.

Treat them like code.

---

Example:

```text id="jlwmga"
v1
Basic RAG

v2
Added source attribution

v3
Added confidence score
```

---

# Why?

Prompt changes affect behavior.

---

# 16. Production Best Practices

## Keep Prompts Separate

```text id="jlwmgb"
app/prompts.py
```

---

## Keep Prompts Focused

One responsibility per prompt.

---

## Use Structured Output

Prefer:

```python id="jlwmgc"
with_structured_output()
```

when possible.

---

## Version Prompts

Track changes.

---

## Evaluate Prompts

Use:

```text id="jlwmgd"
Golden Datasets
LangSmith
Evaluation Reports
```

---

# 17. Common Mistakes

## Mistake 1

Hardcoding prompts everywhere.

---

## Mistake 2

One giant prompt doing multiple jobs.

---

## Mistake 3

No output format.

---

## Mistake 4

No evaluation.

---

## Mistake 5

Treating prompts as static text instead of application logic.

---

# 18. Prompt Templates vs Structured Output

Prompt Template:

```text id="jlwmge"
Controls Input
```

---

Structured Output:

```text id="jlwmgf"
Controls Output
```

---

Together:

```text id="jlwmgg"
Reliable Input
+
Reliable Output
```

---

# 19. Interview Questions

### What is a Prompt Template?

A reusable prompt with variables.

---

### Why use Prompt Templates?

Maintainability and reusability.

---

### Difference between PromptTemplate and ChatPromptTemplate?

PromptTemplate:

```text id="jlwmgh"
Text Prompt
```

ChatPromptTemplate:

```text id="jlwmgi"
Message-Based Prompt
```

---

### Why use System Messages?

To define behavior and constraints.

---

### Why keep prompts separate?

Prompts are application logic and should be versioned and maintained.

---

### What is prompt composition?

Combining prompts with models and parsers using LCEL.

---

# Summary

Prompt Templates are the foundation of LangChain applications.

They provide:

```text id="jlwmgj"
Reusability
Dynamic Variables
Message Structure
Maintainability
```

and allow us to build:

```text id="jlwmgk"
RAG
Agents
Routers
Evaluation Systems
```

in a consistent and production-friendly way.

The next document:

```text id="jlwmgl"
04_prompt_engineering_patterns.md
```

covers advanced prompting strategies, few-shot prompting, role prompting, routing prompts, RAG prompts, evaluation prompts, and production prompt design.
