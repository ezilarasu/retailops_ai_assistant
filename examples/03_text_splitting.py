from app.rag import load_documents, split_documents

docs = load_documents()
chunks = split_documents(docs)

print("Documents:", len(docs))
print("Chunks:", len(chunks))

for i, chunk in enumerate(chunks, start=1):
    print("\n--- Chunk", i, "---")
    print("Source:", chunk.metadata.get("source"))
    print(chunk.page_content[:300])