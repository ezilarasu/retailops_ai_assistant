from app.chains import build_tool_agent


agent = build_tool_agent()

questions = [
    "Which items are low stock in store 102?",
    "Who is the vendor for SKU DENIM-4421?",
    "Are there any open incidents for store 102?",
]

for question in questions:
    print("\nQuestion:")
    print(question)

    result = agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": question
            }
        ]
    })

    print("\nAnswer:")
    print(result["messages"][-1].content)