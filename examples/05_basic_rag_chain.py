from app.container import get_container

chain = get_container().rag_chain

result = chain.invoke({
    "question": "Can store associates work remotely?"
})

print(result)