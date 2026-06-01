from src.tools.wren_sql_guard import wren_modeled_sql_violation

MODELED = (
    "SELECT customer_name, SUM(total_price) AS total_order_value "
    "FROM customer JOIN orders ON customer.customer_key = orders.customer_key "
    "GROUP BY customer_name ORDER BY total_order_value DESC LIMIT 5"
)

EXPANDED = (
    "WITH customer AS (SELECT __source.customer_key FROM "
    "SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER AS __source) "
    "SELECT customer_name FROM customer"
)


def test_modeled_sql_allowed():
    assert wren_modeled_sql_violation(MODELED) is None


def test_expanded_sql_rejected_with_hint():
    msg = wren_modeled_sql_violation(EXPANDED)
    assert msg is not None
    assert "use_modeled_sql_only" in msg
    assert "wren_dry_plan" in msg


def test_raw_tpch_rejected():
    msg = wren_modeled_sql_violation("SELECT * FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS")
    assert msg is not None
    assert "use_mdl_models" in msg
