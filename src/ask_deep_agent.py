"""Phase 2: NL→SQL using LangChain Deep Agents + Snowflake tools."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agent_factory import build_agent_graph
from src.agent_streaming import stream_agent
from src.check_setup import check_all

check_all()

agent = build_agent_graph()


def ask(question: str, history: list, *, verbose: bool = False) -> tuple[str, list]:
    """Send a question with conversation history. Returns (answer, updated history)."""
    messages = list(history)
    messages.append({"role": "user", "content": question})

    if verbose:
        return stream_agent(agent, messages)

    result = agent.invoke({"messages": messages})
    updated = list(result["messages"])
    return updated[-1].content, updated


def main() -> None:
    parser = argparse.ArgumentParser(description="Deep Agent NL→SQL (Phase 2)")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show planning steps, tool calls, and SQL as the agent runs",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("AI SQL ASSISTANT - Deep Agent (Phase 2)")
    if args.verbose:
        print("Verbose mode: ON (showing steps)")
    print("Conversation memory: ON (follow-ups use prior questions)")
    print("=" * 70)
    print("Commands: 'quit' | 'clear' (new conversation) | 'help'\n")

    history: list = []

    while True:
        try:
            question = input("❓ Question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Goodbye!")
            break

        if not question:
            continue
        if question.lower() in {"quit", "exit", "q"}:
            print("👋 Goodbye!")
            break
        if question.lower() == "clear":
            history = []
            print("🧹 Conversation cleared.\n")
            continue
        if question.lower() == "help":
            print(
                "Ask data questions in plain English. Follow-ups work, e.g.:\n"
                "  1) Revenue by customer market segment\n"
                "  2) show percentage instead\n"
                "Type 'clear' to start a new topic.\n"
            )
            continue

        if not args.verbose:
            print("\n🤖 Agent working (may take 15–30 seconds)...")
            print("Tip: --verbose shows steps | 'clear' resets memory\n")

        try:
            answer, history = ask(question, history, verbose=args.verbose)
            print(answer)
        except Exception as exc:
            print(f"❌ Error: {exc}")
        print()


if __name__ == "__main__":
    main()
