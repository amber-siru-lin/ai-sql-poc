# Phase guide — what to run for Phase 1, 2, or 3

Each phase builds on the one before. You can run them **in isolation** using only the files listed below.

---

## Phase 1 — ChatBedrock (single-shot NL→SQL)

**What it is:** One prompt → Nova Pro writes SQL → Snowflake returns data. No agent loop.

### Files you need

| Role | Path |
|------|------|
| **Core logic** | `src/nl2sql.py` — `ChatBedrock` + `ask_ai()` + `run_sql()` |
| **One-shot test** | `src/run_baseline_test.py` |
| **Interactive CLI** | `src/ask_questions.py` |
| **Startup checks** | `src/check_setup.py` |
| **Schema (in prompt)** | `schema/tpch_sf1.md` |
| **Snowflake creds** | `config/snowflake_config.py` (copy from `.example`) |
| **AWS helper** | `scripts/diagnose_bedrock.py`, `scripts/setup_aws.sh` |
| **Python runner** | `scripts/py` |

### Do **not** need for Phase 1 only

- `src/ask_deep_agent.py`
- `src/agent_streaming.py`
- `src/tools/` (Deep Agent tools)

### Install (minimal)

```bash
scripts/py -m pip install langchain langchain-aws snowflake-connector-python boto3
```

Or full `requirements.txt` (includes Phase 2 packages too — harmless).

### Run

```bash
export AWS_PROFILE=Brainfore-Team-Set-654654461736
aws sso login --profile $AWS_PROFILE

scripts/py src/run_baseline_test.py    # one question
scripts/py src/ask_questions.py        # interactive
```

### Plan doc

`docs/plans/2026-05-28-002-feat-simple-ai-nl2sql-poc-plan.md`

---

## Phase 2 — Deep Agents (tools + memory)

**What it is:** Agent plans, calls tools, retries SQL errors, remembers follow-ups in the same session.

### Files you need (includes Phase 1 shared code)

| Role | Path |
|------|------|
| **Everything from Phase 1** | `src/nl2sql.py`, `config/`, `schema/`, etc. |
| **Deep Agent entrypoint** | `src/ask_deep_agent.py` |
| **Verbose step streaming** | `src/agent_streaming.py` |
| **Snowflake tools** | `src/tools/snowflake_tools.py` |

### Install extra

```bash
scripts/py -m pip install deepagents langgraph
```

(already in `requirements.txt`)

### Run

```bash
export AWS_PROFILE=Brainfore-Team-Set-654654461736
aws sso login --profile $AWS_PROFILE

scripts/py src/ask_deep_agent.py              # interactive + memory
scripts/py src/ask_deep_agent.py --verbose  # show tool calls / steps
```

**REPL commands:** `clear` (new conversation) · `help` · `quit`

### Plan doc

`docs/plans/2026-05-29-003-feat-deep-agents-nl2sql-upgrade-plan.md`

---

## Phase 3 — Web UI

| Track | What | Folder | Status |
|-------|------|--------|--------|
| **3B (active)** | CopilotKit chat + FastAPI AG-UI | `ui/` + `api/` | **Working locally** |
| **3A (parked)** | Amplify Gen 2 + Lambda | `web/` | Blocked on CDK bootstrap |

**What it is:** Browser chat UI → Python Deep Agent → Bedrock + Snowflake (same logic as Phase 2).

---

### Phase 3B — CopilotKit (active, local)

Chat in the browser via CopilotKit sidebar; agent runs through FastAPI + AG-UI.

**Docs:** [plan](plans/2026-05-29-004-feat-copilotkit-local-ui-plan.md) · [learnings](solutions/copilotkit-local-ui-learnings.md)

#### Files you need (includes Phase 1 + 2 shared code)

| Role | Path |
|------|------|
| **Everything from Phase 2** | `src/agent_factory.py`, `src/tools/`, `config/`, `schema/`, etc. |
| **FastAPI AG-UI server** | `api/main.py` |
| **CopilotKit UI** | `ui/src/App.tsx`, `ui/src/config.ts` |
| **Python runner** | `scripts/py` |

#### Do **not** need for Phase 3B only

- `web/` (Amplify — parked)
- Phase 1-only scripts unless you are testing baseline separately

#### Install (first time)

From repo root:

```bash
cd ~/Documents/GitHub/personal_build

# Python (API + agent) — full requirements includes Phase 2 deps
scripts/py -m pip install -r requirements.txt

# Node (CopilotKit UI)
cd ui && npm install && cd ..
```

Copy Snowflake config if you have not already:

```bash
cp config/snowflake_config.example.py config/snowflake_config.py
# edit config/snowflake_config.py
```

#### Run — two terminals

**Terminal 1 — API** (keep running; leave this window open):

```bash
cd ~/Documents/GitHub/personal_build

export AWS_PROFILE=Brainfore-Team-Set-654654461736
aws sso login --profile $AWS_PROFILE

scripts/py -m uvicorn api.main:app --reload --port 8000
```

Wait for `Application startup complete`.

**Terminal 2 — UI** (keep running):

```bash
cd ~/Documents/GitHub/personal_build/ui

npm run dev
```

Open the URL Vite prints — usually **http://localhost:5173/**

Use the **SQL Assistant** panel on the right. Header should show **API connected**.

#### Restart / stop

```bash
# Stop API (if port 8000 is stuck)
lsof -ti :8000 | xargs kill

# Stop UI (if port 5173 is stuck)
lsof -ti :5173 | xargs kill

# Then re-run the two terminals above
```

If SSO expired, run `aws sso login --profile $AWS_PROFILE` again in Terminal 1 before restarting the API.

#### Optional env (`ui/.env.local`)

Only if the API is not on `localhost:8000`:

```bash
VITE_API_URL=http://localhost:8000
VITE_COPILOT_RUNTIME_URL=http://localhost:8000/copilotkit
```

See `ui/.env.example`.

#### Phase 3.4 — Session & memory (UI)

- **Clear conversation** — Right sidebar starts a new LangGraph `thread_id` and resets chat.
- **Semantic mode change** — Also starts a new thread (avoids mixed tool/prompt state).
- **Memory docs in UI** — Explains LangGraph `MemorySaver`, Wren LanceDB under `wren/tpch/target/`, and retry counters.

**Where queries/logs live:** [architecture/query-and-memory-storage.md](architecture/query-and-memory-storage.md) — nothing is persisted to a repo query log; Snowflake keeps warehouse history.

#### Troubleshooting

| Symptom | See |
|---------|-----|
| Blank page, 422, `network error`, chat fails | [CopilotKit learnings](solutions/copilotkit-local-ui-learnings.md) |
| `API offline` in header | Terminal 1 not running or wrong port |
| Bedrock / Snowflake errors | Re-run `aws sso login`; check `config/snowflake_config.py` |

---

### Phase 3A — Amplify (parked)

Blocked until IT fixes CDK bootstrap. Do not use for daily dev.

```bash
# Blocked — see docs/solutions/aws-amplify-cdk-bootstrap-blocked.md
cd web
export AWS_PROFILE=Brainfore-Team-Set-654654461736
NODE_OPTIONS="--no-webstorage" npx ampx sandbox --profile $AWS_PROFILE
```

**Docs:** [PHASE3-AMPLIFY-GETTING-STARTED.md](PHASE3-AMPLIFY-GETTING-STARTED.md) · [Amplify learnings](solutions/aws-amplify-cdk-bootstrap-blocked.md)

---

## Quick comparison

| | Phase 1 | Phase 2 | Phase 3 |
|---|---------|---------|---------|
| **Entry script** | `src/ask_questions.py` | `src/ask_deep_agent.py` | **3B:** `ui/` + `api/` → http://localhost:5173 |
| **AI pattern** | `ChatBedrock.invoke()` | Deep Agent + tools | Same as Phase 2 via AG-UI |
| **Follow-up memory** | No | Yes (`clear` to reset) | Yes (LangGraph checkpointer) |
| **Extra pip packages** | langchain-aws | + deepagents | + fastapi, ag-ui-langgraph |
| **Status** | Done | Done | **Working locally** — CopilotKit (`ui/`+`api/`); Amplify (`web/`) parked |
