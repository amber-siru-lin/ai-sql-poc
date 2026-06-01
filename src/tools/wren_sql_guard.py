"""Reject raw Snowflake TPCH references in Wren-mode SQL."""

from __future__ import annotations

import re

# Wren dry-plan output — agent must not pass this to wren_run_sql.
_WREN_EXPANDED = re.compile(r"__source|wren_src_", re.I)

# Modeled SQL should use: customer, orders, nation and columns like customer_name.
_PHYSICAL_SQL = re.compile(
    r"""
    SNOWFLAKE_SAMPLE_DATA |
    \bTPCH_SF1\. |
    \bC_CUSTKEY\b | \bC_NAME\b | \bC_NATIONKEY\b | \bC_MKTSEGMENT\b |
    \bO_ORDERKEY\b | \bO_CUSTKEY\b | \bO_TOTALPRICE\b |
    \bN_NATIONKEY\b | \bN_NAME\b
    """,
    re.I | re.VERBOSE,
)


def wren_modeled_sql_violation(sql: str) -> str | None:
    """Return a user-facing hint if SQL is not valid modeled input for Wren tools."""
    if _WREN_EXPANDED.search(sql):
        return (
            "ERROR [retryable:use_modeled_sql_only]: You passed Wren **expanded** SQL "
            "(from wren_dry_plan) to wren_run_sql. Dry-plan output is preview-only and "
            "contains physical table names — that is expected. "
            "Call wren_run_sql with the same **modeled** SQL you used in wren_dry_plan "
            "(models: customer, orders, nation — no SNOWFLAKE_SAMPLE_DATA or C_/O_ columns)."
        )
    if _PHYSICAL_SQL.search(sql):
        return (
            "ERROR [retryable:use_mdl_models]: In Wren mode, do not use "
            "SNOWFLAKE_SAMPLE_DATA, TPCH_SF1.*, or C_/O_/N_ column names. "
            "Use MDL models: customer, orders, nation and columns "
            "customer_name, customer_key, order_key, total_price, nation_name, nation_key. "
            "Example: SELECT c.customer_name, SUM(o.total_price) FROM customer c "
            "JOIN orders o ON c.customer_key = o.customer_key GROUP BY 1 LIMIT 5. "
            "Call wren_memory_fetch if you need schema."
        )
    return None
