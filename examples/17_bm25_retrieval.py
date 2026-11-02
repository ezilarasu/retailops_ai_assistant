from app.rag import load_documents, split_documents
from app.bm25_retriever import BM25Retriever


docs = load_documents()
chunks = split_documents(docs)

retriever = BM25Retriever(chunks)

queries = [
    "What does P1 mean?",
    "What happens by October 31?",
    "What is HR Connect?",
]

for query in queries:
    print("\nQuery:", query)

    results = retriever.invoke(query, top_k=3)

    for index, doc in enumerate(results, start=1):
        print("\nResult:", index)
        print("Source:", doc.metadata.get("source"))
        print("BM25 Score:", doc.metadata.get("bm25_score"))
        print(doc.page_content[:300])