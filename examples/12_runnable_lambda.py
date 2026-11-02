from langchain_core.runnables import RunnableLambda


def clean_question(question: str) -> str:
    return question.strip().lower()


cleaner = RunnableLambda(clean_question)

result = cleaner.invoke("   HOW MANY VACATION DAYS?   ")

print(result)