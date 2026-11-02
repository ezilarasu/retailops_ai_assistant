import json
from datetime import datetime
from pathlib import Path

from app.config import settings


RESULTS_DIR = Path("evals/results")


def save_evaluation_report(
    total: int,
    passed: int,
    details: list,
    metrics: dict | None = None,
):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

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
        "metrics": metrics or {},
        "details": details,
    }

    filename = (
        RESULTS_DIR /
        f"eval_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    )

    with open(filename, "w") as file:
        json.dump(report, file, indent=2)

    return filename