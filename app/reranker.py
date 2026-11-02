from sentence_transformers import CrossEncoder


class CrossEncoderReranker:
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        min_score: float | None = None,
    ):
        self.model = CrossEncoder(model_name)
        self.min_score = min_score

    def rerank(
        self,
        query: str,
        documents: list,
        top_k: int = 4,
    ):
        if not documents:
            return []

        pairs = [
            (query, doc.page_content)
            for doc in documents
        ]

        scores = self.model.predict(pairs)

        scored_docs = list(zip(scores, documents))

        scored_docs.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        reranked_docs = []

        for score, doc in scored_docs[:top_k]:
            # Drop clearly irrelevant chunks, but always keep the best one.
            if reranked_docs and self.min_score is not None and score < self.min_score:
                break

            doc.metadata["rerank_score"] = float(score)
            reranked_docs.append(doc)

        return reranked_docs