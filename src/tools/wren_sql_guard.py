"""Reject raw Snowflake physical references in Wren-mode SQL."""

from __future__ import annotations

import re

from config.settings import snowflake_database, snowflake_schema, wren_physical_sql_pattern

# Wren dry-plan output — agent must not pass this to wren_run_sql.
_WREN_EXPANDED = re.compile(r"__source|wren_src_", re.I)


def wren_modeled_sql_violation(sql: str) -> str | None:
    """Return a user-facing hint if SQL is not valid modeled input for Wren tools."""
    if _WREN_EXPANDED.search(sql):
        return (
            "ERROR [retryable:use_modeled_sql_only]: You passed Wren **expanded** SQL "
            "(from wren_dry_plan) to wren_run_sql. Dry-plan output is preview-only and "
            "contains physical table names — that is expected. "
            "Call wren_run_sql with the same **modeled** SQL you used in wren_dry_plan "
            "(MDL model names only — not physical database/schema/table references)."
        )

    pattern = wren_physical_sql_pattern()
    if pattern.search(sql):
        db = snowflake_database()
        sch = snowflake_schema()
        physical_hint = f"{db}.{sch}" if db and sch else sch or "physical Snowflake names"
        return (
            "ERROR [retryable:use_mdl_models]: In Wren mode, do not use raw Snowflake "
            f"references such as {physical_hint} or {sch}.* table prefixes. "
            "Use MDL model and column names from wren_memory_fetch. "
            "Example: SELECT c.customer_name, SUM(o.total_price) FROM customer c "
            "JOIN orders o ON c.customer_key = o.customer_key GROUP BY 1 LIMIT 5."
        )
    return None
