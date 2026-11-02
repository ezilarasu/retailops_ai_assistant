# RAG Evaluation
> The difference between "it looks good" and "it works" — measuring what the system actually does.

## 📌 What Is It?

**RAG evaluation** is the systematic process of measuring retrieval quality and answer quality against a **golden dataset** — a set of known questions with expected answers and source documents.

It answers three questions:
1. **Did the retriever find the right document?** (source accuracy)
2. **Is the answer factually correct?** (correctness)
3. **Is the answer grounded in the retrieved context?** (groundedness — the anti-hallucination metric)

RetailOps uses an **LLM-as-judge** approach: an LLM evaluates each question-answer pair against the golden expected answer and returns a structured `JudgeResult`:

```python
@dataclass
class JudgeResult:
    correct: bool       # does the answer match the expected answer?
    grounded: bool      # is every claim in the answer supported by context?
    complete: bool      # does the answer cover all key points?
    score: float        # overall quality 0.0–1.0
    reasoning: str      # step-by-step explanation of the scores
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
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

load_dotenv()

judge_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# ── JudgeResult schema ────────────────────────────────────────────────────
class JudgeResult(BaseModel):
    correct: bool = Field(description="Is the answer factually correct per the expected answer?")
    grounded: bool = Field(description="Is every claim in the answer supported by the provided context?")
    complete: bool = Field(description="Does the answer cover all key information from the expected answer?")
    score: float = Field(description="Overall quality score 0.0–1.0")
    reasoning: str = Field(description="Step-by-step evaluation explaining each score")

# ── Judge chain ───────────────────────────────────────────────────────────
JUDGE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert evaluator for a RAG system.
Evaluate the answer against the expected answer and the retrieved context.
Think step by step before scoring. Be strict about groundedness — any claim
not found in the context should be marked as NOT grounded."""),
    ("human", """Question: {question}
Retrieved Context: {context}
Expected Answer: {expected}
Actual Answer: {actual}

Evaluate: correctness, groundedness, completeness."""),
])

judge_chain = JUDGE_PROMPT | judge_llm.with_structured_output(JudgeResult)

# ── Golden dataset ────────────────────────────────────────────────────────
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
    result = rag_chain.invoke({"question": test_case["question"], "history": []})

    # Source accuracy: did retrieval find the expected document?
    source_correct = test_case["expected_source"] in result.sources

    # LLM judge for generation quality
    judge_result = judge_chain.invoke({
        "question": test_case["question"],
        "context": f"Sources: {result.sources}\nAnswer: {result.answer}",
        "expected": test_case["expected_answer"],
        "actual": result.answer,
    })

    return {
        "question": test_case["question"],
        "source_correct": source_correct,
        "correct": judge_result.correct,
        "grounded": judge_result.grounded,
        "complete": judge_result.complete,
        "score": judge_result.score,
        "passed": source_correct and judge_result.correct and judge_result.grounded,
    }
```

## 🔧 Real-World Example

RetailOps' full evaluation pipeline — runs against the golden dataset, generates a JSON report, and supports comparison between retrieval configurations.

```python
import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

load_dotenv()

judge_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# ══════════════════════════════════════════════════════════════════════════
# evals/run_rag_eval.py — RetailOps evaluation pipeline
# Run: python -m evals.run_rag_eval
# Output: evals/reports/eval_TIMESTAMP.json
# ══════════════════════════════════════════════════════════════════════════

class JudgeResult(BaseModel):
    correct: bool = Field(description="Answer matches expected answer")
    grounded: bool = Field(description="Every claim is supported by the retrieved context")
    complete: bool = Field(description="Answer covers all key points from expected answer")
    score: float = Field(description="Overall quality score 0.0–1.0")
    reasoning: str = Field(description="Step-by-step explanation of scores")


JUDGE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a strict evaluator for a retail operations AI assistant.

Evaluate the actual answer against:
1. The expected answer — for correctness and completeness
2. The retrieved context — for groundedness (no hallucinations)

Be strict: if ANY claim in the answer is not supported by the context,
mark grounded=false. Paraphrasing is fine; adding new facts is not."""),
    ("human", """Question: {question}

Retrieved Context:
{context}

Expected Answer: {expected}
Actual Answer: {actual}

Evaluate step by step."""),
])

judge_chain = JUDGE_PROMPT | judge_llm.with_structured_output(JudgeResult)


def load_golden_dataset(path: str = "evals/golden_dataset.json") -> list[dict]:
    """Load the golden dataset from JSON.

    Format: [{"question": str, "expected_answer": str, "expected_source": str}]
    """
    with open(path) as f:
        return json.load(f)


def run_evaluation(
    rag_chain,
    golden_dataset: list[dict],
    config_name: str = "default",
) -> dict:
    """Run evaluation against the golden dataset.

    Args:
        rag_chain: Chain that accepts {"question": str, "history": list}
                   and returns RAGResponse (with .answer, .sources, .confidence)
        golden_dataset: List of {"question", "expected_answer", "expected_source"}
        config_name: Label for this eval run (e.g., "hybrid_with_reranking")

    Returns:
        Evaluation report dict with per-question results and aggregate metrics
    """
    results = []

    for i, test_case in enumerate(golden_dataset):
        print(f"Evaluating [{i+1}/{len(golden_dataset)}]: {test_case['question'][:50]}")

        # Run the RAG chain
        try:
            rag_result = rag_chain.invoke({
                "question": test_case["question"],
                "history": [],
            })
            answer = rag_result.answer
            sources = rag_result.sources
        except Exception as e:
            results.append({
                "question": test_case["question"],
                "error": str(e),
                "passed": False,
            })
            continue

        # Source accuracy check (no LLM call needed)
        source_correct = test_case["expected_source"] in sources

        # LLM judge for generation quality
        context_for_judge = "\n".join(f"- {s}" for s in sources) + f"\n\nAnswer: {answer}"
        judge = judge_chain.invoke({
            "question": test_case["question"],
            "context": context_for_judge,
            "expected": test_case["expected_answer"],
            "actual": answer,
        })

        result = {
            "question": test_case["question"],
            "expected_source": test_case["expected_source"],
            "retrieved_sources": sources,
            "source_correct": source_correct,
            "answer": answer,
            "expected_answer": test_case["expected_answer"],
            "correct": judge.correct,
            "grounded": judge.grounded,
            "complete": judge.complete,
            "score": judge.score,
            "reasoning": judge.reasoning,
            "passed": source_correct and judge.correct and judge.grounded,
        }
        results.append(result)

    # Aggregate metrics
    n = len(results)
    n_valid = [r for r in results if "error" not in r]

    report = {
        "config": config_name,
        "timestamp": datetime.now().isoformat(),
        "total_questions": n,
        "metrics": {
            "pass_rate": sum(r.get("passed", False) for r in results) / n,
            "source_accuracy": sum(r.get("source_correct", False) for r in n_valid) / len(n_valid) if n_valid else 0,
            "judge_correct_rate": sum(r.get("correct", False) for r in n_valid) / len(n_valid) if n_valid else 0,
            "judge_grounded_rate": sum(r.get("grounded", False) for r in n_valid) / len(n_valid) if n_valid else 0,
            "judge_complete_rate": sum(r.get("complete", False) for r in n_valid) / len(n_valid) if n_valid else 0,
            "avg_score": sum(r.get("score", 0) for r in n_valid) / len(n_valid) if n_valid else 0,
        },
        "results": results,
    }

    # Save report
    Path("evals/reports").mkdir(parents=True, exist_ok=True)
    report_path = f"evals/reports/eval_{config_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n=== Evaluation Report: {config_name} ===")
    for k, v in report["metrics"].items():
        print(f"  {k}: {v:.1%}" if isinstance(v, float) else f"  {k}: {v}")
    print(f"  Report saved: {report_path}")

    return report
```

## 🏭 Production Best Practices

1. **Build the golden dataset before you build the system** — Writing test cases forces you to clarify what "correct" means before measuring. A good dataset has 20–50 questions covering each document category and edge cases. **How:** For each source document, write 3–5 questions whose answers are clearly verifiable. Include questions that should return "I don't know" (unanswerable questions test groundedness).

2. **Fix retrieval before tuning prompts** — Source accuracy is the most actionable metric. If `source_accuracy < 0.70`, your retriever isn't finding the right documents. No prompt change fixes bad retrieval. **How:** Check source accuracy first; only tune the RAG prompt after source accuracy is above 80%.

3. **Evaluate after every significant change** — Every change to chunking, embedding model, retrieval strategy, or prompt changes the quality profile. Without eval runs, regressions are invisible. **How:** Run `python -m evals.run_rag_eval` after each change and compare reports with `evals/compare_reports.py`.

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

- **RAG Chains** (doc 18) — The chain being evaluated; evaluation reveals which component is the bottleneck
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
- **Next doc:** `20_tools_and_function_calling.md` — giving the LLM access to live data via callable functions
- **Official docs:** https://python.langchain.com/docs/guides/productionization/evaluation/
