# Agent error handling and SQL retry policy

Policy for the Deep Agent NL→SQL POC (Off / Wren / Cortex modes).

## Layers

| Layer | Location | Role |
|-------|----------|------|
| **Spec (human)** | This doc | Classification, limits, product behavior |
| **Enforcement** | `src/semantic_layer/retry_policy.py` | Counters, fingerprints, error tags |
| **Tools** | `wren_tools.py`, `snowflake_tools.py` | Apply policy on `wren_run_sql` / `execute_snowflake_sql` |
| **Graph** | `src/ag_ui_agent.py` | `recursion_limit`, `thread_id` in config |
| **Prompt** | `src/semantic_layer/prompts.py` | Short rules aligned with code |

Constants: `MAX_SQL_ATTEMPTS = 3`, `GRAPH_RECURSION_LIMIT = 25`.

## Error tags returned to the model

| Tag | Meaning | Model should |
|-----|---------|--------------|
| `ERROR [retryable:…]` | Likely fixable SQL | Fix SQL, retry if attempts remain |
| `ERROR [repeat_error]` | Same failure twice | Stop; explain; no more SQL tools |
| `ERROR [max_attempts]` | 3 failures this turn | Stop; summarize failures |
| `ERROR [non_retryable:…]` | Auth, wrong mode, engine bug | Stop; no retry |

## Classification (code)

Non-retryable patterns include: wrong semantic mode, Wren not ready, timeouts, auth/login, `__SOURCE` engine errors, policy violations.

## Wren MDL notes

- Use `customer_name` / `nation_name`, not `name` (Wren + Snowflake expansion bug).
- After MDL edits: `wren context build` and `wren memory index`.

## Local setup

- Snowflake secrets: `config/snowflake_config.py` (gitignored).
- Wren profile: `scripts/sync_wren_profile.py` → `~/.wren/profiles.yml` (gitignored).
