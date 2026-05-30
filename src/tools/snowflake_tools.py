"""Tools the Deep Agent can call to query Snowflake."""

from __future__ import annotations

import re

import snowflake.connector
from langchain.tools import tool

from src.check_setup import ensure_repo_on_path, repo_root

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
def execute_snowflake_sql(sql: str) -> str:
    """Run a read-only SELECT on Snowflake TPCH_SF1. Returns columns and up to 20 rows."""
    sql = sql.strip().rstrip(";")
    if FORBIDDEN.search(sql):
        return "ERROR: Only SELECT queries are allowed in the sandbox."
    if not sql.upper().lstrip().startswith("SELECT"):
        return "ERROR: Query must start with SELECT."

    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(f"USE SCHEMA {SNOWFLAKE_SCHEMA}")
        cur.execute(sql)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchmany(20)
        return f"Columns: {cols}\nRows ({len(rows)} shown):\n{rows}"
    except Exception as exc:
        return f"SNOWFLAKE ERROR: {exc}\nFix the SQL and try again."
    finally:
        conn.close()


@tool
def get_schema_summary() -> str:
    """Return table and column names for TPCH_SF1."""
    return SCHEMA_PATH.read_text(encoding="utf-8")
