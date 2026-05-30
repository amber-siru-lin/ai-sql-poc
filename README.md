# AI SQL POC

Natural language → SQL using **Amazon Bedrock (Nova Pro)** + **Snowflake**, with a planned upgrade to **LangChain Deep Agents**.

## Repository layout

```
.
├── config/                 # Local secrets (snowflake_config.py is gitignored)
├── docs/
│   ├── architecture/       # Interactive architecture diagram (HTML)
│   ├── brainstorms/      # Requirements & meeting prep
│   └── plans/              # Implementation plans (Phase 1, 2, CTA POC)
├── schema/                 # Table/column definitions for the AI
├── scripts/                # AWS setup & Bedrock diagnostics
├── sql/                    # Optional Snowflake setup scripts
├── src/                    # Python POC code
│   ├── nl2sql.py           # Core Bedrock + Snowflake logic
│   ├── run_baseline_test.py
│   └── ask_questions.py
├── .env.example
├── .gitignore
└── requirements.txt
```

## Quick start (Phase 1)

### 1. Install dependencies

```bash
cd ~/Documents/GitHub/personal_build
scripts/py -m pip install -r requirements.txt
```

**Important:** On this Mac, plain `python` points at Homebrew (no packages). Always use:

```bash
scripts/py scripts/diagnose_bedrock.py
scripts/py src/run_baseline_test.py
scripts/py src/ask_questions.py
```

Or the full path: `/opt/anaconda3/bin/python`

### 2. Configure Snowflake (local only — never committed)

```bash
cp config/snowflake_config.example.py config/snowflake_config.py
# Edit config/snowflake_config.py with your credentials
```

### 3. Configure AWS

```bash
aws sso login
# or: bash scripts/setup_aws.sh
python scripts/diagnose_bedrock.py
```

### 4. Run the POC

```bash
export AWS_PROFILE=Brainfore-Team-Set-654654461736   # your SSO profile

# One-shot test
scripts/py src/run_baseline_test.py

# Interactive questions
scripts/py src/ask_questions.py
```

## Phases

| Phase | Status | Doc |
|-------|--------|-----|
| **1** Baseline NL→SQL (ChatBedrock) | Working | `docs/plans/2026-05-28-002-feat-simple-ai-nl2sql-poc-plan.md` |
| **2** Deep Agents + tool calling | Next | `docs/plans/2026-05-29-003-feat-deep-agents-nl2sql-upgrade-plan.md` |
| **3** Amplify web UI | Planned | Simple plan Days 3–5 |

## Security

- `config/snowflake_config.py` and `.env` are **gitignored**
- Never commit passwords or AWS keys
- See `config/README.md`

## Docs index

See [docs/README.md](docs/README.md)
