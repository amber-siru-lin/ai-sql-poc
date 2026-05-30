# AI SQL POC

Natural language → SQL using **Amazon Bedrock (Nova Pro)** + **Snowflake**.

| Phase | What | Status |
|-------|------|--------|
| **1** | ChatBedrock single-shot NL→SQL | Done |
| **2** | LangChain Deep Agents + tools + chat memory | Done |
| **3** | Web UI (CopilotKit local) | Working locally — [learnings](docs/solutions/copilotkit-local-ui-learnings.md) |

**Phase-by-phase file guide:** [docs/PHASES.md](docs/PHASES.md)

---

## Repository layout

```
.
├── src/                    # Python POC (Phase 1 + 2 + shared agent)
│   ├── agent_factory.py    # Deep Agent graph (CLI + API)
│   ├── nl2sql.py           # Phase 1 core: ChatBedrock + Snowflake
│   ├── run_baseline_test.py
│   ├── ask_questions.py    # Phase 1 interactive
│   ├── ask_deep_agent.py   # Phase 2 interactive
│   ├── agent_streaming.py  # Phase 2 --verbose steps
│   └── tools/              # Phase 2 Snowflake tools
├── ui/                     # Phase 3B — CopilotKit + Vite React
├── api/                    # Phase 3B — FastAPI AG-UI server
├── config/                 # Local secrets (snowflake_config.py gitignored)
├── schema/                 # tpch_sf1.md — shared by all phases
├── scripts/                # py, setup_aws.sh, diagnose_bedrock.py
├── sql/                    # Optional Snowflake setup
├── docs/                   # Plans + PHASES.md
└── web/                    # Phase 3A (parked) — Amplify Gen 2 scaffold
```

---

## Setup (all phases)

```bash
cd ~/Documents/GitHub/personal_build   # or your clone of ai-sql-poc

scripts/py -m pip install -r requirements.txt

cp config/snowflake_config.example.py config/snowflake_config.py
# edit config/snowflake_config.py

export AWS_PROFILE=Brainfore-Team-Set-654654461736
aws sso login --profile $AWS_PROFILE
scripts/py scripts/diagnose_bedrock.py
```

Use `scripts/py` instead of plain `python` on Mac (Homebrew vs Anaconda).

---

## Run Phase 1 only (ChatBedrock)

**Files:** `src/nl2sql.py` · `src/run_baseline_test.py` · `src/ask_questions.py`

```bash
scripts/py src/run_baseline_test.py   # one-shot test
scripts/py src/ask_questions.py       # ask your own questions
```

No Deep Agent files involved.

---

## Run Phase 2 only (Deep Agents)

**Files:** Phase 1 core + `src/ask_deep_agent.py` · `src/tools/` · `src/agent_streaming.py`

```bash
scripts/py src/ask_deep_agent.py              # interactive + follow-up memory
scripts/py src/ask_deep_agent.py --verbose    # show planning / tool steps
```

Type `clear` in the REPL to reset conversation memory.

---

## Phase 3 — Web UI (CopilotKit, local)

**Files:** `ui/` · `api/` · `src/agent_factory.py` (shared with Phase 2 CLI)

**Active path:** CopilotKit + Vite in `ui/`, FastAPI agent server in `api/`. Reuses `src/` Python logic. No AWS deploy required.

**Parked path:** `web/` Amplify Gen 2 — blocked on CDK bootstrap ([learnings](docs/solutions/aws-amplify-cdk-bootstrap-blocked.md)).

### Install (first time)

```bash
scripts/py -m pip install -r requirements.txt
cd ui && npm install && cd ..
```

### Run — two terminals

```bash
# Terminal 1 — API
export AWS_PROFILE=Brainfore-Team-Set-654654461736
aws sso login --profile $AWS_PROFILE
scripts/py -m uvicorn api.main:app --reload --port 8000

# Terminal 2 — UI
cd ui && npm run dev
```

Open **http://localhost:5173** — chat in the **SQL Assistant** panel on the right.

Full steps, restart commands, and troubleshooting: [docs/PHASES.md](docs/PHASES.md#phase-3b--copilotkit-active-local).

| Doc | Purpose |
|-----|---------|
| [CopilotKit plan](docs/plans/2026-05-29-004-feat-copilotkit-local-ui-plan.md) | Folder layout, phases, architecture |
| [CopilotKit learnings](docs/solutions/copilotkit-local-ui-learnings.md) | Errors, fixes, two-URL pattern |
| [Amplify getting started](docs/PHASE3-AMPLIFY-GETTING-STARTED.md) | When IT unblocks bootstrap |
| [PHASES.md](docs/PHASES.md) | Phase isolation |

---

## Security

- `config/snowflake_config.py` and `.env` are **gitignored**
- Never commit passwords or AWS keys
- See [config/README.md](config/README.md)

## Docs

- [docs/PHASES.md](docs/PHASES.md) — isolate Phase 1 / 2 / 3
- [docs/README.md](docs/README.md) — plans and requirements index
