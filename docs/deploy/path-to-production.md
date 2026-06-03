# Path to production (Amplify + Lambda + Postgres)

How this repo moves from **local dev** to **client-ready production**, and what to provision at each stage.

**Related:** [deploy/clients/README.md](../../deploy/clients/README.md) · [secrets-checklist.md](../../deploy/clients/_template/secrets-checklist.md) · [PHASE3-AMPLIFY-GETTING-STARTED.md](../PHASE3-AMPLIFY-GETTING-STARTED.md) · [novice-aws-amplify-and-this-poc.md](../guides/novice-aws-amplify-and-this-poc.md)

---

## What runs where today (June 2026)

| Capability | Local (`api/` + Docker) | Lambda (sandbox Function URL) |
|------------|-------------------------|-------------------------------|
| NL→SQL agent + CopilotKit UI | ✅ `ui/` or `web/` → `127.0.0.1:8000` | ✅ `api.main` image; UI often hybrid → local API |
| Chat history / checkpoints (Postgres) | ✅ Docker `ai-sql-poc-postgres` | ❌ in-memory unless `LAMBDA_DATABASE_URL` set |
| Audit log (S3) | ✅ when `AUDIT_S3_BUCKET` in `.env` | ✅ wired from repo `.env` at sandbox deploy |
| Snowflake | ✅ `config/snowflake_config.py` | ✅ baked in image (sandbox); prefer SM in prod |
| Cognito auth | — | ✅ sandbox outputs; optional `VITE_REQUIRE_AUTH` |
| Amplify Hosting (public UI) | — | ⏸ IAM `AmplifySSRLoggingRole` blocker — use Vite dev |
| CopilotKit **SSE streaming** on Lambda | ✅ local | ⏸ needs Lambda Web Adapter or stay on local API |

---

## Four phases (recommended progression)

### Phase A — Local product loop (**default daily dev**)

**Goal:** Build features without cloud DB cost or VPC complexity.

```bash
docker start ai-sql-poc-postgres   # or: docker compose up -d
export AWS_PROFILE=Brainfore-Team-Set-654654461736
aws sso login --profile "$AWS_PROFILE"
./scripts/py -m uvicorn api.main:app --reload --port 8000

cd web && cp .env.example .env.local   # VITE_API_URL=http://127.0.0.1:8000
npm run dev -- --host 127.0.0.1 --port 5174
```

- Postgres: **Docker only** (`DATABASE_URL` → `localhost:5432`).
- Reference stack **`ui/` + `api/`** on 5173/8000 remains valid; do not break it.

**Exit criteria:** Chat, sessions, audit, semantic editor work locally; `npm run build` in `web/` passes.

---

### Phase B — Cloud API on Lambda (**sandbox / POC**)

**Goal:** Prove `api.main` on **Function URL** with real audit + Snowflake + Bedrock; optional cloud Postgres for sessions.

**Already in repo:**

- `web/amplify/backend.ts` — Docker Lambda, Function URL (`BUFFERED` for Mangum JSON).
- `web/amplify/loadRepoEnv.ts` — reads repo `.env` at deploy (audit bucket, etc.).
- `LAMBDA_DATABASE_URL` — if set and **not** `localhost`, copied to Lambda as `DATABASE_URL`.

```bash
cd web
NODE_OPTIONS="--no-webstorage --max-old-space-size=8192" \
  npx ampx sandbox --profile "$AWS_PROFILE" --once
```

**Do not require Aurora in this phase.** Personal `ampx sandbox` stacks are for iteration, not long-lived prod data.

**Exit criteria:**

- `curl -s "$FUNCTION_URL/api/status"` → `"status":"ok"`, audit `s3_status: ok`.
- One successful agent turn (local API if Lambda SSE not ready yet).

---

### Phase B2 — Cloud Postgres for Lambda sessions (**optional bridge**)

**Goal:** Chat history and checkpoints on the **Function URL** without VPC/Aurora yet.

Use any **Internet-reachable** Postgres with TLS:

| Option | Pros | Cons |
|--------|------|------|
| **Supabase** / **Neon** / **Railway** | Fast setup, public connection string, good for POC | Not in your AWS account; data residency / compliance |
| **RDS with public access** | Stays in AWS | Security review; still not “private Aurora” |

1. Create a project; copy the **PostgreSQL connection URI** (pooler URL if offered).
2. Add to repo `.env` (gitignored):

   ```bash
   LAMBDA_DATABASE_URL=postgresql://user:pass@host:5432/dbname?sslmode=require
   ```

3. Redeploy sandbox (`ampx sandbox --once`).
4. Verify: `/api/status` → `checkpoint.backend: postgres`, `sessions.available: true`.

**App code is the same** as Aurora — only the URL and network path differ.

**Exit criteria:** Lambda-backed UI (`VITE_API_URL` = Function URL) shows chat history after redeploy.

---

### Phase C — AWS-shaped staging (**dev/staging account**)

**Goal:** Match production architecture: **private Aurora**, **Lambda in VPC**, **RDS Proxy**, **Secrets Manager**.

Typical new resources (not in sandbox CDK today — add a stable stack or separate CDK app):

- Aurora PostgreSQL in **private subnets**
- **RDS Proxy** (recommended for Lambda concurrency)
- Lambda **VPC** attachment + security groups (5432 → proxy → Aurora)
- `DATABASE_URL` in **Secrets Manager** (not plaintext in `environment`)
- Snowflake JSON in SM; `npx ampx sandbox secret set` or pipeline secrets

Work through [deploy/clients/_template/secrets-checklist.md](../../deploy/clients/_template/secrets-checklist.md).

**Exit criteria:** No `localhost` in Lambda env; sessions survive cold starts; restore drill documented.

---

### Phase D — Production per client

**Goal:** Repeat Phase C per [deploy/clients/](../../deploy/clients/) manifest — separate account or isolated env, Hosting or CI, portability proof.

- `pipeline-deploy` / branch per environment
- Amplify Hosting when `AmplifySSRLoggingRole` exists (or CI → `dist/`)
- Second-account deploy proof (Unit 8) or documented waiver
- Monitoring, backups, least-privilege IAM

---

## Should you provision Aurora in the personal sandbox?

| Answer | When |
|--------|------|
| **Usually no** | You are still on Phase A/B; Docker + local API is enough. |
| **Use Phase B2 first** | You need Lambda-hosted chat history **this week** — Supabase/Neon + `LAMBDA_DATABASE_URL`. |
| **Yes (Phase C)** | Client deploy, private network, compliance, or team staging that must mirror prod. |

Aurora in a **throwaway sandbox** adds cost, VPC work, and state you may delete with the sandbox. Prefer a **named dev/staging stack** for Aurora.

---

## Supabase vs Aurora — what to pick next

| Your question | Recommendation |
|---------------|----------------|
| “Easiest way to get Postgres on Lambda?” | **Supabase or Neon** (Phase B2) — ~30 minutes, no VPC CDK. |
| “What does production look like?” | **Private Aurora + VPC + RDS Proxy + SM** (Phase C/D) — days, ops-owned. |
| “What should I do tomorrow?” | Stay **Phase A** for feature work; only add Supabase if you **must** demo history on the Function URL. |

You do **not** need both. Supabase is a **stepping stone**, not a replacement for production Aurora in AWS.

---

## Environment variables (cheat sheet)

| Variable | Where | Purpose |
|----------|--------|---------|
| `DATABASE_URL` | Local `.env` | Docker Postgres (`localhost`) |
| `LAMBDA_DATABASE_URL` | Local `.env` | Cloud Postgres URL for Lambda only (skip if localhost) |
| `AUDIT_S3_BUCKET` | `.env` → Lambda via `loadRepoEnv` | Audit writes |
| `VITE_API_URL` | `web/.env.local` | UI → local API **or** Function URL |
| Snowflake | `config/snowflake_config.py` (local) / SM (prod) | Queries |

See [.env.example](../../.env.example) and [web/.env.example](../../web/.env.example).

---

## Suggested next steps (in order)

1. **Default:** Keep **Phase A** — Docker Postgres + `web/.env.local` → `http://127.0.0.1:8000` until Lambda SSE and Hosting are sorted.
2. **If demoing cloud-only UI:** Complete Phase B checks (`/api/status`, audit OK on Function URL).
3. **If demoing cloud chat history:** Phase B2 — **Supabase/Neon** + `LAMBDA_DATABASE_URL` + sandbox redeploy (not Aurora yet).
4. **Before a client go-live:** Phase C — Aurora + VPC + secrets checklist + second account proof.

---

## Open engineering items (not blocked by Postgres choice)

- CopilotKit **streaming** on Lambda (Lambda Web Adapter; Mangum + `BUFFERED` URL is status-only friendly).
- Snowflake + DB credentials in **Secrets Manager** (remove baked `snowflake_config.py` from image for prod).
- Amplify **Hosting** IAM role for console builds.
- Full **IAM** on Lambda for all tools (already started: Bedrock, audit S3).

---

## Diagram

```mermaid
flowchart TB
  subgraph phaseA [Phase A - Local]
    Docker[(Docker Postgres)]
    API[api.main :8000]
    Vite[web Vite :5174]
    Vite --> API
    API --> Docker
  end

  subgraph phaseB [Phase B - Lambda POC]
    Lambda[Lambda Function URL]
    S3[S3 audit]
    SF[Snowflake / Bedrock]
    Lambda --> S3
    Lambda --> SF
  end

  subgraph phaseB2 [Phase B2 - Optional]
    Hosted[(Supabase / Neon)]
    Lambda --> Hosted
  end

  subgraph phaseC [Phase C/D - Production]
    Aurora[(Private Aurora)]
    VPC[VPC + RDS Proxy]
    SM[Secrets Manager]
    LambdaProd[Lambda in VPC]
    LambdaProd --> VPC
    VPC --> Aurora
    SM --> LambdaProd
  end

  phaseA --> phaseB
  phaseB --> phaseB2
  phaseB2 --> phaseC
```
