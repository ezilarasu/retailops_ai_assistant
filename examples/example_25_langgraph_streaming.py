from app.graph.graph import build_retailops_graph


graph = build_retailops_graph()

config = {
    "configurable": {
        "thread_id": "stream-demo-user-1"
    }
}

# stream() yields one event per node as it finishes, instead of waiting for the end
for event in graph.stream(
    {"question": "What does P1 mean?"},
    config=config,
):
    for node_name, node_output in event.items():
        print("\nNode:", node_name)
        print("Route:", node_output.get("route"))
        print("Answer:", node_output.get("answer"))
        print("Timings:", node_output.get("timings"))