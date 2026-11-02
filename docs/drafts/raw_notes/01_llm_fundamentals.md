# 01 - LLM Fundamentals

# Learning Objectives

After completing this document, you should understand:

* What an LLM is
* How LLMs generate responses
* Tokens and tokenization
* Context windows
* Sampling parameters
* Temperature
* Top-P
* Max Tokens
* Chat Models
* System, User, and Assistant messages
* Hallucinations
* Function Calling
* Embeddings
* Vector Databases
* RAG Fundamentals

---

# 1. What is an LLM?

## Definition

LLM stands for:

```text
Large Language Model
```

An LLM is a machine learning model trained on massive amounts of text data to predict the next token in a sequence.

Examples:

```text
GPT
Claude
Gemini
Llama
Mistral
Qwen
DeepSeek
```

---

## Common Misconception

Many people think:

```text
Question
 ↓
Thinking
 ↓
Answer
```

This is not how an LLM works.

An LLM fundamentally performs:

```text
Previous Tokens
 ↓
Predict Next Token
```

---

## Example

Input:

```text
The capital of France is
```

Predicted token:

```text
Paris
```

The model chooses the most probable continuation.

---

## Why It Matters

Understanding this explains:

* Hallucinations
* Prompt engineering
* Context windows
* RAG
* Function calling

---

# 2. How LLMs Work

The process:

```text
Input
 ↓
Tokenization
 ↓
Neural Network
 ↓
Probability Distribution
 ↓
Next Token
 ↓
Repeat
```

Example:

```text
Tell me a joke
```

May become:

```text
Tell
me
a
joke
```

The model predicts:

```text
Why
```

Then:

```text
Tell me a joke Why
```

Predicts:

```text
did
```

And so on.

---

## Key Insight

LLMs do not retrieve answers.

They generate likely continuations.

---

# 3. Tokens

## Definition

Tokens are the units processed by an LLM.

A token is not always a word.

Examples:

```text
Hello
```

might be:

```text
1 token
```

while:

```text
internationalization
```

might become:

```text
intern
ation
al
ization
```

Multiple tokens.

---

## Why Tokens Matter

Tokens affect:

```text
Cost
Latency
Context Window
Memory Usage
```

---

## Production Impact

Large prompts:

```text
More tokens
Higher cost
Slower responses
```

---

# 4. Context Window

## Definition

The maximum number of tokens the model can process in a single request.

---

## What Consumes Context?

Everything.

```text
System Prompt
User Message
Conversation History
Retrieved Documents
Tool Outputs
```

---

## Example

```text
System Prompt: 500 tokens
History: 4000 tokens
RAG Context: 3000 tokens
Question: 100 tokens

Total: 7600 tokens
```

---

## Why It Exists

Transformer models require memory and computation.

Unlimited context would be impractical.

---

## Pros of Large Context

```text
More information
Longer conversations
Large documents
```

---

## Cons

```text
Higher latency
Higher cost
Lost-in-the-middle problems
```

---

## Production Recommendation

Do not use large context as a replacement for retrieval.

Use:

```text
RAG
Summarization
Context Compression
```

---

# 5. Sampling Parameters

Sampling controls how responses are generated.

---

# Temperature

## Definition

Controls randomness.

---

## Temperature = 0

Most deterministic.

Use for:

```text
Code Generation
RAG
Structured Output
Classification
```

Pros:

```text
Consistent
Reliable
```

Cons:

```text
Less creative
```

---

## Temperature = 0.7

Balanced.

Use for:

```text
Chatbots
Assistants
Learning Applications
```

---

## Temperature = 1+

Creative.

Use for:

```text
Stories
Marketing
Brainstorming
```

---

# Top-P

## Definition

Nucleus sampling.

Restricts token selection to the most likely token set.

---

## Production Recommendation

```python
temperature=0.2
top_p=1
```

---

# Max Tokens

## Definition

Maximum output length.

---

## Why Use It?

```text
Control cost
Control latency
Control output size
```

---

# 6. Chat Models

Modern LLMs are chat models.

Instead of:

```text
Prompt
 ↓
Response
```

They process:

```text
System Message
User Message
Assistant Message
```

---

# System Message

## Definition

Instructions controlling model behavior.

Example:

```text
You are a senior Python instructor.
```

---

## Why Use It?

Creates consistent behavior.

---

# User Message

The current request.

Example:

```text
Explain decorators.
```

---

# Assistant Message

Previous model responses.

Used for conversation continuity.

---

# 7. Hallucinations

## Definition

Generating incorrect information that sounds plausible.

---

## Example

Question:

```text
Who won the FIFA World Cup in 2050?
```

The model may invent an answer.

---

## Why Hallucinations Occur

The model must generate tokens.

Even when knowledge is missing.

---

## How To Reduce Hallucinations

Use:

```text
RAG
Tools
Grounding
Structured Prompts
```

---

# 8. Function Calling

## Definition

Allows the model to decide when a tool should be used.

---

## Traditional LLM

```text
Question
 ↓
LLM
 ↓
Answer
```

---

## Function Calling

```text
Question
 ↓
LLM
 ↓
Tool Selection
 ↓
Tool Execution
 ↓
Answer
```

---

## Example

Question:

```text
What is the weather in Toronto?
```

Tool:

```python
get_weather(city)
```

The model selects the tool.

---

## Important

The model does not execute code.

Your application executes the tool.

---

# 9. Embeddings

## Definition

Numerical representation of semantic meaning.

Example:

```text
Vacation Policy
```

becomes:

```text
[0.22, -0.14, 0.88, ...]
```

---

## Why Use Embeddings?

Computers compare numbers better than text.

Embeddings enable:

```text
Semantic Search
Similarity Search
Retrieval
```

---

## Example

Query:

```text
PTO policy
```

Document:

```text
Vacation policy
```

Embeddings recognize similarity.

Keyword search may not.

---

# 10. Vector Databases

## Definition

Databases optimized for storing and searching embeddings.

---

## Traditional Database

```text
id
name
price
```

---

## Vector Database

```text
id
embedding
```

---

## Popular Options

```text
Chroma
FAISS
Pinecone
Weaviate
Qdrant
```

---

## Why Use Them?

Efficient similarity search.

---

# 11. RAG Fundamentals

RAG stands for:

```text
Retrieval Augmented Generation
```

---

## Problem

LLMs do not know:

```text
Company Documents
Internal Policies
Today's Data
Private Knowledge
```

---

## Traditional LLM

```text
Question
 ↓
LLM
 ↓
Answer
```

---

## RAG

```text
Question
 ↓
Retriever
 ↓
Relevant Documents
 ↓
LLM
 ↓
Answer
```

---

## Example

Question:

```text
How many vacation days do employees receive?
```

Retriever finds:

```text
Employees receive 18 paid vacation days...
```

The LLM answers using retrieved context.

---

## Why Use RAG?

Pros:

```text
Fresh Knowledge
No Retraining
Lower Cost
Easy Updates
```

Cons:

```text
Requires Retrieval Infrastructure
Retrieval Quality Matters
```

---

# Fine-Tuning vs RAG

| Fine-Tuning      | RAG                 |
| ---------------- | ------------------- |
| Learns behavior  | Retrieves knowledge |
| Expensive        | Cheaper             |
| Static knowledge | Dynamic knowledge   |
| Hard to update   | Easy to update      |

---

# Production Recommendations

Use:

```text
Fine-Tuning
```

for:

```text
Style
Tone
Format
Behavior
```

Use:

```text
RAG
```

for:

```text
Knowledge
Documents
Policies
FAQs
```

---

# Common Mistakes

## Mistake 1

Assuming LLMs think like humans.

---

## Mistake 2

Ignoring context window limits.

---

## Mistake 3

Using temperature 1.0 for production RAG.

---

## Mistake 4

Using fine-tuning instead of RAG for company knowledge.

---

## Mistake 5

Believing embeddings store facts.

Embeddings store meaning, not knowledge.

---

# Interview Questions

### What is an LLM?

A model trained to predict the next token.

---

### What is a token?

The smallest unit processed by the model.

---

### What is a context window?

The maximum number of tokens processed in one request.

---

### What causes hallucinations?

Generating likely text when knowledge is missing.

---

### What is temperature?

A parameter controlling randomness.

---

### What is an embedding?

A numerical representation of semantic meaning.

---

### Why use a vector database?

Efficient similarity search over embeddings.

---

### What is RAG?

Retrieval Augmented Generation.

Combines retrieval with generation.

---

### RAG vs Fine-Tuning?

RAG retrieves knowledge.

Fine-tuning changes model behavior.

---

# Relation to RetailOps Project

This project uses:

```text
Groq LLM
↓
Prompt Templates
↓
Embeddings
↓
Chroma Vector Store
↓
Retriever
↓
RAG
↓
Tools
↓
Agents
```

Every advanced concept in LangChain, LangGraph, and LangSmith builds upon the foundations covered in this document.
