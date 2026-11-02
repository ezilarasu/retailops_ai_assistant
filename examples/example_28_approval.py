from langchain_core.messages import HumanMessage
from app.graph.graph import build_retailops_graph
from langgraph.types import Command

graph = build_retailops_graph()


result = graph.invoke(
    {"question": "Show low stock items for store 102."},
    config={
        "configurable": {
            "thread_id": "approval-demo-1"
        }
    },
)

print(result.get("__interrupt__"))

result = graph.invoke(
    Command(
        resume={
            "approved": True,
            "reason": "Approved for store manager review.",
        }
    ),
    config={
        "configurable": {
            "thread_id": "approval-demo-1"
        }
    },
)

print(result.get("answer"))