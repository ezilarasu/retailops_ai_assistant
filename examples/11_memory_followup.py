from app.memory import clear_memory
from app.router import run_router


clear_memory()

questions = [
    "How many vacation days do full-time store employees receive?",
    "What about part-time employees?",
    "Which items are low stock in store 102?",
    "What about store 310?",
]

for question in questions:
    print("\nQuestion:")
    print(question)

    result = run_router(question)

    print("Route:", result["route"])
    print("Reason:", result["reason"])
    print("Answer:", result["answer"])

    if "sources" in result:
        print("Sources:", result["sources"])

    if "confidence" in result:
        print("Confidence:", result["confidence"])