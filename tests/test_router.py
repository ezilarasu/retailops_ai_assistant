import re

from app.router import run_router
from app.memory import clear_memory


def test_router_general_question():
    clear_memory()

    result = run_router("Hello, who are you?")

    assert result["route"] == "general"
    assert "answer" in result


def test_router_rag_question():
    clear_memory()

    result = run_router(
        "How many vacation days do full-time store employees receive?"
    )

    assert result["route"] == "rag"
    assert "18" in result["answer"]


def test_router_tools_question():
    clear_memory()

    result = run_router("Which items are low stock in store 102?")

    assert result["route"] == "tools"

    # Some models write SKUs with a non-breaking hyphen (U+2011); normalise before matching.
    answer = re.sub("[‐-―−]", "-", result["answer"])
    assert "DENIM-4421" in answer or "JKT-7781" in answer