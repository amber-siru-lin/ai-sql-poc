# Secrets & IAM checklist (per client account)

## Secrets (never in git, never in Amplify `environment` plaintext)

| Secret / var | Purpose | Set via |
|--------------|---------|---------|
| Snowflake JSON | Warehouse queries | Secrets Manager + `secret('...')` in Lambda |
| `DATABASE_URL` | LangGraph + chat sessions Postgres | Amplify secret / SM |
| `AUDIT_S3_BUCKET` | Query audit JSON | Env on Lambda (bucket name is not secret) |

## Lambda execution role (minimum)

- `bedrock:InvokeModel` (or inference profile ARN used by the app)
- `secretsmanager:GetSecretValue` on Snowflake + DB secrets
- `s3:GetObject`, `s3:PutObject`, `s3:ListBucket` on audit bucket/prefix
- CloudWatch Logs
- **VPC** ENI permissions if Lambda reaches private Aurora

## Human SSO role (deployer)

Typically needs CloudFormation, Lambda, Cognito, S3, Amplify — **may not** include `iam:CreateRole` (blocks Hosting UI build; sandbox backend can still work).

## Postgres

- Prefer **Aurora PostgreSQL** or RDS in the **same account**
- Use **RDS Proxy** when Lambda concurrency > 1
- Local dev uses Docker Postgres (`docker compose`); same `DATABASE_URL` shape in cloud

## Verify after deploy

- `curl -s "$VITE_API_URL/api/status"` → `"status":"ok"`
- One chat message streams SSE (no `ERR_INCOMPLETE_CHUNKED_ENCODING` without log crash)
- Audit write appears under `s3://$AUDIT_S3_BUCKET/audit/...`
