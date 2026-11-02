import time

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import interrupt

from app.container import get_container
from app.exceptions import RetailOpsError
from app.graph.state import RetailOpsState
from app.graph.utils import add_total_timing, history_before_question, record_timing
from app.llm import invoke_with_retry
from app.router import HISTORY_WINDOW, route_question

# Chains are fetched with get_container() when a node runs, not when this module is
# imported, so importing app.graph does not build the app (or need an API key).


def route_node(state: RetailOpsState) -> RetailOpsState:
    start = time.perf_counter()

    try:
        decision = route_question(
            question=state["question"],
            messages=state.get("messages", []),
        )
    except RetailOpsError as error:
        return {**state, "route": "error", "error": error.user_message}

    # debug and timings start empty each turn; the saved state would otherwise carry
    # the previous turn's values forward when a thread_id is reused.
    debug = {
        "router": {
            "route": decision.route,
            "reason": decision.reason,
        }
    }
    timings = record_timing({}, "router_ms", start)

    return {
        **state,
        "debug": debug,
        "route": decision.route,
        "route_reason": decision.reason,
        "messages": [
            HumanMessage(content=state["question"])
        ],
        "timings": timings,
    }


def general_node(state: RetailOpsState) -> RetailOpsState:
    try:
        start = time.perf_counter()

        answer = invoke_with_retry(lambda: get_container().general_chat_chain.invoke({
            "question": state["question"],
            "history": history_before_question(state)[-HISTORY_WINDOW:],
        }))

        timings = record_timing(
            state,
            "general_ms",
            start,
        )
        timings = add_total_timing(state, timings)

        return {
            **state,
            "answer": answer,
            "sources": [],
            "confidence": "medium",
            "debug": {
                **state.get("debug", {}),
                "general": {},
            },
            "messages": [
                AIMessage(content=answer)
            ],
            "timings": timings,
        }
    except Exception as exc:
        return {
            **state,
            "error": getattr(exc, "user_message", str(exc)),
            "route": "error",
        }


def tools_node(state: RetailOpsState) -> RetailOpsState:
    try:
        start = time.perf_counter()

        result = invoke_with_retry(lambda: get_container().tool_agent.invoke({
            "messages": [
                *history_before_question(state)[-HISTORY_WINDOW:],
                {
                    "role": "user",
                    "content": state["question"],
                },
            ]
        }))

        # create_agent returns {"messages": [...]}; the answer is the last message.
        messages = result.get("messages") if isinstance(result, dict) else None
        answer = messages[-1].content if messages else str(result)

        debug = state.get("debug", {})
        debug["tools"] = {
            "raw_result_type": type(result).__name__,
        }
        timings = record_timing(
            state,
            "tools_ms",
            start,
        )
        timings = add_total_timing(state, timings)
        return {
            **state,
            "answer": answer,
            "sources": [],
            "confidence": "medium",
            "debug": debug,
            "messages": [
                AIMessage(content=answer)
            ],
            "timings": timings,
        }
    except Exception as exc:
        return {
            **state,
            "error": getattr(exc, "user_message", str(exc)),
            "route": "error",
        }


def error_node(state: RetailOpsState) -> RetailOpsState:
    error = state.get("error", "Unknown error")

    answer = (
        "I ran into an issue while processing your request. "
        "Please try again or rephrase your question."
    )

    return {
        **state,
        "answer": answer,
        "sources": [],
        "confidence": "low",
        "debug": {
            **state.get("debug", {}),
            "error": error,
        },
        "messages": [
            AIMessage(content=answer)
        ],
    }


def validation_node(state: RetailOpsState) -> RetailOpsState:
    question = state.get("question", "").strip()

    if not question:
        return {
            **state,
            "route": "error",
            "error": "Question is empty.",
        }

    if len(question) < 2:
        return {
            **state,
            "route": "error",
            "error": "Question is too short.",
        }

    return {
        **state,
        "question": question,
        "route": "router",
        "_workflow_start": time.perf_counter(),
    }


def approval_node(state: RetailOpsState) -> RetailOpsState:
    decision = interrupt({
        "question": state["question"],
        "proposed_answer": state.get("answer"),
        "reason": "Human approval required before continuing.",
    })

    return {
        **state,
        "approved": decision.get("approved", False),
        "approval_reason": decision.get("reason", ""),
    }
