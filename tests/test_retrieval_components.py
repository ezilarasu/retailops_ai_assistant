import json
from pathlib import Path

import pytest
from langchain_core.documents import Document

from app import indexing
from app.chains import rewrite_question
from app.config import settings
from app.multi_query import retrieve_with_multi_query
from app.reranker import CrossEncoderReranker


def make_reranker(scores, min_score):
    """A reranker with a fake model, so the test needs no model download."""

    class FakeModel:
        def predict(self, pairs):
            return scores

    reranker = object.__new__(CrossEncoderReranker)
    reranker.model = FakeModel()
    reranker.min_score = min_score

    return reranker


def docs(n):
    return [Document(page_content=f"chunk {i}", metadata={"source": f"s{i}"}) for i in range(n)]


def test_reranker_drops_chunks_below_the_cutoff_but_keeps_the_best():
    reranker = make_reranker([8.0, -9.5, 1.0, -3.0], min_score=-8.5)

    kept = reranker.rerank("q", docs(4), top_k=4)

    assert [d.page_content for d in kept] == ["chunk 0", "chunk 2", "chunk 3"]
    assert kept[0].metadata["rerank_score"] == 8.0

    # Even when everything scores below the cut-off, the single best chunk survives.
    kept = make_reranker([-10.0, -9.0, -11.0], min_score=-8.5).rerank("q", docs(3), top_k=3)

    assert [d.page_content for d in kept] == ["chunk 1"]


def test_reranker_without_a_cutoff_keeps_top_k():
    kept = make_reranker([8.0, -9.5, 1.0], min_score=None).rerank("q", docs(3), top_k=2)

    assert [d.page_content for d in kept] == ["chunk 0", "chunk 2"]


class FakeRetriever:
    def __init__(self, reranker):
        self.reranker = reranker

    def get_candidates(self, query):
        return docs(3)


def test_multi_query_reuses_the_retrievers_reranker(monkeypatch):
    monkeypatch.setattr("app.multi_query.generate_queries", lambda q: [q, q + " alt"])
    reranker = make_reranker([5.0, 1.0, 0.0], min_score=None)

    result = retrieve_with_multi_query("q", FakeRetriever(reranker), final_top_k=2)

    assert [d.page_content for d in result] == ["chunk 0", "chunk 1"]


def test_multi_query_skips_reranking_when_the_retriever_has_none(monkeypatch):
    monkeypatch.setattr("app.multi_query.generate_queries", lambda q: [q])

    result = retrieve_with_multi_query("q", FakeRetriever(None), final_top_k=2)

    assert [d.page_content for d in result] == ["chunk 0", "chunk 1"]


class ExplodingChain:
    def invoke(self, *args, **kwargs):
        raise AssertionError("the rewriter must not be called on the first turn")


def test_first_question_skips_the_rewrite_llm_call():
    assert rewrite_question("What does P1 mean?", "", ExplodingChain()) == "What does P1 mean?"
    assert rewrite_question("What does P1 mean?", "   \n ", ExplodingChain()) == "What does P1 mean?"


def test_follow_up_is_rewritten_using_history():
    class Chain:
        def invoke(self, inputs):
            return f"standalone: {inputs['question']} | {inputs['chat_history']}"

    assert rewrite_question("And part-time?", "human: vacation days?", Chain()) == (
        "standalone: And part-time? | human: vacation days?"
    )


@pytest.fixture
def index_dir(tmp_path, monkeypatch):
    store = tmp_path / "chroma"
    store.mkdir()
    monkeypatch.setattr(settings, "vectorstore_dir", str(store))
    monkeypatch.setattr(settings, "document_version", "v1")
    monkeypatch.setattr(settings, "enable_semantic_chunking", True)

    rebuilds = []
    monkeypatch.setattr(indexing, "rebuild_index", lambda: rebuilds.append(1) or {"status": "rebuilt"})

    return tmp_path, rebuilds


def write_current_manifest(folder: Path):
    (folder / "manifest.json").write_text(json.dumps({**indexing.index_fingerprint(), "chunk_count": 7}))


def test_manifest_lives_next_to_the_index_folder(index_dir):
    folder, _ = index_dir

    assert indexing.manifest_path() == folder / "manifest.json"


def test_missing_manifest_triggers_a_rebuild(index_dir):
    _, rebuilds = index_dir

    indexing.ensure_index_current()

    assert rebuilds == [1]


def test_matching_manifest_means_no_rebuild(index_dir):
    folder, rebuilds = index_dir
    write_current_manifest(folder)

    status = indexing.ensure_index_current()

    assert status["status"] == "current"
    assert rebuilds == []


def test_changed_settings_trigger_a_rebuild(index_dir, monkeypatch):
    folder, rebuilds = index_dir
    write_current_manifest(folder)

    monkeypatch.setattr(settings, "document_version", "v2")
    indexing.ensure_index_current()
    assert len(rebuilds) == 1

    monkeypatch.setattr(settings, "document_version", "v1")
    monkeypatch.setattr(settings, "enable_semantic_chunking", False)
    indexing.ensure_index_current()
    assert len(rebuilds) == 2


def test_chunk_size_only_matters_for_recursive_chunking(index_dir, monkeypatch):
    folder, rebuilds = index_dir
    write_current_manifest(folder)

    monkeypatch.setattr(settings, "chunk_size", 999)
    indexing.ensure_index_current()
    assert rebuilds == []  # semantic chunking ignores chunk_size

    monkeypatch.setattr(settings, "enable_semantic_chunking", False)
    write_current_manifest(folder)
    monkeypatch.setattr(settings, "chunk_size", 123)
    indexing.ensure_index_current()
    assert len(rebuilds) == 1


def test_missing_index_folder_triggers_a_rebuild(index_dir):
    folder, rebuilds = index_dir
    write_current_manifest(folder)
    (folder / "chroma").rmdir()

    indexing.ensure_index_current()

    assert rebuilds == [1]
