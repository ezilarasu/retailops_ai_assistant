import logging
import time

from langchain_core.documents import Document

from app.bm25_retriever import BM25Retriever
from app.reranker import CrossEncoderReranker

from app.config import settings
logger = logging.getLogger(__name__)


class HybridRetriever:
    def __init__(
        self,
        vector_retriever,
        documents: list[Document],
        top_k: int = 4,
    ):
        self.vector_retriever = vector_retriever
        self.documents = documents
        self.top_k = top_k
        self.bm25_retriever = BM25Retriever(documents)
        self.reranker = (
            CrossEncoderReranker(min_score=settings.rerank_min_score)
            if settings.enable_reranking
            else None
        )

    def get_candidates(self, query: str) -> list[Document]:
        vector_docs = self.vector_retriever.invoke(query)
        bm25_docs = self.bm25_retriever.invoke(query, top_k=10)

        seen = set()
        merged = []

        for doc in vector_docs + bm25_docs:
            key = (
                doc.metadata.get("source", ""),
                doc.page_content[:100],
            )

            if key not in seen:
                seen.add(key)
                merged.append(doc)

        return merged

    def invoke(self, query: str) -> list[Document]:
        
        start_total = time.perf_counter()

        start_candidates = time.perf_counter()
        candidates = self.get_candidates(query)
        candidates_ms = round(
            (time.perf_counter() - start_candidates) * 1000,
            2,
        )

        start_rerank = time.perf_counter()
        if self.reranker is None:
            return candidates[:self.top_k]
        reranked_docs = self.reranker.rerank(
            query=query,
            documents=candidates,
            top_k=self.top_k,
        )
        rerank_ms = round(
            (time.perf_counter() - start_rerank) * 1000,
            2,
        )

        total_ms = round(
            (time.perf_counter() - start_total) * 1000,
            2,
        )

        logger.info(
            "hybrid_retrieval_timing candidates_ms=%s rerank_ms=%s total_ms=%s candidate_count=%s final_count=%s",
            candidates_ms,
            rerank_ms,
            total_ms,
            len(candidates),
            len(reranked_docs),
        )

        return reranked_docs