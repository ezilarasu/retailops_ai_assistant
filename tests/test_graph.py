from app.graph import nodes
from app.graph.graph import build_retailops_graph
from app.graph.nodes import route_node


def thread(name):
    return {"configurable": {"thread_id": name}}


def test_graph_builds_without_building_the_app():
    # Importing and building the graph must not need an API key or load any model.
    assert build_retailops_graph() is not None


def test_empty_question_is_rejected_by_validation_without_any_llm_call():
    graph = build_retailops_graph()

    result = graph.invoke({"question": "   "}, config=thread("validation-test"))

    assert result["route"] == "error"
    assert result["error"] == "Question is empty."
    assert "ran into an issue" in result["answer"]


class _Decision:
    route = "general"
    reason = "greeting"


def test_each_turn_starts_with_fresh_timings_and_debug(monkeypatch):
    monkeypatch.setattr(nodes, "route_question", lambda question, messages: _Decision())

    previous_turn = {
        "question": "second question",
        "messages": [],
        "timings": {"router_ms": 1.0, "rag_ms": 999.0},
        "debug": {"rag": {"old": True}},
    }

    update = route_node(previous_turn)

    assert list(update["timings"]) == ["router_ms"]
    assert update["debug"] == {"router": {"route": "general", "reason": "greeting"}}
