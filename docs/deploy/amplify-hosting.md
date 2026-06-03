# Amplify Hosting vs sandbox

## Sandbox (`npx ampx sandbox`)

Deploys **backend** from `web/amplify/` (Cognito, Lambda Function URL, optional AppSync scaffold).

Outputs `amplify_outputs.json` and custom `apiFunctionUrl` in outputs.

**Sandbox deploy tips:** Use `NODE_OPTIONS="--no-webstorage --max-old-space-size=8192"`. Do not put `OPTIONS` in Function URL CORS `allowedMethods` (CloudFormation rejects it). For full LangGraph image, point `backend.ts` at `Dockerfile` (not `Dockerfile.spike`) after heap fix.

## Hosting build (Amplify Console)

Builds the **React** app and serves `dist/` on a public URL.

## Known blocker (Brainforge SSO)

Hosting first-time setup may fail with:

```text
not authorized to perform: iam:CreateRole on ... AmplifySSRLoggingRole-...
```

**Workaround:** Use `cd web && npm run dev` with `VITE_API_URL` set to the sandbox Function URL until IT creates the logging role or grants `iam:CreateRole`.

## Cognito callbacks

When Hosting works, add the exact hosting URL to `web/amplify/auth/resource.ts` `callbackUrls` and `logoutUrls`.
