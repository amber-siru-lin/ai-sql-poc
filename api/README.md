# api/ — FastAPI AG-UI server (Phase 3B)

Exposes the Phase 2 Deep Agent to the browser via **AG-UI** (`ag-ui-langgraph`). CopilotKit in `ui/` uses a local `HttpAgent` for chat plus a small **runtime stub** for CopilotKit sync.

**Integration learnings:** [docs/solutions/copilotkit-local-ui-learnings.md](../docs/solutions/copilotkit-local-ui-learnings.md)

## Run

From repo root (so `src/` and `config/` imports resolve):

```bash
export AWS_PROFILE=Brainfore-Team-Set-654654461736
aws sso login --profile $AWS_PROFILE

scripts/py scripts/sync_wren_profile.py   # optional, for Wren mode
scripts/py -m uvicorn api.main:app --reload --port 8000
```

## Endpoints

| Path | Purpose |
|------|---------|
| `GET /api/status` | UI health badge + `semantic_layer` readiness (wren / cortex) |
| `POST /` | **AG-UI agent runs** (SSE stream) — used by `HttpAgent` |
| `GET /copilotkit/info` | CopilotKit runtime info (REST transport) |
| `POST /copilotkit` | CopilotKit single-endpoint info (`{"method":"info"}`) |

The `/copilotkit` stub returns `{ "version": "0.2.0", "agents": {} }` so CopilotKit sync succeeds without replacing the local `HttpAgent`.

## Semantic layer toggle (UI)

CopilotKit sends `forwardedProps.semanticLayer` (`off` | `wren` | `cortex`) on each AG-UI run. The API injects it into `config.configurable.semantic_layer` for tool gating.

- **off** — markdown schema + `execute_snowflake_sql`
- **wren** — `wren_*` tools (see `wren/tpch/README.md`)
- **cortex** — placeholder until Semantic View + Analyst REST are wired

## Dependencies

```bash
scripts/py -m pip install -r requirements.txt
```

(from repo root, or `api/requirements.txt` which includes root deps)
