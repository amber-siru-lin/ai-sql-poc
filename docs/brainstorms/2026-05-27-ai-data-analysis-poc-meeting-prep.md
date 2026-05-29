---
date: 2026-05-27
topic: ai-data-analysis-poc-meeting-prep
author: smooth-tinkerer-3703
status: draft
purpose: meeting-prep-for-katherine
---

# AI Data Analysis POC — Meeting Prep

**Attendees:** smooth-tinkerer-3703, Katherine (CTA), Senior Engineering
**Goal:** Align on POC approach, get Cambria details, evaluate 3 prebuilt NL→SQL harnesses against Snowflake

---

## Background

We are running a quick POC (1-2 weeks) to validate which NL→SQL approach works best for CTA's data before committing to a full architecture. Rather than building custom RAG from scratch immediately, we will evaluate **3 prebuilt harnesses** connected to Snowflake, with a **fallback to custom Claude SDK** if none fit.

**Hosting:** Cambria (CTA's custom app platform). We need Katherine's input on integration details.

---

## 1. POC Options

We will test the following in parallel over 1-2 weeks:

| # | Option | What It Is | Why Consider It | Risk |
|---|--------|-----------|----------------|------|
| **1** | **LangChain Deep Agents** | Framework for agentic NL→SQL with tool-calling and reasoning chains | Mature ecosystem, easy Snowflake connector, active community | May be over-engineered for simple queries; agent complexity adds latency |
| **2** | **WrenAI** ([Canner/WrenAI](https://github.com/Canner/WrenAI) ⭐ 15,303) | Open-source semantic layer + NL→SQL with custom RAG | Purpose-built for semantic modeling (matches our YAML approach), Git-native semantic layer, has "Ask" and "Copilot" modes | Requires semantic model upfront; less control over prompts |
| **3** | **SuperSonic** ([tencentmusic/supersonic](https://github.com/tencentmusic/supersonic) ⭐ 4,864) | Enterprise semantic chat BI with headless BI architecture | Built for non-technical users, semantic model builder, headless BI for embedding | Enterprise complexity; may be heavier than needed; unclear Snowflake connector maturity |
| **4** | **Fallback: Claude SDK + custom code** | Build minimal NL→SQL directly with Claude API and Snowflake connector | Full control, no framework overhead, fastest to iterate | We build everything; no pre-built semantic layer; more upfront work |

**Evaluation owner:** Katherine and the CTA team will use real business questions to judge which produces the best answers.

---

## 2. What We Will Test

Each option gets connected to **Snowflake production or sandbox** and evaluated on:

| Test | Description | Pass Criteria |
|------|-------------|---------------|
| **Basic NL→SQL** | "What was Q1 revenue?" "How many active members do we have?" | Produces correct SQL; returns plausible result |
| **Multi-table joins** | "What is revenue by member type and region?" | Handles JOINs across CTA's schema without hallucinating tables |
| **Business term mapping** | "What was attendance at CES 2026?" (table might be `events` or `conferences`) | Maps business terms to actual table/column names |
| **Error recovery** | Intentionally ask about non-existent columns | Fails gracefully; suggests rephrasing; does not crash |
| **Latency** | End-to-end time: question → SQL → result | Under 15 seconds for simple queries |
| **Security** | Runs in read-only mode; does not generate DROP/DELETE/INSERT | Sandbox-safe; no destructive SQL generated |

**Test data:** Use CTA's actual Snowflake schema (`INFORMATION_SCHEMA`) and 5-10 real business questions from Katherine's team.

---

## 3. Infrastructure: Cambria

**Open questions for Katherine:**

1. **What is Cambria?** Is it a React/Vue app platform, a backend framework, or both? What stack does it use?
2. **How do we deploy?** Do we add a new page/module to Cambria, or is it a separate app that embeds in Cambria?
3. **Authentication:** Does Cambria use Okta SSO? Can we pass through the user's identity to Snowflake, or do we use a service account?
4. **Environment:** Is there a dev/staging Cambria instance for the POC? Where do we deploy the test harnesses?
5. **Backend hosting:** Can we run Python/Node.js services inside Cambria, or do we need a separate AWS Lambda/EC2 for the NL→SQL engine?
6. **API access:** Does Cambria have existing API patterns we should follow for connecting to Snowflake?

---

## 4. Observability Options

We need to track: query latency, SQL generation quality, user feedback, token/credit costs, and error rates.

| Option | What It Is | Pros | Cons | Best For |
|--------|-----------|------|------|----------|
| **Braintrust** | LLM evaluation platform with tracing, evals, and regression testing | Purpose-built for LLM apps; prompt comparison; eval suites; easy to set up | Paid service; another vendor; may be overkill for a quick POC | Teams serious about systematic LLM evaluation and regression testing |
| **Langfuse** | Open-source LLM observability (tracing, metrics, prompt management, evals) | **Open-source** (self-hostable); native LangChain integration; prompt versioning; cost tracking | Requires hosting (can run locally for POC); newer project | Teams that want full control, open-source stack, and are already using LangChain |
| **AWS CloudTrail + custom** | CloudTrail for API auditing + custom CloudWatch metrics + S3 logs | **No extra vendor**; fits existing AWS stack; free for management events; audit compliance | No LLM-specific features (no prompt comparison, no eval suites); more DIY | Teams that prioritize compliance, minimal vendors, and can build basic dashboards |

**Recommendation for POC:**
- **If using LangChain:** Start with **Langfuse** (native integration, quick setup, tracks chains/agents out of the box). We can self-host it for the POC in 30 minutes.
- **If NOT using LangChain:** Use **CloudTrail + CloudWatch** for the POC (no extra setup) and evaluate Braintrust or Langfuse if the POC succeeds and we need systematic evals.

---

## 5. Decision Criteria

After the 1-2 week POC, we will score each option 1-5 on:

| Criteria | Weight | What We Measure |
|----------|--------|----------------|
| **Accuracy** | 30% | % of test questions that return correct, useful answers |
| **Ease of integration** | 25% | How hard to connect to Snowflake and Cambria |
| **Latency** | 15% | Average response time for test questions |
| **Security** | 15% | Does it safely sandbox queries? Prevent destructive SQL? |
| **Observability** | 10% | Can we see what it's doing, debug failures, track costs? |
| **Future extensibility** | 5% | Can it grow into the full architecture (semantic model, teach mode, audit)? |

**Decision owner:** Katherine + CTA stakeholders decide which option to proceed with. Engineering provides technical feasibility assessment.

---

## 6. Proposed POC Timeline

| Day | Activity | Owner |
|-----|----------|-------|
| **Day 1** (This meeting) | Get Cambria details from Katherine; confirm Snowflake access | Katherine + smooth-tinkerer-3703 |
| **Day 2-3** | Set up Snowflake sandbox; deploy 3 harness options | Engineering |
| **Day 4-7** | Katherine's team tests each option with real questions | Katherine + CTA staff |
| **Day 8** | Score results; decide: prebuilt option vs. custom Claude SDK | Team |
| **Day 9-10** | Document decision; write up findings; plan MVP | smooth-tinkerer-3703 |

---

## 7. Open Questions for This Meeting

1. **Cambria details** (see Section 3) — Katherine
2. **Snowflake access** — Can we get a read-only service account for the POC sandbox?
3. **Test questions** — Can Katherine provide 5-10 real business questions the team wants answered?
4. **Semantic model** — Do we have existing table descriptions / business definitions we can feed the harnesses?
5. **Observability preference** — Any existing tools CTA uses for monitoring (Datadog, CloudWatch, etc.)?

---

## Next Steps After Meeting

1. Get Cambria access and integration details
2. Set up Snowflake sandbox with CTA schema
3. Deploy Langfuse for observability (if using LangChain)
4. Run parallel POC tests
5. Score and decide

---

*Document prepared for meeting on 2026-05-27*
