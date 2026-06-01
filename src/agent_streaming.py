"""Pretty-print Deep Agent steps while streaming."""

from __future__ import annotations

from typing import Any


INTERESTING_NODES = {"model_request", "tools", "SummarizationMiddleware.before_model"}


def _truncate(text: str, limit: int = 400) -> str:
    text = str(text).strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def _tool_calls_from_message(msg: Any) -> list[dict]:
    calls = getattr(msg, "tool_calls", None) or []
    result = []
    for call in calls:
        if isinstance(call, dict):
            result.append(call)
        else:
            result.append(
                {
                    "name": getattr(call, "name", "?"),
                    "args": getattr(call, "args", {}),
                    "id": getattr(call, "id", ""),
                }
            )
    return result


def stream_agent(agent, messages: list, config: dict | None = None) -> tuple[str, list]:
    """Run the agent with live step output. Returns (answer text, updated messages)."""
    input_state = {"messages": messages}
    final_answer_parts: list[str] = []
    step = 0

    print("── Agent steps ──")

    stream_kwargs: dict = {
        "stream_mode": ["updates", "messages"],
        "subgraphs": True,
        "version": "v2",
    }
    if config:
        stream_kwargs["config"] = config

    try:
        chunks = agent.stream(input_state, **stream_kwargs)
    except TypeError:
        stream_kwargs.pop("version", None)
        chunks = agent.stream(input_state, **stream_kwargs)

    for chunk in chunks:
        if isinstance(chunk, dict) and chunk.get("type") in {"updates", "messages"}:
            chunk_type = chunk["type"]
            data = chunk.get("data")
        elif isinstance(chunk, tuple) and len(chunk) == 2:
            chunk_type, data = chunk
            if isinstance(data, tuple) and len(data) == 2:
                chunk_type, data = data
        else:
            continue

        if chunk_type == "updates" and isinstance(data, dict):
            for node_name, node_data in data.items():
                if node_name not in INTERESTING_NODES and not node_name.startswith("tools"):
                    continue
                step += 1
                print(f"\n[{step}] step: {node_name}")

                node_messages = node_data.get("messages", []) if isinstance(node_data, dict) else []
                for msg in node_messages:
                    msg_type = getattr(msg, "type", None) or getattr(msg, "role", "")

                    if msg_type in {"ai", "assistant"}:
                        for call in _tool_calls_from_message(msg):
                            name = call.get("name", "?")
                            args = call.get("args", {})
                            print(f"    → tool call: {name}")
                            if name == "write_todos":
                                todos = args.get("todos") or args
                                print(f"      plan: {_truncate(todos)}")
                            elif name == "execute_snowflake_sql":
                                print(f"      sql: {_truncate(args.get('sql', args))}")
                            elif name == "get_schema_summary":
                                print("      reading schema file")
                            else:
                                print(f"      args: {_truncate(args)}")

                    if msg_type == "tool":
                        name = getattr(msg, "name", "tool")
                        print(f"    ← tool result [{name}]:")
                        for line in _truncate(msg.content, 500).splitlines()[:6]:
                            print(f"       {line}")

        elif chunk_type == "messages":
            token, _metadata = data if isinstance(data, tuple) else (data, {})
            if getattr(token, "type", None) == "ai" and token.content:
                if isinstance(token.content, str):
                    final_answer_parts.append(token.content)
                elif isinstance(token.content, list):
                    for block in token.content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            final_answer_parts.append(block.get("text", ""))
                        elif isinstance(block, str):
                            final_answer_parts.append(block)

            if getattr(token, "tool_call_chunks", None):
                for tc in token.tool_call_chunks:
                    if tc.get("name"):
                        print(f"    → tool call: {tc['name']}")

    print("\n── Final answer ──\n")
    invoke_kwargs = {"config": config} if config else {}
    result = agent.invoke(input_state, **invoke_kwargs)
    updated_messages = list(result["messages"])
    final = "".join(final_answer_parts).strip() or updated_messages[-1].content
    return final, updated_messages
