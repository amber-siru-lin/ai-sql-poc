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

## Phase 3 — Amplify web UI (not built yet)

**What it will be:** Browser chat UI → Lambda → same Python logic as Phase 2.

### Recommended repo layout (when you start)

Keep **one repo**. Add a `web/` folder for Amplify — do **not** mix React `src/` with Python `src/`.

```
ai-sql-poc/
├── backend/              # rename src/ → backend/ when starting Phase 3 (optional but clearer)
│   ├── nl2sql.py         # Phase 1
│   ├── ask_deep_agent.py # Phase 2
│   └── tools/
├── web/                  # NEW — Amplify Gen 2 project root
│   ├── amplify/
│   │   ├── backend.ts
│   │   └── functions/
│   │       └── aiSql/    # Lambda handler → imports backend/
│   ├── src/              # React pages (Amplify default)
│   └── package.json
├── config/               # local Snowflake (gitignored)
├── schema/
├── scripts/
└── docs/
```

**Why `web/`:** Amplify expects its own `src/` for React. Your Python code stays separate under `backend/` (today: `src/`).

### Phase 3 files (future)

| Role | Path (planned) |
|------|----------------|
| React UI | `web/src/App.tsx` |
| Amplify config | `web/amplify/backend.ts` |
| Lambda handler | `web/amplify/functions/aiSql/handler.ts` or `.py` |
| Shared Python | import from `backend/` (Phase 1 or 2) |

### Run (future)

```bash
cd web
npm install
npx ampx sandbox          # local Amplify backend
npm run dev               # React dev server
```

### Plan doc

`docs/plans/2026-05-28-002-feat-simple-ai-nl2sql-poc-plan.md` (Days 3–5)

---

## Quick comparison

| | Phase 1 | Phase 2 | Phase 3 |
|---|---------|---------|---------|
| **Entry script** | `src/ask_questions.py` | `src/ask_deep_agent.py` | `web/` (browser) |
| **AI pattern** | `ChatBedrock.invoke()` | Deep Agent + tools | Same as Phase 2 in Lambda |
| **Follow-up memory** | No | Yes (`clear` to reset) | Yes (session in UI) |
| **Extra pip packages** | langchain-aws | + deepagents | Lambda deps bundled |
| **Status** | Done | Done | Not started |
