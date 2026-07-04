from __future__ import annotations

from app.agents import build_agent


def run_cli() -> None:
    """Start the interactive command-line Agent session."""
    agent = build_agent()

    print("DeepSeek Agent is ready. Type 'exit' or 'quit' to stop.")
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue

        result = agent.invoke({"messages": [("user", user_input)]})
        answer = result["messages"][-1].content
        print(f"\nAgent: {answer}")


if __name__ == "__main__":
    run_cli()
