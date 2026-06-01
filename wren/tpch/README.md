# Wren MDL — TPCH_SF1

Used when CopilotKit **Semantics → Wren** is enabled.

## One-time setup

```bash
# From repo root
scripts/py -m pip install "wrenai[snowflake,memory]" pyyaml

# Reuse repo Snowflake credentials → ~/.wren/profiles.yml (gitignored)
scripts/py scripts/sync_wren_profile.py

cd wren/tpch
wren context set-profile tpch-sf1

# If validate says "references unknown model", the project is on legacy layout:
wren context upgrade   # sets schema_version: 3 so models/*/metadata.yml are loaded

wren context validate
wren context build
wren memory index
```

After `wren context build`, `target/mdl.json` exists and `/api/status` reports `wren_ready: true`.

## Troubleshooting

### `ORDERS` / `TPCH_SF1` table not found (Wren mode)

Usually the agent wrote **physical** Snowflake SQL (`SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS`) instead of **MDL** SQL (`FROM orders`).

1. Verify access: `scripts/py scripts/verify_tpch_setup.py`
2. Re-sync profile: `scripts/py scripts/sync_wren_profile.py` (needs `account: wzqidsn-ib45431`, `sf_schema: TPCH_SF1`)
3. New chat in UI → **Semantics → Wren** → ask again
4. SQL must use models: `customer`, `orders`, `nation` and columns `customer_name`, `nation_name`, `total_price` — **not** `name`, **not** `C_*` / `O_*`

If verification passes but the UI still fails, restart the API from a shell where `which wren` works (same conda env as `scripts/py`).

### Off mode as fallback

**Semantics → Off** uses `execute_snowflake_sql` with `TPCH_SF1.*` table names (no Wren MDL).
