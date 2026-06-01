# Documentation index

## Start here

| Doc | Purpose |
|-----|---------|
| [PHASES.md](PHASES.md) | **Which files to run for Phase 1, 2, or 3** |
| [PHASE3-AMPLIFY-GETTING-STARTED.md](PHASE3-AMPLIFY-GETTING-STARTED.md) | **Phase 3A (parked):** SSO, CDK bootstrap, Amplify sandbox |
| [plans/2026-05-29-004-feat-copilotkit-local-ui-plan.md](plans/2026-05-29-004-feat-copilotkit-local-ui-plan.md) | **Phase 3B (active):** CopilotKit + `ui/` + `api/` |
| [solutions/aws-amplify-cdk-bootstrap-blocked.md](solutions/aws-amplify-cdk-bootstrap-blocked.md) | Why Amplify is blocked + IT unblock steps |
| [solutions/copilotkit-local-ui-learnings.md](solutions/copilotkit-local-ui-learnings.md) | **Phase 3B:** CopilotKit + AG-UI errors we hit and fixes |
| [solutions/chat-memory-and-session-learnings.md](solutions/chat-memory-and-session-learnings.md) | **Phase 3.6:** Memory, sessions, switching, Postgres |
| [../README.md](../README.md) | Repo setup and quick commands |

## Plans (implementation)

| Doc | Purpose |
|-----|---------|
| [2026-05-28-002 simple sandbox POC](plans/2026-05-28-002-feat-simple-ai-nl2sql-poc-plan.md) | Phase 1: personal AWS + Snowflake, 2–3 days |
| [2026-05-29-004 CopilotKit local UI](plans/2026-05-29-004-feat-copilotkit-local-ui-plan.md) | Phase 3B: CopilotKit + FastAPI (active) |
| [2026-05-29-003 Deep Agents upgrade](plans/2026-05-29-003-feat-deep-agents-nl2sql-upgrade-plan.md) | Phase 2: tool-calling agent on top of baseline |
| [2026-06-01-004 Wren + Cortex harness](plans/2026-06-01-004-feat-wren-ai-phase-4-plan.md) | Phase 4: Wren `main` vs Cortex Analyst (no v1 / no Wren UI) |
| [2026-06-01-005 CopilotKit semantic toggle](plans/2026-06-01-005-feat-copilotkit-semantic-layer-toggle-plan.md) | Off / Wren / Cortex switch in existing Copilot UI |
| [2026-06-01-006 Semantic layer editor](plans/2026-06-01-006-feat-semantic-layer-editor-plan.md) | Third UI page: edit MDL, consumers map, PR workflow, editor AI |
| [NL→SQL harness comparison](architecture/nl2sql-harness-comparison.md) | Deep Agents, Claude SDK, Wren, Cortex, Phase 1 |
| [Wren vs Cortex Analyst](architecture/wren-vs-snowflake-cortex-analyst.md) | Research: Wren vs Snowflake native semantics |
| [2026-05-28-001 full CTA POC](plans/2026-05-28-001-feat-ai-nl2sql-poc-plan.md) | Production POC: 4 harnesses, 10 days |

## Requirements & strategy

| Doc | Purpose |
|-----|---------|
| [POC requirements (beginner)](brainstorms/2026-05-28-ai-data-analysis-poc-requirements.md) | Step-by-step guides, glossary |
| [Meeting prep](brainstorms/2026-05-27-ai-data-analysis-poc-meeting-prep.md) | Harness options, Cambria questions |
| [PRD](brainstorms/2026-05-18-ai-data-analysis-app-PRD.md) | Client-ready product doc |
| [Consolidated requirements](brainstorms/2026-05-18-ai-data-analysis-app-consolidated-requirements.md) | 58 requirements |
| [Planning brief](brainstorms/2026-05-18-ai-data-analysis-app-planning-brief.md) | Bridge to full plan |

## Architecture

| Doc | Purpose |
|-----|---------|
| [nl2sql-harness-comparison.md](architecture/nl2sql-harness-comparison.md) | All harness options + how to combine them |
| [wren-vs-snowflake-cortex-analyst.md](architecture/wren-vs-snowflake-cortex-analyst.md) | Wren vs Cortex Analyst deep dive |
| [agent-error-handling.md](architecture/agent-error-handling.md) | SQL retry limits, error tags, where policy lives |
| [cta-ai-architecture.html](architecture/cta-ai-architecture.html) | Interactive 8-layer diagram — open in a browser |
| [query-and-memory-storage.md](architecture/query-and-memory-storage.md) | **Where memory & query logs live** (POC vs CTA target) |
| [chat-memory-and-sessions.md](architecture/chat-memory-and-sessions.md) | **Chat threads, sessions, snapshots, and follow-ups** |
| [postgres-local-dev.md](architecture/postgres-local-dev.md) | **Docker Compose + Postgres** for LangGraph checkpoints (Phase 3.6) |
| [audit-logs/README.md](audit-logs/README.md) | **Query audit log** — S3 bucket, env vars, restart API, inspect records |
