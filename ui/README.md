# ui/ — CopilotKit chat UI (Phase 3B)

React + **Vite** frontend with [CopilotKit](https://docs.copilotkit.ai) sidebar chat.

Requires the Python API in `../api/` running on port **8000**.

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

Open http://localhost:5173 — chat panel on the right, placeholder panels on the left.

**Wren mode:** API `/api/status` must show `wren_ready: true`. From repo root: `scripts/py scripts/sync_wren_profile.py`, then `cd wren/tpch && wren context build`. Toggle **Semantics → Wren** in the header (chat remounts when you switch modes).

## Config

Copy `.env.example` to `.env.local` if the API runs on a different host:

```
VITE_API_URL=http://localhost:8000
VITE_COPILOT_RUNTIME_URL=http://localhost:8000/copilotkit
```

**Troubleshooting:** [docs/solutions/copilotkit-local-ui-learnings.md](../docs/solutions/copilotkit-local-ui-learnings.md)

## MVP vs upcoming

| Area | Status |
|------|--------|
| CopilotKit sidebar chat | MVP |
| Deep Agent via AG-UI | MVP |
| Tool cards: Snowflake SQL + Wren run/dry-plan/memory | MVP |
| SQL preview panel | Placeholder |
| Results table panel | Placeholder |
| Agent steps / verbose tools | Placeholder (Phase 3.3) |
| Session reset UI | Placeholder (Phase 3.4) |

Plan: [docs/plans/2026-05-29-004-feat-copilotkit-local-ui-plan.md](../docs/plans/2026-05-29-004-feat-copilotkit-local-ui-plan.md)

Learnings (errors + fixes): [docs/solutions/copilotkit-local-ui-learnings.md](../docs/solutions/copilotkit-local-ui-learnings.md)
