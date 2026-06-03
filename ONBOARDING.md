# Onboarding

## Start here (one command)

```bash
./scripts/onboard.sh
```

Interactive walkthrough: installs deps, scaffolds config, helps set AWS + Snowflake, verifies Bedrock, optionally starts the app.

| Command | When |
|---------|------|
| `./scripts/onboard.sh` | **First day** — full guided setup |
| `./scripts/onboard.sh --check` | Re-verify after SSO expiry or config change |
| `./scripts/setup.sh` | CI / quick reinstall (non-interactive) |
| `./scripts/dev.sh` | Daily dev — API `:8000` + UI `:5173` |
| `make onboard` | Same as `./scripts/onboard.sh` |

Help: `./scripts/onboard.sh --help`

---

## What this repo is

Natural language → SQL on **Snowflake**, orchestrated by **Amazon Bedrock**, with an optional **CopilotKit** UI and **Wren** semantic layer.

| Path | Status |
|------|--------|
| `api/` + `ui/` + `src/` | **Active** — local dev stack |
| `wren/tpch/` | Optional Wren MDL (update for client schema) |
| `web/` | Parked Amplify scaffold — not required daily |

```
Browser (ui/) → FastAPI (api/) → Deep Agent (src/) → Bedrock + Snowflake
                                      ↓
                         Semantics: Off | Wren | Cortex
```

Config: **`config/settings.py`** reads `.env` + `config/snowflake_config.py`.

## After onboard.sh

1. Open http://localhost:5173
2. Chat → Semantics **Off**
3. Ask a natural-language question about your Snowflake data

## Reference docs

| Topic | Doc |
|-------|-----|
| Setup details | [SETUP.md](SETUP.md) |
| Client secrets / IAM | [docs/CLIENT-CREDENTIALS.md](docs/CLIENT-CREDENTIALS.md) |
| Phase isolation | [docs/PHASES.md](docs/PHASES.md) |
| Agent dev rules | [AGENTS.md](AGENTS.md) |

## Client schema (not TPCH sample)

1. `database`, `schema`, `dataset_label` in `config/snowflake_config.py`
2. Markdown schema at `schema_markdown_path`
3. Wren MDL under `wren/` if using Wren mode
4. Optional: `ui/src/config.ts` `SAMPLE_QUESTIONS`

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Bedrock errors | `aws sso login`, check `BEDROCK_MODEL_ID` |
| Snowflake errors | `config/snowflake_config.py` warehouse/database/schema |
| UI offline | `./scripts/dev.sh` or check `curl localhost:8000/api/status` |
| Re-check everything | `./scripts/onboard.sh --check` |
