from app.rag import load_documents, split_documents
from app.vectorstore import build_vectorstore, get_hybrid_retriever


docs = load_documents()
chunks = split_documents(docs)
db = build_vectorstore(chunks)
retriever = get_hybrid_retriever(db, chunks)

queries = [
    "What does P1 mean?",
    "What happens by October 31?",
    "What should happen during POS outage?",
]

for query in queries:
    print("\nQuery:", query)

    results = retriever.invoke(query)

    for i, doc in enumerate(results, start=1):
        print("\n--- Result", i, "---")
        print("Source:", doc.metadata.get("source"))
        print(doc.page_content[:300])