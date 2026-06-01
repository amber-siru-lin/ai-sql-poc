# TPCH_SF1 (Snowflake sample)

- Use Snowflake SQL dialect after Wren expands modeled SQL.
- "Revenue" means sum of order totals (`O_TOTALPRICE`) unless the user specifies otherwise.
- Prefer model names (`customer`, `orders`, `nation`) in Wren SQL, not raw `TPCH_SF1.*` table names.
- Name columns are `customer_name` and `nation_name` (not `name` — reserved in the engine).
