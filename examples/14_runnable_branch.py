from langchain_core.runnables import RunnableBranch, RunnableLambda


def answer_inventory(question: str) -> str:
    return "This should go to the inventory/tool workflow."


def answer_policy(question: str) -> str:
    return "This should go to the RAG policy workflow."


branch = RunnableBranch(
    (
        lambda question: "sku" in question.lower()
        or "stock" in question.lower()
        or "inventory" in question.lower(),
        RunnableLambda(answer_inventory),
    ),
    RunnableLambda(answer_policy),
)

questions = [
    "Which items are low stock in store 102?",
    "What is the return policy?",
]

for question in questions:
    print("\nQuestion:", question)
    print("Answer:", branch.invoke(question))