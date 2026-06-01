# ui/ — CopilotKit chat UI (Phase 3B)

React + **Vite** frontend with a Cursor-style layout: left controls, center chat, right context.

Requires the Python API in `../api/` on port **8000**.

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

**Wren mode:** API `/api/status` must show `wren_ready: true`. From repo root: `scripts/py scripts/sync_wren_profile.py`, then `cd wren/tpch && wren context build && wren memory index`. Toggle **Semantics → Wren** in the left sidebar (starts a new LangGraph thread when the mode changes).

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
| Query audit log viewer | Left sidebar → **Audit logs** — see [audit-logs/README.md](../docs/audit-logs/README.md) |
| Chat history list (left sidebar) | Done — grouped from audit log + local message cache |

Plan: [docs/plans/2026-05-29-004-feat-copilotkit-local-ui-plan.md](../docs/plans/2026-05-29-004-feat-copilotkit-local-ui-plan.md)

**Where queries & memory are stored:** [docs/architecture/query-and-memory-storage.md](../docs/architecture/query-and-memory-storage.md) · [Chat memory & sessions](../docs/architecture/chat-memory-and-sessions.md)
