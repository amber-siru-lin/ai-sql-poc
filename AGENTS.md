# Agent instructions (AI SQL POC)

## Dev servers — restart without asking

When work requires a fresh API (backend changes, `.env` updates, audit/S3 config, or the user reports API offline / stale behavior), **restart the API yourself** in the background. Do not only print restart commands unless the user explicitly wants manual control.

From repo root:

```bash
export AWS_PROFILE="${AWS_PROFILE:-Brainfore-Team-Set-654654461736}"
lsof -ti :8000 2>/dev/null | xargs kill 2>/dev/null
sleep 1
scripts/py -m uvicorn api.main:app --reload --port 8000
```

Verify: `curl -s http://localhost:8000/api/status` → `"status": "ok"`.

For UI changes, restart Vite when needed:

```bash
cd ui && npm run dev
```

Default URLs: API `http://localhost:8000`, UI `http://localhost:5173`.

See [api/README.md](api/README.md) and [docs/audit-logs/README.md](docs/audit-logs/README.md).
