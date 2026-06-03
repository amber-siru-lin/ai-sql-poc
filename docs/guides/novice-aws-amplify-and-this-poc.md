# Novice guide: AWS, Amplify, and this POC

A plain-language reference for revisiting later. You do **not** need to memorize this — use it when a term shows up in chat, the mission plan, or an error message.

**Last aligned with:** June 2026 · repo layout `ui/` + `api/` + `web/` + `src/`

---

## The biggest misconception (read this first)

### “Moving to Amplify means rebuilding the UI”

**Usually no.**

| What people fear | What actually happens |
|------------------|------------------------|
| Throw away CopilotKit and redesign every screen | **Copy** the existing React layout from `ui/` into `web/` and point it at a new API address |
| Learn a whole new design system from AWS | Amplify gives **login** and **hosting** helpers — not a replacement for your chat UI |
| Rewrite the AI agent in AWS-only code | The **same** Python agent in `src/` runs behind FastAPI — first on your laptop, later in **Lambda** |

**Amplify is mostly about:**

- Where the **built** React app is served (optional public URL)
- **Who can log in** (Cognito)
- Where the **API** runs in AWS (Lambda + Function URL)
- **Secrets and deploy** per account

Your **product UI** (sidebar, chat, SQL cards) stays React + CopilotKit. You are **moving and wiring**, not redesigning from scratch.

---

## What you already have (three homes)

```text
ui/          → Chat app you see in the browser (Vite, port 5173)
api/         → FastAPI server the chat talks to (port 8000)
src/         → Brain: LangGraph agent, Snowflake tools, Bedrock calls

web/         → Future “client deploy” copy: same UI idea + Amplify config
               (amplify/ folder = how AWS resources get created)
```

**Local today:** laptop runs `ui` + `api`. **Cloud tomorrow:** AWS runs the API (Lambda); browser still runs React (your machine or Hosting).

---

## “Local” vs “cloud” — not a simple switch

You were already using **cloud services** on your laptop:

| Piece | Where it really lives |
|-------|------------------------|
| Bedrock (AI model) | AWS |
| Snowflake (data) | Snowflake’s cloud |
| Audit logs (if enabled) | Often **S3** in AWS |
| Vite + FastAPI | **Your laptop** |

**Moving to Amplify** means: move **your app processes** (API, and optionally the built React site) into AWS — not “turn on cloud” from zero.

---

## Glossary (friendly)

### AWS

**Amazon’s platform.** You use pieces of it (login, AI, storage, run code) through the console or CLI.

### SSO / profile (`AWS_PROFILE`)

How **you** (the human) prove who you are when running commands on your Mac.

- **Access portal** = company login page for AWS
- **Profile** = name in `~/.aws/config` that picks account + role

Not the same as Lambda’s role (below).

### IAM

**Who is allowed to do what** in an account.

- Your SSO role might deploy apps but **not** create IAM roles → Hosting build failed with `iam:CreateRole`
- **Lambda execution role** = what the **running API** is allowed to do (Bedrock, S3, read secrets)

### CDK bootstrap

**One-time setup** per AWS account + region so Amplify/CDK can create resources. If someone says “region not bootstrapped,” an admin must fix it once.

### CloudFormation / stack

When you run **sandbox**, AWS creates a named **stack** — a group of resources (Cognito, Lambda, etc.). If deploy fails, open the stack **Events** tab and read the first red line.

---

### Amplify Gen 2

**A way to define backend + frontend deploy** from this repo (`web/amplify/backend.ts`), not a separate product from your chat.

| Piece | What it does for you |
|-------|----------------------|
| `npx ampx sandbox` | Deploy **backend** to **your** cloud sandbox; writes `amplify_outputs.json` |
| `amplify_outputs.json` | Config the React app needs (auth endpoints, etc.) — generated, don’t hand-edit blindly |
| Amplify **Hosting** | Build React and put it on a **public URL** |
| Amplify **UI** (`@aws-amplify/ui-react`) | Pre-made **sign-in / sign-up** screens — optional wrapper around your app |

### Sandbox vs Hosting build

| | Sandbox | Hosting build |
|--|---------|----------------|
| **Deploys** | Backend (Lambda, Cognito, …) | Frontend (`npm run build` → `dist/`) |
| **You run** | `npx ampx sandbox` in terminal | Often Amplify Console “Build” on a branch |
| **Need for mission** | **Yes** | **Nice later** — you can use `npm run dev` + Function URL until IAM is fixed |
| **Your error** | Worked | `AmplifySSRLoggingRole` / `iam:CreateRole` blocked |

**Memory trick:** Sandbox = **plumbing**. Hosting = **put the website on the sign**.

### AppSync

GraphQL API that came with the **default Amplify template** (Todo app). **Your NL→SQL chat does not need it.** You can ignore or remove it from the backend later. Chat goes through **FastAPI**, not AppSync.

### Cognito

**User accounts** for the web app (email login). Localhost POC has no login; hosted demo should.

---

### Lambda

**Run your API code in AWS without a server you manage.**

- On laptop: you start `uvicorn` and keep a terminal open
- On Lambda: AWS runs your function when a request hits the **Function URL**

Same **FastAPI** idea; different **place it runs**.

### Function URL

An **https://…** address that triggers your Lambda. The React app’s `VITE_API_URL` should point here in cloud mode.

### Container Lambda

Your agent has **large** Python dependencies (LangGraph, Snowflake, etc.). A **container image** is a packaged box AWS runs — not a tiny zip. The mission assumes this for the real agent.

### SSE / streaming (not “Lambda SSE”)

**Server-Sent Events** = the answer arrives in **chunks** over time (like ChatGPT typing).

- Chat **needs** streaming from the API
- If Lambda only returns one big response at the end, the UI feels broken or shows “network error”

Locally, FastAPI already streams. In AWS, you must enable **response streaming** on the Function URL.

---

### FastAPI

The Python **web server** in `api/main.py`. Stays in the mission — it moves **into** Lambda, not replaced by Amplify.

### CopilotKit

The **chat UI library** (sidebar, messages, tool cards). **Keep it** when moving to `web/`. Amplify does not replace it.

### AG-UI / HttpAgent

The **wire protocol** between CopilotKit’s chat and your FastAPI agent (`POST /` with streaming). Two URLs on port 8000:

| URL | Purpose |
|-----|---------|
| `/` | Real chat (AG-UI) |
| `/copilotkit` | Small stub so CopilotKit’s “info” check succeeds |

### UI shell port

**Copy** layout pieces from `ui/src` to `web/src`: sidebar, AppShell, audit page shell — then connect config. **Not** a network port like 5173.

---

### Postgres vs Aurora PostgreSQL

Both speak the **same SQL** your app uses.

| | Postgres (Docker / RDS) | Aurora PostgreSQL |
|--|-------------------------|-------------------|
| **Plain English** | One database server you rent or run locally | AWS’s fancier managed cluster version |
| **Local dev** | `docker compose` in this repo | Don’t run Aurora on your laptop — use Docker Postgres locally |
| **Cloud** | Fine for POC | Common for “real” production |
| **App code** | Same `DATABASE_URL` style connection string | Same |

**Checkpointer** = LangGraph saving conversation state per `thread_id`. Works with Postgres when `DATABASE_URL` is set (`src/checkpoint_factory.py`).

---

### S3 and audit

**S3** = file storage in AWS. Each **audit run** is a JSON file (question, SQL, timing, etc.).

| Question | Answer |
|----------|--------|
| New bucket for Amplify mission? | **Same account:** usually **reuse** existing audit bucket env var |
| New client AWS account? | **New bucket in that account** |
| `?source=api` on audit API | Filter **inside** the same data — not “a different bucket” |

---

### Secrets Manager vs `.env` on laptop

| Local | Cloud |
|-------|-------|
| `config/snowflake_config.py`, `.env` | **Secrets Manager** + Amplify `secret()` — never commit passwords |

---

### Terraform

**Another** infrastructure language. This repo already uses **Amplify → CDK → CloudFormation**. You do **not** need Terraform to start the mission unless your IT team standardizes on it separately.

---

### Wren / semantic layer / editor

| Term | Meaning |
|------|---------|
| **Semantic layer toggle** | Off / Wren / Cortex — changes which tools the agent uses |
| **Wren** | Extra semantic engine; needs CLI + files under `wren/tpch/` — hard in Lambda |
| **Editor view** | Third screen in `ui/` for editing YAML + PRs — **not** in first Amplify mission |

---

## Four kinds of “memory” (easy to mix up)

| What | Where | Survives closing laptop? |
|------|-------|---------------------------|
| **Chat UI snapshots** | Browser `localStorage` | Same browser only |
| **Agent thread memory** | Postgres or RAM on API | Postgres yes; RAM no |
| **Audit history** | S3 (and maybe local files in dev) | Yes |
| **Wren recall** | Files under `wren/tpch/target/` | On disk where built |

Sidebar **chat history** today is built from **audit**, not a perfect chat replay.

---

## How far is “production”?

| Level | What you have |
|-------|----------------|
| **Personal POC** | Local UI + API, real Bedrock + Snowflake — **you are here** |
| **Cloud demo** | Lambda + Cognito + S3 audit + optional Postgres in AWS — **mission target** |
| **True production** | Monitoring, multi-env, security review, HA database, cost controls, runbooks — **later, team effort** |

---

## Common confusions (quick answers)

**“I have Amplify access but Hosting failed.”**  
Different permissions. Sandbox deploy ≠ permission to **create IAM roles** for Hosting logging.

**“Do I need AppSync?”**  
No for this chat app.

**“Is AWS just cloud vs local?”**  
Your API is local; Bedrock/Snowflake/S3 were already remote. You’re moving **the API (and maybe the built UI)**.

**“Do I rebuild the agent?”**  
No — reuse `src/`. Package `api/main.py` for Lambda.

**“What’s the first hard technical step?”**  
Unit 2: Lambda + **streaming** + container — prove `curl` or chat gets SSE from Function URL.

**“Can I skip Hosting?”**  
Yes for a long time: `npm run dev` in `web/` + Function URL from sandbox.

**“network error” in chat**  
Often API crashed mid-stream (e.g. missing checkpointer), not Wi‑Fi. Check API/Lambda logs.

**“reading 'length'” on load**  
React bug — usually `sessions` not passed to sidebar; default to `[]`.

---

## What to learn yourself vs let AI implement

| You should touch | AI can draft |
|------------------|--------------|
| `aws sso login`, `sts get-caller-identity` | Copying React files `ui/` → `web/` |
| One chat request in Network tab + API logs | Dockerfile / `backend.ts` |
| CloudFormation Events when sandbox fails | Client manifest templates |
| “Does status endpoint work?” `curl` | Tests |
| IAM errors in plain English — ask IT with exact message | Large refactors |

**Rule:** After each milestone, **you** run one command and open **one** AWS console page so failures feel familiar.

---

## Suggested reading order in this repo

1. This file (you are here)
2. `docs/solutions/copilotkit-local-ui-learnings.md` — two URLs, fetch, checkpointer
3. `docs/solutions/chat-memory-and-session-learnings.md` — four stores
4. `docs/PHASE3-AMPLIFY-GETTING-STARTED.md` — account checklist
5. `docs/plans/2026-06-02-007-feat-amplify-copilotkit-port-plan.md` — when you run the mission

---

## One-page picture

```text
Browser (React + CopilotKit)
    │
    ├─ sign in? ──► Cognito (Amplify auth)     [hosted / later]
    │
    └─ chat ──► HttpAgent ──► FastAPI
                    │              │
                    │              ├─ LangGraph + src/ tools
                    │              ├─ Bedrock
                    │              ├─ Snowflake (secret)
                    │              ├─ Postgres? (thread memory)
                    │              └─ S3 audit writes

Today:  FastAPI on laptop (8000), UI on laptop (5173)
Mission: FastAPI in Lambda (Function URL), UI in web/ (5174 dev or Hosting later)
```

---

## When something breaks — where to look

| Symptom | First place |
|---------|-------------|
| CLI / sandbox deploy | Terminal output → CloudFormation Events |
| Chat send fails | Browser Network tab → Lambda **CloudWatch** logs |
| Status badge red | `curl …/api/status` |
| Blank sidebar | React props / `AGENTS.md` sessions chain |
| Hosting build | IAM / ask admin for AmplifySSRLoggingRole |
| Forgot password / login | Cognito user pool in console |

---

*Questions to add later: write them at the bottom of this file as you learn.*
