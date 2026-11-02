from typing import Annotated, Literal, TypedDict

from langgraph.graph.message import add_messages


RouteName = Literal["general", "rag", "tools", "error"]

class RetailOpsState(TypedDict, total=False):
    question: str
    messages: Annotated[list, add_messages]

    route: RouteName
    route_reason: str
    debug: dict
    answer: str
    sources: list[str]
    confidence: str
    error: str
    timings: dict
    approval_required: bool
    approved: bool
    approval_reason: str

    # Filled in by the RAG subgraph steps (rewrite -> retrieve -> generate)
    rewritten_question: str
    context: str
