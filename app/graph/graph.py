"""LangGraph version of the RetailOps workflow (a parallel demo).

The CLI (app/main.py) and the API (app/api.py) use run_router() in app/router.py, not
this graph. The graph shows the same flow as explicit state, nodes and edges, and adds
two things run_router() does not have: checkpointed memory per thread_id and a
human-approval pause (interrupt) after the tools route. Run it with examples/example_23
to example_28 (docs/33_langchain_limitations_and_langgraph).
"""

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, StateGraph

from app.graph.nodes import (
    approval_node,
    error_node,
    general_node,
    route_node,
    tools_node,
    validation_node,
)
from app.graph.rag_subgraph import build_rag_subgraph
from app.graph.state import RetailOpsState


def choose_route(state: RetailOpsState) -> str:
    return state["route"]


def choose_after_validation(state: RetailOpsState) -> str:
    return state["route"]


def error_or(next_step):
    """Edge function: go to the error node if the previous node failed, else to `next_step`."""

    def choose(state: RetailOpsState) -> str:
        return "error" if state.get("route") == "error" else next_step

    return choose


def build_retailops_graph():
    graph = StateGraph(RetailOpsState)

    graph.add_node("router", route_node)
    graph.add_node("general", general_node)
    graph.add_node("rag", build_rag_subgraph())
    graph.add_node("tools", tools_node)
    graph.add_node("error", error_node)
    graph.add_node("validation", validation_node)
    graph.add_node("approval", approval_node)
    graph.set_entry_point("validation")

    graph.add_conditional_edges(
        "validation",
        choose_after_validation,
        {
            "router": "router",
            "error": "error",
        },
    )
    graph.add_conditional_edges(
        "router",
        choose_route,
        {
            "general": "general",
            "rag": "rag",
            "tools": "tools",
            "error": "error",
        },
    )

    graph.add_conditional_edges("general", error_or("done"), {"done": END, "error": "error"})
    graph.add_conditional_edges("rag", error_or("done"), {"done": END, "error": "error"})
    graph.add_conditional_edges("tools", error_or("approval"), {"approval": "approval", "error": "error"})
    graph.add_edge("approval", END)
    graph.add_edge("error", END)

    checkpointer = InMemorySaver()

    return graph.compile(
        checkpointer=checkpointer
    )
