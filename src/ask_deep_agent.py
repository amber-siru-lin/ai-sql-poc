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
from src.semantic_layer.retry_policy import GRAPH_RECURSION_LIMIT
from src.semantic_layer.types import SEMANTIC_LAYER_MODES, SemanticLayerMode, normalize_semantic_layer

check_all()


def ask(
    question: str,
    history: list,
    *,
    semantic_layer: SemanticLayerMode = "off",
    verbose: bool = False,
) -> tuple[str, list]:
    """Send a question with conversation history. Returns (answer, updated history)."""
    agent = build_agent_graph(semantic_layer)
    messages = list(history)
    messages.append({"role": "user", "content": question})
    run_config = {
        "configurable": {"semantic_layer": semantic_layer, "thread_id": "cli"},
        "recursion_limit": GRAPH_RECURSION_LIMIT,
    }

    if verbose:
        return stream_agent(agent, messages, config=run_config)

    result = agent.invoke({"messages": messages}, config=run_config)
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
    parser.add_argument(
        "--semantic-layer",
        choices=SEMANTIC_LAYER_MODES,
        default="off",
        help="Semantic layer mode: off (markdown schema), wren (MDL), cortex (placeholder)",
    )
    args = parser.parse_args()
    mode = normalize_semantic_layer(args.semantic_layer)

    print("=" * 70)
    print("AI SQL ASSISTANT - Deep Agent (Phase 2)")
    print(f"Semantic layer: {mode}")
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
            answer, history = ask(
                question,
                history,
                semantic_layer=mode,
                verbose=args.verbose,
            )
            print(answer)
        except Exception as exc:
            print(f"❌ Error: {exc}")
        print()


if __name__ == "__main__":
    main()
