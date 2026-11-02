from langchain_core.prompts import ChatPromptTemplate

from app.llm import get_llm
from app.schemas import JudgeResult


judge_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        You are an evaluator for a RAG assistant.

        Judge the assistant answer against the expected answer.

        Criteria:
        - correct: answer matches the expected answer
        - grounded: answer does not invent unsupported information
        - complete: answer contains the key expected information

        Return structured output only.
        """
    ),
    (
        "human",
        """
        Question:
        {question}

        Expected answer:
        {expected_answer}

        Actual answer:
        {actual_answer}

        Sources returned:
        {sources}
        """
    )
])


def judge_answer(
    question: str,
    expected_answer: str,
    actual_answer: str,
    sources: list[str],
) -> JudgeResult:
    llm = get_llm()
    judge_llm = llm.with_structured_output(JudgeResult)

    chain = judge_prompt | judge_llm

    return chain.invoke({
        "question": question,
        "expected_answer": expected_answer,
        "actual_answer": actual_answer,
        "sources": sources,
    })