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