---
title: "Semantic layer editor (UI page + PR workflow + editor AI)"
type: feat
status: active
implementation: planned
date: 2026-06-01
origin:
  - User request — third app view beside Chat and Audit logs
depends_on:
  - Phase 3B CopilotKit UI (`ui/`, `api/main.py`)
  - Phase 4 Wren MDL (`wren/tpch/`)
  - Query audit log (`src/audit_logger.py`, `GET /api/audit/*`)
  - Semantic layer toggle (plan 005 — Off / Wren / Cortex)
related:
  - docs/plans/2026-06-01-005-feat-copilotkit-semantic-layer-toggle-plan.md
  - docs/architecture/query-and-memory-storage.md
  - docs/architecture/chat-memory-and-sessions.md
  - docs/audit-logs/README.md
  - wren/tpch/README.md
---

# Semantic layer editor (UI page + PR workflow + editor AI)

## Overview

Add a third **AppView** — **Semantic layer** — alongside **Chat** and **Audit logs**. On this page the user can:

1. **See consumers** — which runtime paths read the semantic layer today (Wren MDL, Cortex Semantic View stub, Off-mode markdown schema).
2. **Edit artifacts** — relationship files, model `metadata.yml`, project config, and (later) Cortex YAML / business glossary.
3. **Validate and preview** — run `wren context validate` / dry-plan against sample SQL before shipping.
4. **Open a PR** — branch + commit + GitHub PR with a generated title/body grounded in the diff and audit context.
5. **Use an editor AI** — a dedicated CopilotKit (or AG-UI) agent with tools for schema, audit history, and (future) feedback logs — separate from the NL→SQL chat agent.

This plan is **product + architecture** for the POC repo. It does not replace Wren’s product UI or Snowflake’s Semantic View editor; it is a **git-first, PR-first** workflow aligned with how semantics already live in this repo.

---

## Problem frame

Today semantics are edited only on disk (`wren/tpch/`, `schema/tpch_sf1.md`) and activated via the sidebar **Semantics** toggle. There is no in-app map of “who uses this file,” no guided edit flow, and no link from failed chat queries to a modeling fix that becomes a reviewable PR.

The NL→SQL **Chat** agent is optimized for answering questions, not for safe bulk YAML edits. A separate **editor agent** with different tools, prompts, and guardrails avoids conflating “run this query” with “change the join condition.”

---

## What exists today (integration points)

| Concern | Today | Editor page should build on |
|--------|--------|------------------------------|
| App routing | `AppView = "chat" \| "audit"` in `ui/src/config.ts`; switch in `LeftSidebar` + `AppShell` | Extend to `"semantic"` (or `"editor"`) |
| Wren MDL | `wren/tpch/` — `wren_project.yml`, `relationships.yml`, `models/*/metadata.yml` | Primary editable tree for Wren mode |
| Off-mode schema | `schema/tpch_sf1.md` | Read/edit for Off mode; document as separate consumer |
| Cortex | Stub tool + `cortex_ready` in `/api/status` | Show “not configured” until Semantic View YAML exists |
| Query history | `GET /api/audit/logs`, `GET /api/audit/sessions` | Editor AI + PR description context |
| DB access | Snowflake via existing tools (`execute_snowflake_sql`, Wren expand) | Editor agent: schema probe + sample queries, not full chat replay |
| Chat memory | LangGraph `MemorySaver` (ephemeral) + UI snapshots | Do **not** reuse NL→SQL thread; optional link audit `thread_id` → editor session |
| Validation | CLI: `wren context validate`, `wren context build` | API wrapper + UI “Validate” / “Rebuild index” buttons |

---

## Requirements trace

| ID | Requirement |
|----|-------------|
| R1 | New nav item **Semantic layer** (or **Model editor**) in `LeftSidebar` |
| R2 | **Consumers panel** lists each semantic backend and which files/paths it loads |
| R3 | **File tree + editor** for allowed paths under repo root (YAML/MD); unsaved buffer + save to working tree |
| R4 | **Validate** runs Wren validate (and later Cortex/SQL checks) and surfaces errors in UI |
| R5 | **PR flow** creates branch, commits changes, opens GitHub PR with title + body (human-editable before submit) |
| R6 | **Editor AI** pane: suggest edits, explain relationships, propose diffs; does not auto-merge |
| R7 | Editor AI may use **Snowflake** (schema/row samples), **audit logs** (questions, SQL, errors), and placeholder for **feedback logs** |
| R8 | Changing MDL does not require API restart; **Rebuild** triggers `wren context build` + optional `wren memory index` (async job) |
| R9 | Agent-native: same REST/AG-UI endpoints usable without the browser (future CLI/SDK) |

---

## Consumers map (page header)

Static manifest in API (versioned in git), enriched by `/api/status`:

| Consumer | Mode | Primary paths | Runtime hook |
|----------|------|---------------|--------------|
| **Wren AI** | `wren` | `wren/tpch/wren_project.yml`, `relationships.yml`, `models/**/metadata.yml` | `wren_dry_plan`, `wren_run_sql`, `wren_memory_fetch`; built `target/mdl.json` (gitignored) |
| **Off / markdown** | `off` | `schema/tpch_sf1.md` | `get_schema_summary` + prompt in `src/semantic_layer/prompts.py` |
| **Cortex Analyst** | `cortex` | TBD e.g. `semantic/cortex/` (not in repo yet) | `ask_cortex_analyst` when `cortex_ready` |
| **NL→SQL chat** | all | Indirect — uses active mode from sidebar | CopilotKit chat; audit log tags `semantic_layer` per run |

UI: table or cards with status badges (`wren_ready`, `cortex_ready`) and links to open the relevant file in the editor.

---

## Scope boundaries

**In scope (MVP)**

- Third view in existing `AppShell` layout (reuse left sidebar; main = editor; optional right = AI pane).
- Backend module `src/semantic_editor/` (or `api/semantic_editor.py`) for: list files, read/write working copy, validate, PR draft.
- GitHub PR via **GitHub REST** or `gh` subprocess from API (POC: single repo, PAT or GitHub App in `.env`).
- Editor agent: new `agent_id` / graph with tools: `read_semantic_file`, `propose_patch`, `list_audit_entries`, `snowflake_describe` / thin wrapper around existing Snowflake helpers.
- PR body template: summary of files changed, recent audit failures (same `thread_id` or semantic mode), validation output.

**Out of scope (MVP)**

- Multi-repo semantic monorepos
- Production RBAC (Okta) per file — dev-only POC
- Bi-directional sync Wren MDL ↔ Snowflake Semantic View
- In-browser merge conflict resolution across collaborators
- Auto-approve / auto-merge PRs

**Deferred**

- Feedback log ingestion (S3 prefix or app DB) — design hook only in editor agent context
- Durable editor session store (Postgres)
- Semantic diff across versions (S3 versioned semantic-model from CTA architecture)
- Inline Monaco collaborative editing

---

## Additional recommendations (“anything else?”)

These are not strict MVP requirements but should be planned early to avoid rework:

| Topic | Recommendation |
|-------|----------------|
| **Draft workspace** | Edit in a git worktree or branch (`editor/{user}/{session}`) so Chat keeps using `main` until PR merges; never write directly to `main` from the UI. |
| **Pre-PR gates** | Block PR creation if `wren context validate` fails or dirty secrets paths are touched (`wren/profiles.yml`, `.env`). |
| **Post-merge ops** | Document: after merge, run `wren context build` + `wren memory index` on deploy host (or CI job). |
| **PR template** | Repo `.github/pull_request_template.md` + API fills sections: *What changed*, *Validation*, *Audit examples*, *Risk*. |
| **Change impact** | Show “last N audit errors mentioning model X” when a model file is selected (grep audit JSON). |
| **Separate agent** | `semantic_editor_agent` — do not reuse `nl2sql_assistant` graph; different system prompt (YAML-safe, no arbitrary execute without confirm). |
| **Human-in-the-loop** | AI proposes patches as unified diffs; user applies selected hunks (CopilotKit generative UI or simple diff viewer). |
| **Secrets** | GitHub token in `.env` (`GITHUB_TOKEN`); scope: `repo` for PR create; never send token to browser — API only. |
| **CI** | GitHub Action on PR: `wren context validate`, optional `pytest` for guard tests. |
| **Agent-native** | Document OpenAPI for editor endpoints so automations can open PRs the same way as the UI. |
| **Observability** | Audit log event type `semantic_edit` / `pr_opened` when editor actions occur (extends `audit_logger`). |

---

## High-level architecture

```mermaid
flowchart TB
  subgraph UI
    Nav[LeftSidebar: Chat | Audit | Semantic]
    Cons[Consumers panel]
    Ed[File tree + YAML editor]
    Val[Validate / Rebuild]
    PR[PR wizard]
    AI[Editor AI pane]
  end

  subgraph API
    Files["GET/PUT /api/semantic/files"]
    Manifest["GET /api/semantic/consumers"]
    Validate["POST /api/semantic/validate"]
    Rebuild["POST /api/semantic/rebuild"]
    PRAPI["POST /api/semantic/pr"]
    EditorAG["POST /copilotkit or /api/semantic/agent"]
  end

  subgraph Data
    Git[(Git working tree / branch)]
    WrenCLI[wren context validate/build]
    GH[GitHub REST]
    S3[(Audit S3)]
    SF[(Snowflake)]
  end

  Nav --> Cons & Ed & Val & PR & AI
  Ed --> Files
  Val --> Validate --> WrenCLI
  PR --> PRAPI --> GH
  AI --> EditorAG
  EditorAG --> Files
  EditorAG --> S3
  EditorAG --> SF
  Files --> Git
```

---

## UI changes (concrete)

| File | Change |
|------|--------|
| `ui/src/config.ts` | `AppView` += `"semantic"` |
| `ui/src/components/LeftSidebar.tsx` | Nav button **Semantic layer** |
| `ui/src/components/AppShell.tsx` | Route `activeView === "semantic"` → `SemanticLayerPage` |
| `ui/src/components/SemanticLayerPage.tsx` | **New** — consumers, editor, validate, PR, AI split layout |
| `ui/src/hooks/useSemanticFiles.ts` | **New** — fetch tree, load/save file |
| `ui/src/hooks/useSemanticPr.ts` | **New** — PR draft + submit |
| `ui/src/components/SemanticEditorPane.tsx` | **New** — CodeMirror/Monaco for YAML/MD |
| `ui/src/components/SemanticEditorChat.tsx` | **New** — CopilotKit with `agent: semantic_editor` |

**Layout suggestion:** Main column = consumers (collapsible) + file editor; right column = editor AI (mirror `ContextSidebar` on chat, but editor-specific tools).

**Sidebar behavior:** On semantic view, chat history section shows placeholder (like audit) or “related sessions” filtered by semantic_layer from audit API.

---

## API surface (proposed)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/semantic/consumers` | Manifest + live status from `_semantic_layer_status()` |
| GET | `/api/semantic/tree?root=wren/tpch` | Allowed paths glob list |
| GET | `/api/semantic/file?path=...` | Read UTF-8 text (path allowlist) |
| PUT | `/api/semantic/file?path=...` | Write to working tree (branch checkout server-side) |
| POST | `/api/semantic/validate` | Run `wren context validate` (cwd `wren/tpch`) |
| POST | `/api/semantic/rebuild` | `wren context build` (+ optional memory index) async |
| GET | `/api/semantic/audit-context` | Recent failures for mode/model (query audit) |
| POST | `/api/semantic/pr` | Body: `{ title, body, base_branch, paths[] }` → branch, commit, `gh pr create` |
| POST | `/api/semantic/agent` or CopilotKit route | Editor AG-UI stream |

**Path allowlist (security):** Only under `wren/tpch/`, `schema/`, `semantic/` (when added). Reject `..`, absolute paths, and gitignored secrets.

---

## PR workflow (detailed)

1. User edits files in UI (or applies AI-suggested patch).
2. **Save** writes to local branch (API checks out `feat/semantic-edit-{timestamp}` or uses session branch).
3. **Validate** — must pass for Wren-owned files.
4. **PR wizard** — prefill:
   - **Title:** `semantic(wren/tpch): <short change>` (conventional commit style)
   - **Body:** bullets from diff stat; “Motivation” from selected audit entries; “Test plan” checklist (`wren context validate`, manual chat question)
5. **Submit** — API: `git add`, `git commit`, `git push`, `gh pr create --fill` or REST equivalent.
6. User merges in GitHub; optional webhook later to trigger rebuild (out of MVP).

**Env:** `GITHUB_REPO`, `GITHUB_TOKEN`, optional `GITHUB_DEFAULT_BRANCH=main`.

---

## Editor AI — context and tools

**System prompt themes:** MDL model names, relationship cardinality, TPCH column mapping, “propose diff don’t execute destructive SQL,” cite audit examples.

| Tool | Source | Use |
|------|--------|-----|
| `list_semantic_files` | New | Tree under allowlist |
| `read_semantic_file` / `write_semantic_file` | New | With user confirmation for writes |
| `wren_validate` | Wrap CLI | Same as UI validate |
| `get_schema_summary` | Existing | Off-mode + physical truth |
| `execute_snowflake_sql` | Existing | Limited: `LIMIT 10` enforced in guard |
| `search_audit_logs` | `audit_reader` | Filter by `semantic_layer`, error tags, model name in SQL |
| `feedback_search` | Stub | Future: S3/DB feedback index |

**Context injection per turn (optional):** active file path + content, selected audit entries, `wren_ready` message from status.

**Thread model:** New `editor_thread_id` in `localStorage` (`ai-sql-poc-editor-thread-id`), independent from chat `thread_id`.

---

## Implementation units

### Unit 1: App shell + consumers (½ day)

- Extend `AppView` and nav.
- `GET /api/semantic/consumers` static JSON + status merge.
- `SemanticLayerPage` read-only consumers + links.

**Verify:** Navigate to Semantic layer; see Wren / Off / Cortex rows and `wren_ready` badge.

---

### Unit 2: File read/write API + editor UI (1 day)

- Allowlisted read/write endpoints.
- CodeMirror (or textarea POC) with save.
- Dirty-state warning on navigate away.

**Verify:** Edit `relationships.yml`, save, `git diff` shows change on disk.

---

### Unit 3: Validate + rebuild (½ day)

- `POST /api/semantic/validate` and rebuild subprocess with timeout + streamed logs in UI.

**Verify:** Introduce intentional YAML error → validate fails with message; fix → passes.

---

### Unit 4: GitHub PR API (1 day)

- Branch lifecycle, commit, PR create, error handling (no token, push rejected).
- PR body builder from diff + optional audit IDs.

**Verify:** End-to-end PR opened on a test repo fork or branch with CI skipped for POC.

---

### Unit 5: Editor AI agent (1–2 days)

- `build_editor_agent_graph()` in `src/agent_factory.py` or `src/semantic_editor/agent.py`.
- Register second CopilotKit agent or dedicated `/api/semantic/agent` AG-UI endpoint.
- Wire audit + Snowflake tools with stricter guards than NL→SQL agent.

**Verify:** Ask “why did orders join fail?” with audit context → proposes relationship fix diff.

---

### Unit 6: Audit context + PR enrichment (½ day)

- `GET /api/semantic/audit-context?model=orders&limit=10`
- PR wizard pulls recent errors into body template.

---

### Unit 7: Docs + agent-native checklist (2 hours)

- Update `docs/README.md`, `ui/README.md`, `AGENTS.md` dev restart notes.
- OpenAPI snippet or `docs/architecture/semantic-layer-editor.md`.

---

## Testing strategy

| Layer | Tests |
|-------|--------|
| API | Path traversal rejected; allowlist enforced; validate returns structured errors |
| UI | Smoke: nav, open file, save, validate button |
| Integration | Optional: mock GitHub API for PR unit test |
| Manual | Edit MDL → validate → chat Wren question → open PR |

---

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| API writes corrupt MDL | Validate before save optional; require validate before PR |
| GitHub token exposure | Server-side only; short-lived PAT |
| Concurrent edit + chat | Worktree/branch per editor session |
| `wren` CLI missing on server | Same as chat: `/api/status` + disable rebuild |
| Editor AI runs wide SQL | Tool guard: read-only role or `LIMIT` enforcement |

---

## Success criteria

- User can open **Semantic layer** view without leaving the app.
- User sees which subsystem consumes which files.
- User can edit `relationships.yml` / model YAML, validate, and open a PR with a useful description.
- Editor AI can reference at least one audit log example and Snowflake schema info in a suggested change.

---

## Branch

Implementation tracking branch: **`feat/semantic-layer-editor`** (this plan lands on that branch first; implementation units follow in separate commits/PRs).
