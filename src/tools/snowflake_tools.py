"""Tools the Deep Agent can call to query Snowflake."""

from __future__ import annotations

import re
from typing import Annotated

import snowflake.connector
from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg

from src.check_setup import ensure_repo_on_path, repo_root
from src.semantic_layer.retry_policy import (
    check_sql_attempt_allowed,
    register_sql_failure,
    reset_sql_attempts,
)
from src.semantic_layer.runtime import semantic_layer_from_config

ensure_repo_on_path()

try:
    from config.snowflake_config import (
        account,
        database,
        password,
        schema,
        user,
        warehouse,
    )
except ImportError as exc:
    raise SystemExit(
        "Missing config/snowflake_config.py — "
        "cp config/snowflake_config.example.py config/snowflake_config.py"
    ) from exc

SCHEMA_PATH = repo_root() / "schema" / "tpch_sf1.md"
SNOWFLAKE_SCHEMA = "TPCH_SF1"
FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|GRANT|REVOKE)\b",
    re.I,
)


def _block_unless_off_mode(config: RunnableConfig | None) -> str | None:
    mode = semantic_layer_from_config(config)
    if mode == "wren":
        return (
            "ERROR: execute_snowflake_sql is disabled in Wren mode. "
            "Use wren_memory_fetch, wren_dry_plan, and wren_run_sql with MDL model names "
            "(e.g. SELECT c.customer_name, SUM(o.total_price) FROM customer c JOIN orders o ...)."
        )
    if mode == "cortex":
        return "ERROR: Use ask_cortex_analyst in Cortex mode, not execute_snowflake_sql."
    return None


def _connect():
    return snowflake.connector.connect(
        account=account,
        user=user,
        password=password,
        warehouse=warehouse,
        database=database,
        schema=schema,
    )


@tool
def execute_snowflake_sql(
    sql: str,
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """Run a read-only SELECT on Snowflake TPCH_SF1. Returns columns and up to 20 rows."""
    if block := _block_unless_off_mode(config):
        return block
    if block := check_sql_attempt_allowed(config, tool_name="execute_snowflake_sql"):
        return block
    sql = sql.strip().rstrip(";")
    if FORBIDDEN.search(sql):
        msg = "ERROR: Only SELECT queries are allowed in the sandbox."
        return register_sql_failure(config, msg, tool_name="execute_snowflake_sql")
    if not sql.upper().lstrip().startswith("SELECT"):
        msg = "ERROR: Query must start with SELECT."
        return register_sql_failure(config, msg, tool_name="execute_snowflake_sql")

    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(f"USE SCHEMA {SNOWFLAKE_SCHEMA}")
        cur.execute(sql)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchmany(20)
        reset_sql_attempts(config)
        return f"Columns: {cols}\nRows ({len(rows)} shown):\n{rows}"
    except Exception as exc:
        msg = f"SNOWFLAKE ERROR: {exc}"
        return register_sql_failure(config, msg, tool_name="execute_snowflake_sql")
    finally:
        conn.close()


@tool
def get_schema_summary(
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """Return table and column names for TPCH_SF1."""
    if block := _block_unless_off_mode(config):
        return block
    return SCHEMA_PATH.read_text(encoding="utf-8")
