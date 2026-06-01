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
