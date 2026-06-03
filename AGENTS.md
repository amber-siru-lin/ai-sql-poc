# Agent instructions (AI SQL POC)

## Dev servers — restart without asking

When work requires a fresh API (backend changes, `.env` updates, audit/S3 config, or the user reports API offline / stale behavior), **restart the API yourself** in the background. Do not only print restart commands unless the user explicitly wants manual control.

From repo root:

```bash
export AWS_PROFILE="${AWS_PROFILE:-your-sso-profile-name}"
lsof -ti :8000 2>/dev/null | xargs kill 2>/dev/null
sleep 1
scripts/py -m uvicorn api.main:app --reload --port 8000
```

Verify: `curl -s http://localhost:8000/api/status` → `"status": "ok"`.

**Wren (Semantics → Wren):** On local API startup, if `wren` is on PATH and `target/mdl.json` is missing, the API runs `sync_wren_profile.py` + `wren context build` automatically. Requires `config/snowflake_config.py` and `pip install "wrenai[snowflake,memory]"`. Set `WREN_SKIP_BOOTSTRAP=1` to disable. See [wren/tpch/README.md](wren/tpch/README.md).

For UI changes, restart Vite when needed:

```bash
cd ui && npm run dev
```

Default URLs: API `http://localhost:8000`, UI `http://localhost:5173`.

**Semantic layer editor:** third app view with its own agent at `POST /semantic-agent` (`semantic_editor`). Restart the API after changes under `src/semantic_editor/` or semantic REST routes in `api/main.py`. See [docs/architecture/semantic-layer-editor.md](docs/architecture/semantic-layer-editor.md).

See [api/README.md](api/README.md) and [docs/audit-logs/README.md](docs/audit-logs/README.md).

---

## Localhost UI errors — fix loop (do not stop at “check the console”)

When the user reports the **ErrorBoundary** page (“Something went wrong”), a **blank chat**, or **`Cannot read properties of undefined (reading 'length')`** on `http://localhost:5173`, **diagnose and fix in a loop** without asking them to paste the stack trace first.

### 1. Reproduce and locate

```bash
cd ui && npm run build          # TypeScript catches missing props
rg "\.length" ui/src --glob "*.{tsx,ts}"   # find unsafe .length on maybe-undefined
```

Read the error message in the ErrorBoundary `<pre>` if the user quoted it. Common pattern: **`undefined.length`** on chat history or CopilotKit `messages`.

### 2. Known failure modes (fix all that apply)

| Symptom | Usual cause | Fix |
|---------|-------------|-----|
| `reading 'length'` on load | `sessions` not passed `App` → `AppShell` → `LeftSidebar` → `ChatHistoryList` | Wire props; default `sessions = []` in list/sidebar |
| Same after adding chat history | `LeftSidebar` omits `sessions` when rendering `ChatHistoryList` | Pass `sessions`, `loading`, `error`, `onRefresh` |
| Session panel crash | `useCopilotChatHeadless_c().messages` undefined before CopilotKit mounts | Use `messages?.length ?? 0` |
| Blank chat on session click | `connectAgent` clears messages after restore; or `CopilotKit threadId` reconnect | Use `useSqlAgent` only; no `threadId` on `<CopilotKit>`; see session learnings doc |
| Chat restore crash | `ChatPane` saves raw CopilotKit messages or reads undefined `messages` | Guard with `messages?.length`; use `toStoredMessages()` before save |
| Stale UI after fix | Vite HMR missed a prop change | Restart `npm run dev`; hard refresh browser |

Reference: [docs/solutions/chat-memory-and-session-learnings.md](docs/solutions/chat-memory-and-session-learnings.md)

### 3. Verify before handing back

```bash
cd ui && npm run build
curl -s http://localhost:8000/api/status   # API up
```

Reload `http://localhost:5173` — sidebar **Chat history** should render (empty list is OK; crash is not).

### 4. When to stop looping

Stop when `npm run build` passes **and** the UI loads without ErrorBoundary. If a new runtime error appears, repeat from step 1 — do not ask the user to “try again” until you have fixed the new trace.

Only escalate to the user if: API is down and SSO cannot be refreshed from this environment, or the error is outside `ui/` (e.g. Bedrock/Snowflake credentials).
