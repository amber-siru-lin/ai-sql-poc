# Chat memory and sessions

How conversations, threads, and history work in this POC — and how that differs from audit logging and Wren semantic memory.

**See also:** [query-and-memory-storage.md](query-and-memory-storage.md) (full storage map) · [audit-logs/README.md](../audit-logs/README.md) · [agent-error-handling.md](agent-error-handling.md)

---

## Terms (don’t conflate these)

| Term | What it is | Example in this repo |
|------|------------|----------------------|
| **Thread** | One conversation keyed by a UUID | `24b28d33-3ca2-425e-8212-dccc30ea568c` |
| **Session (UI)** | A thread the user can pick from **Chat history** | Listed from Postgres `GET /api/sessions` |
| **Chat memory** | What the agent uses for **follow-ups** (“same but by region”) | LangGraph checkpointer + message list |
| **Chat transcript** | **Display** copy of messages for restore | Postgres `messages` table (+ UI flush via PUT) |
| **Audit log** | **Compliance / debug** record per agent run | S3 `audit/YYYY/MM/DD/{thread_id}/{run_id}.json` |
| **Wren memory** | **Semantic** NL↔SQL recall for similar questions | `wren memory index` → LanceDB under `wren/tpch/target/` |

Chat memory, Postgres transcripts, audit, and Wren memory are **four different stores** with different lifetimes and purposes.

---

## End-to-end flow

```mermaid
sequenceDiagram
  participant User
  participant UI as CopilotKit UI
  participant PG as Postgres
  participant API as FastAPI / LangGraph
  participant S3 as S3 audit

  User->>UI: Ask question
  UI->>API: AG-UI run (threadId, semanticLayer)
  API->>API: Postgres checkpointer for thread_id
  API->>S3: audit JSON (question, SQL, timing)
  API->>PG: append_run_turn (user + assistant)
  API-->>UI: Stream assistant + tool cards
  UI->>PG: PUT messages on flush (replace-all POC)

  User->>UI: Click past session in sidebar
  UI->>PG: GET /api/sessions/{id}/messages
  UI->>UI: agent.setMessages(restored)
  UI->>API: Next message uses same thread_id
```

---

## Thread ID lifecycle

| Event | What happens to `thread_id` |
|-------|----------------------------|
| First visit | New UUID; stored in `localStorage` (`ai-sql-poc-thread-id`) |
| **+ New** (sidebar) | New UUID; old server checkpoint stays until process exit or Postgres retention |
| **Chat history** click | Reuses that session’s UUID; UI restores messages from Postgres |
| **Semantics** toggle (Off / Wren / Cortex) | New UUID (new LangGraph context for the mode) |
| API restart | Same UUID in browser, but **server follow-up memory is empty** |

The thread ID is the join key across UI, LangGraph, retry policy, and audit.

---

## Where each layer lives

### 1. Server follow-up memory (LangGraph)

| | |
|--|--|
| **Code** | `MemorySaver()` (default) or `AsyncPostgresSaver` via `src/checkpoint_factory.py` when `DATABASE_URL` is set |
| **Key** | `config.configurable.thread_id` (from AG-UI / `HttpAgent`) |
| **Survives** | Browser refresh **if** same thread id **and** API still running; **API restart** only with Postgres |
| **Lost when** | uvicorn restart with MemorySaver; deploy without durable checkpointer |

This is what lets the model answer “now filter that to 2024” without you repeating the first question. With `DATABASE_URL` set, checkpoints survive API restart.

### 2. Postgres chat transcript (UI restore + sidebar)

| | |
|--|--|
| **Code** | `src/chat_sessions/store.py`, `src/chat_sessions/routes.py`, `ui/src/lib/sessionApi.ts` |
| **Tables** | `conversations`, `messages` (same DB as LangGraph checkpoints) |
| **Read** | `GET /api/sessions`, `GET /api/sessions/{id}/messages` |
| **Write** | UI flush → `PUT /api/sessions/{id}/messages` (replace-all POC); agent run → `append_run_turn` |
| **Limit** | Last **80** messages per thread |
| **Survives** | API restart, browser refresh (when Postgres available) |

Legacy `localStorage` snapshots are migrated once on startup, then deleted. SQL chat does **not** read audit for restore.

### 3. Chat history list (sidebar)

| | |
|--|--|
| **API** | `GET /api/sessions` → Postgres `conversations` ordered by `updated_at` |
| **UI** | `ui/src/components/ChatHistoryList.tsx`, `ui/src/hooks/useChatSessions.ts` |
| **Title** | First user message (or `title` column) |
| **Fallback** | Clear error if Postgres unavailable — no audit fallback for SQL chat |

### 4. Query audit (per run, not full transcript)

| | |
|--|--|
| **Code** | `src/audit_logger.py`, `src/ag_ui_agent.py` |
| **Primary store** | S3 (see [audit-logs/README.md](../audit-logs/README.md)) |
| **Per run** | `question`, `semantic_layer`, `sql_executions`, `duration_ms`, `status` |
| **Not stored** | Full assistant prose, full result rows, tool UI state |

Audit is for the **Audit logs** page and compliance — not SQL chat restore (since 3.6.3).

### 5. SQL retry state (per thread, ephemeral)

| | |
|--|--|
| **Code** | `src/semantic_layer/retry_policy.py` → `_SESSION` |
| **Purpose** | Max 3 SQL attempts, detect repeated errors |
| **Lost when** | API restart |

### 6. Wren semantic memory (optional, Wren mode only)

| | |
|--|--|
| **Code** | `wren_memory_fetch` in `src/tools/wren_tools.py` |
| **Store** | `wren/tpch/target/` after `wren memory index` |
| **Purpose** | Retrieve similar past **questions/SQL** for the semantic layer |
| **Not** | Full chat history or user sessions |

---

## UI surfaces

| Surface | Role |
|---------|------|
| **Left sidebar → Chat history** | Pick a past thread; **+ New** starts fresh |
| **Right sidebar → Session** | Current thread id, message count, clear chat, memory explainer |
| **Left sidebar → Audit logs** | Inspect runs (SQL, timing, errors) — not the chat UX |

`ActiveThreadFlushBridge` saves the outgoing thread **before** `threadId` changes. `ChatPane` loads from Postgres via `resolveThreadMessages`, then `setMessages()`. Re-clicking a session reloads from API.

---

## Key files

```
src/agent_factory.py              # MemorySaver checkpointer
src/ag_ui_agent.py                # thread_id + audit + append_run_turn after each run
src/chat_sessions/store.py        # conversations, messages, append_run_turn
src/chat_sessions/routes.py       # /api/sessions
src/semantic_layer/retry_policy.py
src/audit_logger.py / audit_reader.py
api/main.py                       # /api/audit/sessions, /api/audit/logs

ui/src/App.tsx                    # selectThread: flush → set threadId; HttpAgent injects thread per request
ui/src/lib/httpAgent.ts           # threadId on each AG-UI request
ui/src/lib/chatPersistence.ts
ui/src/lib/resolveThreadMessages.ts
ui/src/components/ChatPane.tsx
ui/src/components/ActiveThreadFlushBridge.tsx
ui/src/components/ChatHistoryList.tsx
ui/src/hooks/useActiveThreadPersistence.ts
ui/src/hooks/useChatSession.ts
```

---

## POC limitations (intentional)

1. **Replace-all PUT on flush** — full transcript rewrite on tab switch; append-only before production (3.6.7).
2. **Postgres required for chat history** — without `DATABASE_URL`, sidebar shows an error (no audit fallback for SQL chat).
3. **Audit ≠ transcript** — audit page is run-oriented; chat restore uses Postgres `messages`.
4. **Semantic mode change = new thread** — Off/Wren/Cortex don’t share one LangGraph checkpoint.
5. **80-message cap** per thread in Postgres.
6. **Editor chat** still uses audit + localStorage — not yet migrated (3.6.3 pattern for editor is future work).

---

## Troubleshooting

| Symptom | Likely cause | What to check |
|---------|--------------|---------------|
| Follow-up ignores prior answer | API restarted without Postgres | `/api/status` → `checkpoint.backend: postgres` |
| Sidebar empty | Postgres down or no sessions yet | `docker compose up -d`, `DATABASE_URL`, restart API; click **+ New** |
| Old messages missing after session click | Outgoing thread not flushed before switch | Fixed: flush before `threadId` change; re-click session |
| Session in sidebar but empty chat | No rows in `messages` for that thread | Run backfill script or ask a new question (server append writes on run) |

---

## Roadmap (CTA / production-shaped)

From [query-and-memory-storage.md](query-and-memory-storage.md):

1. **Durable checkpointer** — Postgres via Docker Compose when `DATABASE_URL` is set ([postgres-local-dev.md](postgres-local-dev.md)). CLI still uses MemorySaver.
2. **Server-side session store** — relational `sessions` + `messages` (**3.6.2 — done**).
3. **Chat UX from Postgres only** — ✅ 3.6.3 / 3.6.6 done; S3 only for Audit log page.
4. **User-scoped history** — auth + row-level security; no cross-user session leakage (3.6.4).
5. **Semantic NL↔SQL recall (optional)** — Postgres **[pgvector](https://github.com/pgvector/pgvector)** for verified question→SQL examples, as a future replacement for Wren’s on-disk memory index — **not** the same as chat `messages`; see [query-and-memory-storage.md § Wren semantic memory](query-and-memory-storage.md#future-postgres--pgvector-optional-replacement-for-wren-memory).

**Learnings doc:** [chat-memory-and-session-learnings.md](../solutions/chat-memory-and-session-learnings.md)

---

## Related docs

- [query-and-memory-storage.md](query-and-memory-storage.md) — POC vs CTA storage matrix
- [postgres-local-dev.md](postgres-local-dev.md) — Docker Compose + `DATABASE_URL`
- [audit-logs/README.md](../audit-logs/README.md) — S3 audit setup and record shape
- [copilotkit-local-ui-learnings.md](../solutions/copilotkit-local-ui-learnings.md) — AG-UI, checkpointer, UI pitfalls
- [chat-memory-and-session-learnings.md](../solutions/chat-memory-and-session-learnings.md) — session switching pitfalls and fixes
