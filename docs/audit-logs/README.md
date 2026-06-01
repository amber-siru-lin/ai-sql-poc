# Query audit logs

Append-only audit trail for every completed **Deep Agent** run (CopilotKit UI via API, or CLI). Each record captures the natural-language question, semantic layer mode, SQL tool calls, timing, and a hash of result text—not full result rows.

**Related:** [query-and-memory-storage.md](../architecture/query-and-memory-storage.md) (full storage map) · [api/README.md](../../api/README.md) (how to run the API)

---

## What we built (2026-06-01)

| Item | Detail |
|------|--------|
| **S3 bucket** | `cta-poc-ai-sql-audit-dev-654654461736` (`us-east-1`, versioning on, public access blocked) |
| **Local fallback** | `logs/audit/YYYY-MM-DD.jsonl` (gitignored) — always written |
| **S3 objects** | `audit/YYYY/MM/DD/{thread_id}/{run_id}.json` — one JSON file per run when `AUDIT_S3_BUCKET` is set |
| **Code** | `src/audit_logger.py`, `src/audit_extract.py` |
| **Hooks** | `SemanticLayerLangGraphAgent.run` (API), `ask_deep_agent.ask` (CLI) |
| **Config** | Repo-root `.env` or shell: `AUDIT_S3_BUCKET`, optional `AUDIT_S3_PREFIX`, `AUDIT_LOCAL_DIR` |
| **API** | `api/main.py` loads `.env` on startup; `GET /api/status` returns `audit` block |

This matches the CTA architecture **auditLogger → S3** path for POC troubleshootability (see [cta-ai-architecture.html](../architecture/cta-ai-architecture.html)).

---

## Restart the API

From repo root (loads `.env` including `AUDIT_S3_BUCKET`):

```bash
export AWS_PROFILE=Brainfore-Team-Set-654654461736
aws sso login --profile "$AWS_PROFILE"   # if session expired

lsof -ti :8000 | xargs kill 2>/dev/null
sleep 1
scripts/py -m uvicorn api.main:app --reload --port 8000
```

Verify:

```bash
curl -s http://localhost:8000/api/status | python3 -m json.tool
# Expect audit.s3_bucket = "cta-poc-ai-sql-audit-dev-654654461736"
```

---

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `AUDIT_S3_BUCKET` | *(empty)* | If set, upload one JSON object per run to S3 |
| `AUDIT_S3_PREFIX` | `audit/` | Key prefix inside the bucket |
| `AUDIT_LOCAL_DIR` | `logs/audit` | Directory under repo root for daily JSONL |
| `AWS_PROFILE` / `AWS_REGION` | — | Standard AWS creds for S3 `PutObject` |

Copy from [.env.example](../../.env.example). Your local `.env` should include:

```bash
AUDIT_S3_BUCKET=cta-poc-ai-sql-audit-dev-654654461736
AUDIT_S3_PREFIX=audit/
```

---

## Record shape (one JSON object per run)

```json
{
  "timestamp": "2026-06-01T17:30:00.000Z",
  "source": "api",
  "thread_id": "copilot-thread-uuid",
  "run_id": "run-uuid",
  "semantic_layer": "off",
  "question": "Revenue by market segment?",
  "sql_executions": [
    {
      "tool": "execute_snowflake_sql",
      "sql": "SELECT ...",
      "result_fingerprint": "sha256hex...",
      "result_preview": "Columns: [...] (first 240 chars)",
      "error": null
    }
  ],
  "status": "ok",
  "duration_ms": 18500,
  "error": null
}
```

| Field | Notes |
|-------|--------|
| `source` | `api` (CopilotKit) or `cli` |
| `result_fingerprint` | SHA-256 of result text (up to 4 KB) for dedup / compliance without storing full rows |
| `result_preview` | Truncated tool output for debugging only |
| `status` | `ok` or `error` |

SQL is extracted from tool calls: `execute_snowflake_sql`, `wren_run_sql`, `wren_dry_plan`, `ask_cortex_analyst`.

---

## UI viewer

In the local app, open **Audit logs** in the left sidebar (next to Chat). The page loads entries from `GET /api/audit/logs` and shows a run list plus SQL step detail.

## How to inspect logs

### Local (after any API or CLI run)

```bash
tail -f logs/audit/$(date -u +%Y-%m-%d).jsonl
# Pretty-print last line:
tail -1 logs/audit/$(date -u +%Y-%m-%d).jsonl | python3 -m json.tool
```

### S3

```bash
export AWS_PROFILE=Brainfore-Team-Set-654654461736
aws s3 ls s3://cta-poc-ai-sql-audit-dev-654654461736/audit/ --recursive | tail -20
aws s3 cp s3://cta-poc-ai-sql-audit-dev-654654461736/audit/2026/06/01/THREAD_ID/RUN_ID.json - | python3 -m json.tool
```

Later (CTA target): query with **Athena** over the `audit/` prefix; add **S3 Object Lock** for production immutability.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| No `logs/audit/` files | Run a question in the UI or CLI; check API logs for `audit logging failed` |
| Local works, no S3 objects | Set `AUDIT_S3_BUCKET`, restart API, confirm `curl .../api/status` shows bucket; `aws sso login` |
| S3 `AccessDenied` | IAM needs `s3:PutObject` on `arn:aws:s3:::cta-poc-ai-sql-audit-dev-654654461736/audit/*` |
| Empty `sql_executions` | Agent answered without calling a SQL tool (schema-only or error before execute) |

---

## File map

```
src/audit_logger.py      # write_audit_record, build_audit_record, S3 + JSONL
src/audit_extract.py     # question + SQL from LangGraph messages
src/ag_ui_agent.py       # audit after each AG-UI run
src/ask_deep_agent.py    # audit after each CLI run
api/main.py              # .env load, /api/status audit block
logs/audit/              # local output (gitignored)
```
