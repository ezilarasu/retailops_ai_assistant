from app.rag import load_documents

docs = load_documents()

print("Documents loaded:", len(docs))

for doc in docs:
    print("\nSource:", doc.metadata.get("source"))
    print(doc.page_content[:300])