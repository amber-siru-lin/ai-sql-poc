"""SQL tool retry limits and error classification (enforced in code, not prompt-only)."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from langchain_core.runnables import RunnableConfig

# LangGraph default for deep agents is very high; cap agent+tool steps per user turn.
GRAPH_RECURSION_LIMIT = 25
MAX_SQL_ATTEMPTS = 3

_NON_RETRYABLE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"only available when semantic layer", re.I), "wrong_semantic_mode"),
    (re.compile(r"not ready", re.I), "wren_not_ready"),
    (re.compile(r"timed out", re.I), "timeout"),
    (re.compile(r"not found on PATH", re.I), "cli_missing"),
    (re.compile(r"Only SELECT", re.I), "policy_violation"),
    (re.compile(r"authentication|login-request|401|403", re.I), "auth"),
    (re.compile(r"__SOURCE", re.I), "wren_engine"),
]

_SESSION: dict[str, dict[str, Any]] = {}


def _session_key(config: RunnableConfig | None) -> str:
    if not config:
        return "default"
    configurable = config.get("configurable") or {}
    return str(
        configurable.get("thread_id")
        or configurable.get("checkpoint_id")
        or configurable.get("run_id")
        or "default"
    )


def reset_sql_attempts(config: RunnableConfig | None) -> None:
    """Clear attempt state after a successful SQL execution."""
    _SESSION.pop(_session_key(config), None)


def _error_fingerprint(message: str) -> str:
    normalized = re.sub(r"\s+", " ", message.strip().lower())[:500]
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def classify_sql_error(message: str) -> tuple[str, bool]:
    """Return (code, retryable)."""
    for pattern, code in _NON_RETRYABLE_PATTERNS:
        if pattern.search(message):
            return code, False
    if message.startswith("ERROR:") and "disabled" in message.lower():
        return "disabled_tool", False
    lower = message.lower()
    if "use_mdl_models" in lower:
        return "use_mdl_models", True
    if (
        "does not exist" in lower
        or "not authorized" in lower
        or "object '" in lower
    ) and ("tpch_sf1" in lower or "snowflake_sample_data" in lower):
        return "tpch_object_missing", True
    if "compilation error" in lower or "invalid identifier" in lower:
        return "sql_compilation", True
    if "SNOWFLAKE ERROR" in message or "WREN ERROR" in message:
        return "execution", True
    return "unknown", True


def check_sql_attempt_allowed(
    config: RunnableConfig | None,
    *,
    tool_name: str,
) -> str | None:
    """Return an error string if the tool must not run; else None."""
    key = _session_key(config)
    state = _SESSION.setdefault(key, {"count": 0, "last_fp": None, "repeat": 0})

    if state["count"] >= MAX_SQL_ATTEMPTS:
        return (
            f"ERROR [max_attempts]: Stopped after {MAX_SQL_ATTEMPTS} failed SQL attempts "
            f"for this conversation turn. Summarize the failures for the user and do not "
            f"call {tool_name} again."
        )
    return None


def register_sql_failure(
    config: RunnableConfig | None,
    error_message: str,
    *,
    tool_name: str,
) -> str:
    """Record failure; return message to return from tool (may include stop instruction)."""
    key = _session_key(config)
    state = _SESSION.setdefault(key, {"count": 0, "last_fp": None, "repeat": 0})

    fp = _error_fingerprint(error_message)
    if state["last_fp"] == fp:
        state["repeat"] += 1
    else:
        state["repeat"] = 1
        state["last_fp"] = fp

    state["count"] += 1
    code, retryable = classify_sql_error(error_message)

    if state["repeat"] >= 2:
        return (
            f"ERROR [repeat_error]: The same error occurred again ({code}). "
            f"Do not retry. Explain the issue and suggest MDL/schema fixes or Off mode.\n\n"
            f"{error_message}"
        )

    if not retryable:
        return (
            f"ERROR [non_retryable:{code}]: Do not call {tool_name} again for this question.\n\n"
            f"{error_message}"
        )

    remaining = max(0, MAX_SQL_ATTEMPTS - state["count"])
    if remaining == 0:
        return (
            f"ERROR [max_attempts]: No SQL retries left.\n\n{error_message}"
        )

    return (
        f"ERROR [retryable:{code}] ({remaining} attempt(s) left): Fix the SQL, then retry.\n\n"
        f"{error_message}"
    )


def format_success_prefix() -> str:
    return ""
