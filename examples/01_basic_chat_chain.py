from app.chains import build_general_chat_chain

chain = build_general_chat_chain()

response = chain.invoke({
    "question": "Who are you?"
})

print(response)