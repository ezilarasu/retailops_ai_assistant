# 25 - RAG Evaluation

# Learning Objectives

After completing this document, you should understand:

* Why RAG Evaluation is important
* What RAG Evaluation measures
* Retrieval Evaluation
* Generation Evaluation
* Golden Datasets
* Source Accuracy
* Groundedness
* Completeness
* Correctness
* LLM-as-Judge
* Evaluation Reports
* Production Evaluation Strategy
* RetailOps Implementation

---

# 1. Why RAG Evaluation Matters

One of the biggest mistakes in AI projects:

```text id="eval1"
"It looks good."
```

---

This is NOT evaluation.

---

Good answers can still be:

```text id="eval2"
Wrong
Incomplete
Ungrounded
```

---

Therefore:

```text id="eval3"
AI Systems Must Be Measured
```

---

# 2. What is RAG Evaluation?

## Definition

RAG Evaluation is the process of measuring retrieval quality and answer quality.

---

Question:

```text id="eval4"
Did the system retrieve the correct information?

Did the system generate the correct answer?
```

---

Both matter.

---

# 3. Two Types of Evaluation

## Retrieval Evaluation

Measures:

```text id="eval5"
Was the right document retrieved?
```

---

## Generation Evaluation

Measures:

```text id="eval6"
Was the answer correct?
```

---

# Example

Question:

```text id="eval7"
What does P1 mean?
```

---

Retriever:

```text id="eval8"
Wrong Document
```

---

LLM:

```text id="eval9"
Wrong Answer
```

---

Problem:

```text id="eval10"
Retrieval Failure
```

---

Not:

```text id="eval11"
LLM Failure
```

---

# 4. Golden Dataset

## Definition

A set of known questions and expected answers.

---

Example:

```json id="eval12"
{
  "question":
  "How many vacation days do employees receive?",

  "expected_answer":
  "18 paid vacation days",

  "expected_source":
  "hr_policy.txt"
}
```

---

# Why Use It?

Provides:

```text id="eval13"
Repeatable Evaluation
```

---

Without golden datasets:

```text id="eval14"
No objective measurement
```

---

# 5. Retrieval Evaluation

Question:

```text id="eval15"
What does P1 mean?
```

---

Expected Source:

```text id="eval16"
it_support_kb.txt
```

---

Actual Source:

```text id="eval17"
it_support_kb.txt
```

---

Result:

```text id="eval18"
Success
```

---

# Retrieval Metric

Called:

```text id="eval19"
Source Accuracy
```

---

# Formula

\text{Source Accuracy}=\frac{\text{Correct Sources}}{\text{Total Questions}}

---

# Why Important?

Good retrieval is required for good answers.

---

# 6. Generation Evaluation

Measures answer quality.

---

Question:

```text id="eval20"
How many vacation days do employees receive?
```

---

Expected:

```text id="eval21"
18 vacation days
```

---

Generated:

```text id="eval22"
18 vacation days
```

---

Result:

```text id="eval23"
Correct
```

---

# But Simple String Matching Is Limited

Example:

Expected:

```text id="eval24"
18 paid vacation days
```

---

Generated:

```text id="eval25"
Employees receive eighteen vacation days annually.
```

---

Meaning:

```text id="eval26"
Same
```

---

String matching:

```text id="eval27"
May Fail
```

---

# 7. LLM-as-Judge

Modern evaluation technique.

---

Use an LLM to evaluate another LLM.

---

Judge Prompt:

```text id="eval28"
Question

Expected Answer

Actual Answer

Sources
```

---

Judge decides:

```text id="eval29"
Correct?
Grounded?
Complete?
```

---

# RetailOps

Current:

```python id="eval30"
JudgeResult
```

---

Fields:

```text id="eval31"
correct
grounded
complete
explanation
```

---

# 8. Correctness

Question:

```text id="eval32"
What does P1 mean?
```

---

Answer:

```text id="eval33"
P1 means full store outage.
```

---

Correct?

```text id="eval34"
Yes
```

---

# Metric

```text id="eval35"
Correctness
```

---

# 9. Groundedness

One of the most important production metrics.

---

Question:

```text id="eval36"
What does P1 mean?
```

---

Document:

```text id="eval37"
P1 means full store outage.
```

---

Answer:

```text id="eval38"
P1 means full store outage.
```

---

Grounded:

```text id="eval39"
Yes
```

---

Answer:

```text id="eval40"
P1 means full store outage and requires CEO approval.
```

---

Document:

```text id="eval41"
No CEO reference
```

---

Grounded?

```text id="eval42"
No
```

---

# This Is Hallucination

Groundedness measures:

```text id="eval43"
Did answer come from evidence?
```

---

# 10. Completeness

Question:

```text id="eval44"
Explain vacation policy.
```

---

Document:

```text id="eval45"
Vacation Days

Approval Process

Carry-over Rules
```

---

Answer:

```text id="eval46"
18 vacation days.
```

---

Correct?

```text id="eval47"
Yes
```

---

Complete?

```text id="eval48"
No
```

---

Missing:

```text id="eval49"
Approval
Carry-over
```

---

# Why Completeness Matters

Answers can be:

```text id="eval50"
Correct
```

but still:

```text id="eval51"
Incomplete
```

---

# 11. RetailOps Evaluation Pipeline

Current:

```text id="eval52"
Question
 ↓
RAG
 ↓
Answer

Judge
 ↓
Correct
Grounded
Complete
```

---

# Additional Checks

```text id="eval53"
Source Match
```

---

Therefore:

```text id="eval54"
Retrieval
+
Generation
```

are evaluated.

---

# 12. Evaluation Reports

RetailOps stores:

```text id="eval55"
Timestamp
Model
Document Version
Retrieval Config
Metrics
```

---

Why?

Track quality over time.

---

# Example

```text id="eval56"
Before Reranking
Score = 0.70

After Reranking
Score = 0.92
```

---

Evidence-based improvement.

---

# 13. Evaluation Metrics

RetailOps tracks:

```text id="eval57"
Pass Rate
Source Accuracy
Judge Correct Rate
Judge Grounded Rate
Judge Complete Rate
```

---

# Why Multiple Metrics?

One metric is insufficient.

---

Example:

```text id="eval58"
Correct
```

does not imply:

```text id="eval59"
Grounded
```

---

# 14. Evaluation vs Testing

Testing:

```text id="eval60"
Code Works
```

---

Evaluation:

```text id="eval61"
AI Works
```

---

Different concepts.

---

# Example

Test:

```text id="eval62"
API returns response
```

---

Evaluation:

```text id="eval63"
Response is correct
```

---

# 15. Production Evaluation Strategy

Strong strategy:

```text id="eval64"
Golden Dataset
+
Source Accuracy
+
LLM Judge
+
Human Review
```

---

Never rely on:

```text id="eval65"
One Metric
```

---

# 16. RetailOps Evaluation Components

Files:

```text id="eval66"
evals/run_rag_eval.py

evals/judge.py

evals/evaluation_report.py

evals/compare_reports.py
```

---

Provides:

```text id="eval67"
Automated Evaluation
```

---

# 17. Production Best Practices

## Always Evaluate Retrieval

Not only answers.

---

## Keep Golden Dataset

Version it.

---

## Evaluate Prompt Changes

Do not assume:

```text id="eval68"
Prompt v2
```

is better.

---

## Evaluate Retrieval Changes

Examples:

```text id="eval69"
BM25
Reranking
Multi Query
```

---

## Track Results Over Time

Store reports.

---

# 18. Common Mistakes

## Mistake 1

Using only manual testing.

---

## Mistake 2

Ignoring retrieval quality.

---

## Mistake 3

Using only correctness.

---

## Mistake 4

No groundedness evaluation.

---

## Mistake 5

No golden dataset.

---

# 19. Interview Questions

### Why is RAG evaluation important?

To measure retrieval and answer quality objectively.

---

### What is a Golden Dataset?

Questions with expected answers and sources.

---

### What is Groundedness?

Whether an answer is supported by retrieved evidence.

---

### What is Completeness?

Whether an answer contains all important information.

---

### What is LLM-as-Judge?

Using an LLM to evaluate another model's output.

---

### Retrieval Evaluation vs Generation Evaluation?

Retrieval:

```text id="eval70"
Document Quality
```

Generation:

```text id="eval71"
Answer Quality
```

---

# Summary

Evaluation is what separates:

```text id="eval72"
Demo
```

from:

```text id="eval73"
Production System
```

RetailOps uses:

```text id="eval74"
Golden Datasets
Source Accuracy
LLM-as-Judge
Evaluation Reports
```

to systematically measure RAG quality and compare retrieval strategies.

The next document:

```text id="eval75"
26_tools.md
```

begins the Agents section and explains how LangChain tools allow LLMs to interact with external systems and structured data.
