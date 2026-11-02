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
| **Retrieval tests** | Source accuracy (did expected doc get retrieved?) and the retrieval parts (reranker cut-off, multi-query, index freshness) | 5–15s | After retrieval changes — *RetailOps has `tests/test_rag.py` (load, split, retrieve) and `tests/test_retrieval_components.py` (the parts, with fakes); a source-accuracy suite over many questions is something you would add* |
| **RAG evaluation** | Answer quality: correctness, groundedness, completeness | Minutes | After prompt/retrieval changes — *lives in `evals/`, not `tests/`* |
| **Agent tests** | Correct tool selection for operational questions | 5–15s | After tool/agent changes — *not in the repo; `test_router_tools_question` partly covers the tools route* |
| **API tests** | Endpoints, auth, validation (FastAPI `TestClient`) | 1–5s | After API changes — *partly in the repo: `tests/test_errors.py` checks the `/chat` status-code mapping with `TestClient`, `tests/test_security.py` checks the API-key logic; a full endpoint suite is something you would add* |

## 🔀 When to Use Which Type

**Always run unit and router tests** — they're cheap, fast, and catch the most common regression types. A prompt change that accidentally breaks routing will be caught in seconds.

**Run retrieval tests** whenever you change chunk size, embedding model, retrieval type, or how BM25 and vector results are merged. These tests check source accuracy (did `expected_source` appear in retrieved docs?) which is a 1-line check with no LLM call.

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

An **illustrative** set of tests showing the shape of each layer. This is *not* the file in `tests/` (the real tests are in the Real-World Example below); some assertions here are examples you would adapt to your own data. Run from the repository root, because the tools read `data/` with relative paths.

```python
import pytest

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

def test_get_vendor_for_sku_unknown_sku():
    """Tool should handle an unknown SKU gracefully."""
    from app.tools import get_vendor_for_sku
    result = get_vendor_for_sku.invoke({"sku": "NOT-A-REAL-SKU"})
    assert isinstance(result, str)  # no exception raised


# ── Router tests: verify routing decisions ────────────────────────────────
# Router uses structured output at temperature 0, so the route is usually stable
# (but it is still an LLM call: expect the occasional borderline question to flip).
# These tests call the real LLM, so they need GROQ_API_KEY in .env.

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
    from app.rag import load_documents, split_documents
    from app.vectorstore import build_vectorstore, get_retriever

    db = build_vectorstore(split_documents(load_documents()))
    retriever = get_retriever(db)
    docs = retriever.invoke("How many vacation days do employees receive?")
    sources = [doc.metadata.get("source", "") for doc in docs]
    # TextLoader stores the whole path (e.g. "data/hr_policy.txt") as the source,
    # so check with `in` on each string rather than exact list membership.
    assert any("hr_policy.txt" in s for s in sources), f"Expected hr_policy.txt in {sources}"
```

## 🔧 Real-World Example

RetailOps' actual test suite — eight files under `tests/` and 46 tests. The first three (the original suite) cover tools, RAG building blocks and router classification; the other five use fakes in place of the model, so they run in seconds with no API key and no model download. What each one needs to run and covers:

| File | Needs | Notes |
|---|---|---|
| `tests/test_tools.py` | Nothing but the repo (`data/` CSV/JSON files) | Fast, deterministic, no LLM |
| `tests/test_rag.py` | The embedding model (downloaded on first run) | No LLM call. Note it calls `build_vectorstore()`, which writes into the configured `VECTORSTORE_DIR`, and the retrieval test builds its own index in a temporary folder (so it never touches the app's real `vectorstore/`) |
| `tests/test_router.py` | `GROQ_API_KEY` | Real LLM calls through the full app container (builds the index and loads the models); assertions depend on LLM output, so occasional flakiness is possible. They also use real tokens, which matters on the free tier's daily limit |
| `tests/test_errors.py` (8 tests) | Nothing (fake provider errors) | A refusal, rate limit or retired model becomes a typed error; one retry for unparseable model output; `run_router()` returns a friendly error; `/chat` maps error codes to HTTP 422/429/503/502/500 |
| `tests/test_services.py` (6) | Nothing (fake `run_router`) | Cache rules (only first-turn `general`/`rag` answers, never `tools`, never follow-ups), a cache hit still records the turn, per-session chat history |
| `tests/test_security.py` (8) | Nothing | Correct key accepted; missing/wrong/near-miss keys rejected with 401; the placeholder key is refused outside `APP_ENV=local` |
| `tests/test_retrieval_components.py` (12) | Nothing (fake model, temp folder) | Reranker relevance cut-off keeps the best chunk; multi-query reuses the retriever's reranker; the first question skips the rewrite call; the index manifest fingerprint triggers a rebuild only when it should |
| `tests/test_graph.py` (3) | Nothing | The LangGraph version builds without a key; an empty question is rejected by validation with no LLM call; each turn starts with fresh timings and debug info |

**Testing patterns each file teaches** (worth copying into your own project):

- **Fakes instead of the model** (`test_errors.py`, `test_services.py`, `test_retrieval_components.py`, `test_graph.py`). A test that needs a real LLM is slow, costs tokens and can flake. `test_errors.py` builds real `groq.BadRequestError` / `RateLimitError` objects by hand and checks that they become typed errors and that only the right ones are retried. `test_services.py` swaps `run_router` for a small `FakeRouter` that counts calls, so the cache rules can be checked exactly ("was the model called once or twice?"). `test_retrieval_components.py` builds a reranker around a fake model that returns fixed scores, so the relevance cut-off is tested without downloading anything.
- **`monkeypatch` to swap a function or a setting for one test.** It undoes itself afterwards, so tests cannot leak into each other. Assigning `services.run_router = fake` directly would have changed it for every later test.
- **`tmp_path` for anything that writes to disk.** `test_rag.py` points `settings.vectorstore_dir` at a temporary folder and `test_retrieval_components.py` builds its index folders there, so the tests never touch the app's real `vectorstore/`.
- **Test the rule, not just the happy path.** `test_security.py` checks wrong, missing *and almost-right* keys (`@pytest.mark.parametrize` runs one test body over a list of inputs), and `test_retrieval_components.py` checks that changing `chunk_size` triggers an index rebuild only when recursive chunking is on.
- **Normalise before you assert on model text.** `test_router.py` replaces typographic hyphens (U+2010 to U+2015, U+2212) with `-` before looking for `DENIM-4421`, because some models write SKUs with a non-breaking hyphen.

> **Lesson from this project:** both of the first two bugs below were found only because a fresh checkout ran `pytest`. (1) `test_rag.py` once built its index in the app's real `vectorstore/` folder; with no manifest present (exactly what a new clone has), the first router test rebuilt the index by deleting that folder while `test_rag.py`'s connection was still open, and Chroma failed with "attempt to write a readonly database". Giving the test its own temporary folder fixed it. (2) The tools router test asserted that the answer contains `DENIM-4421`, but the model's answer was correct and spelled the SKU with a non-breaking hyphen, so the string match failed. The first is a test-isolation lesson, the second an LLM-output lesson: never let a test depend on shared on-disk state, and never match model text byte for byte.

```python
# ══════════════════════════════════════════════════════════════════════════
# RetailOps test suite (tests/) — shown together here for reading
#
# Run all tests (from the repository root): pytest tests/ -v
# Run evaluation separately: python -m evals.run_rag_eval
#
# Test files (tests/, 46 tests):
#   test_tools.py    — unit tests for @tool functions
#   test_router.py   — end-to-end routing through run_router() (real LLM call)
#   test_rag.py      — document loading, chunking and basic retrieval
#   test_errors.py, test_services.py, test_security.py,
#   test_retrieval_components.py, test_graph.py — fast tests that use fakes
#                      instead of the model (no API key needed)
# ══════════════════════════════════════════════════════════════════════════


# ── tests/test_tools.py ───────────────────────────────────────────────────
# Unit tests for the @tool functions — plain function calls, no LLM involved.

from app.tools import (
    get_low_stock_items,
    get_vendor_for_sku,
    get_open_incidents,
)


def test_get_low_stock_items_returns_string():
    result = get_low_stock_items.invoke({"store_id": "102"})
    assert isinstance(result, str)
    assert "DENIM-4421" in result


def test_get_vendor_for_sku_returns_string():
    result = get_vendor_for_sku.invoke({"sku": "DENIM-4421"})
    assert isinstance(result, str)
    assert "BlueRiver Denim Supply" in result


def test_get_open_incidents_returns_string():
    result = get_open_incidents.invoke({"store_id": "102"})
    assert isinstance(result, str)
    assert "INC-1001" in result


# ── tests/test_router.py ──────────────────────────────────────────────────
# Integration tests: exercises the live router (real LLM call) end-to-end
# and checks that each question lands on the expected route.

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


# ── tests/test_rag.py ──────────────────────────────────────────────────────
# Covers the RAG pipeline itself: document loading, chunking, and retrieval.

from app.config import settings
from app.rag import load_documents, split_documents
from app.vectorstore import build_vectorstore, get_retriever


def test_load_documents():
    docs = load_documents()
    assert len(docs) > 0
    assert any("RetailOps HR Policy" in doc.page_content for doc in docs)


def test_split_documents():
    docs = load_documents()
    chunks = split_documents(docs)
    assert len(chunks) >= len(docs)


def test_retriever_finds_hr_policy(monkeypatch, tmp_path):
    # Use a throwaway index so this test never shares (or deletes) the app's real
    # vectorstore/ folder, which the router tests rebuild on a fresh checkout.
    monkeypatch.setattr(settings, "vectorstore_dir", str(tmp_path / "chroma"))

    docs = load_documents()
    chunks = split_documents(docs)

    db = build_vectorstore(chunks)
    retriever = get_retriever(db)

    results = retriever.invoke(
        "How many vacation days do full-time store employees receive?"
    )
    combined_text = " ".join(doc.page_content for doc in results)
    assert "18 paid vacation days" in combined_text


# The other five files (test_errors, test_services, test_security,
# test_retrieval_components, test_graph) are not reproduced here: read them in tests/.
# They use fakes in place of the model; see the patterns listed above.
```

**Honest coverage summary.** The suite has 46 tests: 9 original ones (3 tool unit tests, 3 router end-to-end tests, 3 RAG building-block tests) and 37 fast tests with fakes for error handling, the cache and sessions, the API key, retrieval components and the LangGraph version. Only the 3 router tests call the LLM. Not covered today: a full suite of API endpoints against the real container, source accuracy over many questions, the hybrid retriever's merge logic end to end, and negative cases such as an unknown store or a question that isn't in the documents. The evaluation set in `evals/rag_questions.jsonl` has only 5 questions — enough to demonstrate the harness (doc 19), not enough to trust as a quality gate. Treat the missing layers as your next exercises. One practical warning: the free Groq tier has a daily token limit per model, and running the router tests, examples and evals repeatedly in one day can use it up; the app then returns its friendly rate-limit message and the router tests fail with it, which is a quota problem, not a code bug.

## 🏭 Production Best Practices

1. **Test the router separately from the RAG chain** — The most impactful test you can add is a parametrized router test. If routing is wrong, everything downstream is wrong. 20 router test cases with `pytest.mark.parametrize` take 2 minutes and catch the most common class of failure. **How:** See `test_router_classification` in the Basic Example (illustrative). RetailOps' own `tests/test_router.py` has three separate, non-parametrized cases that you could convert to this style.

2. **Test source accuracy without the LLM** — Source accuracy tests (does `expected_source` appear in retrieved docs?) require no LLM call. They run in seconds and diagnose the most common RAG failure type. **How:** Call `retriever.invoke(question)` and check `doc.metadata["source"]` against expected.

3. **Use `scope="module"` fixtures for expensive setup** — Building the vector store, loading documents, and constructing the retriever takes 10–30 seconds. Doing it once per test module (not per test case) keeps the test suite fast. **How:** `@pytest.fixture(scope="module") def retriever(): ...`. (RetailOps' `tests/test_rag.py` does not do this yet — `test_retriever_finds_hr_policy` builds its own index inside the test, so adding more retrieval tests would rebuild it each time; a good first refactor.)

4. **Keep evaluation tests separate from unit/integration tests** — Evaluation tests call the LLM multiple times and cost money. Don't run them in your fast test suite (`pytest tests/`). Run them separately via `python -m evals.run_rag_eval`. **How:** Put evaluation code in `evals/` not `tests/`.

5. **Include negative test cases** — Test that the system says "I don't know" for questions not in the knowledge base, and that missing data files return safe error messages rather than raising exceptions. These edge cases cause the most embarrassing production failures. **How:** `test_tool_handles_missing_csv()`, `test_rag_returns_not_found_for_unknown_topic()`.

6. **Run router tests in CI/CD** — Router accuracy is easy to check automatically and represents the most common regression type after prompt changes. Add to your CI pipeline. **How:** `pytest tests/test_router.py -v` as a CI step (store `GROQ_API_KEY` as a CI secret; there is no CI configuration in this repo yet).

## ⚠️ Common Mistakes to Avoid

⚠️ **Only manual testing** — Running 5 questions by hand before deploying misses systematic failures. A prompt change that breaks routing for inventory questions won't appear in your 5 chosen test questions. The parametrized router tests above cover this in seconds.

⚠️ **Testing only the happy path** — Test what happens when the CSV is missing, the vector store is empty, and the question has no answer in the knowledge base. Production is full of edge cases that happy-path testing misses.

⚠️ **Treating evaluation as your only test** — Running the full LLM-judge evaluation on every code change is slow and expensive. Unit and integration tests (which don't need LLM calls) catch most regression types faster and cheaper.

⚠️ **Not testing retrieval separately from generation** — When a test fails in evaluation (wrong answer), you need to know: was it the retriever's fault or the LLM's fault? Without separate retrieval tests, you can't tell. Source accuracy tests give you this immediately.

⚠️ **Asserting exact LLM output** — `assert result.answer == "P1 means a full store outage."` will fail when the LLM rephrases. Use semantic comparison (LLM judge) for answer text, and structural assertions (`isinstance(result, RAGResponse)`, `"hr_policy.txt" in result.sources`) for everything else.

## 🔗 How It Connects to Other Concepts

- **RAG Evaluation** (doc 19) — The evaluation pipeline (LLM judge, question set in `evals/rag_questions.jsonl`, JSON reports) is the evaluation test layer; this doc describes the unit and integration layers that sit below it
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

- **Example files:** everything under `tests/` (`test_tools.py`, `test_router.py`, `test_rag.py`, `test_errors.py`, `test_services.py`, `test_security.py`, `test_retrieval_components.py`, `test_graph.py`) — run with `pytest -v` from the repository root; only `test_router.py` needs `GROQ_API_KEY`, and `pytest tests/test_errors.py tests/test_services.py tests/test_security.py tests/test_retrieval_components.py tests/test_graph.py` runs the 37 key-free tests
- **Previous doc:** `../27_langsmith/README.md`
- **Next doc:** `../29_caching/README.md` — reducing LLM call costs and latency with response and retrieval caching
- **Official docs:** https://docs.pytest.org/en/stable/
