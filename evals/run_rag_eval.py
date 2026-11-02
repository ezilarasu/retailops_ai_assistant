import json
from pathlib import Path

from app.container import get_container
from evals.evaluation_report import save_evaluation_report
from evals.judge import judge_answer


EVAL_FILE = Path("evals/rag_questions.jsonl")


def normalize(text: str) -> str:
    return text.lower().strip()



def run_eval():
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

            result = container.rag_chain.invoke({
                "question": question
            })

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

            print("\nQuestion:", question)
            print("Expected Answer:", expected_answer_raw)
            print("Actual Answer:", result.answer)
            print("Expected Source:", expected_source)
            print("Actual Sources:", result.sources)
            print("Answer Match:", answer_match)
            print("Source Match:", source_match)
            print("Judge Correct:", judge.correct)
            print("Judge Grounded:", judge.grounded)
            print("Judge Complete:", judge.complete)
            print("Judge Explanation:", judge.explanation)
            print("Passed:", success)

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

    print("\nRAG Eval Summary")
    print("Passed:", passed)
    print("Total:", total)
    print("Score:", f"{passed}/{total}")
    
    metrics = {
        "total": total,
        "passed": passed,
        "pass_rate": round(passed / total, 4),
        "source_accuracy": round(source_hits / total, 4),
        "judge_correct_rate": round(judge_correct_count / total, 4),
        "judge_grounded_rate": round(judge_grounded_count / total, 4),
        "judge_complete_rate": round(judge_complete_count / total, 4),
    }

    print("\nMetrics:")
    for key, value in metrics.items():
        print(key, ":", value)    

    report_file = save_evaluation_report(
        total=total,
        passed=passed,
        details=details,
        metrics=metrics,
    )

    print("\nSaved report:", report_file)


if __name__ == "__main__":
    run_eval()