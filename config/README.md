# Config

| File | Committed? | Purpose |
|------|------------|---------|
| `snowflake_config.example.py` | Yes | Template — copy and rename |
| `snowflake_config.py` | **No** (gitignored) | Snowflake credentials + optional dataset labels |
| `settings.py` | Yes | Reads env + `snowflake_config` overrides (Bedrock, schema paths, labels) |

**Guided setup (recommended):** `./scripts/onboard.sh`

```bash
cp config/snowflake_config.example.py config/snowflake_config.py
# Edit snowflake_config.py with client database, schema, and credentials
cp .env.example .env
# Set AWS_PROFILE, AWS_REGION, BEDROCK_MODEL_ID, AUDIT_S3_BUCKET as needed
```

## AWS credentials

Use standard AWS CLI setup — not files in this folder:

```bash
aws configure sso          # first time
export AWS_PROFILE=your-org-profile-name
aws sso login --profile "$AWS_PROFILE"
scripts/py scripts/diagnose_bedrock.py
```

## Key settings

| Setting | Where | Purpose |
|---------|-------|---------|
| `database`, `schema` | `snowflake_config.py` | Client Snowflake target |
| `dataset_label` | `snowflake_config.py` | UI + API display name |
| `schema_markdown_path` | `snowflake_config.py` | Markdown schema for Off mode |
| `AWS_PROFILE` | `.env` or shell | SSO profile name |
| `BEDROCK_MODEL_ID` | `.env` | Model enabled in client account |
| `AUDIT_S3_BUCKET` | `.env` | Query audit log bucket |

See [SETUP.md](../SETUP.md) and [docs/CLIENT-CREDENTIALS.md](../docs/CLIENT-CREDENTIALS.md).
