import logging
import time
import uuid

from app.container import get_container
from app.exceptions import RetailOpsError
from app.llm import invoke_with_retry
from app.memory import DEFAULT_SESSION, add_user_message, add_ai_message, get_messages
from app.tracing import trace_config

logger = logging.getLogger(__name__)

HISTORY_WINDOW = 6  # how many recent messages the router, the tools agent and the general chat see


def format_history_text(messages: list) -> str:
    return "\n".join(
        f"{message.type}: {message.content}"
        for message in messages[-HISTORY_WINDOW:]
        if hasattr(message, "content")
    )


def route_question(question: str, messages: list | None = None, config: dict | None = None):
    container = get_container()

    return invoke_with_retry(lambda: container.router_chain.invoke(
        {
            "question": question,
            "chat_history": format_history_text(messages or []),
        },
        config=config,
    ))


def _finish(request_id: str, route: str, start_time: float, **fields) -> dict:
    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

    logger.info(
        "request_completed request_id=%s route=%s%s latency_ms=%s",
        request_id,
        route,
        f" confidence={fields['confidence']}" if "confidence" in fields else "",
        latency_ms,
    )

    return {"request_id": request_id, "route": route, "latency_ms": latency_ms, **fields}


def run_router(question: str, session_id: str = DEFAULT_SESSION) -> dict:
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    logger.info(
        "request_started request_id=%s question=%s",
        request_id,
        question,
    )

    try:
        container = get_container()
        history = get_messages(session_id)

        decision = route_question(
            question,
            history,
            config=trace_config("router", request_id),
        )

        logger.info(
            "route_selected request_id=%s route=%s reason=%s",
            request_id,
            decision.route,
            decision.reason,
        )

        if decision.route == "general":
            answer = invoke_with_retry(lambda: container.general_chat_chain.invoke(
                {"question": question, "history": history[-HISTORY_WINDOW:]},
                config=trace_config("general", request_id),
            ))

            add_user_message(question, session_id)
            add_ai_message(answer, session_id)

            return _finish(
                request_id, decision.route, start_time,
                reason=decision.reason,
                answer=answer,
            )

        if decision.route == "rag":
            result = invoke_with_retry(lambda: container.rag_chain.invoke(
                {"question": question, "messages": history},
                config=trace_config("rag", request_id),
            ))

            add_user_message(question, session_id)
            add_ai_message(result.answer, session_id)

            return _finish(
                request_id, decision.route, start_time,
                reason=decision.reason,
                answer=result.answer,
                sources=result.sources,
                confidence=result.confidence,
            )

        if decision.route == "tools":
            result = invoke_with_retry(lambda: container.tool_agent.invoke(
                {
                    "messages": [
                        # Recent history first, so follow-ups like "What about store 310?" work.
                        *history[-HISTORY_WINDOW:],
                        {
                            "role": "user",
                            "content": question,
                        },
                    ]
                },
                config=trace_config("tools", request_id),
            ))

            answer = result["messages"][-1].content

            add_user_message(question, session_id)
            add_ai_message(answer, session_id)

            return _finish(
                request_id, decision.route, start_time,
                reason=decision.reason,
                answer=answer,
            )

        answer = "I could not route this question."

        add_user_message(question, session_id)
        add_ai_message(answer, session_id)

        logger.warning(
            "unknown_route request_id=%s route=%s",
            request_id,
            decision.route,
        )

        return _finish(
            request_id, "unknown", start_time,
            reason="No valid route selected.",
            answer=answer,
        )

    except RetailOpsError as error:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        logger.warning(
            "request_failed request_id=%s code=%s latency_ms=%s detail=%s",
            request_id,
            error.code,
            latency_ms,
            str(error)[:300],
        )

        return {
            "request_id": request_id,
            "route": "error",
            "reason": f"The request could not be completed ({error.code}).",
            "answer": error.user_message,
            "latency_ms": latency_ms,
            "error": error.code,
        }

    except Exception as error:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        logger.exception(
            "request_failed request_id=%s latency_ms=%s error=%s",
            request_id,
            latency_ms,
            str(error),
        )

        return {
            "request_id": request_id,
            "route": "error",
            "reason": "An internal error occurred.",
            "answer": RetailOpsError.user_message,
            "latency_ms": latency_ms,
            "error": RetailOpsError.code,
        }
