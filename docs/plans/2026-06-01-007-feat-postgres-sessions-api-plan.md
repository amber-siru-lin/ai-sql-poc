---
title: "Phase 3.6.2 — Postgres sessions & messages API"
type: feat
status: active
date: 2026-06-01
origin:
  - docs/plans/2026-05-29-004-feat-copilotkit-local-ui-plan.md
  - docs/architecture/chat-memory-and-sessions.md
  - docs/solutions/chat-memory-and-session-learnings.md
depends_on:
  - Phase 3.6.1 LangGraph Postgres checkpointer (code landed; ops often skipped)
  - PR #11 session switching (UI flush + restore)
related:
  - docs/architecture/postgres-local-dev.md
  - docs/architecture/query-and-memory-storage.md
---

# Phase 3.6.2 — Postgres sessions & messages API

## Overview

Replace **audit-derived chat UX** and **localStorage-as-authority** with a **Postgres-backed sessions + messages API** in the same database LangGraph already uses for checkpoints.

After this work:

| Concern | Before (today) | After (3.6.2) |
|---------|----------------|---------------|
| Sidebar session list | `GET /api/audit/sessions` (S3 scan) | `GET /api/sessions` (Postgres) |
| Transcript restore | localStorage → audit fallback | API first → localStorage fallback |
| Persist on chat | localStorage only | `PUT /api/sessions/{id}/messages` on flush/autosave |
| Agent follow-ups | LangGraph checkpoint (if Postgres up) | Same — unchanged |
| Compliance log | S3 audit | S3 audit — **unchanged** |

**Not in scope for 3.6.2:** auth / multi-user (`3.6.4`), context summarization (`3.6.5`), removing localStorage entirely (`3.6.6`), Wren memory changes.

---

## Problem frame

We have four “memory” mechanisms because nothing is the **source of truth for chat UX**. Session switching works (PR #11), but:

1. **Sidebar and restore still depend on S3 audit** — slow, incomplete for UI (Q&A-shaped, no tool cards).
2. **localStorage is per-browser** — not shareable, easy to lose, capped at 80 messages.
3. **Postgres is configured but often unused** — `.env` may have `DATABASE_URL`, but Docker Postgres is frequently stopped and the API falls back to `MemorySaver`.

**Observed locally (Jun 2026):**

- `.env` contains `DATABASE_URL=postgresql://ai_sql:ai_sql_dev@localhost:5432/ai_sql_poc`
- `docker compose ps` → **no running postgres container**
- `/api/status` → API offline or `checkpoint.backend: memory`

So 3.6.1 is **implemented in code** but **not operational** until Docker is up and the API restarted.

---

## Requirements trace

| ID | Requirement |
|----|-------------|
| R1 | Postgres running locally via `docker compose up -d`; API reports `checkpoint.backend: postgres` |
| R2 | App tables `conversations` + `messages` in the **same** DB as LangGraph checkpoints |
| R3 | `GET /api/sessions` — list sessions for sidebar (same shape as today’s `AuditSession` where possible) |
| R4 | `GET /api/sessions/{thread_id}/messages` — ordered transcript for restore |
| R5 | `PUT /api/sessions/{thread_id}/messages` — upsert full transcript (replace-all, idempotent) |
| R6 | `POST /api/sessions` — create/register session on **+ New** (optional title) |
| R7 | UI loads messages **API → localStorage → audit** (graceful degradation) |
| R8 | UI writes to API on `flush()` and debounced autosave (same triggers as today) |
| R9 | Sidebar uses `/api/sessions`; keep `/api/audit/sessions` for audit page only |
| R10 | Tests with mocked DB or test Postgres; no S3 required for session tests |
| R11 | `/api/status` reports `sessions.backend: postgres` when DB reachable |

**Deferred to 3.6.3+:** stop writing sidebar from audit; backfill old threads from audit/localStorage; server-side write from agent hook on each run.

---

## Scope boundaries

**In scope**

- Finish 3.6.1 ops path (document + verify script)
- SQL migration / `setup()` for app tables
- `src/chat_sessions/` module (store + pydantic models)
- FastAPI routes under `/api/sessions`
- UI: `useChatSessions`, `resolveThreadMessages`, `useActiveThreadPersistence`
- Unit/integration tests
- Update architecture + learnings docs

**Out of scope**

- OAuth / `user_id` scoping (use constant `user_id = 'local'` for POC)
- Real-time sync / websockets
- Tool-card binary storage (text-only messages, same as `StoredChatMessage`)
- CopilotKit Cloud thread sync
- Production deploy (Amplify/Lambda)

---

## Prerequisite — make Postgres actually work (3.6.1 ops)

Before building 3.6.2, confirm the foundation:

```bash
docker compose up -d
docker compose ps                    # postgres healthy
scripts/py scripts/verify_postgres_setup.py
export AWS_PROFILE=Brainfore-Team-Set-654654461736
scripts/py -m uvicorn api.main:app --reload --port 8000
curl -s http://localhost:8000/api/status | jq '.checkpoint'
# → { "backend": "postgres", "database_url_configured": true }
```

**Common failure:** Docker Desktop not running, or container stopped after reboot. `DATABASE_URL` alone does nothing if nothing listens on `:5432`.

**Decision:** 3.6.2 implementation assumes Postgres is available in dev. API startup should **fail loudly** (log + status flag) if `DATABASE_URL` is set but connection fails — optional follow-up, not blocking 3.6.2 schema work.

---

## Data model

One database (`ai_sql_poc`), two concerns:

```mermaid
erDiagram
  conversations ||--o{ messages : contains
  conversations {
    uuid thread_id PK
    text user_id
    text title
    text semantic_layer
    timestamptz created_at
    timestamptz updated_at
  }
  messages {
    uuid id PK
    uuid thread_id FK
    text role
    text content
    int seq
    timestamptz created_at
  }
```

LangGraph owns `checkpoints`, `checkpoint_blobs`, `checkpoint_writes` — do not touch.

### `conversations`

| Column | Type | Notes |
|--------|------|-------|
| `thread_id` | `UUID` PK | Same id UI sends as AG-UI `threadId` |
| `user_id` | `TEXT` NOT NULL DEFAULT `'local'` | Placeholder until 3.6.4 |
| `title` | `TEXT` | First user message truncated, or “New chat” |
| `semantic_layer` | `TEXT` | Last known mode: `off` / `wren` / `cortex` |
| `created_at` | `TIMESTAMPTZ` | |
| `updated_at` | `TIMESTAMPTZ` | Bump on each message upsert |

Index: `(user_id, updated_at DESC)` for sidebar list.

### `messages`

| Column | Type | Notes |
|--------|------|-------|
| `id` | `UUID` PK | Client-provided id (CopilotKit message id) |
| `thread_id` | `UUID` FK | |
| `role` | `TEXT` | `user` / `assistant` / `system` |
| `content` | `TEXT` | Plain text (same as `toStoredMessages`) |
| `seq` | `INT` | Order within thread (0-based) |
| `created_at` | `TIMESTAMptz` | Optional; default now |

Unique: `(thread_id, id)`. Index: `(thread_id, seq)`.

### Migration approach

**Decision:** Plain SQL file + idempotent `setup()` on API startup (matches LangGraph `checkpointer.setup()` pattern).

- Add `src/chat_sessions/schema.sql`
- Add `init_chat_sessions_from_env()` called from `api/main.py` startup (after checkpointer init)
- No Alembic for POC — keep it one file, version comment in SQL

---

## API design

Base path: `/api/sessions` (distinct from `/api/audit/sessions`).

### `GET /api/sessions?limit=40`

Response (align with UI `AuditSession`):

```json
{
  "sessions": [
    {
      "thread_id": "uuid",
      "title": "What were total sales…",
      "first_timestamp": "2026-06-01T12:00:00Z",
      "last_timestamp": "2026-06-01T12:05:00Z",
      "run_count": 3,
      "semantic_layer": "wren",
      "last_status": null
    }
  ]
}
```

- `run_count` → count of **user** messages (or total messages / 2) for display parity
- `last_status` → `null` for now (audit field; drop from UI later or map from last assistant message)

### `GET /api/sessions/{thread_id}/messages`

```json
{
  "thread_id": "uuid",
  "messages": [
    { "id": "…", "role": "user", "content": "…" }
  ]
}
```

404 if conversation never registered — UI falls back to localStorage/audit.

### `PUT /api/sessions/{thread_id}/messages`

Replace-all upsert (matches flush semantics):

```json
{
  "semantic_layer": "wren",
  "messages": [ { "id": "…", "role": "user", "content": "…" } ]
}
```

- Creates `conversations` row if missing
- Deletes existing messages for thread, inserts new set in transaction
- Cap at 80 messages server-side (match localStorage)
- Returns `{ "saved": N, "thread_id": "…" }`

### `POST /api/sessions`

Optional explicit create on **+ New**:

```json
{ "thread_id": "uuid", "semantic_layer": "off", "title": "New chat" }
```

**Decision (POC):** Replace-all `PUT` on flush/autosave — send the full message list each time. See [Before production](#before-production--change-these-poc-shortcuts).

**Decision (+ New):** `POST /api/sessions` on **+ New** so the empty thread appears in the sidebar immediately (not only after first message).

### Status extension

```json
"checkpoint": { "backend": "postgres", "database_url_configured": true },
"sessions": { "backend": "postgres", "available": true }
```

When `DATABASE_URL` unset: `"sessions": { "backend": "memory", "available": false }` — UI keeps audit/localStorage path.

---

## Backend implementation units

| Unit | Files | Notes |
|------|-------|-------|
| **U1 — Schema + init** | `src/chat_sessions/schema.sql`, `src/chat_sessions/store.py`, `src/chat_sessions/__init__.py` | Async psycopg pool or reuse checkpoint pool |
| **U2 — API routes** | `api/main.py` or `api/routes/sessions.py` | Thin handlers → store |
| **U3 — Startup wiring** | `api/main.py` | `init_chat_sessions_from_env()` after checkpointer |
| **U4 — Verify script** | `scripts/verify_postgres_setup.py` | Also check `conversations` / `messages` tables exist |

### Pool sharing decision

**Recommendation:** Separate small `AsyncConnectionPool` in `chat_sessions/store.py` (same `DATABASE_URL`). Simpler than sharing LangGraph’s pool; one extra pool is fine for POC. Revisit if connection limits become an issue.

### Error handling

- DB down + `DATABASE_URL` set → routes return 503 with clear message; UI falls back
- Invalid UUID → 400
- Empty message list on PUT → 400 (don’t wipe with empty unless explicit DELETE added later)

---

## Frontend implementation units

| Unit | Files | Notes |
|------|-------|-------|
| **U5 — Session list hook** | `ui/src/hooks/useChatSessions.ts` | Fetch `/api/sessions`; fallback to `/api/audit/sessions` if 503 or `sessions.available: false` |
| **U6 — Message resolve** | `ui/src/lib/resolveThreadMessages.ts` | Order: API → localStorage → audit |
| **U7 — Persist to API** | `ui/src/lib/chatPersistence.ts` or new `sessionApi.ts` | `saveThreadMessages` also calls PUT (fire-and-forget with console warn on fail) |
| **U8 — Types** | `ui/src/types/session.ts` | Shared session/message types (decouple from audit types over time) |
| **U9 — Status badge** | `ui/src/components/AppShell.tsx` (optional) | Show postgres sessions indicator in dev |

**Keep PR #11 invariants:** single `useSqlAgent`, no `CopilotKit threadId`, flush-before-switch, re-apply after `connectAgent` clear.

---

## Suggested build order

```mermaid
flowchart TD
  P0[0. Docker up + checkpoint postgres] --> P1[1. Schema + store module]
  P1 --> P2[2. API routes + tests]
  P2 --> P3[3. UI read path API first]
  P3 --> P4[4. UI write path on flush]
  P4 --> P5[5. Switch sidebar to /api/sessions]
  P5 --> P6[6. Docs + verify script]
```

| Phase | Deliverable | Verify |
|-------|-------------|--------|
| **0** | Postgres operational | `verify_postgres_setup.py` + status checkpoint |
| **1** | Tables + store CRUD | pytest against test DB or transactional fixtures |
| **2** | REST endpoints | curl list/get/put |
| **3** | UI read | Click session → messages from API (DevTools network) |
| **4** | UI write | New message → refresh → still there after API restart |
| **5** | Sidebar | New chats appear without S3 audit lag |
| **6** | Docs | Update learnings + postgres-local-dev |

---

## Test scenarios

### `tests/test_chat_sessions_store.py`

| Scenario | Assertion |
|----------|-----------|
| Create conversation on first message upsert | Row in `conversations` |
| Replace-all PUT | Old messages removed, new seq order correct |
| List sessions by `updated_at` | Newest first, respects `limit` |
| 80-message cap | Only last 80 stored |
| Unknown thread GET | Empty list or 404 per API contract |
| Invalid UUID | Raises / 400 |

### `tests/test_chat_sessions_api.py`

| Scenario | Assertion |
|----------|-----------|
| `GET /api/sessions` empty | `{ "sessions": [] }` |
| Round-trip PUT → GET | Messages match |
| No DATABASE_URL | Routes 503 or status `available: false` |

Use `TestClient` against a **real Postgres service** in CI (see below).

### CI testing

**Decision:** Real Postgres in GitHub Actions — not mocks.

Add a `postgres:16-alpine` service container to the `python-tests` workflow (same credentials as `docker-compose.yml`). Tests use `DATABASE_URL=postgresql://ai_sql:ai_sql_dev@localhost:5432/ai_sql_poc` (or the Actions service hostname). This catches schema/SQL/connection bugs that mocked stores miss.

| Approach | POC choice | Rationale |
|----------|------------|-----------|
| Real Postgres service in CI | **Yes** | Matches local dev; validates migrations and async pool |
| Mock store only | No | Fast but hides SQL bugs |

---

## Before production — change these POC shortcuts

Track these explicitly when moving from POC → production. They are **intentional for 3.6.2** but not production-final.

| POC choice (3.6.2) | Why it's OK now | Change before production |
|--------------------|-----------------|--------------------------|
| **Replace-all `PUT`** — full transcript on every flush/autosave | Matches localStorage today; simple, idempotent, easy to debug | **Append-only writes** (`POST` per message or batched deltas); avoid delete-all + reinsert on every autosave (write amplification, race conditions, lost concurrent edits) |
| **`user_id = 'local'`** constant | Single developer, no auth | Real auth + row-level scoping (3.6.4) |
| **localStorage fallback** on read/write failure | Graceful dev without Docker | API-only authority; localStorage optional offline cache (3.6.6) |
| **80-message cap** | Matches current browser store | Configurable retention + summarization (3.6.5) |
| **Text-only messages** (no tool-card payload) | Same as `toStoredMessages` | Structured message parts / tool results in DB if UI needs pixel-perfect replay |
| **Backfill from localStorage/audit** | One-time migration for existing dev data | Not needed in prod; use proper import pipeline |
| **Separate sessions DB pool** | Simple vs sharing LangGraph pool | Tune pool size / shared pool under load |

**Replace-all detail:** Each flush sends e.g. 40 messages even if only 1 is new. Fine for POC (small threads, debounced saves). Production should append new/changed messages only and use versioning or `updated_at` per row to detect conflicts.

---

## Why we’re not at “production” after 3.6.2

See [Before production — change these POC shortcuts](#before-production--change-these-poc-shortcuts) for intentional POC tradeoffs (including replace-all PUT).

3.6.2 gets us **one source of truth for chat UX in dev**. Still blocking production:

| Gap | Phase | Why it matters |
|-----|-------|----------------|
| No real auth / `user_id` | 3.6.4 | Everyone would see `user_id='local'` |
| localStorage still used as fallback | 3.6.6 | Offline/cache semantics not productized |
| Audit still separate | 3.6.3 | Compliance OK; no unified write path from agent |
| No deploy / SSO / multi-tenant | CTA plan | POC repo scope |
| Long-thread / summarization | 3.6.5 | Model context limits |
| Tool-card fidelity | Future | Text-only messages |
| Background runs on session switch | Session Phase 2 | Agent run lost if user switches away |

---

## Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Docker not running → dev confusion | Phase 0 checklist; status endpoint flags; AGENTS.md note |
| Dual-write (localStorage + API) drift | API is authority on read; localStorage write after successful PUT |
| S3-only dev (no DATABASE_URL) | Feature degrades gracefully to today’s behavior |
| Pool / connection exhaustion | Small pool (max 5) for sessions store |
| Breaking sidebar shape | Keep response compatible with `AuditSession` initially |

---

## Decisions (locked)

| # | Topic | Choice |
|---|-------|--------|
| 1 | Save semantics | **Replace-all PUT** on flush/autosave (POC); append-only before production — see [Before production](#before-production--change-these-poc-shortcuts) |
| 2 | + New in sidebar | **Immediately** — `POST /api/sessions` on + New |
| 3 | CI testing | **Real Postgres** service container in GitHub Actions |
| 4 | Existing history | **Backfill** from localStorage + audit |

---

## Success criteria

- [ ] `docker compose up -d` + API → `checkpoint.backend: postgres` **and** `sessions.available: true`
- [ ] Chat in browser → messages in Postgres (visible via `psql` or GET)
- [ ] API restart → sidebar + restore still work (no localStorage required for happy path)
- [ ] S3 audit still written per run (unchanged)
- [ ] `npm run build` + python tests pass
- [ ] Session switch (PR #11 behavior) still works with API-backed restore

---

## Related docs to update after implementation

- `docs/solutions/chat-memory-and-session-learnings.md`
- `docs/architecture/chat-memory-and-sessions.md`
- `docs/architecture/postgres-local-dev.md`
- `docs/architecture/query-and-memory-storage.md` (POC today column)
- `AGENTS.md` (dev server + postgres checklist)
