from app.chains import format_docs, format_history, retrieve_documents, rewrite_question
from app.config import settings
from app.container import get_container
from app.memory import DEFAULT_SESSION, get_messages


def debug_retrieval(question: str, session_id: str = DEFAULT_SESSION) -> dict:
    # Reuses the retriever and rewriter the running app already built; nothing is re-indexed.
    container = get_container()

    rewritten_question = rewrite_question(
        question,
        format_history(get_messages(session_id)),
        container.rewriter_chain,
    )

    retrieved_docs = retrieve_documents(rewritten_question, container.retriever)

    return {
        "original_question": question,
        "rewritten_question": rewritten_question,
        "multi_query_enabled": settings.enable_multi_query,
        "retrieved": [
            {
                "rank": index,
                "source": doc.metadata.get("source"),
                "rerank_score": doc.metadata.get("rerank_score"),
                "bm25_score": doc.metadata.get("bm25_score"),
                "content_preview": doc.page_content[:500],
            }
            for index, doc in enumerate(retrieved_docs, start=1)
        ],
        "formatted_context": format_docs(retrieved_docs),
    }
