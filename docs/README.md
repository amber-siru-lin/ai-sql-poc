# Documentation index

## Plans (implementation)

| Doc | Purpose |
|-----|---------|
| [2026-05-28-002 simple sandbox POC](plans/2026-05-28-002-feat-simple-ai-nl2sql-poc-plan.md) | Phase 1: personal AWS + Snowflake, 2–3 days |
| [2026-05-29-003 Deep Agents upgrade](plans/2026-05-29-003-feat-deep-agents-nl2sql-upgrade-plan.md) | Phase 2: tool-calling agent on top of baseline |
| [2026-06-01-004 Wren + Cortex harness](plans/2026-06-01-004-feat-wren-ai-phase-4-plan.md) | Phase 4: Wren `main` vs Cortex Analyst (no v1 / no Wren UI) |
| [2026-06-01-005 CopilotKit semantic toggle](plans/2026-06-01-005-feat-copilotkit-semantic-layer-toggle-plan.md) | Off / Wren / Cortex switch in existing Copilot UI |
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
