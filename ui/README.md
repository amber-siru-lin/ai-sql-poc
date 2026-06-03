# ui/ — CopilotKit UI (Phase 3B)

React + **Vite** frontend with a Cursor-style layout: left controls, center content, right context (chat or editor AI).

Requires the Python API in `../api/` on port **8000** (or `VITE_API_URL` in `.env.local`).

## Run

```bash
# Terminal 1 — API
export AWS_PROFILE=Brainfore-Team-Set-654654461736
aws sso login --profile $AWS_PROFILE
cd ~/Documents/GitHub/personal_build
scripts/py -m uvicorn api.main:app --reload --port 8000

# Terminal 2 — UI
cd ui
npm install
npm run dev
```

Open http://localhost:5173/

**Wren mode:** API `/api/status` must show `wren_ready: true`. Local API startup runs `sync_wren_profile.py` + `wren context build` when `target/mdl.json` is missing (needs `wren` on PATH + `config/snowflake_config.py`). Optional: `wren memory index` or `WREN_BOOTSTRAP_MEMORY_INDEX=1`. See [wren/tpch/README.md](../wren/tpch/README.md). Toggle **Semantics → Wren** in the left sidebar (starts a new LangGraph thread when the mode changes).

## App views

| View | Center | Right column |
|------|--------|--------------|
| **Chat** | Chat transcript | SQL Assistant (`nl2sql_assistant` → `POST /`) |
| **Audit logs** | Audit table | — |
| **Semantic layer** | Consumers + file editor + validate + PR | Editor AI (`semantic_editor` → `POST /semantic-agent`) |

Editor session history appears in the left sidebar on the Semantic layer view (same audit + localStorage pattern as chat). Toggle the right sidebar width from the header on Chat and Semantic views.

Architecture: [docs/architecture/semantic-layer-editor.md](../docs/architecture/semantic-layer-editor.md)

## Config

Copy `.env.example` to `.env.local` if the API runs on a different host:

```
VITE_API_URL=http://localhost:8000
VITE_COPILOT_RUNTIME_URL=http://localhost:8000/copilotkit
```

**Troubleshooting:** [docs/solutions/copilotkit-local-ui-learnings.md](../docs/solutions/copilotkit-local-ui-learnings.md)

## Feature status

| Area | Status |
|------|--------|
| Three-column layout + dark theme | Done |
| CopilotKit chat → Deep Agent (AG-UI) | Done |
| Tool cards in chat (Snowflake, Wren, schema) | Done |
| Collapsible thinking + compact intermediate steps | Done |
| Session panel (clear chat, memory explanation) | Done (Phase 3.4) |
| SQL preview / results side panels | Removed (results live in chat) |
| Query audit log viewer | Left sidebar → **Audit logs** — filter by source (`api`, `semantic_editor`, `cli`) |
| Chat history list (left sidebar) | Done — grouped from audit log + local message cache |
| Semantic layer editor | **Semantic layer** view — file tree, validate, PR wizard, editor AI + history |

Plan: [docs/plans/2026-05-29-004-feat-copilotkit-local-ui-plan.md](../docs/plans/2026-05-29-004-feat-copilotkit-local-ui-plan.md) · Semantic editor: [006 plan](../docs/plans/2026-06-01-006-feat-semantic-layer-editor-plan.md)

**Where queries & memory are stored:** [docs/architecture/query-and-memory-storage.md](../docs/architecture/query-and-memory-storage.md) · [Chat memory & sessions](../docs/architecture/chat-memory-and-sessions.md)
