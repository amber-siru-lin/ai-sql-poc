# Client credentials

Use this when moving the repo into a client monorepo or account.

## Secrets matrix

| Secret / config | File | Who provisions | Required? |
|-----------------|------|----------------|-----------|
| Snowflake account, user, password/key | `config/snowflake_config.py` | Client DBA | Yes |
| Database + schema | `config/snowflake_config.py` | Client DBA | Yes |
| Dataset display name | `config/snowflake_config.py` (`dataset_label`) | Team | Yes |
| Markdown schema path | `config/snowflake_config.py` (`schema_markdown_path`) | Team | Yes for Off mode |
| AWS SSO profile | `~/.aws/config` + `AWS_PROFILE` in `.env` | Client IT | Yes |
| AWS region | `.env` (`AWS_REGION`) | Client IT | Yes |
| Bedrock model ID | `.env` (`BEDROCK_MODEL_ID`) | Client IT | Yes |
| Audit S3 bucket | `.env` (`AUDIT_S3_BUCKET`) | Client platform | Optional |
| Postgres URL | `.env` (`DATABASE_URL`) | Dev: Docker; Prod: RDS | Optional |
| GitHub token (semantic editor PRs) | `.env` (`GITHUB_TOKEN`) | Team | Optional |

**Never commit:** `config/snowflake_config.py`, `.env`, `~/.wren/profiles.yml`, `config/working_model.txt`

## AWS IAM (minimum)

Dev role used by engineers running the API locally:

- `bedrock:InvokeModel` / inference profile for configured model
- `sts:GetCallerIdentity`
- If audit enabled: `s3:PutObject`, `s3:GetObject`, `s3:ListBucket` on audit prefix

## Snowflake (minimum)

- `USAGE` on warehouse, database, schema
- `SELECT` on tables/views in the target schema
- For Wren mode: same physical tables referenced by MDL under `wren/`

## Replacing TPCH sample data

1. Update `config/snowflake_config.py` with client `database` and `schema`
2. Replace or add markdown at `schema_markdown_path` (column/table docs for Off mode)
3. Update Wren MDL under `wren/` if using Wren mode
4. Set `dataset_label` to the client-facing name
5. Run `scripts/py scripts/verify_tpch_setup.py`

## Docker (local dev only)

`docker compose up -d` starts Postgres for checkpoint persistence. Default credentials are for **local containers only**. Do not reuse in client shared environments.
