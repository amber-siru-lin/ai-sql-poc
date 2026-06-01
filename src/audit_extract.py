"""Extract audit fields from LangChain message lists."""

from __future__ import annotations

import json
from typing import Any

from src.audit_logger import SQL_TOOL_NAMES, result_fingerprint

try:
    from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
except ImportError:
    from langchain.schema import AIMessage, BaseMessage, HumanMessage, ToolMessage  # type: ignore


def _message_content(msg: Any) -> str:
    if isinstance(msg, dict):
        content = msg.get("content", "") or ""
    else:
        content = getattr(msg, "content", "") or ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return str(content)


def _message_type(msg: Any) -> str | None:
    if isinstance(msg, dict):
        raw = msg.get("type") or msg.get("role")
        return str(raw) if raw is not None else None
    return getattr(msg, "type", None)


def _is_human_message(msg: Any) -> bool:
    if isinstance(msg, HumanMessage):
        return True
    kind = _message_type(msg)
    if kind in ("human", "HumanMessage", "user"):
        return True
    return isinstance(msg, dict) and msg.get("role") == "user"


def _is_ai_message(msg: Any) -> bool:
    if isinstance(msg, AIMessage):
        return True
    kind = _message_type(msg)
    if kind in ("ai", "AIMessage", "assistant"):
        return True
    return isinstance(msg, dict) and msg.get("role") == "assistant"


def last_user_question(messages: list[Any]) -> str | None:
    for msg in reversed(messages):
        if _is_human_message(msg):
            text = _message_content(msg).strip()
            if text:
                return text
    return None


def last_assistant_reply(messages: list[Any]) -> str | None:
    """Assistant prose after the final user turn (for audit transcript restore)."""
    last_human_idx = -1
    for i, msg in enumerate(messages):
        if _is_human_message(msg):
            last_human_idx = i

    if last_human_idx < 0:
        return None

    parts: list[str] = []
    for msg in messages[last_human_idx + 1 :]:
        if _is_human_message(msg):
            break
        if _is_ai_message(msg):
            text = _message_content(msg).strip()
            if text:
                parts.append(text)

    if not parts:
        return None
    return "\n\n".join(parts)


def _sql_from_tool_call(tc: dict[str, Any]) -> str | None:
    name = tc.get("name") or tc.get("tool")
    if name not in SQL_TOOL_NAMES:
        return None
    args = tc.get("args") or {}
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            return None
    if not isinstance(args, dict):
        return None
    sql = args.get("sql") or args.get("query")
    return str(sql).strip() if sql else None


def extract_sql_executions(messages: list[Any]) -> list[dict[str, Any]]:
    """Pair tool SQL calls with tool results where possible."""
    pending: dict[str, dict[str, Any]] = {}
    ordered: list[dict[str, Any]] = []

    for msg in messages:
        if isinstance(msg, AIMessage) or getattr(msg, "type", None) == "ai":
            tool_calls = getattr(msg, "tool_calls", None) or []
            for tc in tool_calls:
                if not isinstance(tc, dict):
                    continue
                tc_id = tc.get("id")
                sql = _sql_from_tool_call(tc)
                if not sql:
                    continue
                entry: dict[str, Any] = {
                    "tool": tc.get("name"),
                    "sql": sql,
                    "result_fingerprint": None,
                    "result_preview": None,
                    "error": None,
                }
                if tc_id:
                    pending[tc_id] = entry
                ordered.append(entry)

        if isinstance(msg, ToolMessage) or getattr(msg, "type", None) == "tool":
            tool_name = getattr(msg, "name", None)
            content = _message_content(msg)
            tc_id = getattr(msg, "tool_call_id", None)
            target = pending.pop(tc_id, None) if tc_id else None
            if target is None and tool_name in SQL_TOOL_NAMES:
                target = {
                    "tool": tool_name,
                    "sql": None,
                    "result_fingerprint": None,
                    "result_preview": None,
                    "error": None,
                }
                ordered.append(target)
            if target is None:
                continue
            if content.upper().startswith("ERROR") or "SNOWFLAKE ERROR" in content or "WREN ERROR" in content:
                target["error"] = content[:500]
            else:
                target["result_fingerprint"] = result_fingerprint(content)
                target["result_preview"] = content[:240] if content else None

    return ordered
