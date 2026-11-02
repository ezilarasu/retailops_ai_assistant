from typing import Annotated, TypedDict

from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.config import settings
from app.llm import get_llm
from app.tools import tools


class ToolGraphState(TypedDict):
    messages: Annotated[list, add_messages]


def should_continue(state: ToolGraphState) -> str:
    last_message = state["messages"][-1]

    if getattr(last_message, "tool_calls", None):
        return "tools"

    return "end"


def build_prebuilt_tools_graph():
    # Built here, not at import time, so importing this module needs no API key.
    llm_with_tools = get_llm(settings.tools_llm_model).bind_tools(tools)

    def call_model(state: ToolGraphState) -> ToolGraphState:
        response = llm_with_tools.invoke(state["messages"])

        return {
            "messages": [response]
        }

    graph = StateGraph(ToolGraphState)

    graph.add_node("model", call_model)
    graph.add_node("tools", ToolNode(tools))

    graph.set_entry_point("model")

    graph.add_conditional_edges(
        "model",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        },
    )

    graph.add_edge("tools", "model")

    return graph.compile()
