import time
import uuid

from app.cache import response_cache
from app.memory import DEFAULT_SESSION, add_ai_message, add_user_message, get_messages
from app.router import run_router

# Tool answers come from live operational data, so they are never cached.
CACHEABLE_ROUTES = {"general", "rag"}


class RetailOpsAssistantService:
    def ask(self, question: str, session_id: str = DEFAULT_SESSION) -> dict:
        start_time = time.perf_counter()

        # Only the first question of a conversation is cached or served from the cache.
        # With earlier turns the same words can mean something else ("What about
        # part-time employees?"), so a follow-up must always be answered in context.
        first_turn = not get_messages(session_id)

        cached = response_cache.get(question) if first_turn else None

        if cached:
            result = dict(cached)
            result["cache_hit"] = True
            result["request_id"] = str(uuid.uuid4())
            result["latency_ms"] = round((time.perf_counter() - start_time) * 1000, 2)

            # A hit skips run_router(), so record the turn here to keep the conversation whole.
            add_user_message(question, session_id)
            add_ai_message(result["answer"], session_id)

            return result

        result = run_router(question, session_id)
        result["cache_hit"] = False

        if first_turn and result["route"] in CACHEABLE_ROUTES:
            response_cache.set(question, result)

        return result


assistant_service = RetailOpsAssistantService()
