---
title: Amplify Gen 2 sandbox blocked on CDK bootstrap
date: 2026-05-29
category: aws-deployment
tags:
  - amplify
  - cdk
  - sso
  - brainforge
  - phase-3
status: resolved
account_id: "654654461736"
region: us-east-1
---

# Amplify Gen 2 sandbox blocked on CDK bootstrap (historical)

> **Update (2026-06):** Bootstrap succeeded; sandbox deploy works. Use [deploy/clients/README.md](../../deploy/clients/README.md) for new accounts. Hosting UI build may still require admin `iam:CreateRole`.

## Symptom

`npx ampx sandbox` fails in account `654654461736`, region `us-east-1`:

```text
The region us-east-1 has not been bootstrapped.
Sign in to the AWS console as a Root user or Admin to complete the bootstrap process.
```

Re-running bootstrap fails with:

```text
Stack ... CDKToolkit ... is in DELETE_FAILED state and can not be updated.
```

## Root cause

1. **Amplify Gen 2 requires CDK bootstrap** — there is no supported bypass for `ampx sandbox`.
2. A prior **`CDKToolkit`** CloudFormation stack exists but is stuck in **`DELETE_FAILED`** (partial cleanup).
3. **`Brainfore-Team-Set`** permission set does **not** include rights to fix or re-bootstrap the stack.

## What we tried

| Step | Result |
|------|--------|
| Add `region = us-east-1` to SSO profile in `~/.aws/config` | Fixed `Region is missing` |
| `NODE_OPTIONS="--no-webstorage"` on Node 25 | Fixed `localStorage.getItem is not a function` |
| `aws sso login` + `--profile Brainfore-Team-Set-654654461736` | Credentials OK (`aws sts get-caller-identity` works) |
| `npx cdk bootstrap aws://654654461736/us-east-1` | Blocked by `CDKToolkit` `DELETE_FAILED` |

## SSO vs IAM user sign-in (learning)

Brainforge uses **IAM Identity Center** (access portal), not IAM user passwords.

- **Use:** `https://d-9067f93bbe.awsapps.com/start` → brainforge → Brainfore-Team-Set
- **Do not use:** `signin.aws.amazon.com` (Account ID + IAM username + password)
- SSO username (e.g. `ambersiru.lin`) appears in STS ARN only — not for IAM sign-in page

## Decision (May 2026)

**Park Amplify Gen 2 path.** Keep `web/` scaffold as-is; do not delete.

**Active Phase 3 path:** CopilotKit + local FastAPI backend — see [CopilotKit plan](../plans/2026-05-29-004-feat-copilotkit-local-ui-plan.md) and [integration learnings](../solutions/copilotkit-local-ui-learnings.md).

## Unblock Amplify later (IT / admin)

1. CloudFormation → `us-east-1` → delete stuck **`CDKToolkit`** (empty retained S3 bucket if needed).
2. Run: `npx cdk bootstrap aws://654654461736/us-east-1 --profile Brainfore-Team-Set-654654461736`
3. Retry: `NODE_OPTIONS="--no-webstorage" npx ampx sandbox --profile ...`

Full checklist: [PHASE3-AMPLIFY-GETTING-STARTED.md](../PHASE3-AMPLIFY-GETTING-STARTED.md)

## Related files

- `web/` — Amplify Gen 2 scaffold (parked)
- `web/README.md` — parked status note
