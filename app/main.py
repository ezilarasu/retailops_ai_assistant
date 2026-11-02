from app.container import get_container
from app.logging_config import configure_logging
from app.services import assistant_service


def main():
    print("RetailOps AI Assistant - Production CLI")

    # Build everything up front (index check, embedding model, reranker, chains) so the
    # first question is as fast as the rest instead of paying the startup cost.
    print("Loading models and index (the first start can take a few seconds)...")
    try:
        get_container()
    except Exception as error:
        print(f"\nStartup failed: {error}")
        print("Check your .env file (GROQ_API_KEY, LLM_MODEL) and try again.")
        return

    print("Ready. Type 'exit' to stop.")

    while True:
        question = input("\nYou: ")

        if question.lower() == "exit":
            break

        result = assistant_service.ask(question)

        print("\nRoute:", result["route"])
        print("Reason:", result["reason"])

        print("\nAssistant:")
        print(result["answer"])

        if result.get("sources"):
            print("\nSources:")
            for source in result["sources"]:
                print("-", source)

        if result.get("confidence"):
            print("\nConfidence:")
            print(result["confidence"])

        print("\nLatency ms:")
        print(result["latency_ms"])

        if result.get("cache_hit"):
            print("(served from cache)")


if __name__ == "__main__":
    configure_logging()
    main()
