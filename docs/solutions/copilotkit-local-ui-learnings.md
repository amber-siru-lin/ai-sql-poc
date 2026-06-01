---
title: CopilotKit local UI — integration learnings
date: 2026-05-30
category: frontend-integration
tags:
  - copilotkit
  - ag-ui
  - langgraph
  - fastapi
  - vite
  - phase-3
status: resolved
---

# CopilotKit local UI — integration learnings

Phase 3B wires **CopilotKit** (`ui/`) to a **FastAPI AG-UI** server (`api/`) that runs the Phase 2 Deep Agent. This doc captures errors we hit and the working pattern so we do not rediscover them.

**Related:** [CopilotKit plan](../plans/2026-05-29-004-feat-copilotkit-local-ui-plan.md) · [PHASES.md](../PHASES.md) · [Amplify blocked](./aws-amplify-cdk-bootstrap-blocked.md)

---

## Working architecture

Two HTTP surfaces on port **8000** — do not collapse them into one URL.

```
Browser (localhost:5173)
  │
  ├─ CopilotKit shell ──► POST /copilotkit  { "method": "info" }   ← runtime sync only
  │                       GET  /copilotkit/info
  │
  └─ HttpAgent (chat) ──► POST /  (AG-UI SSE stream)              ← actual agent runs
```

| URL | Consumer | Purpose |
|-----|----------|---------|
| `http://localhost:8000/` | `@ag-ui/client` `HttpAgent` | Stream agent runs (SSE) |
| `http://localhost:8000/copilotkit` | CopilotKit `runtimeUrl` | Satisfy `/info` sync; returns `{ "agents": {} }` |
| `http://localhost:8000/api/status` | UI header badge | Lightweight health check |

**Why two endpoints:** CopilotKit expects a CopilotKit-style runtime at `runtimeUrl`. Our agent speaks **AG-UI**, not CopilotKit protocol. Pointing `runtimeUrl` at `/` causes 422 on info fetch. Pointing chat at `/copilotkit` would not run the LangGraph agent.

**Working UI config** (`ui/src/App.tsx`):

```tsx
const agents = useMemo(
  () => ({
    [AGENT_ID]: new HttpAgent({
      url: API_URL,                    // http://localhost:8000
      agentId: AGENT_ID,
      fetch: (input, init) => fetch(input, init),  // required — see below
    }),
  }),
  [],
);

<CopilotKit
  runtimeUrl={COPILOT_RUNTIME_URL}     // http://localhost:8000/copilotkit
  agents__unsafe_dev_only={agents}
  agent={AGENT_ID}
>
```

Env vars (`ui/.env.example`):

```bash
VITE_API_URL=http://localhost:8000
VITE_COPILOT_RUNTIME_URL=http://localhost:8000/copilotkit
```

**Backend:** LangGraph must compile with a **checkpointer** — AG-UI calls `graph.aget_state()` during streaming.

```python
from langgraph.checkpoint.memory import MemorySaver

create_deep_agent(..., checkpointer=MemorySaver())
```

See `src/agent_factory.py` and `api/main.py`.

---

## Run (both terminals)

```bash
export AWS_PROFILE=Brainfore-Team-Set-654654461736
aws sso login --profile $AWS_PROFILE

# Terminal 1 — API
cd ~/Documents/GitHub/personal_build
scripts/py -m uvicorn api.main:app --reload --port 8000

# Terminal 2 — UI
cd ui && npm run dev
```

Open **http://localhost:5173** (use the port Vite prints). Header should show **API connected**.

---

## Errors and fixes

### 1. Blank page — `Agent 'nl2sql_assistant' not found`

**Symptom:** Empty `#root`; console: `useAgent: Agent 'nl2sql_assistant' not found after runtime sync`.

**Cause:** CopilotKit `runtimeUrl` pointed at AG-UI `/`. Python CopilotKit SDK returns `agents` as an **array**; JS client expects an **object map**. `Object.entries(array)` registered agent id `"0"` instead of `nl2sql_assistant`.

**Fix:** Use `agents__unsafe_dev_only` with a local `HttpAgent` for chat. Do not rely on runtime `/info` for agent discovery.

---

### 2. `Missing required prop: 'runtimeUrl' or 'publicApiKey'`

**Symptom:** Error boundary: missing `runtimeUrl` / `publicApiKey`.

**Cause:** v1 `CopilotKit` wraps `CopilotKitInternal`, which **always** validates `runtimeUrl` or API key — even when local agents are set (`agents__unsafe_dev_only` only satisfies the inner v2 provider).

**Fix:** Set `runtimeUrl={COPILOT_RUNTIME_URL}` to the **`/copilotkit` stub**, not the AG-UI root.

---

### 3. `Runtime info request failed with status 422`

**Symptom:** Banner on load; `runtime_info_fetch_failed`; context `runtimeUrl: http://localhost:8000`.

**Cause:** CopilotKit POSTs `{ "method": "info" }` to `runtimeUrl`. AG-UI at `/` expects a full run payload → FastAPI **422**.

**Fix:** Add stub routes in `api/main.py`:

- `GET /copilotkit/info`
- `POST /copilotkit` with `{ "method": "info" }` → `{ "version": "0.1.0", "agents": {} }`

Empty `agents` keeps the local `HttpAgent` in control (remote agents would overwrite via spread order in CopilotKit core).

---

### 4. `Failed to execute 'fetch' on 'Window': Illegal invocation`

**Symptom:** Chat send fails; `agent_run_failed`; `Illegal invocation` in stack (`@ag-ui/client`).

**Cause:** `HttpAgent` stores global `fetch` and calls `this.fetch(url, opts)`. Browser `fetch` must not be invoked with a wrong `this`.

**Fix:**

```tsx
fetch: (input, init) => fetch(input, init),
```

---

### 5. `network error` (misleading)

**Symptom:** `agent_run_failed` / `TypeError: network error`; DevTools: `ERR_INCOMPLETE_CHUNKED_ENCODING` on `POST /`.

**Cause:** Not CORS or connectivity — API returned **200** then **crashed mid-SSE**:

```text
ValueError: No checkpointer set
  at ag_ui_langgraph/agent.py → graph.aget_state(config)
```

**Fix:** Pass `checkpointer=MemorySaver()` in `build_agent_graph()` (`src/agent_factory.py`). In-memory is fine for local POC; use persistent checkpointer for production threads.

---

## CopilotKit vs AG-UI — mental model

| Layer | Package / path | Role |
|-------|----------------|------|
| Chat chrome | `@copilotkit/react-ui` `CopilotSidebar` | Input, messages, dev console |
| Agent wiring | `@copilotkit/react-core` + `agents__unsafe_dev_only` | Registers local `HttpAgent` |
| Transport | `@ag-ui/client` `HttpAgent` | POST + SSE to FastAPI |
| Server | `ag-ui-langgraph` + `api/main.py` | LangGraph Deep Agent stream |

We do **not** use the Python `copilotkit` SDK endpoint for chat in the MVP. That path had `/info` format mismatch with the JS client.

---

## Dev tips

| Topic | Note |
|-------|------|
| **Error boundary** | `ui/src/ErrorBoundary.tsx` surfaces React crashes instead of a blank page |
| **Port** | Vite defaults to **5173**; bookmark the URL Vite prints |
| **API reload** | `uvicorn --reload` picks up `api/` and `src/` changes; restart if chat still fails after checkpointer fix |
| **CORS** | `api/main.py` allows any `localhost` / `127.0.0.1` port in dev |
| **SSO** | Agent still needs Bedrock; run `aws sso login` before testing SQL questions |
| **Duplicate `@ag-ui/client`** | CopilotKit and direct dep may diverge; `agents as never` in TS if types conflict |

---

## Still TODO (Phase 3.3+)

- Wire `useRenderToolCall` for `execute_snowflake_sql` / `get_schema_summary`
- Replace placeholder panels (SQL preview, results table, agent steps)
- Session reset UI
- Optional: deploy `ui/` + `api/` when AWS path unblocks

---

## Related files

| Path | Role |
|------|------|
| `ui/src/App.tsx` | CopilotKit provider, HttpAgent, runtimeUrl |
| `ui/src/config.ts` | `API_URL`, `COPILOT_RUNTIME_URL`, `AGENT_ID` |
| `api/main.py` | AG-UI at `/`, CopilotKit stub at `/copilotkit` |
| `src/agent_factory.py` | Shared graph + `MemorySaver` checkpointer |
| `ui/README.md` | UI run instructions |
| `api/README.md` | API endpoints |
