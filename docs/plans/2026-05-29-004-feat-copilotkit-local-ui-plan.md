# Plan: Phase 3 via CopilotKit (local full-stack UI)

**Date:** 2026-05-29  
**Status:** MVP scaffolded (`ui/` + `api/`). Placeholder panels for SQL preview, results table, and verbose tool steps.  
**Goal:** Browser chat UI for NL→SQL without AWS deploy permissions.

---

## Why CopilotKit

| Need | CopilotKit fit |
|------|----------------|
| Chat UI with streaming + tool visibility | `@copilotkit/react-ui` (`CopilotSidebar`) |
| LangChain / Deep Agents backend | Official integration via AG-UI + `LangGraphAGUIAgent` |
| No CDK bootstrap | Runs locally: Vite + FastAPI |
| Phase 2 agent reuse | Wrap existing Deep Agent graph / tools |
| Generative UI (SQL table, charts later) | `useRenderTool`, `useComponent` |

References:

- [LangChain × CopilotKit](https://docs.langchain.com/oss/python/langchain/frontend/integrations/copilotkit)
- [Deep Agents + CopilotKit blog](https://www.copilotkit.ai/blog/how-to-build-a-frontend-for-langchain-deep-agents-with-copilotkit)
- [CopilotKit GitHub](https://github.com/CopilotKit/CopilotKit)

---

## Where it goes in the repo

Keep **Python core unchanged** in `src/`. Add two new top-level folders. **Do not** mix into `web/amplify/`.

```
ai-sql-poc/
├── src/                    # Phase 1 + 2 — shared logic (nl2sql, tools, agent)
├── web/                    # PARKED — Amplify Gen 2 scaffold only
├── ui/                     # NEW — CopilotKit + Vite + React
│   ├── src/
│   │   ├── App.tsx         # CopilotKit provider + sidebar
│   │   └── components/     # SQL table, loading states (generative UI)
│   ├── package.json
│   └── vite.config.ts      # dev proxy optional
├── api/                    # NEW — FastAPI AG-UI server
│   ├── main.py             # uvicorn entry, CORS, health
│   ├── agent.py            # builds graph; imports src.tools.*
│   └── requirements.txt    # fastapi, uvicorn, copilotkit, ag-ui-langgraph, …
├── config/                 # local Snowflake (unchanged)
├── schema/                 # tpch_sf1.md (unchanged)
└── docs/
```

### Why `ui/` + `api/` (not inside `web/`)

| Option | Verdict |
|--------|---------|
| **`ui/` + `api/`** | **Recommended** — clean split; `web/` stays frozen Amplify experiment |
| CopilotKit inside `web/` | Conflicts with Amplify deps, CDK, `amplify/` folder |
| Next.js monorepo | CopilotKit docs favor Next.js API routes; extra migration cost vs Vite |
| Single FastAPI serves built `ui/dist` | Good for **production** deploy later; start with two dev servers |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  ui/  (Vite, port 5173)                                 │
│  CopilotSidebar + generative UI for SQL results         │
│  CopilotKit runtimeUrl → http://localhost:8000/       │
└──────────────────────────┬──────────────────────────────┘
                           │ AG-UI / CopilotKit protocol
┌──────────────────────────▼──────────────────────────────┐
│  api/  (FastAPI, port 8000)                             │
│  add_langgraph_fastapi_endpoint(LangGraphAGUIAgent)     │
│  imports src.tools.snowflake_tools + Deep Agent graph   │
└──────────────────────────┬──────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
   Bedrock (Nova)    Snowflake TPCH     schema/tpch_sf1.md
   via SSO creds     via config/        (bundled in prompt)
```

**Auth:** Same as Phase 1/2 — `export AWS_PROFILE=...` + `aws sso login` on the machine running `api/`. No Lambda yet.

---

## Implementation phases

### Phase 3.1 — Scaffold (½ day)

1. Create `api/` with FastAPI hello + `/health`.
2. Create `ui/` via `npm create vite@latest ui -- --template react-ts`.
3. Install CopilotKit packages in `ui/`:
   ```bash
   npm install @copilotkit/react-core @copilotkit/react-ui
   ```
4. Install Python deps in `api/requirements.txt`:
   ```text
   fastapi
   uvicorn[standard]
   copilotkit
   ag-ui-langgraph
   python-dotenv
   ```
   Plus existing repo deps (`langchain-aws`, `deepagents`, `snowflake-connector-python`, …) — or install from root `requirements.txt`.

5. Add npm scripts at repo root (optional `package.json` or document in README):
   ```bash
   # terminal 1
   export AWS_PROFILE=Brainfore-Team-Set-654654461736 && aws sso login
   scripts/py -m uvicorn api.main:app --reload --port 8000

   # terminal 2
   cd ui && npm run dev
   ```

### Phase 3.2 — Wire Deep Agent (1 day)

1. Extract agent build from `src/ask_deep_agent.py` into `api/agent.py` (or `src/agent_graph.py` imported by both CLI and API).
2. Register graph with CopilotKit:
   ```python
   from copilotkit import LangGraphAGUIAgent
   from ag_ui_langgraph import add_langgraph_fastapi_endpoint

   add_langgraph_fastapi_endpoint(
       app=app,
       agent=LangGraphAGUIAgent(
           name="nl2sql_assistant",
           description="Snowflake TPCH analyst — NL to SQL with tool calls",
           graph=agent_graph,
       ),
       path="/",
   )
   ```
3. Enable CORS on FastAPI for `http://localhost:5173`.
4. In `ui/src/App.tsx`:
   ```tsx
   <CopilotKit runtimeUrl="http://localhost:8000/" agent="nl2sql_assistant">
     <CopilotSidebar />
   </CopilotKit>
   ```
   Use **full URL** with Vite (not relative `/api/copilotkit` — that pattern is Next.js-specific).

5. Verify: ask *What is the total amount of all orders?* — should match CLI Phase 2.

### Phase 3.3 — Generative UI (1 day)

1. **`useRenderTool`** — custom card for `execute_snowflake_sql` (show SQL + row preview + errors).
2. **`useRenderTool`** — schema lookup for `get_schema_summary`.
3. Optional: **`useCopilotReadable`** — expose current dataset context to the agent.
4. Match Phase 2 `--verbose` behavior in the UI (tool steps visible in chat).

### Phase 3.4 — Polish & docs (½ day)

1. Loading states, error toasts, `clear conversation` button.
2. Update `docs/PHASES.md` — Phase 3 active track = CopilotKit.
3. `.gitignore`: `ui/node_modules/`, `ui/dist/`.
4. README run commands for `ui/` + `api/`.

### Phase 3.5 — Deploy (later, when AWS unblocks)

Options (pick one when ready):

| Deploy target | Notes |
|---------------|-------|
| **Single container** | FastAPI serves `ui/dist` + agent endpoint |
| **Amplify Hosting + Lambda** | Revisit when CDK bootstrap fixed |
| **Railway / Render / Fly** | FastAPI + static UI; Bedrock via IAM role on host |

Not in scope until local path works.

### Phase 3.6 — Durable chat memory & sessions

**Master roadmap:** [2026-06-01-008-feat-memory-architecture-roadmap-plan.md](./2026-06-01-008-feat-memory-architecture-roadmap-plan.md) (memory types, CopilotKit rules, PR sequence).

Apply production patterns incrementally while staying local-first. Full context: [chat-memory-and-sessions.md](../architecture/chat-memory-and-sessions.md).

| Step | What | Why | Status |
|------|------|-----|--------|
| **3.6.1** | LangGraph Postgres checkpointer | Follow-ups survive API restart | ✅ Code — [postgres-local-dev.md](../architecture/postgres-local-dev.md) |
| **3.6.2** | Server-side sessions API | Source of truth for sidebar + transcript | ✅ [PR #14](https://github.com/amber-siru-lin/ai-sql-poc/pull/14) |
| **3.6.3** | **Audit out of chat UX** | S3 → Audit log page only | ✅ Done (PR #14) |
| **3.6.6** | **Postgres-only chat path** | Drop localStorage authority | ✅ Done (PR #14) |
| **3.6.3b** | Server-side message write on agent run | Postgres even if UI flush fails | ✅ Done (PR #14) |
| **3.6.4** | User / tenant scoping | `user_id` on sessions | Planned |
| **3.6.5** | Context window / summaries | Long threads | Planned |
| **3.6.7** | Append-only message API | Pre-production (replace replace-all PUT) | Planned |
| **3.7** | pgvector semantic examples | Optional Wren memory replacement | Long-term |

**Target stack:** Postgres (checkpoints + chat + future pgvector) · S3 audit (compliance page only) · Wren LanceDB until 3.7.

**CopilotKit:** self-hosted HttpAgent + Postgres sessions — no Cloud thread sync. Invariants: [session learnings](../solutions/chat-memory-and-session-learnings.md).

**Done in POC (Jun 2026):** session switch (PR #11), Postgres sessions API + Postgres-only chat path + server-side append (PR #14).

---

## Risks & mitigations

| Risk | Mitigation |
|------|------------|
| `create_deep_agent` may not expose LangGraph directly | Use LangChain CopilotKit middleware docs; or refactor to explicit LangGraph `StateGraph` |
| CopilotKit version churn | Pin versions in `ui/package.json`; note in plan when upgrading |
| CORS / wrong `runtimeUrl` | Full URL to FastAPI; test with browser network tab |
| Package weight | Same as Phase 2 CLI — already works locally |
| Two dev servers | Document clearly; optional `concurrently` script later |

---

## Success criteria

- [x] `ui/` + `api/` run locally with SSO (no CDK bootstrap)
- [x] Chat answers TPCH questions (Deep Agent via AG-UI)
- [x] Tool calls visible in UI (SQL execution steps) — Phase 3.3 (inline chat cards)
- [x] Session clear + memory explanation — Phase 3.4
- [x] Phase 1/2 CLI scripts still work unchanged
- [x] `web/` Amplify scaffold untouched (parked)

---

## Implementation learnings (May 2026)

After wiring the MVP, several non-obvious integration issues appeared (blank page, 422 on `/info`, `Illegal invocation`, misleading `network error` from missing LangGraph checkpointer). **Full write-up:** [CopilotKit local UI learnings](../solutions/copilotkit-local-ui-learnings.md).

Key pattern: **two URLs on port 8000** — `HttpAgent` → `POST /` (AG-UI), `runtimeUrl` → `/copilotkit` (empty agents stub).

---

## Related docs

- [CopilotKit local UI learnings](../solutions/copilotkit-local-ui-learnings.md) — errors, fixes, architecture
- [Amplify CDK blocker](../solutions/aws-amplify-cdk-bootstrap-blocked.md)
- [PHASE3-AMPLIFY-GETTING-STARTED.md](../PHASE3-AMPLIFY-GETTING-STARTED.md) (parked path)
- [PHASES.md](../PHASES.md)
- [Deep Agents plan](2026-05-29-003-feat-deep-agents-nl2sql-upgrade-plan.md)
