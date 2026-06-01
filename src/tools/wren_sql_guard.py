"""Reject raw Snowflake TPCH references in Wren-mode SQL."""

from __future__ import annotations

import re

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
    """Return a user-facing hint if SQL uses physical TPCH names instead of MDL models."""
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
