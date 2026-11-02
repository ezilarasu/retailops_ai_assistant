from app.rag import load_documents, split_documents
from app.vectorstore import build_vectorstore, get_retriever

docs = load_documents()
chunks = split_documents(docs)

db = build_vectorstore(chunks)
retriever = get_retriever(db)

query = "How many vacation days do full-time store employees receive?"

results = retriever.invoke(query)

print("Query:", query)
print("Results:", len(results))

for i, doc in enumerate(results, start=1):
    print("\n--- Result", i, "---")
    print("Source:", doc.metadata.get("source"))
    print(doc.page_content[:500])