# Semantic layer editor

Git-first workflow for editing Wren MDL and related artifacts inside the CopilotKit UI. Plan: [006 semantic layer editor](../plans/2026-06-01-006-feat-semantic-layer-editor-plan.md).

## App views

| View | Nav | Purpose |
|------|-----|---------|
| **Chat** | Left sidebar | NL→SQL assistant (`nl2sql_assistant`) |
| **Audit logs** | Left sidebar | Query audit JSONL from S3 |
| **Semantic layer** | Left sidebar | Consumers map, file editor, validate, PR wizard, editor AI |

Routing lives in `ui/src/config.ts` (`AppView`) and `AppShell.tsx`.

## Dual agents (AG-UI)

The API mounts **two** LangGraph agents on separate paths:

| Agent ID | AG-UI path | Module | Role |
|----------|------------|--------|------|
| `nl2sql_assistant` | `POST /` | `src/ag_ui_agent.py` | Answer questions, run SQL / Wren / Cortex tools |
| `semantic_editor` | `POST /semantic-agent` | `src/semantic_editor/ag_ui_agent.py` | Propose MDL edits, search audit logs, limited Snowflake probes |

The UI uses local `HttpAgent` clients (`ui/src/lib/httpAgent.ts`, `editorHttpAgent.ts`) — not a proxied CopilotKit runtime agent. CopilotKit `/copilotkit` remains a stub for sync.

**Semantics toggle** (`off` | `wren` | `cortex`) applies only to the NL→SQL chat agent via `forwardedProps.semanticLayer`.

## Semantic REST API

All paths are under `/api/semantic/`. Path writes are allowlisted to `wren/tpch/`, `schema/`, and `semantic/` (see `src/semantic_editor/paths.py`).

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/semantic/consumers` | Which runtimes load which files + `wren_ready` / `cortex_ready` |
| GET | `/api/semantic/tree?root=` | Editable file list |
| GET | `/api/semantic/file?path=` | Read UTF-8 file |
| PUT | `/api/semantic/file?path=` | Write file (JSON body: `{ "content": "..." }`) |
| POST | `/api/semantic/validate` | Run `wren context validate` in `wren/tpch` |
| GET | `/api/semantic/pr/config` | GitHub repo/branch + token presence (never returns token) |
| GET | `/api/semantic/pr/draft` | Suggest PR title/body from git diff |
| POST | `/api/semantic/pr` | Branch, commit, push, open GitHub PR |

**Deferred:** `POST /api/semantic/rebuild` (`wren context build` + memory index).

**Env for PR flow:** `GITHUB_TOKEN`, `GITHUB_REPO`, optional `GITHUB_DEFAULT_BRANCH`.

## Editor AI tools

Defined in `src/semantic_editor/tools.py`:

| Tool | Notes |
|------|--------|
| `list_semantic_files_tool` | Tree under allowlist |
| `read_semantic_file_tool` / `write_semantic_file_tool` | Writes require user confirmation in prompt |
| `wren_validate_tool` | Same as UI validate button |
| `editor_get_schema_summary` | `schema/tpch_sf1.md` |
| `editor_execute_snowflake_sql` | SELECT only, `LIMIT ≤ 10` |
| `search_audit_logs` | Wraps `search_audit_entries()` in `src/audit_reader.py` |
| `feedback_search_stub` | Placeholder |

Audit search is available to the **agent** today. A separate `GET /api/semantic/audit-context` endpoint (plan Unit 6) is optional — the same logic can be reused inside `build_pr_draft()` when enriching PR bodies.

## Sessions and history

| Concern | Chat | Editor |
|---------|------|--------|
| Thread ID key | `ai-sql-poc-thread-id` | `ai-sql-poc-editor-thread-id` |
| Audit `source` | `api` | `semantic_editor` |
| Sidebar list | `useChatSessions` | `useEditorSessions` |
| Restore | localStorage + S3 audit (`assistant_reply`) | Same pattern |

See [chat-memory-and-sessions.md](chat-memory-and-sessions.md) and [chat-memory-and-session-learnings.md](../solutions/chat-memory-and-session-learnings.md).

## PR workflow

1. Edit files in **Semantic layer** → **Save** (writes working tree).
2. **Validate** — required before PR when Wren paths change.
3. **Pull request** panel → **Draft** → edit title/body → **Open PR**.

Backend: `src/semantic_editor/pr.py`. UI: `SemanticPrWizard` + `useSemanticPr`.

PR body includes diff stat and optional audit entry IDs. Auto-fetching recent errors by model name (Unit 6 enrichment) is not wired in the UI yet.

## Agent-native checklist

Actions an automation can take without the browser:

- [x] List/read/write semantic files via REST
- [x] Validate MDL via REST
- [x] Draft and create PR via REST (with server-side `GITHUB_TOKEN`)
- [x] Run editor agent via AG-UI at `/semantic-agent`
- [x] Search audit logs via editor tool or `GET /api/audit/logs?source=`
- [ ] `POST /api/semantic/rebuild`
- [ ] Dedicated audit-context endpoint for PR templates
- [ ] `semantic_edit` / `pr_opened` audit event types

## Local dev

Restart the API after changes to `src/semantic_editor/` or `api/main.py`:

```bash
export AWS_PROFILE="${AWS_PROFILE:-your-sso-profile-name}"
lsof -ti :8000 2>/dev/null | xargs kill 2>/dev/null; sleep 1
scripts/py -m uvicorn api.main:app --reload --port 8000
```

Semantic layer view: **http://localhost:5173** → left nav **Semantic layer**. Right column = editor AI; toggle width with the sidebar control in the header.

Related: [wren/tpch/README.md](../../wren/tpch/README.md) · [audit-logs/README.md](../audit-logs/README.md) · [api/README.md](../../api/README.md)
