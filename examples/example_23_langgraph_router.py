from app.graph.graph import build_retailops_graph


graph = build_retailops_graph()

config = {
    "configurable": {
        "thread_id": "demo-user-1"
    }
}

# One question per route: general chat, RAG, and tools
questions = [
    "Hello, who are you?",
    "What does P1 mean?",
    "Which items are low stock in store 102?",
]

for question in questions:
    print("\nQuestion:", question)

    result = graph.invoke({
        "question": question
    },
          config=config,
    )

    print("Route:", result.get("route"))
    print("Reason:", result.get("route_reason"))
    print("Answer:", result.get("answer"))
    print("Sources:", result.get("sources"))
    print("Timings:", result.get("timings"))
    print("Last Message:", result["messages"][-1].content)
