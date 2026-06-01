"""LangChain tools for the semantic layer editor agent."""

from __future__ import annotations

import json
import re
from typing import Annotated, Any

from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg

from src.audit_reader import search_audit_entries
from src.check_setup import repo_root
from src.semantic_editor.files import list_semantic_files, read_semantic_file, write_semantic_file
from src.semantic_editor.paths import SemanticPathError
from src.semantic_editor.validate import run_wren_validate
from src.tools.snowflake_tools import FORBIDDEN, _connect, SNOWFLAKE_SCHEMA

SCHEMA_PATH = repo_root() / "schema" / "tpch_sf1.md"
LIMIT_PATTERN = re.compile(r"\blimit\s+(\d+)", re.I)


def _enforce_limit_10(sql: str) -> str | None:
    sql = sql.strip().rstrip(";")
    if FORBIDDEN.search(sql):
        return "ERROR: Only read-only SELECT queries are allowed."
    if not sql.upper().lstrip().startswith("SELECT"):
        return "ERROR: Query must start with SELECT."
    match = LIMIT_PATTERN.search(sql)
    if not match:
        return "ERROR: Editor SQL must include LIMIT 10 or less."
    if int(match.group(1)) > 10:
        return "ERROR: LIMIT must be ≤ 10 for editor probes."
    return None


@tool
def list_semantic_files_tool(root: str | None = None) -> str:
    """List editable semantic layer files under allowlisted roots (optional root filter)."""
    try:
        payload = list_semantic_files(root=root)
    except SemanticPathError as exc:
        return f"ERROR: {exc}"
    paths = [f["path"] for f in payload.get("files", [])]
    return json.dumps({"roots": payload.get("roots", []), "files": paths}, indent=2)


@tool
def read_semantic_file_tool(path: str) -> str:
    """Read one allowlisted semantic layer file (YAML/MD under wren/tpch, schema/, semantic/)."""
    try:
        payload = read_semantic_file(path)
    except SemanticPathError as exc:
        return f"ERROR: {exc}"
    except FileNotFoundError:
        return f"ERROR: not found: {path}"
    content = payload["content"]
    if len(content) > 12000:
        return f"path: {payload['path']}\n\n{content[:12000]}\n… (truncated)"
    return f"path: {payload['path']}\n\n{content}"


@tool
def write_semantic_file_tool(path: str, content: str) -> str:
    """Write an allowlisted semantic file. Use after user confirms a proposed diff."""
    try:
        payload = write_semantic_file(path, content)
    except SemanticPathError as exc:
        return f"ERROR: {exc}"
    return json.dumps({"saved": True, "path": payload["path"], "size": payload["size"]})


@tool
def wren_validate_tool() -> str:
    """Run wren context validate for wren/tpch and return the result."""
    result = run_wren_validate()
    return json.dumps(result, indent=2)


@tool
def editor_get_schema_summary() -> str:
    """Return TPCH markdown schema summary (physical column reference)."""
    return SCHEMA_PATH.read_text(encoding="utf-8")


@tool
def editor_execute_snowflake_sql(
    sql: str,
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """Run a read-only SELECT on Snowflake with LIMIT ≤ 10 (schema probes only)."""
    _ = config
    if block := _enforce_limit_10(sql):
        return block
    sql = sql.strip().rstrip(";")
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(f"USE SCHEMA {SNOWFLAKE_SCHEMA}")
        cur.execute(sql)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchmany(10)
        return f"Columns: {cols}\nRows ({len(rows)} shown):\n{rows}"
    except Exception as exc:
        return f"SNOWFLAKE ERROR: {exc}"
    finally:
        conn.close()


@tool
def search_audit_logs(
    query: str | None = None,
    semantic_layer: str | None = None,
    status: str | None = None,
    limit: int = 10,
) -> str:
    """Search recent query audit logs. Filter by text, semantic_layer (off/wren/cortex), or status (ok/error)."""
    entries = search_audit_entries(
        query=query,
        semantic_layer=semantic_layer,
        status=status,
        limit=min(max(limit, 1), 30),
    )
    if not entries:
        return "No matching audit entries."
    slim: list[dict[str, Any]] = []
    for entry in entries:
        slim.append(
            {
                "timestamp": entry.get("timestamp"),
                "thread_id": entry.get("thread_id"),
                "semantic_layer": entry.get("semantic_layer"),
                "status": entry.get("status"),
                "question": entry.get("question"),
                "error": entry.get("error"),
                "sql_executions": entry.get("sql_executions"),
            }
        )
    return json.dumps(slim, indent=2)


@tool
def feedback_search_stub(query: str) -> str:
    """Placeholder for future user feedback log search (not implemented)."""
    _ = query
    return "Feedback log search is not configured in this POC yet."


EDITOR_TOOLS = [
    list_semantic_files_tool,
    read_semantic_file_tool,
    write_semantic_file_tool,
    wren_validate_tool,
    editor_get_schema_summary,
    editor_execute_snowflake_sql,
    search_audit_logs,
    feedback_search_stub,
]
