import functools
import time

from langchain_core.messages import AIMessage
from langgraph.graph import END, StateGraph

from app.chains import format_docs, format_history, retrieve_documents, rewrite_question
from app.container import get_container
from app.graph.state import RetailOpsState
from app.graph.utils import add_total_timing, history_before_question, record_timing
from app.llm import invoke_with_retry

# A subgraph is a small graph used as one node of a bigger graph. This one has the three
# steps of the RAG pipeline: rewrite the question, retrieve documents, generate the answer.
# Each step uses the same helper functions (app/chains.py) and the same shared pieces
# (get_container()) as the non-graph RAG chain in app/router.py.


def step(node):
    """Skip a step once an earlier one failed; turn an exception into an error entry
    (the parent graph then routes to its error node) instead of crashing the run."""

    @functools.wraps(node)
    def wrapper(state: RetailOpsState):
        if state.get("route") == "error":
            return {}

        try:
            return node(state)
        except Exception as exc:
            return {
                "route": "error",
                "error": getattr(exc, "user_message", str(exc)),
            }

    return wrapper


@step
def rewrite_node(state: RetailOpsState):
    start = time.perf_counter()

    rewritten_question = invoke_with_retry(lambda: rewrite_question(
        state["question"],
        format_history(history_before_question(state)),
        get_container().rewriter_chain,
    ))

    return {
        "rewritten_question": rewritten_question,
        "timings": record_timing(state, "rewrite_ms", start),
    }


@step
def retrieve_node(state: RetailOpsState):
    start = time.perf_counter()

    docs = invoke_with_retry(lambda: retrieve_documents(
        state["rewritten_question"],
        get_container().retriever,
    ))

    return {
        "context": format_docs(docs),
        "timings": record_timing(state, "retrieve_ms", start),
    }


@step
def generate_node(state: RetailOpsState):
    start = time.perf_counter()

    result = invoke_with_retry(lambda: get_container().rag_generator.invoke({
        "context": state["context"],
        "rewritten_question": state["rewritten_question"],
    }))

    timings = record_timing(state, "generate_ms", start)
    timings = add_total_timing(state, timings)

    return {
        "answer": result.answer,
        "sources": result.sources,
        "confidence": result.confidence,
        "debug": {
            **state.get("debug", {}),
            "rag": {
                "rewritten_question": state["rewritten_question"],
                "sources": result.sources,
                "confidence": result.confidence,
            },
        },
        "messages": [AIMessage(content=result.answer)],
        "timings": timings,
    }


def build_rag_subgraph():
    graph = StateGraph(RetailOpsState)

    graph.add_node("rewrite", rewrite_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)

    graph.set_entry_point("rewrite")

    graph.add_edge("rewrite", "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)

    return graph.compile()
