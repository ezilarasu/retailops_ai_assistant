from app.graph.graph import build_retailops_graph


graph = build_retailops_graph()

# The thread_id is the conversation key: the graph's checkpointer saves state per thread,
# so the second question below can see the first one.
config = {
    "configurable": {
        "thread_id": "demo-user-1"
    }
}

# Turn 1: a policy question that the router sends to the RAG subgraph
first = graph.invoke(
    {
        "question": "What does P1 mean?"
    },
    config=config,
)

print("\nFirst route:", first.get("route"))
print("First answer:", first.get("answer"))

# Turn 2: same thread_id, so the saved messages from turn 1 are available as context
# for this short follow-up question
second = graph.invoke(
    {
        "question": "What should managers do?"
    },
    config=config,
)

print("\nSecond route:", second.get("route"))
print("Second answer:", second.get("answer"))

print("\nDebug:")
print(second.get("debug"))

print("\nMessages:")
for message in second.get("messages", []):
    print(message.type, ":", message.content)

# Validation check: an empty question is rejected by the validation node before any LLM call
bad = graph.invoke(
    {
        "question": ""
    },
    config={
        "configurable": {
            "thread_id": "validation-test"
        }
    },
)

print("\nEmpty question answer:", bad.get("answer"))
print("Empty question debug:", bad.get("debug"))
