from app.rag import load_documents, split_documents, semantic_split_documents


docs = load_documents()

recursive_chunks = split_documents(docs)
semantic_chunks = semantic_split_documents(docs)

print("Documents:", len(docs))
print("Recursive chunks:", len(recursive_chunks))
print("Semantic chunks:", len(semantic_chunks))

print("\n--- Recursive chunks preview ---")
for index, chunk in enumerate(recursive_chunks[:5], start=1):
    print("\nChunk:", index)
    print("Source:", chunk.metadata.get("source"))
    print(chunk.page_content[:500])

print("\n--- Semantic chunks preview ---")
for index, chunk in enumerate(semantic_chunks[:5], start=1):
    print("\nChunk:", index)
    print("Source:", chunk.metadata.get("source"))
    print(chunk.page_content[:500])