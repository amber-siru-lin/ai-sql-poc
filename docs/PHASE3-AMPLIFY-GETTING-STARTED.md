# Phase 3 — Amplify getting started (company AWS)

Use this guide with your **company account** (`654654461736`) and SSO profile **`Brainfore-Team-Set-654654461736`**.

The old simple plan (`2026-05-28-002`) shows **Amplify Gen 1** (`amplify init`). Use **Amplify Gen 2** instead (`npm create amplify@latest`, `npx ampx sandbox`).

**Status (June 2026):** **Active** — `web/` CopilotKit port + Lambda API spike. Local reference remains **`ui/` + `api/`**.

| Track | Folder | Status |
|-------|--------|--------|
| Amplify Gen 2 (AWS deploy) | `web/` | **Active** — [mission plan](plans/2026-06-02-007-feat-amplify-copilotkit-port-plan.md), [deploy kit](../deploy/clients/README.md), [path to production](deploy/path-to-production.md) |
| CopilotKit (local UI) | `ui/` + `api/` | **Active** — [plan](plans/2026-05-29-004-feat-copilotkit-local-ui-plan.md) |

---

## AWS auth — SSO access portal, not IAM user sign-in

Brainforge uses **IAM Identity Center (SSO)**. You do **not** have a traditional IAM username/password for `signin.aws.amazon.com`.

| What | Value |
|------|--------|
| Access portal | `https://d-9067f93bbe.awsapps.com/start` |
| AWS account | `654654461736` (brainforge) |
| Permission set / role | `Brainfore-Team-Set` |
| CLI profile name | `Brainfore-Team-Set-654654461736` |
| Your SSO username | e.g. `ambersiru.lin` (shown in `aws sts get-caller-identity` ARN — **not** for IAM sign-in) |
| Region | `us-east-1` |

**Use the access portal** for the AWS Console: portal → **brainforge** → **Brainfore-Team-Set**.

**Do not use** the IAM user page at `signin.aws.amazon.com` (Account ID + IAM username + password). That page is for old-style IAM users; putting your SSO username there will fail.

For CLI and Amplify:

```bash
export AWS_PROFILE=Brainfore-Team-Set-654654461736
aws sso login --profile $AWS_PROFILE          # opens the access portal in browser
aws sts get-caller-identity --profile $AWS_PROFILE
```

Skip `npx ampx configure profile` if `~/.aws/config` already has the profile below.

### `~/.aws/config` (Brainforge — keep `region` on the profile)

```ini
[profile Brainfore-Team-Set-654654461736]
sso_session = brainforge
sso_account_id = 654654461736
sso_role_name = Brainfore-Team-Set
region = us-east-1

[sso-session brainforge]
sso_start_url = https://d-9067f93bbe.awsapps.com/start
sso_region = us-east-1
sso_registration_scopes = sso:account:access
```

Without `region = us-east-1` on the profile, `ampx sandbox` can fail with **`Region is missing`**.

First-time SSO setup (if profile missing): `aws configure sso` — use the values in the table above.

---

## Before you write code — checklist

| # | Task | How |
|---|------|-----|
| 1 | SSO login | `aws sso login --profile Brainfore-Team-Set-654654461736` |
| 2 | Confirm identity | `aws sts get-caller-identity` → Account `654654461736`, role `AWSReservedSSO_Brainfore-Team-Set_...` |
| 3 | **CDK bootstrap (once per account+region)** | See [CDK bootstrap](#cdk-bootstrap-one-time-before-first-sandbox) — required before first `ampx sandbox` |
| 4 | Bedrock works | From repo root: `scripts/py scripts/diagnose_bedrock.py` |
| 5 | IT / permissions | Amplify, Lambda, IAM, API Gateway, CloudFormation, **Bedrock InvokeModel**, Secrets Manager |
| 6 | Node.js | **Node 22 LTS** recommended; Node 25 needs `NODE_OPTIONS="--no-webstorage"` for `ampx` |
| 7 | Decide harness | **Start with Phase 1 (ChatBedrock) in Lambda** — smaller, faster to deploy. Add Deep Agents later (heavy packages). |

---

## Architecture (Phase 3 v1)

```
Browser (React in web/)
    → Amplify Gen 2 Function URL or API
        → Python Lambda
            → ChatBedrock (Nova Pro)     ← same logic as src/nl2sql.py
            → Snowflake                  ← creds from Secrets Manager
    ← JSON { question, sql, columns, rows, answer }
```

Deep Agent (Phase 2) can replace the Lambda handler later — same UI.

---

## Repo layout (add `web/` — do not touch Python `src/` yet)

```
ai-sql-poc/
├── src/                    # Python Phase 1 + 2 (CLI — keep working)
├── web/                    # NEW — all Amplify + React lives here
│   ├── amplify/
│   │   ├── backend.ts
│   │   └── functions/
│   │       └── query/      # Python Lambda
│   ├── src/                # React (Vite)
│   ├── package.json
│   └── amplify_outputs.json   # generated — gitignore or commit per team policy
├── config/                 # local CLI only
└── docs/
```

Optional later: rename `src/` → `backend/` so Python vs React is obvious.

---

## Step 1 — Create the web app (30 min)

From repo root:

```bash
export AWS_PROFILE=Brainfore-Team-Set-654654461736
aws sso login --profile $AWS_PROFILE

cd ~/Documents/GitHub/personal_build
mkdir -p web && cd web

npm create vite@latest . -- --template react-ts
npm install
npm install aws-amplify
```

---

## Step 2 — Add Amplify Gen 2 (30 min)

Still in `web/`:

```bash
npm create amplify@latest
```

When prompted:

| Prompt | Choose |
|--------|--------|
| TypeScript | Yes |
| AWS profile | `Brainfore-Team-Set-654654461736` (or profile name matching your SSO) |
| Region | `us-east-1` (same as Bedrock) |
| Deploy sandbox now? | Yes (or run sandbox manually in Step 4) |

This creates `web/amplify/backend.ts` and related files.

---

## Step 3 — Add a Python Lambda function (1 hr)

In Amplify Gen 2, add a function under `web/amplify/functions/query/`.

**Handler goal:** call the same logic as `src/nl2sql.py` (`ask_ai` + `run_sql`).

**Secrets (never in git):**

1. AWS Console → Secrets Manager → Create secret:
   - Name: `ai-sql-poc/snowflake`
   - JSON: `{ "account", "user", "password", "warehouse", "database", "schema" }`
2. Grant Lambda execution role `secretsmanager:GetSecretValue` on that secret.
3. Grant `bedrock:InvokeModel` / inference profile access for `us.amazon.nova-pro-v1:0`.

**Lambda IAM (minimum):**

- `bedrock:InvokeModel` (or inference profile ARN)
- `secretsmanager:GetSecretValue` (Snowflake secret)
- CloudWatch Logs

Copy `schema/tpch_sf1.md` content into the Lambda package or read from bundled file.

> **Package size:** Phase 1 (`langchain-aws` + `snowflake-connector-python`) usually fits a Lambda zip. Phase 2 (`deepagents` + `langgraph`) may need a **Lambda container image** — defer until Phase 1 web works.

---

## CDK bootstrap (one-time, before first sandbox)

Amplify Gen 2 uses AWS CDK. The account/region must be **bootstrapped** once before the first sandbox deploy.

**Symptom if skipped:**

```text
The region us-east-1 has not been bootstrapped.
Sign in to the AWS console as a Root user or Admin to complete the bootstrap process.
```

**Who runs it:** Someone with **admin** (or equivalent) on account `654654461736` — often IT or account owner. Your `Brainfore-Team-Set` role may or may not have permission; try once, then ask admin if access denied.

**Console sign-in for bootstrap:** Still use the **access portal** (not IAM user sign-in) → brainforge → Brainfore-Team-Set.

**CLI (from any machine with admin SSO/credentials):**

```bash
export AWS_PROFILE=Brainfore-Team-Set-654654461736
aws sso login --profile $AWS_PROFILE

# One-time per account + region
npx cdk bootstrap aws://654654461736/us-east-1 --profile $AWS_PROFILE
```

Alternative from `web/` (same effect):

```bash
cd web
NODE_OPTIONS="--no-webstorage" npx ampx sandbox --profile Brainfore-Team-Set-654654461736 --once
# If bootstrap error appears, run cdk bootstrap above, then retry sandbox
```

After bootstrap succeeds, CloudFormation creates a `CDKToolkit` stack in `us-east-1`. You only do this once per account/region (unless IT deletes it).

### Stuck `CDKToolkit` stack (`DELETE_FAILED`)

If bootstrap fails with:

```text
Stack ... CDKToolkit ... is in DELETE_FAILED state and can not be updated.
```

A previous bootstrap was partially deleted. **Admin must fix in CloudFormation console** (access portal → brainforge → Brainfore-Team-Set):

1. Open **CloudFormation** → **us-east-1** → stack **`CDKToolkit`**
2. If status is `DELETE_FAILED`, delete retained resources (often an S3 bucket `cdk-*-assets-*`) then **Delete stack** again
3. Re-run: `npx cdk bootstrap aws://654654461736/us-east-1 --profile Brainfore-Team-Set-654654461736`

Until this is cleared, `ampx sandbox` will keep reporting that the region is not bootstrapped.

---

## Step 4 — Run sandbox (dev environment)

```bash
cd web
export AWS_PROFILE=Brainfore-Team-Set-654654461736
aws sso login --profile $AWS_PROFILE

# Node 25 workaround (prefer Node 22 LTS via nvm if you can)
NODE_OPTIONS="--no-webstorage" npx ampx sandbox \
  --profile Brainfore-Team-Set-654654461736
```

- Deploys backend to **your** company account (sandbox stack).
- Watches for file changes.
- Writes `amplify_outputs.json` for the React app.

Keep this terminal running while developing.

Single deploy without watch:

```bash
NODE_OPTIONS="--no-webstorage" npx ampx sandbox \
  --profile Brainfore-Team-Set-654654461736 --once
```

---

## Step 5 — Wire React to the API (1 hr)

In `web/src/App.tsx`:

1. Import `amplify_outputs.json` and configure Amplify.
2. Call your function URL / API route with `{ question: "..." }`.
3. Show loading state (15–30s).
4. Display `sql`, table rows, and text answer.

Test question: *What is the total amount of all orders?*

---

## Step 6 — `.gitignore` updates

Add to repo `.gitignore`:

```
web/node_modules/
web/dist/
web/.amplify/
web/amplify_outputs.json   # optional: some teams commit this
```

---

## Step 7 — Deploy a shared URL (when sandbox works)

```bash
cd web
npx ampx pipeline-deploy --branch main --app-id <your-amplify-app-id>
```

Or connect the GitHub repo in **AWS Amplify Console** → Host web app → auto-deploy on push.

---

## Common company-account issues

| Problem | Fix |
|---------|-----|
| Redirected to **IAM user sign-in** (`signin.aws.amazon.com`) | Wrong page — use **access portal** + `aws sso login`. Do not use `npx ampx configure profile` if SSO profile already exists. |
| `Region is missing` / `InvalidCredentialError` | Add `region = us-east-1` under your profile in `~/.aws/config`; pass `--profile Brainfore-Team-Set-654654461736` |
| `Unable to locate credentials` | `export AWS_PROFILE=...` + `aws sso login` |
| `localStorage.getItem is not a function` (Node 25) | `NODE_OPTIONS="--no-webstorage"` or switch to Node 22 LTS |
| **`us-east-1 has not been bootstrapped`** | Run [CDK bootstrap](#cdk-bootstrap-one-time-before-first-sandbox) once (admin) |
| **`CDKToolkit` in `DELETE_FAILED`** | Admin: delete stuck CloudFormation stack + S3 assets, then re-bootstrap (see Phase 3 doc) |
| Bedrock access denied on Lambda | Add Bedrock policy to **Lambda execution role**, not just your user |
| Inference profile required | Use `us.amazon.nova-pro-v1:0` in Lambda (same as CLI) |
| Snowflake connection fails from Lambda | Check secret JSON keys; warehouse must be running |
| Sandbox blocked by org policy | Ask IT to allow Amplify + Lambda + CloudFormation in `654654461736` |

---

## Suggested order for you this week

1. **Today:** Steps 1–2 (create `web/`, Amplify Gen 2 scaffold)
2. **Day 2:** Step 3 — Python Lambda with Phase 1 `ask_ai` / `run_sql` + Secrets Manager
3. **Day 3:** Steps 4–5 — sandbox + minimal React chat UI
4. **Day 4:** Polish UI, error messages, loading states
5. **Later:** Swap Lambda handler to Deep Agent (Phase 2) or add `--verbose` trace to UI

---

## What stays local vs cloud

| Item | Local CLI (`src/`) | Amplify Lambda |
|------|-------------------|----------------|
| AWS auth | SSO profile on laptop | Execution role |
| Snowflake creds | `config/snowflake_config.py` | Secrets Manager |
| Bedrock model | `us.amazon.nova-pro-v1:0` | Same |
| Phase 1 / 2 | Both work today | Start with Phase 1 only |

---

## Related docs

- [PHASES.md](PHASES.md) — which files belong to each phase
- [2026-05-28-002 simple plan](plans/2026-05-28-002-feat-simple-ai-nl2sql-poc-plan.md) — original Amplify sketch (Gen 1 — use this doc instead)
