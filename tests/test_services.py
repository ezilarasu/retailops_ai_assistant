import pytest

from app import services
from app.cache import response_cache
from app.memory import add_user_message, clear_memory, get_messages
from app.services import RetailOpsAssistantService


@pytest.fixture(autouse=True)
def clean_state():
    response_cache.clear()
    clear_memory()
    clear_memory("a")
    clear_memory("b")
    yield
    response_cache.clear()
    clear_memory()
    clear_memory("a")
    clear_memory("b")


class FakeRouter:
    """Stands in for run_router(): counts calls and replies with a route chosen per question."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = 0

    def __call__(self, question, session_id="default"):
        self.calls += 1
        route = self.routes.get(question, "rag")
        answer = f"answer to {question} #{self.calls}"
        add_user_message(question, session_id)
        services.add_ai_message(answer, session_id)

        return {
            "request_id": f"id-{self.calls}",
            "route": route,
            "reason": "test",
            "answer": answer,
            "latency_ms": 5000.0,
        }


def test_first_question_of_a_conversation_is_cached_for_other_conversations(monkeypatch):
    fake = FakeRouter({})
    service = RetailOpsAssistantService()
    monkeypatch.setattr(services, "run_router", fake)

    first = service.ask("What is the return policy?", "a")
    second = service.ask("What is the return policy?", "b")  # another user's first question

    assert fake.calls == 1
    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert second["answer"] == first["answer"]


def test_follow_up_questions_are_never_cached_or_served_from_cache(monkeypatch):
    fake = FakeRouter({})
    service = RetailOpsAssistantService()
    monkeypatch.setattr(services, "run_router", fake)

    service.ask("How many vacation days do full-time employees get?", "a")
    follow_up = service.ask("What about part-time employees?", "a")  # has history
    other = service.ask("What about part-time employees?", "b")  # same words, no history

    assert follow_up["cache_hit"] is False
    assert other["cache_hit"] is False  # the follow-up answer was not stored for others
    assert fake.calls == 3


def test_tools_answers_are_never_cached(monkeypatch):
    fake = FakeRouter({"Which items are low stock in store 102?": "tools"})
    service = RetailOpsAssistantService()
    monkeypatch.setattr(services, "run_router", fake)

    service.ask("Which items are low stock in store 102?", "a")
    again = service.ask("Which items are low stock in store 102?", "b")

    assert fake.calls == 2
    assert again["cache_hit"] is False


def test_cache_hit_gets_its_own_latency_and_request_id(monkeypatch):
    fake = FakeRouter({})
    service = RetailOpsAssistantService()
    monkeypatch.setattr(services, "run_router", fake)

    first = service.ask("What does P1 mean?", "a")
    hit = service.ask("What does P1 mean?", "b")

    assert hit["latency_ms"] < first["latency_ms"]
    assert hit["request_id"] != first["request_id"]


def test_cache_hit_still_records_the_turn_in_memory(monkeypatch):
    fake = FakeRouter({})
    service = RetailOpsAssistantService()
    monkeypatch.setattr(services, "run_router", fake)

    service.ask("What does P1 mean?", "a")
    service.ask("What does P1 mean?", "b")

    assert fake.calls == 1  # b's answer came from the cache
    assert [m.content for m in get_messages("b")][0] == "What does P1 mean?"
    assert len(get_messages("b")) == 2


def test_sessions_have_separate_history():
    add_user_message("hello from a", "a")

    assert [m.content for m in get_messages("a")] == ["hello from a"]
    assert get_messages("b") == []

    clear_memory("a")

    assert get_messages("a") == []
