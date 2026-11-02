# RAG Evaluation
> The difference between "it looks good" and "it works" — measuring what the system actually does.

## 📌 What Is It?

**RAG evaluation** is the systematic process of measuring retrieval quality and answer quality against a **golden dataset** — a set of known questions with expected answers and source documents.

It answers three questions:
1. **Did the retriever find the right document?** (source accuracy)
2. **Is the answer factually correct?** (correctness)
3. **Is the answer grounded in the retrieved context?** (groundedness — the anti-hallucination metric)

RetailOps uses an **LLM-as-judge** approach: an LLM evaluates each question-answer pair against the golden expected answer and returns a structured `JudgeResult` (`app/schemas.py`):

```python
class JudgeResult(BaseModel):
    correct: bool       # does the answer match the expected answer?
    grounded: bool      # is every claim in the answer supported by context?
    complete: bool      # does the answer cover all key points?
    explanation: str    # step-by-step explanation of the scores
```

## ❓ Why Does It Exist?

AI systems have a dangerous property: they *always* produce an answer. Without evaluation, there's no way to distinguish a correct answer from a confident hallucination.

The other reason: diagnosis. When a RAG system gives a wrong answer, there are two possible causes:
1. **Retrieval failure** — the right document wasn't retrieved
2. **Generation failure** — the right document was retrieved but the LLM answered incorrectly

Without separate retrieval evaluation (source accuracy) and generation evaluation (correctness/groundedness), you can't tell which to fix. Most RAG failures are retrieval failures — but developers default to tuning prompts.

## ⏰ When Should You Use It?

✅ Before deploying any RAG system to production  
✅ After changing chunking strategy, embedding model, or retrieval parameters  
✅ After changing the RAG prompt  
✅ To compare two retrieval strategies (e.g., vector-only vs hybrid)  
✅ On a recurring schedule to catch quality regressions  

❌ Don't rely on manual testing of 5–10 queries — this misses systematic failures  
❌ Don't tune prompts before measuring retrieval quality — fix the bottleneck first  
❌ Don't use only correctness — grounded answers that are wrong are worse than "I don't know"  

## 🗂️ Types / Variants

| Metric | What It Measures | How to Compute |
|---|---|---|
| **Source accuracy** | Did retrieval find the expected document? | `expected_source in retrieved_sources` |
| **Correctness** | Does the answer match the expected answer? | LLM judge compares answer to expected |
| **Groundedness** | Is every claim supported by retrieved context? | LLM judge checks for unsupported claims |
| **Completeness** | Does the answer cover all key points? | LLM judge checks for missing information |
| **Pass rate** | Fraction of test cases passing all criteria | `correct AND grounded AND complete` |

## 🔀 When to Use Which Type

**Always measure all three generation metrics.** An answer can be correct (matches expected) but ungrounded (used training data, not context) — that's a hallucination that happened to be right. An answer can be grounded but incomplete — it cites the source accurately but omits half the answer.

**Source accuracy is the fastest signal.** It's a simple string check: did the expected filename appear in the retrieved sources? It doesn't require an LLM call and runs in milliseconds. Use it as your first diagnostic.

**LLM-as-judge** provides richer signal than string matching for correctness and completeness — "18 vacation days" and "Employees receive eighteen paid vacation days annually" are semantically equivalent but string-unequal.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Objective, repeatable measurement vs "looks good" | Building a golden dataset takes time upfront |
| Separates retrieval failures from generation failures | LLM judge adds cost and latency to eval runs |
| LLM-as-judge handles paraphrase and semantic equivalence | Judge quality depends on judge prompt quality |
| Enables before/after comparison for every change | |
| Identifies regression when system changes | |

## 💻 Basic Example

```python
import os
import json
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from app.llm import get_llm

load_dotenv()

# ── JudgeResult schema (app/schemas.py) ───────────────────────────────────
class JudgeResult(BaseModel):
    correct: bool
    grounded: bool
    complete: bool
    explanation: str

# ── Judge chain (evals/judge.py) ──────────────────────────────────────────
JUDGE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an evaluator for a RAG assistant.
Judge the assistant answer against the expected answer.

Criteria:
- correct: answer matches the expected answer
- grounded: answer does not invent unsupported information
- complete: answer contains the key expected information

Return structured output only."""),
    ("human", """Question: {question}
Expected answer: {expected_answer}
Actual answer: {actual_answer}
Sources returned: {sources}"""),
])

llm = get_llm()
judge_chain = JUDGE_PROMPT | llm.with_structured_output(JudgeResult)

# ── Golden dataset (evals/rag_questions.jsonl) ────────────────────────────
golden_dataset = [
    {
        "question": "How many vacation days do employees receive?",
        "expected_answer": "18 paid vacation days",
        "expected_source": "hr_policy.txt",
    },
    {
        "question": "What does P1 mean?",
        "expected_answer": "P1 means full store outage",
        "expected_source": "it_support_kb.txt",
    },
]

# ── Run evaluation ────────────────────────────────────────────────────────
def evaluate_one(rag_chain, test_case: dict) -> dict:
    """Evaluate a single test case."""
    result = rag_chain.invoke({"question": test_case["question"]})

    # Source accuracy: did retrieval find the expected document?
    source_correct = test_case["expected_source"] in " ".join(result.sources)

    # LLM judge for generation quality
    judge_result = judge_chain.invoke({
        "question": test_case["question"],
        "expected_answer": test_case["expected_answer"],
        "actual_answer": result.answer,
        "sources": result.sources,
    })

    return {
        "question": test_case["question"],
        "source_correct": source_correct,
        "correct": judge_result.correct,
        "grounded": judge_result.grounded,
        "complete": judge_result.complete,
        "explanation": judge_result.explanation,
        "passed": (
            source_correct
            and judge_result.correct
            and judge_result.grounded
            and judge_result.complete
        ),
    }
```

## 🔧 Real-World Example

RetailOps' evaluation pipeline — runs against the question set in `evals/rag_questions.jsonl`, generates a JSON report via `evals/evaluation_report.py`, and supports comparison between retrieval configurations via `evals/compare_reports.py`.

**What the repo ships:** the "golden dataset" here is a **small demo set of 5 questions** (topics: vacation days, remote work, the online return window, a POS outage, and what P1 means; one JSON object per line with `question`, `expected_answer`, `expected_source`). It exists to show how the harness works. The advice below to build 20–50 questions is guidance for your own project, not something the repo already contains.

**Judge caveat:** `judge_answer()` in `evals/judge.py` uses `get_llm()`, the same model and temperature as the RAG chain itself. That is exactly the "same LLM as system and judge" weakness described under Common Mistakes, so treat the scores as a regression signal rather than an unbiased grade. Running the eval needs `GROQ_API_KEY`, and each question costs several LLM calls: the RAG chain's own question rewrite, query expansion and answer calls, plus one judge call (the rewrite call is skipped on the first question of a conversation, and the eval asks each question on its own, so in practice it is two calls plus the judge). Both the RAG chain and the judge use `LLM_MODEL`: the eval runs the RAG chain directly, so the separate tool-calling model (`TOOLS_LLM_MODEL`, doc 21) is not involved, and each saved report records the `LLM_MODEL` it ran with. Mind the free tier's per-minute and per-day token limits when you run it repeatedly; if the provider rate-limits the run, the harness stops with that error rather than scoring partial results.

```python
import json
from pathlib import Path

from app.container import get_container
from evals.evaluation_report import save_evaluation_report
from evals.judge import judge_answer

# ══════════════════════════════════════════════════════════════════════════
# evals/run_rag_eval.py — RetailOps evaluation pipeline
# Run: python -m evals.run_rag_eval
# Output: evals/results/eval_<YYYYMMDD_HHMMSS>.json (UTC timestamp)
# ══════════════════════════════════════════════════════════════════════════

EVAL_FILE = Path("evals/rag_questions.jsonl")


def normalize(text: str) -> str:
    return text.lower().strip()


def run_eval():
    """Run the golden dataset against the live RAG chain and save a report.

    For each question: invoke the RAG chain, check source accuracy (a
    deterministic string check — no LLM call), then call the LLM judge
    (evals/judge.py) for correct/grounded/complete. A case passes only if
    source_match AND judge.correct AND judge.grounded AND judge.complete.
    """
    container = get_container()
    total = 0
    passed = 0
    details = []
    source_hits = 0
    judge_correct_count = 0
    judge_grounded_count = 0
    judge_complete_count = 0

    with open(EVAL_FILE, "r") as file:
        for line in file:
            total += 1
            item = json.loads(line)

            question = item["question"]
            expected_answer_raw = item["expected_answer"]
            expected_answer = normalize(expected_answer_raw)
            expected_source = item["expected_source"]

            result = container.rag_chain.invoke({"question": question})

            answer = normalize(result.answer)
            sources_text = " ".join(result.sources)

            answer_match = expected_answer in answer
            source_match = expected_source in sources_text
            if source_match:
                source_hits += 1

            judge = judge_answer(
                question=question,
                expected_answer=expected_answer_raw,
                actual_answer=result.answer,
                sources=result.sources,
            )

            if judge.correct:
                judge_correct_count += 1
            if judge.grounded:
                judge_grounded_count += 1
            if judge.complete:
                judge_complete_count += 1

            success = (
                source_match
                and judge.correct
                and judge.grounded
                and judge.complete
            )
            if success:
                passed += 1

            details.append({
                "question": question,
                "success": success,
                "expected_answer": expected_answer_raw,
                "actual_answer": result.answer,
                "expected_source": expected_source,
                "actual_sources": result.sources,
                "deterministic_checks": {
                    "answer_match": answer_match,
                    "source_match": source_match,
                },
                "judge": {
                    "correct": judge.correct,
                    "grounded": judge.grounded,
                    "complete": judge.complete,
                    "explanation": judge.explanation,
                },
            })

    metrics = {
        "total": total,
        "passed": passed,
        "pass_rate": round(passed / total, 4),
        "source_accuracy": round(source_hits / total, 4),
        "judge_correct_rate": round(judge_correct_count / total, 4),
        "judge_grounded_rate": round(judge_grounded_count / total, 4),
        "judge_complete_rate": round(judge_complete_count / total, 4),
    }

    report_file = save_evaluation_report(
        total=total,
        passed=passed,
        details=details,
        metrics=metrics,
    )

    print("\nSaved report:", report_file)


if __name__ == "__main__":
    run_eval()
```

The report itself is built by `save_evaluation_report()` in `evals/evaluation_report.py`, which writes to `evals/results/eval_<timestamp>.json`:

```python
# evals/evaluation_report.py
report = {
    "timestamp": datetime.utcnow().isoformat(),
    "model": settings.llm_model,
    "document_version": settings.document_version,
    "retrieval_config": {
        "enable_semantic_chunking": settings.enable_semantic_chunking,
        "enable_reranking": settings.enable_reranking,
        "enable_multi_query": settings.enable_multi_query,
        "retrieval_k": settings.retrieval_k,
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap,
        "vectorstore_dir": settings.vectorstore_dir,
    },
    "total": total,
    "passed": passed,
    "score": round(passed / total, 4),
    "metrics": metrics or {},   # pass_rate, source_accuracy, judge_*_rate
    "details": details,        # per-question results, each with a "judge" object
}
```

Here is the shape of a saved report. The values are taken from the committed run `evals/results/eval_20260609_044240.json`, with the per-question `details` shortened. (The `model` shown was current when that report was produced; model names change over time, and every new report records whatever `LLM_MODEL` you ran with.)

```json
{
  "timestamp": "2026-06-09T04:42:40.185766",
  "model": "llama-3.3-70b-versatile",
  "document_version": "2026-06-08-v1",
  "retrieval_config": {
    "enable_semantic_chunking": true,
    "enable_reranking": true,
    "enable_multi_query": true,
    "retrieval_k": 2,
    "chunk_size": 300,
    "chunk_overlap": 50,
    "vectorstore_dir": "vectorstore/chroma"
  },
  "total": 5,
  "passed": 5,
  "score": 1.0,
  "metrics": {
    "total": 5,
    "passed": 5,
    "pass_rate": 1.0,
    "source_accuracy": 1.0,
    "judge_correct_rate": 1.0,
    "judge_grounded_rate": 1.0,
    "judge_complete_rate": 1.0
  },
  "details": [
    {
      "question": "...", "success": true,
      "expected_answer": "...", "actual_answer": "...",
      "expected_source": "...", "actual_sources": ["..."],
      "deterministic_checks": { "answer_match": true, "source_match": true },
      "judge": { "correct": true, "grounded": true, "complete": true, "explanation": "..." }
    }
  ]
}
```

> **Read these numbers with care.** The committed reports in `evals/results/` were produced on this same 5-question set. A perfect score on so few questions tells you the harness works, not that the assistant is accurate. The earliest reports in that folder scored 4/5 and 3/5 before several fixes, and later runs (including October runs on `gpt-oss-20b`) scored 5/5, which is why evaluating after each change matters. Note what a report does *not* record: `RERANK_MIN_SCORE`, the semantic-chunking settings and `TOOLS_LLM_MODEL` are missing from `retrieval_config`, so two runs that differ only in those settings look identical in `python -m evals.compare_reports`. If you compare such runs, add the settings you change to `evals/evaluation_report.py` first.

> **Lesson from this project:** you can test retrieval without calling an LLM at all. To choose the reranker cut-off (doc 15) and to check the chunking fix (doc 10), we wrote a throwaway script outside the repo: for each of 22 questions it listed a phrase that *must* appear in the right chunk ("18 paid vacation", "Review daily staffing plan", ...), ran the retriever and reranker, and printed the score of every candidate marked relevant or not. It cost no model tokens, ran in seconds, and found things the 5-question harness could not: one relevant chunk sitting only 0.1 above the old cut-off, and a split checklist. This is the same "source accuracy" idea as above, widened to more questions and made to show scores. Build this kind of check first; reserve the LLM judge for what only a model can grade.

## 🏭 Production Best Practices

1. **Build the golden dataset before you build the system** — Writing test cases forces you to clarify what "correct" means before measuring. A good dataset has 20–50 questions covering each document category and edge cases. **How:** For each source document, write 3–5 questions whose answers are clearly verifiable. Include questions that should return "I don't know" (unanswerable questions test groundedness).

2. **Fix retrieval before tuning prompts** — Source accuracy is the most actionable metric. If `source_accuracy < 0.70`, your retriever isn't finding the right documents. No prompt change fixes bad retrieval. **How:** Check source accuracy first; only tune the RAG prompt after source accuracy is above 80%.

3. **Evaluate after every significant change** — Every change to chunking, embedding model, retrieval strategy, or prompt changes the quality profile. Without eval runs, regressions are invisible. **How:** Run `python -m evals.run_rag_eval` after each change and compare reports with `python -m evals.compare_reports` (it prints every report in `evals/results/` side by side, including the retrieval settings each run used).

4. **Include "I don't know" test cases** — A system that always gives an answer is dangerous. Add test cases with questions that have no answer in the documents. Groundedness score should be high (the system should say "I don't know") and correctness should also be high (agreeing with the expected "I don't know" response). **Why:** LLMs are biased toward giving answers; this tests the "Answer ONLY from context" constraint.

5. **Use `temperature=0` for the judge LLM** — Evaluation must be deterministic and reproducible. The same question should always receive the same score. **How:** `ChatGroq(temperature=0)` for the judge chain.

6. **Version your evaluation reports** — Include the config name (chunking strategy, retrieval type), timestamp, and document version in every report. **Why:** This lets you compare before/after for each change and build an audit trail of quality over time.

## ⚠️ Common Mistakes to Avoid

⚠️ **Testing 5 queries manually and calling it done** — Manual spot-checks miss systematic failures. One configuration might pass your 5 chosen questions but fail on 40% of real-world queries. Always use a structured golden dataset.

⚠️ **Measuring only correctness** — A correct answer that used training data (not context) will be marked correct, but the system just got lucky on a hallucination. Always measure groundedness separately.

⚠️ **Not evaluating retrieval** — If you only measure answer quality, you can't tell whether a wrong answer came from bad retrieval or bad generation. Source accuracy is a 1-line check that immediately shows which is broken.

⚠️ **Using the same LLM as both RAG system and judge** — The judge should ideally be a different model or at minimum a different chain with different instructions. Using the same model can produce inflated self-evaluation scores.

⚠️ **Changing chunking without running evals** — Chunking changes affect every metric silently. A new chunk size that "looks better" might actually drop source accuracy by 20%. Always measure.

## 🔗 How It Connects to Other Concepts

- **RAG Chains** (doc 18, the previous concept) — The chain being evaluated; evaluation reveals which component is the bottleneck
- **Structured Output** (doc 08) — `JudgeResult` uses `with_structured_output()` for typed evaluation scores
- **Text Splitters** (doc 10) — Source accuracy reveals whether chunking strategy is causing retrieval failures
- **Hybrid Search** (doc 14) — Compare source accuracy with and without BM25 to measure its actual contribution
- **LangSmith** (doc 27) — All evaluation chains are automatically traced; LangSmith provides a visual evaluation dashboard

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Systematic measurement of retrieval quality (source accuracy) and answer quality (correctness, groundedness, completeness) |
| **Why** | Separates retrieval failures from generation failures; provides evidence for every system change |
| **When** | Before deployment, after every significant change, on a recurring schedule |
| **Types** | Source accuracy (retrieval), LLM-as-judge (generation quality), pass rate (overall) |
| **Production gotcha** | Build the golden dataset first; fix retrieval before tuning prompts; always measure groundedness; version all reports |

## ➡️ Next Steps

- **Example files:** `evals/run_rag_eval.py`, `evals/judge.py`, `evals/compare_reports.py`
- **Next doc:** `../20_tools_and_function_calling/README.md` — giving the LLM access to live data via callable functions
- **Official docs:** https://python.langchain.com/docs/guides/productionization/evaluation/
