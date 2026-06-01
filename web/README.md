# web/ — Amplify Gen 2 (parked)

This folder holds an **Amplify Gen 2 + Vite** scaffold created for Phase 3. It is **not the active development path**.

## Status: blocked

Sandbox deploy requires **CDK bootstrap** in account `654654461736` / `us-east-1`. Bootstrap is blocked by a stuck `CDKToolkit` CloudFormation stack (`DELETE_FAILED`) and insufficient admin permissions on `Brainfore-Team-Set`.

**Do not delete this folder** — it may be useful when IT unblocks bootstrap.

## Learnings & unblock steps

See:

- [docs/solutions/aws-amplify-cdk-bootstrap-blocked.md](../docs/solutions/aws-amplify-cdk-bootstrap-blocked.md)
- [docs/PHASE3-AMPLIFY-GETTING-STARTED.md](../docs/PHASE3-AMPLIFY-GETTING-STARTED.md)

## Active Phase 3 path

CopilotKit local UI — see [docs/plans/2026-05-29-004-feat-copilotkit-local-ui-plan.md](../docs/plans/2026-05-29-004-feat-copilotkit-local-ui-plan.md).

New code goes in **`ui/`** (React) and **`api/`** (FastAPI), not here.

## If sandbox is unblocked later

```bash
export AWS_PROFILE=Brainfore-Team-Set-654654461736
aws sso login --profile $AWS_PROFILE
NODE_OPTIONS="--no-webstorage" npx ampx sandbox --profile $AWS_PROFILE
```
