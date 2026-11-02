from langchain_core.runnables import RunnableParallel, RunnableLambda


def extract_question_length(question: str) -> int:
    return len(question)


def detect_store_question(question: str) -> bool:
    return "store" in question.lower()


parallel_chain = RunnableParallel({
    "original_question": RunnableLambda(lambda x: x),
    "question_length": RunnableLambda(extract_question_length),
    "is_store_question": RunnableLambda(detect_store_question),
})

result = parallel_chain.invoke(
    "Which items are low stock in store 102?"
)

print(result)