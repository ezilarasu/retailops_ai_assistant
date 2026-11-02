from app.multi_query import generate_queries


questions = [
    "How much PTO do employees get?",
    "What does P1 mean?",
    "What is the return window for online orders?",
]

for question in questions:
    print("\nOriginal question:")
    print(question)

    queries = generate_queries(question)

    print("\nGenerated retrieval queries:")
    for query in queries:
        print("-", query)