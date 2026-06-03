# api/ — FastAPI AG-UI server (Phase 3B)

Exposes the Phase 2 Deep Agent to the browser via **AG-UI** (`ag-ui-langgraph`). CopilotKit in `ui/` uses a local `HttpAgent` for chat plus a small **runtime stub** for CopilotKit sync.

**Integration learnings:** [docs/solutions/copilotkit-local-ui-learnings.md](../docs/solutions/copilotkit-local-ui-learnings.md)  
**Memory & sessions:** [docs/solutions/chat-memory-and-session-learnings.md](../docs/solutions/chat-memory-and-session-learnings.md)  
**Postgres (optional):** [docs/architecture/postgres-local-dev.md](../docs/architecture/postgres-local-dev.md)  
**Query audit logs:** [docs/audit-logs/README.md](../docs/audit-logs/README.md)

## Run

From repo root (so `src/` and `config/` imports resolve):

```bash
export AWS_PROFILE=your-sso-profile-name
aws sso login --profile "$AWS_PROFILE"

# Optional — durable LangGraph checkpoints (Phase 3.6)
docker compose up -d
# Add DATABASE_URL=postgresql://ai_sql:ai_sql_dev@localhost:5432/ai_sql_poc to .env

# Wren: on startup, syncs profile + runs `wren context build` if target/mdl.json is missing
# (install: scripts/py -m pip install "wrenai[snowflake,memory]" pyyaml)
# WREN_SKIP_BOOTSTRAP=1 to disable; WREN_BOOTSTRAP_MEMORY_INDEX=1 for memory index

# Optional audit → S3 (local logs/audit/*.jsonl always)
export AUDIT_S3_BUCKET=your-org-ai-sql-audit-dev
# or add AUDIT_S3_BUCKET=... to repo-root .env (loaded on API startup)

scripts/py -m uvicorn api.main:app --reload --port 8000
```

## Endpoints

| Path | Purpose |
|------|---------|
| `GET /api/status` | UI health badge + `semantic_layer` readiness (wren / cortex) + `checkpoint.backend` + `sessions.available` + Postgres Docker hint |
| `GET /api/sessions` | SQL chat session list (Postgres `conversations`) — requires `DATABASE_URL` |
| `POST /api/sessions` | Register a new conversation row (e.g. **+ New** in UI) |
| `GET /api/sessions/{thread_id}/messages` | SQL chat transcript restore |
| `PUT /api/sessions/{thread_id}/messages` | Replace-all transcript save on UI flush (POC) |
| `GET /api/audit/logs` | Query audit JSONL for **Audit log page** (`?date=`, `?limit=`, `?thread_id=`, `?source=`) |
| `GET /api/audit/sessions` | Audit-derived session list — **editor history** and audit UI; SQL chat uses `/api/sessions` |
| `POST /` | **NL→SQL AG-UI agent** (`nl2sql_assistant`) — SSE stream |
| `POST /semantic-agent` | **Editor AG-UI agent** (`semantic_editor`) — SSE stream |
| `GET /api/semantic/*` | File tree, read/write, validate, GitHub PR draft/create — see [semantic-layer-editor.md](../docs/architecture/semantic-layer-editor.md) |
| `GET /copilotkit/info` | CopilotKit runtime info (REST transport) |
| `POST /copilotkit` | CopilotKit single-endpoint info (`{"method":"info"}`) |

The `/copilotkit` stub returns `{ "version": "0.2.0", "agents": {} }` so CopilotKit sync succeeds without replacing the local `HttpAgent` clients in `ui/`.

## Semantic layer toggle (UI)

CopilotKit sends `forwardedProps.semanticLayer` (`off` | `wren` | `cortex`) on each AG-UI run. The API injects it into `config.configurable.semantic_layer` for tool gating.

- **off** — markdown schema + `execute_snowflake_sql`
- **wren** — `wren_*` tools (see `wren/tpch/README.md`)
- **cortex** — placeholder until Semantic View + Analyst REST are wired

## Semantic layer editor

Third UI view with REST file APIs and a dedicated editor agent. Full reference: [docs/architecture/semantic-layer-editor.md](../docs/architecture/semantic-layer-editor.md).

**PR workflow env:** `GITHUB_TOKEN`, `GITHUB_REPO` in repo-root `.env`.

## Dependencies

```bash
scripts/py -m pip install -r requirements.txt
```

(from repo root, or `api/requirements.txt` which includes root deps)
