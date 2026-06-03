# Client deploy kit (Amplify Gen 2)

Deploy the NL→SQL app in **`web/`** to another AWS account without forking application code.

## Prerequisites (per account + region)

1. **CDK bootstrap** once: `npx cdk bootstrap aws://ACCOUNT_ID/REGION --profile YOUR_PROFILE`
2. **SSO / CLI profile** with Amplify deploy rights (CloudFormation, Lambda, Cognito, IAM for execution roles — not necessarily `iam:CreateRole` for Hosting)
3. **Bedrock** — model access (e.g. `us.amazon.nova-pro-v1:0`) on the **Lambda execution role**
4. **Snowflake** — credentials in Secrets Manager (JSON keys match app expectations)
5. **Audit S3** — bucket in the **same account** (reuse existing bucket name via env, or create a new bucket)
6. **Postgres (recommended)** — Aurora/RDS + `DATABASE_URL` secret for LangGraph checkpoints and chat sessions

## Quick start (developer sandbox)

```bash
export AWS_PROFILE=your-profile-name
aws sso login --profile "$AWS_PROFILE"

cd web
npm ci
# 8GB heap avoids CDK synth OOM when packaging the Docker Lambda asset
NODE_OPTIONS="--no-webstorage --max-old-space-size=8192" npx ampx sandbox --profile "$AWS_PROFILE"
```

Copy the **Function URL** from sandbox output or CloudWatch/Lambda console into `web/.env.local`:

```bash
VITE_API_URL=https://xxxxxxxx.lambda-url.us-east-1.on.aws
VITE_COPILOT_RUNTIME_URL=$VITE_API_URL/copilotkit
```

```bash
npm run dev -- --host 127.0.0.1 --port 5174
```

Reference UI stays on **`ui/` + `api/`** at ports 5173/8000 — do not break that path while developing `web/`.

## Per-client manifest

1. Copy `_template/` to `clients/<client-slug>/`
2. Fill `client.env.example` values (never commit real secrets)
3. Work through `secrets-checklist.md`
4. Set Amplify secrets: `npx ampx sandbox secret set SECRET_NAME --profile ...`
5. Deploy; record `amplify_outputs.json` and Function URL in your runbook (not in git)

## Amplify Hosting (optional)

Console **Hosting build** may require admin to create `AmplifySSRLoggingRole` (`iam:CreateRole`). Until then, use **Vite dev** or CI build + admin-connected Hosting.

## Cross-account production

See [Amplify cross-account deployments](https://docs.amplify.aws/react/deploy-and-host/fullstack-branching/cross-account-deployments/) — backend `pipeline-deploy` per account/branch, then `ampx generate outputs` for the frontend build.

## Portability proof (Unit 8)

**Target:** Deploy sandbox in a **second** AWS account with only profile + secrets + manifest changes — no application source edits.

**Recorded status (2026-06-03):** Waiver — second-account deploy not executed in this mission run. Brainforge account `654654461736` is the only validated target so far.

**Proof steps when a second account is available:**

1. `npx cdk bootstrap aws://OTHER_ACCOUNT/us-east-1 --profile OTHER_PROFILE`
2. Copy `deploy/clients/_template/` → `deploy/clients/<client-slug>/` and fill manifest + `secrets-checklist.md`
3. `aws sso login --profile OTHER_PROFILE`
4. `cd web && NODE_OPTIONS="--no-webstorage" npx ampx sandbox --profile OTHER_PROFILE --once`
5. Confirm `amplify_outputs.json` includes `custom.apiFunctionUrl`; `curl "$URL/api/status"`
6. Build frontend with `VITE_API_URL` from that URL; smoke-test chat SSE on `POST /`
7. Confirm audit objects land only in that account’s S3 bucket (not Brainforge’s)

**Waiver reason:** No second SSO profile / account was available during mission execution. Kit structure (`deploy/clients/`, env templates, docs) satisfies R4 documentation; runtime proof is deferred.

## Path to production

Phased plan (local Docker → Lambda POC → optional Supabase/Neon → Aurora/VPC prod):

**[docs/deploy/path-to-production.md](../docs/deploy/path-to-production.md)**

## Docs

- [docs/PHASE3-AMPLIFY-GETTING-STARTED.md](../docs/PHASE3-AMPLIFY-GETTING-STARTED.md)
- [docs/deploy/path-to-production.md](../docs/deploy/path-to-production.md)
- [docs/plans/2026-06-02-007-feat-amplify-copilotkit-port-plan.md](../docs/plans/2026-06-02-007-feat-amplify-copilotkit-port-plan.md)
- [docs/guides/novice-aws-amplify-and-this-poc.md](../docs/guides/novice-aws-amplify-and-this-poc.md)
