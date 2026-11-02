import logging
import time

from langchain.agents import create_agent
from langchain_core.output_parsers import StrOutputParser

from app.config import settings
from app.llm import get_llm
from app.multi_query import retrieve_with_multi_query
from app.prompts import (
    general_chat_prompt,
    history_aware_router_prompt,
    question_rewrite_prompt,
    rag_prompt,
)
from app.rag import chunk_documents, load_documents
from app.schemas import RAGResponse, RouteDecision
from app.tools import get_low_stock_items, get_open_incidents, get_vendor_for_sku
from app.memory import get_messages
from app.vectorstore import build_vectorstore, get_hybrid_retriever

logger = logging.getLogger(__name__)


def build_general_chat_chain():
    llm = get_llm()
    parser = StrOutputParser()

    return general_chat_prompt | llm | parser


def format_history(messages):
    return "\n".join(
        f"{message.type}: {message.content}"
        for message in messages[-6:]
        if hasattr(message, "content")
    )


def format_docs(docs):
    formatted = []

    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        score = doc.metadata.get("rerank_score", "not_available")

        formatted.append(
            f"Source: {source}\n"
            f"Rerank Score: {score}\n"
            f"Content:\n{doc.page_content}"
        )

    return "\n\n".join(formatted)


def build_retriever():
    """Load, chunk, index and wrap the documents in the hybrid (vector + BM25 + rerank) retriever."""
    chunks = chunk_documents(load_documents())
    db = build_vectorstore(chunks)

    return get_hybrid_retriever(db, chunks)


def build_question_rewriter_chain():
    llm = get_llm()
    parser = StrOutputParser()

    return question_rewrite_prompt | llm | parser


def rewrite_question(question: str, chat_history: str, rewriter_chain) -> str:
    """Turn a follow-up into a standalone question using the chat history.

    The first question of a conversation has no history, so there is nothing to
    resolve and the extra LLM call is skipped.
    """
    if not chat_history.strip():
        return question

    return rewriter_chain.invoke({
        "question": question,
        "chat_history": chat_history,
    })


def retrieve_documents(rewritten_question: str, retriever) -> list:
    if settings.enable_multi_query:
        return retrieve_with_multi_query(
            question=rewritten_question,
            retriever=retriever,
            final_top_k=settings.retrieval_k,
        )

    return retriever.invoke(rewritten_question)


def build_rag_generator():
    """The answer step: prompt + model that returns a RAGResponse (answer, sources, confidence)."""
    structured_llm = get_llm().with_structured_output(RAGResponse)

    return rag_prompt | structured_llm


def build_rag_chain(retriever=None, rewriter_chain=None, generator=None):
    retriever = retriever or build_retriever()
    rewriter_chain = rewriter_chain or build_question_rewriter_chain()
    generator = generator or build_rag_generator()

    def retrieve_context(inputs):
        question = inputs["question"]

        start_rewrite = time.perf_counter()
        chat_history = format_history(
            inputs.get("messages", get_messages())
        )
        rewritten_question = rewrite_question(question, chat_history, rewriter_chain)
        rewrite_ms = round((time.perf_counter() - start_rewrite) * 1000, 2)

        start_retrieval = time.perf_counter()
        retrieved_docs = retrieve_documents(rewritten_question, retriever)
        retrieval_ms = round((time.perf_counter() - start_retrieval) * 1000, 2)

        logger.info(
            "rag_stage_timing rewrite_ms=%s retrieval_ms=%s multi_query=%s original_question=%s rewritten_question=%s",
            rewrite_ms,
            retrieval_ms,
            settings.enable_multi_query,
            question,
            rewritten_question,
        )

        for index, doc in enumerate(retrieved_docs, start=1):
            logger.info(
                "retrieved_doc rank=%s source=%s rerank_score=%s",
                index,
                doc.metadata.get("source"),
                doc.metadata.get("rerank_score"),
            )

        return {
            "question": question,
            "rewritten_question": rewritten_question,
            "context": format_docs(retrieved_docs),
        }

    return retrieve_context | generator


def build_tool_agent():
    llm = get_llm(settings.tools_llm_model)

    tools = [
        get_low_stock_items,
        get_vendor_for_sku,
        get_open_incidents,
    ]

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt="""
        You are RetailOps AI Assistant.

        You help retail operations teams answer questions using available tools.

        Tool rules:
        - Use inventory tools for stock and SKU questions.
        - Use vendor tools for vendor contact questions.
        - Use incident tools for store incident questions.
        - Do not invent data.
        - If a tool returns no results, clearly say no matching data was found.
        """
    )

    return agent


def build_router_chain():
    llm = get_llm()
    structured_llm = llm.with_structured_output(RouteDecision)

    return history_aware_router_prompt | structured_llm
