from langchain_core.messages import HumanMessage

from app.graph.prebuilt_tools_graph import build_prebuilt_tools_graph


graph = build_prebuilt_tools_graph()

result = graph.invoke({
    "messages": [
        HumanMessage(
            content="Show low stock items for store 102."
        )
    ]
})

print("\nMessages:")
for message in result["messages"]:
    print(message.type, ":", message.content)