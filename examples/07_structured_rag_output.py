from app.chains import build_rag_chain


chain = build_rag_chain()

result = chain.invoke({
    "question": "How many vacation days do full-time store employees receive?"
})

print("Answer:")
print(result.answer)

print("\nSources:")
for source in result.sources:
    print("-", source)

print("\nConfidence:")
print(result.confidence)