# Where queries and memory are stored

Storage is split by layer. **Query audit** (question, SQL, timing, result fingerprint) is written on every completed API/CLI agent run when audit logging is enabled.

## Conversation memory (follow-ups in one chat)

| Layer | Location | Survives API restart? |
|-------|----------|------------------------|
| **LangGraph checkpointer** | `MemorySaver()` in `src/agent_factory.py` — state keyed by `thread_id` in the uvicorn process | **No** |
| **UI thread id** | `localStorage` key `ai-sql-poc-thread-id` + CopilotKit / AG-UI `threadId` on each run | Survives browser refresh; server state still lost on restart |
| **Clear conversation** | UI assigns a new `thread_id` and resets chat messages | Old server checkpoint remains in RAM until process exit |

AG-UI passes `thread_id` from the browser agent into `SemanticLayerLangGraphAgent` (`src/ag_ui_agent.py`) → `config.configurable.thread_id` for retry policy and checkpointing.

## SQL retry policy (per thread)

| Location | File | Notes |
|----------|------|--------|
| In-process dict | `src/semantic_layer/retry_policy.py` → `_SESSION` | Counts attempts / fingerprints per `thread_id`; cleared on API restart |

## Wren semantic memory (NL↔SQL recall)

| Location | Notes |
|----------|--------|
| `wren/tpch/target/` (gitignored via `wren/**/target/`) | Built by `wren context build` and `wren memory index` |
| Tool | `wren_memory_fetch` in `src/tools/wren_tools.py` |

This is **separate** from LangGraph chat memory: it recalls past verified questions/SQL for Wren mode, not full chat transcripts.

## What runs on Snowflake

| Data | Where |
|------|--------|
| Query execution | Snowflake warehouse history (account-level) |
| Result rows | Returned to the agent → shown in CopilotKit chat tool cards only |

The app does not export Snowflake `QUERY_HISTORY` into this repo.

## CLI (Phase 2)

| Data | Where |
|------|--------|
| Conversation | In-memory `history` list in `src/ask_deep_agent.py` |
| Clear | `clear` command starts a new in-process history (thread id `cli`) |
| Verbose steps | Printed to terminal only (`src/agent_streaming.py`) — not persisted |

## Query audit log (implemented)

Full guide: **[docs/audit-logs/README.md](../audit-logs/README.md)** (bucket setup, env vars, restart API, record schema, troubleshooting).

| Layer | Location | Notes |
|-------|----------|--------|
| **Local dev** | `logs/audit/YYYY-MM-DD.jsonl` (gitignored) | One JSON object per line per run |
| **S3 (optional)** | `s3://cta-poc-ai-sql-audit-dev-654654461736/audit/YYYY/MM/DD/{thread_id}/{run_id}.json` | Set `AUDIT_S3_BUCKET` in `.env` or shell; requires `AWS_PROFILE` with `s3:PutObject` |
| **Code** | `src/audit_logger.py`, `src/audit_extract.py` | Hooked from `SemanticLayerLangGraphAgent.run` (API) and `ask_deep_agent.ask` (CLI) |

`GET /api/status` includes an `audit` object with resolved bucket/prefix paths.

## Not implemented yet

- Thread list / search in the left sidebar
- Durable checkpointer (Postgres, SQLite, etc.)

---

## CTA target architecture — where each “memory” should live

Source: [cta-ai-architecture.html](cta-ai-architecture.html) (Layers 5–7) and [POC requirements](../brainstorms/2026-05-28-ai-data-analysis-poc-requirements.md) (POC defers Aurora; uses S3 + CloudWatch).

Use this table when **troubleshooting** or planning MVP storage. “POC today” is what this repo does now; “CTA plan” is where production-shaped data should go.

| What you need to remember / debug | CTA plan (store here) | POC today (this repo) | How to troubleshoot now |
|-----------------------------------|------------------------|------------------------|-------------------------|
| **Business definitions** (metrics, joins, synonyms) | **Git** `semantic-model/*.yml` → synced to **S3** (versioned) + **Aurora pgvector** (Titan embeddings for RAG) | **Git:** `schema/tpch_sf1.md` (Off) or `wren/tpch/models/` MDL (Wren) | Wrong SQL / wrong table names → read MDL or markdown in repo; PR history in Git |
| **Verified NL↔SQL examples** (“memory” for similar questions) | Aurora: schema metadata + example queries in pgvector | **Wren:** `wren/tpch/target/` after `wren memory index` (LanceDB; not in git) | Wren mode: re-run `wren memory fetch` from CLI; rebuild index if MDL changed |
| **Chat follow-ups** (same conversation) | Aurora **query/session history** (relational) + optional thread id in app | **LangGraph `MemorySaver`** in API RAM (`thread_id` from UI) | Lost after uvicorn restart; use **Clear conversation** for new thread; check `localStorage` `ai-sql-poc-thread-id` |
| **User feedback** (thumbs down, “revenue should include…”) | **Aurora feedback table** → **EventBridge** → nightly analysis → Git PR on YAML | Not implemented | N/A in POC |
| **Every AI query (audit / compliance)** | **S3 audit bucket** — immutable JSON per query (user, question, SQL, latency, credits, result hash); query with **Athena** | Not written by app | Use **Snowflake** `ACCOUNT_USAGE.QUERY_HISTORY` (or equivalent) for SQL that actually ran; browser chat is not logged |
| **Ops / latency / errors** | **CloudWatch** (Lambda metrics + logs); **CloudTrail** (AWS API calls) | Terminal: uvicorn stdout; CopilotKit browser console | Run API in foreground; `aws sso login` + Bedrock/Snowflake errors in terminal |
| **Agent step trace** (tool calls, retries) | CloudWatch structured logs from `queryHandler` / Lambdas | CLI: `ask_deep_agent.py --verbose`; UI: inline tool cards only | Reproduce with CLI `--verbose`; no persisted trace file |
| **SQL retry state** (attempt 2 of 3) | Part of request context in Lambda + optional row in query history | `src/semantic_layer/retry_policy.py` `_SESSION` (RAM, per `thread_id`) | Restart API clears counters; same thread id after restart may behave oddly — clear chat |

### Layer 7 flow (CTA) — what to build toward for troubleshooting

When Alice asks a question, the **auditLogger** path in the CTA diagram is what makes post-hoc debugging possible:

1. **S3 audit** — one JSON object per request (question, generated SQL, execution time, credits, result hash). Partition by `date/user_id/`. Use **S3 Object Lock** for immutability.
2. **CloudWatch** — latency, error rate, alarm on failures (Slack). Short retention; not your 7-year record.
3. **Snowflake** — ground truth for **what SQL actually executed** and warehouse cost (independent of your app logs).

For **semantic** debugging (wrong definition, not wrong syntax), use **Git + Aurora** (CTA) or **Git MDL + Wren memory** (current Wren path)—not the audit bucket.

### POC vs CTA: intentional simplifications

From the original POC requirements:

- **Aurora** — skipped for POC (“use S3 + in-memory caching; add Aurora for MVP”).
- **S3** — planned for semantic YAML and test results; POC uses git + Wren `target/` instead.
- **CloudWatch** — assumed available when on Lambda; local dev uses terminal only.

Your current stack (Deep Agents + CopilotKit + optional Wren) maps to CTA **Layer 3–4** (agent + Bedrock) but not yet **Layer 5–7** persistence. Closing that gap for troubleshootability means adding at minimum:

1. **`auditLogger` → S3** (+ local `logs/audit/` in dev) — **done** for API and CLI runs.
2. **Durable checkpointer** (SQLite file or Aurora) instead of `MemorySaver()` only in RAM.
3. **Structured CloudWatch** (or file logging) with `thread_id`, tool name, SQL fingerprint, semantic mode.

### Recommended dev layout (until AWS MVP)

If you want CTA-like troubleshootability **before** Aurora/Lambda:

| Purpose | Suggested path (repo or machine) |
|---------|----------------------------------|
| Audit JSONL (one line per query) | `logs/audit/YYYY-MM-DD.jsonl` (gitignored) |
| LangGraph checkpoints | `data/checkpoints.sqlite` (gitignored) |
| Wren memory | keep `wren/tpch/target/` (already gitignored) |
| Semantic source of truth | keep in **git** (`wren/tpch/`, `schema/`) |

Add `logs/` and `data/` to `.gitignore` when you implement.

---

See also: [agent-error-handling.md](agent-error-handling.md), [copilotkit-local-ui-learnings.md](../solutions/copilotkit-local-ui-learnings.md), [cta-ai-architecture.html](cta-ai-architecture.html).
