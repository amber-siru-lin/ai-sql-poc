# Postgres local dev (Phase 3.6)

Run **PostgreSQL** locally for LangGraph checkpoints. One database will later hold app `sessions` / `messages` tables too (Phase 3.6.2).

**Learnings:** [chat-memory-and-session-learnings.md](../solutions/chat-memory-and-session-learnings.md)  
**Memory overview:** [chat-memory-and-sessions.md](chat-memory-and-sessions.md)

---

## What Docker Compose does here

[Docker Compose](https://docs.docker.com/compose/) runs Postgres from a small config file so you don’t install Postgres on your Mac. One command starts the database; data persists in a Docker volume until you delete it.

This repo’s `docker-compose.yml` defines a single service:

| Setting | Default |
|---------|---------|
| Image | `postgres:16-alpine` |
| Host port | `5432` |
| User / password / database | `ai_sql` / `ai_sql_dev` / `ai_sql_poc` |
| Volume | `ai_sql_pgdata` (survives `docker compose down`) |

---

## Quick start

Choose **one** path:

| Path | Best if… |
|------|----------|
| [Docker Compose](#path-a-docker-compose) | You want an isolated DB, same setup as CI/teammates |
| [Homebrew Postgres](#path-b-homebrew-no-docker) | `docker: command not found` — install Postgres directly on your Mac |

### Path A: Docker Compose

**Requires [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)** (free). After install, open Docker Desktop once so the daemon is running.

From repo root:

```bash
docker compose up -d
docker compose ps    # should show postgres healthy
```

### Path B: Homebrew (no Docker)

If `docker compose` fails with `command not found`, use Postgres via Homebrew instead. Same `DATABASE_URL` shape; only the install step differs.

```bash
brew install postgresql@16
brew services start postgresql@16

# Create role + database (matches docker-compose defaults)
/opt/homebrew/opt/postgresql@16/bin/psql postgres -c "CREATE USER ai_sql WITH PASSWORD 'ai_sql_dev' CREATEDB;" 2>/dev/null || true
/opt/homebrew/opt/postgresql@16/bin/psql postgres -c "CREATE DATABASE ai_sql_poc OWNER ai_sql;" 2>/dev/null || true
```

On Intel Macs, replace `/opt/homebrew` with `/usr/local`.

Verify:

```bash
/opt/homebrew/opt/postgresql@16/bin/psql "postgresql://ai_sql:ai_sql_dev@localhost:5432/ai_sql_poc" -c "SELECT 1"
```

Then continue with [Configure the API](#2-configure-the-api) below.

---

### 2. Configure the API

Copy env vars into repo-root `.env` (see `.env.example`):

```bash
DATABASE_URL=postgresql://ai_sql:ai_sql_dev@localhost:5432/ai_sql_poc
```

Install Python deps (if not already):

```bash
scripts/py -m pip install -r requirements.txt
```

### 3. Start the API (creates checkpoint tables)

```bash
export AWS_PROFILE=your-sso-profile-name
aws sso login --profile $AWS_PROFILE

scripts/py -m uvicorn api.main:app --reload --port 8000
```

On first startup with `DATABASE_URL` set, LangGraph runs `checkpointer.setup()` and creates tables such as `checkpoints`, `checkpoint_blobs`, `checkpoint_writes`.

### 4. Verify

```bash
scripts/py scripts/verify_postgres_setup.py
curl -s http://localhost:8000/api/status | jq '.checkpoint'
# → { "backend": "postgres", "database_url_configured": true }
curl -s http://localhost:8000/api/status | jq '.sessions'
# → { "backend": "postgres", "available": true }
curl -s http://localhost:8000/api/sessions | jq '.sessions | length'
```

---

## Without Postgres (default)

If `DATABASE_URL` is **unset**, the API uses in-memory `MemorySaver` — same as before Phase 3.6. Follow-ups are lost when uvicorn restarts. No Docker required.

---

## Commands

| Command | Effect |
|---------|--------|
| `docker compose up -d` | Start Postgres in background |
| `docker compose logs -f postgres` | Tail DB logs |
| `docker compose stop` | Stop container, keep data |
| `docker compose down` | Stop and remove container, keep volume |
| `docker compose down -v` | **Delete all checkpoint data** |

Connect with `psql`:

```bash
docker compose exec postgres psql -U ai_sql -d ai_sql_poc
```

---

## How it plugs into the app

```mermaid
flowchart LR
  DC[docker compose] --> PG[(Postgres)]
  ENV[.env DATABASE_URL] --> API[FastAPI startup]
  API --> CF[checkpoint_factory.py]
  CF --> PS[PostgresSaver + pool]
  PS --> PG
  PS --> LG[LangGraph graph]
  UI[CopilotKit UI] -->|threadId| API
```

- **`src/checkpoint_factory.py`** — opens `ConnectionPool`, `PostgresSaver.setup()`, closes pool on shutdown
- **`api/main.py`** — calls `init_checkpointer_from_env()` before `build_agent_graph(..., checkpointer=...)`
- **`src/ask_deep_agent.py`** — unchanged; CLI still uses `MemorySaver()` per run

---

## Environment variables

| Variable | Default (compose) | Purpose |
|----------|-------------------|---------|
| `POSTGRES_USER` | `ai_sql` | DB user (compose + URL) |
| `POSTGRES_PASSWORD` | `ai_sql_dev` | DB password |
| `POSTGRES_DB` | `ai_sql_poc` | Database name |
| `POSTGRES_PORT` | `5432` | Host port mapping |
| `DATABASE_URL` | — | Full URL for the API (`postgresql://…`) |

Override compose defaults by exporting vars before `docker compose up`, or use a `.env` file in the repo root (Compose reads it automatically for `${POSTGRES_*}` substitution).

---

## Next steps (Phase 3.6)

- **Done (3.6.2):** `conversations` + `messages` tables, `GET/POST /api/sessions`, `GET/PUT /api/sessions/{id}/messages`
- **Done (3.6.3 / 3.6.6):** SQL chat UX reads Postgres only — no audit or localStorage fallback for sidebar/restore
- **Done (3.6.3b):** `append_run_turn` writes user/assistant pair after each agent run (idempotent by `run_id`)
- One-time migration: legacy `localStorage` snapshots pushed on startup via `migrateLocalSnapshotsOnce()`
- Server-side backfill from audit (one-time ops): `scripts/py scripts/backfill_chat_sessions_from_audit.py`
- Keep S3 audit separate for compliance (Audit log page only)
- **Before production:** replace-all PUT → append-only writes — see [plan Phase 3.6.2](../plans/2026-06-01-007-feat-postgres-sessions-api-plan.md#before-production--change-these-poc-shortcuts)
- **Later (not chat):** optional **pgvector** in the same Postgres DB for semantic NL↔SQL recall — future replacement for Wren LanceDB memory; see [query-and-memory-storage.md § pgvector](../architecture/query-and-memory-storage.md#future-postgres--pgvector-optional-replacement-for-wren-memory)

See [CopilotKit plan Phase 3.6](../plans/2026-05-29-004-feat-copilotkit-local-ui-plan.md).

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `connection refused` on 5432 | **Docker:** `docker compose up -d`. **Homebrew:** `brew services start postgresql@16` |
| `docker: command not found` | Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) **or** use [Homebrew path](#path-b-homebrew-no-docker) |
| `checkpoint.backend` still `memory` | Set `DATABASE_URL` in `.env`; restart API |
| Port 5432 in use | `POSTGRES_PORT=5433 docker compose up -d` and use port 5433 in `DATABASE_URL` |
| Permission / auth errors | Match user/password/db in URL to compose env |
| `CREATE INDEX CONCURRENTLY` / setup fails | Connection pool needs `autocommit=True` | Fixed in `checkpoint_factory.py` via pool `configure` callback |
