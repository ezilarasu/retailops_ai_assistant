# 35 - Testing AI Systems

# Learning Objectives

After completing this document, you should understand:

* Why AI testing is different
* Unit Testing
* Integration Testing
* RAG Testing
* Agent Testing
* Golden Datasets
* Evaluation Testing
* Deterministic vs Non-Deterministic Systems
* Testing Pyramid for AI
* Production Testing Strategy
* RetailOps Implementation

---

# 1. Why AI Testing Is Different

Traditional software:

```python id="test1"
2 + 2 = 4
```

---

Expected:

```text id="test2"
Always
```

---

AI systems:

Question:

```text id="test3"
What is Python?
```

---

Possible answers:

```text id="test4"
Python is a programming language.

Python is a popular programming language.

Python is an interpreted language.
```

---

All may be correct.

---

# Problem

Exact equality testing often fails.

---

# 2. Traditional Testing

Example:

```python id="test5"
assert add(2, 2) == 4
```

---

Works because:

```text id="test6"
Deterministic
```

---

# AI Systems

Need:

```text id="test7"
Probabilistic Testing
```

---

Instead of:

```text id="test8"
Exact Match
```

---

# 3. Testing Pyramid for AI

```text id="test9"
Evaluation
↑

Integration Tests
↑

Unit Tests
```

---

Most systems focus only on:

```text id="test10"
Evaluation
```

---

This is a mistake.

---

# 4. Unit Testing

## Definition

Testing individual functions.

---

Example:

```python id="test11"
normalize()
```

---

Test:

```python id="test12"
assert normalize(
    "Hello"
) == "hello"
```

---

RetailOps Examples:

```text id="test13"
Tools
Utility Functions
Parsers
```

---

# Why?

Fast feedback.

---

# 5. Integration Testing

## Definition

Testing multiple components together.

---

Example:

```text id="test14"
Retriever
+
Vector Store
```

---

Question:

```text id="test15"
What does P1 mean?
```

---

Verify:

```text id="test16"
Correct Documents Retrieved
```

---

# Why?

Many failures happen:

```text id="test17"
Between Components
```

---

# 6. RAG Testing

Specialized testing.

---

Question:

```text id="test18"
What does P1 mean?
```

---

Expected:

```text id="test19"
P1 means full store outage.
```

---

Source:

```text id="test20"
it_support_kb.txt
```

---

Verify:

```text id="test21"
Answer
+
Source
```

---

# Why?

RAG failures usually come from:

```text id="test22"
Retrieval
```

---

not:

```text id="test23"
Generation
```

---

# 7. Golden Datasets

## Definition

Questions with expected answers.

---

Example:

```json id="test24"
{
  "question":"What does P1 mean?",
  "expected_answer":"P1 means full store outage.",
  "expected_source":"it_support_kb.txt"
}
```

---

RetailOps:

```text id="test25"
rag_questions.jsonl
```

---

# Why?

Provides:

```text id="test26"
Repeatable Evaluation
```

---

# 8. Evaluation Testing

Question:

```text id="test27"
Did answer contain expected information?
```

---

Metrics:

```text id="test28"
Correctness
Groundedness
Completeness
```

---

RetailOps:

```text id="test29"
LLM-as-Judge
```

---

# Why?

String matching is insufficient.

---

# 9. Agent Testing

Question:

```text id="test30"
Show low stock items.
```

---

Verify:

```text id="test31"
Correct Tool Selected
```

---

Not only:

```text id="test32"
Correct Answer
```

---

Need:

```text id="test33"
Tool Behavior
```

---

# 10. Router Testing

Question:

```text id="test34"
What is the return policy?
```

---

Expected Route:

```text id="test35"
rag
```

---

Verify:

```text id="test36"
Correct Route Selected
```

---

RetailOps:

```text id="test37"
RouteDecision
```

---

# 11. Structured Output Testing

Question:

```text id="test38"
What does P1 mean?
```

---

Verify:

```python id="test39"
RAGResponse
```

---

instead of:

```text id="test40"
Random Text
```

---

# Why?

Schemas are contracts.

---

# 12. Retrieval Testing

Measure:

```text id="test41"
Source Accuracy
```

---

Question:

```text id="test42"
Vacation Policy
```

---

Expected:

```text id="test43"
hr_policy.txt
```

---

Retrieved:

```text id="test44"
hr_policy.txt
```

---

Success.

---

# Why Important?

Good retrieval:

```text id="test45"
Good RAG
```

---

# 13. Testing vs Evaluation

Very common confusion.

---

# Testing

Purpose:

```text id="test46"
System Correctness
```

---

Example:

```text id="test47"
API Works
```

---

# Evaluation

Purpose:

```text id="test48"
AI Quality
```

---

Example:

```text id="test49"
Answer Correctness
```

---

Different goals.

---

# 14. Deterministic vs Non-Deterministic

Traditional software:

```text id="test50"
Deterministic
```

---

AI:

```text id="test51"
Probabilistic
```

---

Therefore:

```text id="test52"
Flexible Evaluation
```

is required.

---

# 15. RetailOps Testing Layers

Current:

```text id="test53"
Unit Tests
Evaluation Tests
RAG Evaluation
```

---

Files:

```text id="test54"
tests/
evals/
```

---

# 16. Production Testing Strategy

Strong strategy:

```text id="test55"
Unit Tests
+
Integration Tests
+
Golden Dataset
+
LLM Judge
+
Human Review
```

---

Not:

```text id="test56"
Manual Testing Only
```

---

# 17. Regression Testing

Question:

```text id="test57"
Did retrieval improve?
```

---

Compare:

```text id="test58"
Before
After
```

---

Examples:

```text id="test59"
BM25

Cross Encoder

Multi Query
```

---

Need evidence.

---

# 18. Production Best Practices

## Keep Golden Dataset

Version it.

---

## Evaluate Retrieval

Not just answers.

---

## Test Routers

Very important.

---

## Test Tools

Independently.

---

## Track Metrics

Examples:

```text id="test60"
Pass Rate
Source Accuracy
Groundedness
```

---

# 19. Common Mistakes

## Mistake 1

Only manual testing.

---

## Mistake 2

Ignoring retrieval.

---

## Mistake 3

No golden dataset.

---

## Mistake 4

Testing only answers.

---

## Mistake 5

No regression testing.

---

# 20. Interview Questions

### Why is AI testing different?

AI systems are probabilistic.

---

### What is a Golden Dataset?

Questions with expected answers and sources.

---

### Testing vs Evaluation?

Testing:

```text id="test61"
System Correctness
```

Evaluation:

```text id="test62"
AI Quality
```

---

### Why evaluate retrieval separately?

Many RAG failures originate from retrieval.

---

### Why use LLM-as-Judge?

Meaning-based evaluation is stronger than string matching.

---

### Why does RetailOps use evaluation reports?

To compare retrieval and prompt improvements objectively.

---

# Summary

Testing AI systems requires:

```text id="test63"
Traditional Testing
+
AI Evaluation
```

RetailOps combines:

```text id="test64"
Golden Datasets
Source Accuracy
LLM-as-Judge
Evaluation Reports
```

to measure quality systematically and avoid relying on subjective impressions.

The next document:

```text id="test65"
36_caching.md
```

covers response caching, retrieval caching, cost reduction, and performance optimization in production AI systems.
