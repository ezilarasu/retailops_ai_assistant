import json
from pathlib import Path


RESULTS_DIR = Path("evals/results")


def load_reports():
    reports = []

    for file_path in sorted(RESULTS_DIR.glob("eval_*.json")):
        with open(file_path, "r") as file:
            report = json.load(file)

        report["_file"] = str(file_path)
        reports.append(report)

    return reports


def main():
    reports = load_reports()

    if not reports:
        print("No evaluation reports found.")
        return

    print("\nEvaluation Report Comparison\n")

    for report in reports:
        config = report.get("retrieval_config", {})
        metrics = report.get("metrics", {})

        print("File:", report["_file"])
        print("Timestamp:", report.get("timestamp"))
        print("Model:", report.get("model"))
        print("Document Version:", report.get("document_version"))
        print("Score:", report.get("score"))
        print("Pass Rate:", metrics.get("pass_rate"))
        print("Source Accuracy:", metrics.get("source_accuracy"))
        print("Correct Rate:", metrics.get("judge_correct_rate"))
        print("Grounded Rate:", metrics.get("judge_grounded_rate"))
        print("Complete Rate:", metrics.get("judge_complete_rate"))

        print("Config:")
        print("  Semantic Chunking:", config.get("enable_semantic_chunking"))
        print("  Reranking:", config.get("enable_reranking"))
        print("  Multi Query:", config.get("enable_multi_query"))
        print("  Retrieval K:", config.get("retrieval_k"))
        print("  Chunk Size:", config.get("chunk_size"))
        print("  Chunk Overlap:", config.get("chunk_overlap"))
        print("-" * 80)


if __name__ == "__main__":
    main()