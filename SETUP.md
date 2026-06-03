# Setup

**New colleague? Run one command from repo root:**

```bash
./scripts/onboard.sh
```

That walks you through prerequisites, config, AWS SSO, Snowflake, verification, and optionally starts the app. Non-interactive alternatives:

```bash
./scripts/setup.sh              # install + scaffold only
./scripts/onboard.sh --check    # verify credentials only
make onboard                    # same as ./scripts/onboard.sh
make dev                        # start API + UI
```

Context and architecture: [ONBOARDING.md](ONBOARDING.md) · secrets matrix: [docs/CLIENT-CREDENTIALS.md](docs/CLIENT-CREDENTIALS.md)

---

## What the guided script does

| Step | Action |
|------|--------|
| 1 | `setup.sh` — Node/Python checks, `pip install`, `npm ci`, create config templates |
| 2 | Prompts for `AWS_PROFILE`, region, Bedrock model, optional audit bucket → writes `.env` |
| 3 | Guides edit of `config/snowflake_config.py` (database, schema, `dataset_label`) |
| 4 | Optional Postgres via Docker |
| 5 | Verifies AWS, Snowflake, Bedrock |
| 6 | Offers to run `./scripts/dev.sh` |

## Manual setup (if you prefer)

### Credentials

```bash
cp config/snowflake_config.example.py config/snowflake_config.py
cp .env.example .env
```

Edit **`config/snowflake_config.py`**: account, user, password, warehouse, **database**, **schema**, `dataset_label`, `schema_markdown_path`.

Edit **`.env`**: `AWS_PROFILE`, `AWS_REGION`, `BEDROCK_MODEL_ID`, optional `AUDIT_S3_BUCKET`.

```bash
export AWS_PROFILE=your-sso-profile
aws sso login --profile "$AWS_PROFILE"
scripts/py scripts/diagnose_bedrock.py
scripts/py scripts/verify_tpch_setup.py
```

### Run

```bash
./scripts/dev.sh
# → http://localhost:5173  (UI)
# → http://localhost:8000/api/status  (API)
```

Or two terminals — see [docs/PHASES.md](docs/PHASES.md) Phase 3.

## Docker note

`docker-compose.yml` is **local Postgres only** for LangGraph checkpoints (optional, dev-only). Not used for Snowflake or Bedrock.
