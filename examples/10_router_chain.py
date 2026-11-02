from app.router import run_router


questions = [
    "Hello, who are you?",
    "How many vacation days do full-time store employees receive?",
    "Which items are low stock in store 102?",
    "Who is the vendor for SKU DENIM-4421?",
]

for question in questions:
    print("\nQuestion:")
    print(question)

    result = run_router(question)

    print("Route:", result["route"])
    print("Reason:", result["reason"])
    print("Answer:", result["answer"])
    