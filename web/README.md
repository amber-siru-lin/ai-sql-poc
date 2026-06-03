# web/ — Amplify Gen 2 + CopilotKit (NL→SQL)

Hosts the **portable** NL→SQL UI (from `ui/`) and Amplify backend (`amplify/`).

## Status

| Piece | State |
|-------|--------|
| CDK bootstrap + `ampx sandbox` | Working in dev account (see deploy kit) |
| CopilotKit UI in `web/src` | Ported from `ui/` |
| API on Lambda | Docker image spike (`api/lambda_spike.py`); full agent = Unit 7 |
| Amplify Hosting console build | May need admin for `iam:CreateRole` — use `npm run dev` until fixed |

Reference implementation remains **`ui/` + `api/`** on ports 5173/8000.

## Local dev (UI + cloud API)

```bash
export AWS_PROFILE=your-profile
aws sso login --profile "$AWS_PROFILE"

cd web
npm ci
cp .env.example .env.local
# Set VITE_API_URL to sandbox Function URL after deploy

NODE_OPTIONS="--no-webstorage" npx ampx sandbox --profile "$AWS_PROFILE"
npm run dev -- --host 127.0.0.1 --port 5174
```

## Local dev (UI + local API)

Point `.env.local` at localhost and run repo-root `api/` on port 8000 (same as `ui/`).

## Docs

- [deploy/clients/README.md](../deploy/clients/README.md)
- [docs/plans/2026-06-02-007-feat-amplify-copilotkit-port-plan.md](../docs/plans/2026-06-02-007-feat-amplify-copilotkit-port-plan.md)
- [docs/guides/novice-aws-amplify-and-this-poc.md](../docs/guides/novice-aws-amplify-and-this-poc.md)
