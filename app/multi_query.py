from functools import lru_cache

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.llm import get_llm
from app.config import settings

multi_query_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        Generate 3 different search queries for retrieving relevant company policy or operations documents.

        Rules:
        - Return one query per line.
        - Do not answer the question.
        - Do not number the queries.
        - Keep each query concise.
        """
    ),
    (
        "human",
        """
        Original question:
        {question}
        """
    ),
])


@lru_cache(maxsize=1)  # build the chain (and its LLM client) once, not on every question
def build_multi_query_chain():
    llm = get_llm()
    parser = StrOutputParser()

    return multi_query_prompt | llm | parser


def generate_queries(question: str) -> list[str]:
    chain = build_multi_query_chain()

    result = chain.invoke({
        "question": question
    })

    queries = [
        line.strip("- ").strip()
        for line in result.splitlines()
        if line.strip()
    ]

    queries.insert(0, question)

    deduped = []
    seen = set()

    for query in queries:
        normalized = query.lower()

        if normalized not in seen:
            seen.add(normalized)
            deduped.append(query)

    return deduped[:4]

def retrieve_with_multi_query(
    question: str,
    retriever,
    final_top_k: int | None = None,
) -> list:
    queries = generate_queries(question)

    all_docs = []
    seen = set()

    for query in queries:
        if hasattr(retriever, "get_candidates"):
            docs = retriever.get_candidates(query)
        else:
            docs = retriever.invoke(query)

        for doc in docs:
            key = (
                doc.metadata.get("source", ""),
                doc.page_content[:100],
            )

            if key not in seen:
                seen.add(key)
                all_docs.append(doc)

    top_k = final_top_k or settings.retrieval_k

    # Reuse the reranker the retriever loaded once at startup (loading the model
    # per question costs seconds). It is None when ENABLE_RERANKING=false, or when
    # the retriever is not a HybridRetriever; in both cases keep the pooled order.
    reranker = getattr(retriever, "reranker", None)

    if reranker is None:
        return all_docs[:top_k]

    return reranker.rerank(
        query=question,
        documents=all_docs,
        top_k=top_k,
    )