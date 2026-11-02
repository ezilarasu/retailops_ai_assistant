from langchain_core.messages import HumanMessage

from app.graph.react_agent_graph import build_react_agent_graph


agent = build_react_agent_graph()

result = agent.invoke({
    "messages": [
        HumanMessage(
            content="Show low stock items for store 102."
        )
    ]
})

print("\nMessages:")
for message in result["messages"]:
    print(message.type, ":", message.content)