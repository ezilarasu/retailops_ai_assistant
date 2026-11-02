import re
from rank_bm25 import BM25Okapi


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9\-]+", text.lower())


class BM25Retriever:
    def __init__(self, documents):
        self.documents = documents
        self.corpus = [
            tokenize(doc.page_content)
            for doc in documents
        ]
        self.bm25 = BM25Okapi(self.corpus)

    def invoke(self, query: str, top_k: int = 10):
        tokenized_query = tokenize(query)

        scores = self.bm25.get_scores(tokenized_query)

        ranked = sorted(
            zip(scores, self.documents),
            key=lambda item: item[0],
            reverse=True,
        )

        results = []

        for score, doc in ranked[:top_k]:
            if score > 0:
                doc.metadata["bm25_score"] = float(score)
                results.append(doc)

        return results