# Testing AI Systems
> Testing AI is different from testing normal software — here's exactly what to test and how.

## 📌 What Is It?

**Testing AI systems** means verifying that each layer of your application behaves correctly — from individual utility functions (unit tests) to the full pipeline answer quality (evaluation tests). It's harder than traditional testing because AI outputs are probabilistic: the same question can produce slightly different answers on each run, making exact-equality assertions fragile.

The solution is a layered testing strategy:

```
Testing Pyramid for AI:

  ┌─────────────────────┐
  │    Evaluation        │  ← Quality: does the answer match expected? (LLM judge)
  ├─────────────────────┤
  │  Integration Tests   │  ← Behavior: does retrieval find the right doc?
  ├─────────────────────┤
  │    Unit Tests        │  ← Correctness: do utility functions work?
  └─────────────────────┘
```

Each layer tests something different:
- **Unit tests** — deterministic functions: tool implementations, parsers, validators
- **Integration tests** — component behavior: does the router select the right route? does retrieval find the expected source?
- **Evaluation tests** — answer quality: is the answer correct, grounded, and complete? (uses the LLM judge from doc 19)

## ❓ Why Does It Exist?

Without tests, every change to your system — new chunk size, modified prompt, different retrieval strategy — is a black box. You run it manually, it "looks fine", and you deploy. Three days later users report that half the inventory questions are going to RAG instead of the tools agent.

The testing pyramid gives you systematic coverage:
- Unit tests catch regressions in utility functions immediately (sub-second)
- Integration tests catch routing and retrieval failures without running the full pipeline (seconds)
- Evaluation tests catch quality regressions against the full golden dataset (minutes)

**The key insight:** most developers skip to evaluation tests and ignore unit and integration tests. But routing and retrieval failures are caught much faster and cheaper by targeted integration tests than by running a full LLM-judge evaluation.

## ⏰ When Should You Use It?

✅ Run unit tests on every code change (fast, always)  
✅ Run integration tests before every pull request  
✅ Run evaluation tests after any change to prompts, chunking, or retrieval  
✅ Run evaluation tests on a schedule to detect quality regressions  

❌ Don't use exact string matching for LLM output — use semantic evaluation  
❌ Don't skip retrieval testing — most RAG failures are retrieval failures  
❌ Don't test only the happy path — include edge cases and "I don't know" cases  

## 🗂️ Types / Variants

| Test Type | What It Tests | Speed | When to Run |
|---|---|---|---|
| **Unit tests** | Individual functions: tools, parsers, validators | < 1s | Every change |
| **Router tests** | Route classification accuracy | 2–5s | Every change |
| **Retrieval tests** | Source accuracy (did expected doc get retrieved?) | 5–15s | After retrieval changes |
| **RAG evaluation** | Answer quality: correctness, groundedness, completeness | Minutes | After prompt/retrieval changes |
| **Agent tests** | Correct tool selection for operational questions | 5–15s | After tool/agent changes |

## 🔀 When to Use Which Type

**Always run unit and router tests** — they're cheap, fast, and catch the most common regression types. A prompt change that accidentally breaks routing will be caught in seconds.

**Run retrieval tests** whenever you change chunk size, embedding model, retrieval type, or BM25 weights. These tests check source accuracy (did `expected_source` appear in retrieved docs?) which is a 1-line check with no LLM call.

**Run full RAG evaluation** after major changes — it's slower and costs LLM calls for the judge. Don't run it on every commit; run it when you've made a change that could affect answer quality.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Catches regressions before users see them | AI testing requires more thought than `assert a == b` |
| Different test layers catch different failure types | Evaluation tests cost LLM calls and take minutes |
| Router and retrieval tests don't require LLM calls | LLM non-determinism means some flakiness is expected |
| Golden dataset makes quality measurable over time | Building a good golden dataset takes upfront work |
| Forces clarity about what "correct" means | Over-testing evaluation creates false confidence |

## 💻 Basic Example

```python
import pytest
from unittest.mock import patch

# ── Unit tests: test tool functions directly ──────────────────────────────
# Tools are plain Python functions — test them like any function.

def test_get_low_stock_items_valid_store():
    """Tool should return items for a valid store."""
    from app.tools import get_low_stock_items
    result = get_low_stock_items.invoke({"store_id": "101"})
    # The tool returns a string — check it contains the right shape
    assert "Low stock items" in result or "No low-stock items" in result

def test_get_low_stock_items_missing_store():
    """Tool should return safe message for unknown store."""
    from app.tools import get_low_stock_items
    result = get_low_stock_items.invoke({"store_id": "999"})
    # Should not raise — should return a message
    assert isinstance(result, str)
    assert len(result) > 0

def test_get_store_sales_invalid_period():
    """Tool should handle unexpected period values gracefully."""
    from app.tools import get_store_sales
    result = get_store_sales.invoke({"store_id": "101", "period": "last_decade"})
    assert isinstance(result, str)  # no exception raised


# ── Router tests: verify routing decisions ────────────────────────────────
# Router uses structured output — the route field is deterministic at temp=0.

@pytest.mark.parametrize("question,expected_route", [
    ("Hello, how are you?", "general"),
    ("What is the return policy?", "rag"),
    ("What does P1 mean?", "rag"),
    ("Which items are low in stock?", "tools"),
    ("Show me today's sales for store 101.", "tools"),
    ("How many vacation days do employees get?", "rag"),
])
def test_router_classification(question, expected_route):
    """Router should classify questions into the correct route."""
    from app.router import route_question
    decision = route_question(question)
    assert decision.route == expected_route, (
        f"Expected '{expected_route}' for '{question}', got '{decision.route}' "
        f"(reason: {decision.reason})"
    )


# ── Retrieval test: check source accuracy ────────────────────────────────
def test_retrieval_finds_vacation_policy():
    """Retriever should find hr_policy.txt for vacation day questions."""
    from app.vector_store import build_retriever  # your retriever builder
    retriever = build_retriever()
    docs = retriever.invoke("How many vacation days do employees receive?")
    sources = [doc.metadata.get("source", "") for doc in docs]
    assert "hr_policy.txt" in sources, f"Expected hr_policy.txt in {sources}"
```

## 🔧 Real-World Example

RetailOps' complete test suite — organized by layer, with parametrized router tests, retrieval source accuracy tests, and the integration between the test suite and the RAG evaluation pipeline.

```python
import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# ══════════════════════════════════════════════════════════════════════════
# tests/test_suite.py — RetailOps layered test suite
#
# Run unit + integration tests: pytest tests/ -v
# Run evaluation separately: python -m evals.run_rag_eval
#
# Test categories:
#   test_tools.py        — unit tests for @tool functions
#   test_router.py       — routing accuracy (LLM call, parametrized)
#   test_retrieval.py    — source accuracy (real vector store, no LLM)
#   test_api.py          — FastAPI endpoint tests (TestClient)
# ══════════════════════════════════════════════════════════════════════════


# ── tests/test_tools.py ───────────────────────────────────────────────────

class TestGetLowStockItems:
    """Unit tests for the get_low_stock_items tool."""

    def test_returns_string(self):
        from app.tools import get_low_stock_items
        result = get_low_stock_items.invoke({"store_id": "101"})
        assert isinstance(result, str)

    def test_unknown_store_returns_message(self):
        from app.tools import get_low_stock_items
        result = get_low_stock_items.invoke({"store_id": "999"})
        assert "999" in result  # error message includes store ID

    def test_all_stores(self):
        from app.tools import get_low_stock_items
        result = get_low_stock_items.invoke({"store_id": "all"})
        assert isinstance(result, str)
        assert len(result) > 0

    def test_missing_csv_returns_safe_message(self):
        """When CSV file is missing, tool should return error string, not raise."""
        from app.tools import get_low_stock_items
        with patch("app.tools.DATA_DIR", "/nonexistent/path/"):
            result = get_low_stock_items.invoke({"store_id": "101"})
        assert "Unable to retrieve" in result  # safe error message


# ── tests/test_router.py ──────────────────────────────────────────────────

ROUTING_TEST_CASES = [
    # (question, expected_route)
    ("Hello!", "general"),
    ("Who are you?", "general"),
    ("What is the return policy for damaged items?", "rag"),
    ("What does P1 mean?", "rag"),
    ("How many vacation days do employees receive?", "rag"),
    ("Which stores have low inventory?", "tools"),
    ("Show me today's sales for store 102.", "tools"),
    ("Are there any open P1 incidents?", "tools"),
    ("What is the escalation procedure for P2?", "rag"),
]


@pytest.mark.parametrize("question,expected", ROUTING_TEST_CASES)
def test_router(question, expected):
    """Router should classify each question into the correct route.

    Uses the live LLM (ChatGroq) — requires GROQ_API_KEY in environment.
    """
    from app.router import route_question
    decision = route_question(question)
    assert decision.route == expected, (
        f"\nQuestion: {question!r}\n"
        f"Expected: {expected}\n"
        f"Got:      {decision.route}\n"
        f"Reason:   {decision.reason}"
    )


# ── tests/test_retrieval.py ───────────────────────────────────────────────

RETRIEVAL_TEST_CASES = [
    ("How many vacation days do employees receive?", "hr_policy.txt"),
    ("What does P1 mean?", "it_support_kb.txt"),
    ("What is the returns policy?", "returns_policy.txt"),
    ("How do I process a refund?", "returns_policy.txt"),
    ("What is the escalation process for P2?", "it_support_kb.txt"),
]


@pytest.fixture(scope="module")
def retriever():
    """Build retriever once for all retrieval tests (expensive)."""
    from app.vector_store import initialize_vectorstore, build_reranking_retriever
    from app.document_loader import load_all_documents
    vectorstore = initialize_vectorstore()
    all_docs = load_all_documents()
    return build_reranking_retriever(vectorstore, all_docs)


@pytest.mark.parametrize("question,expected_source", RETRIEVAL_TEST_CASES)
def test_retrieval_source_accuracy(question, expected_source, retriever):
    """Retriever should return the expected source document.

    This is a pure retrieval test — no LLM call, no generation.
    Failing tests here indicate chunking, embedding, or retrieval config issues.
    """
    docs = retriever.invoke(question)
    sources = [doc.metadata.get("source", "") for doc in docs]
    assert expected_source in sources, (
        f"\nQuestion: {question!r}\n"
        f"Expected source: {expected_source}\n"
        f"Retrieved:       {sources}"
    )


# ── tests/test_api.py ─────────────────────────────────────────────────────

def test_health_endpoint():
    """Health endpoint should return 200 with status ok."""
    from fastapi.testclient import TestClient
    from app.api import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_endpoint_returns_answer():
    """Chat endpoint should return an answer and route."""
    from fastapi.testclient import TestClient
    from app.api import app
    client = TestClient(app)
    response = client.post("/chat", json={"question": "Hello"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["route"] in ("general", "rag", "tools")


def test_chat_endpoint_rejects_empty_question():
    """Chat endpoint should reject empty questions with 422."""
    from fastapi.testclient import TestClient
    from app.api import app
    client = TestClient(app)
    response = client.post("/chat", json={"question": ""})
    assert response.status_code == 422  # Pydantic min_length=1 validation
```

## 🏭 Production Best Practices

1. **Test the router separately from the RAG chain** — The most impactful test you can add is a parametrized router test. If routing is wrong, everything downstream is wrong. 20 router test cases with `pytest.mark.parametrize` take 2 minutes and catch the most common class of failure. **How:** See `ROUTING_TEST_CASES` parametrized tests above.

2. **Test source accuracy without the LLM** — Source accuracy tests (does `expected_source` appear in retrieved docs?) require no LLM call. They run in seconds and diagnose the most common RAG failure type. **How:** Call `retriever.invoke(question)` and check `doc.metadata["source"]` against expected.

3. **Use `scope="module"` fixtures for expensive setup** — Building the vector store, loading documents, and constructing the retriever takes 10–30 seconds. Doing it once per test module (not per test case) keeps the test suite fast. **How:** `@pytest.fixture(scope="module") def retriever(): ...`

4. **Keep evaluation tests separate from unit/integration tests** — Evaluation tests call the LLM multiple times and cost money. Don't run them in your fast test suite (`pytest tests/`). Run them separately via `python -m evals.run_rag_eval`. **How:** Put evaluation code in `evals/` not `tests/`.

5. **Include negative test cases** — Test that the system says "I don't know" for questions not in the knowledge base, and that missing data files return safe error messages rather than raising exceptions. These edge cases cause the most embarrassing production failures. **How:** `test_tool_handles_missing_csv()`, `test_rag_returns_not_found_for_unknown_topic()`.

6. **Run router tests in CI/CD** — Router accuracy is easy to check automatically and represents the most common regression type after prompt changes. Add to your CI pipeline. **How:** `pytest tests/test_router.py -v` as a CI step.

## ⚠️ Common Mistakes to Avoid

⚠️ **Only manual testing** — Running 5 questions by hand before deploying misses systematic failures. A prompt change that breaks routing for inventory questions won't appear in your 5 chosen test questions. The parametrized router tests above cover this in seconds.

⚠️ **Testing only the happy path** — Test what happens when the CSV is missing, the vector store is empty, and the question has no answer in the knowledge base. Production is full of edge cases that happy-path testing misses.

⚠️ **Treating evaluation as your only test** — Running the full LLM-judge evaluation on every code change is slow and expensive. Unit and integration tests (which don't need LLM calls) catch most regression types faster and cheaper.

⚠️ **Not testing retrieval separately from generation** — When a test fails in evaluation (wrong answer), you need to know: was it the retriever's fault or the LLM's fault? Without separate retrieval tests, you can't tell. Source accuracy tests give you this immediately.

⚠️ **Asserting exact LLM output** — `assert result.answer == "P1 means a full store outage."` will fail when the LLM rephrases. Use semantic comparison (LLM judge) for answer text, and structural assertions (`isinstance(result, RAGResponse)`, `"hr_policy.txt" in result.sources`) for everything else.

## 🔗 How It Connects to Other Concepts

- **RAG Evaluation** (doc 19) — The evaluation pipeline (LLM judge, golden dataset, JSON reports) is the evaluation test layer; this doc describes the unit and integration layers that sit below it
- **Router Pattern** (doc 23) — Router accuracy is the most impactful integration test to add; routing errors cascade to every downstream component
- **Tools & Function Calling** (doc 20) — Tools are plain Python functions and the easiest thing to unit test; test them in isolation before testing the agent
- **FastAPI Integration** (doc 25) — FastAPI's `TestClient` lets you test endpoints without starting a server; test validation, routing, and error responses
- **LangSmith** (doc 27) — Failed tests become investigation starting points; LangSmith traces help diagnose why a test failed

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Layered test strategy: unit tests (functions), integration tests (routing/retrieval), evaluation tests (answer quality) |
| **Why** | AI systems fail silently; systematic tests catch routing and retrieval regressions before users see wrong answers |
| **When** | Unit/integration: every change; evaluation: after prompt/retrieval/model changes |
| **Types** | Unit (tools, parsers), router (classification), retrieval (source accuracy), evaluation (LLM judge), API (endpoints) |
| **Production gotcha** | Test routing first; source accuracy tests need no LLM; keep evaluation separate from unit/integration tests |

## ➡️ Next Steps

- **Example files:** `tests/test_tools.py`, `tests/test_router.py`, `tests/test_retrieval.py`, `tests/test_api.py`
- **Next doc:** `29_caching.md` — reducing LLM call costs and latency with response and retrieval caching
- **Official docs:** https://docs.pytest.org/en/stable/
