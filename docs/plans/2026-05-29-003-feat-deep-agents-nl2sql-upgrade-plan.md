---
title: Deep Agents NL-to-SQL Upgrade Plan (Simple POC Phase 2)
type: feat
status: active
date: 2026-05-29
origin: docs/plans/2026-05-28-002-feat-simple-ai-nl2sql-poc-plan.md
depends_on:
  - ~/ai-sql-test/test_ai_sql.py (working baseline)
  - docs/brainstorms/2026-05-27-ai-data-analysis-poc-meeting-prep.md (Harness Option 1)
---

# Deep Agents NL-to-SQL Upgrade Plan

## Does the simple POC plan already cover this?

**No.** `docs/plans/2026-05-28-002-feat-simple-ai-nl2sql-poc-plan.md` stops at:

| What the simple plan has | What Deep Agents adds |
|--------------------------|------------------------|
| One Python script | Agent loop with tool calling |
| Single `llm.invoke(prompt)` → SQL string | Plan → tool calls → retry on errors |
| You run SQL in a separate function | Agent calls `execute_sql` as a tool |
| Hard-coded schema in a string | Agent can `read_file` schema / examples |
| No observability | LangGraph traces (LangSmith optional) |

The meeting prep doc (`2026-05-27-ai-data-analysis-poc-meeting-prep.md`) lists **LangChain Deep Agents** as Harness Option #1. This plan closes that gap without jumping to Amplify or CTA infrastructure yet.

---

## Goal

Upgrade your working sandbox (`~/ai-sql-test/`) from **single-shot NL→SQL** to a **Deep Agent** that:

1. Reads the schema (from a file or tool)
2. Writes SQL
3. Executes SQL on Snowflake via a tool
4. **Fixes itself** when Snowflake returns an error
5. Returns a plain-English answer plus the final SQL

**Success looks like:** Ask *"Which nation has the most customers?"* — agent runs SQL, hits a bad column name once, fixes it, and returns the correct answer without you editing code.

---

## Architecture shift

### Today (Phase 1 — done)

```
Question → ChatBedrock (one prompt) → SQL string → run_sql() → results
```

### Phase 2 (Deep Agents)

```
Question
  → Deep Agent (Nova Pro via Bedrock)
       ├── write_todos (plan)
       ├── read_file (schema / examples)
       ├── execute_snowflake_sql (tool)
       └── (optional) list_tables (tool)
  → Final answer + SQL + row preview
```

**Key idea:** The model is no longer guessing SQL in one shot. It can **call tools**, see real errors, and try again — matching the "method correctness" principle from the PRD.

---

## What we are NOT doing yet

Keep scope tight. Defer these to later phases:

- ❌ Aurora pgvector / custom RAG
- ❌ Amplify web UI (Phase 3 — still in simple plan Days 3–5)
- ❌ Subagents (until basic tools work)
- ❌ WrenAI comparison
- ❌ Okta / read-only enforcement (sandbox only)
- ❌ Langfuse / Braintrust (optional add-on in Phase 2B)

---

## Prerequisites (you already have most of this)

- [x] Working baseline: `~/ai-sql-test/test_ai_sql.py` + `ask_questions.py`
- [x] AWS Bedrock with inference profile: `us.amazon.nova-pro-v1:0`
- [x] Snowflake sample data: `SNOWFLAKE_SAMPLE_DATA.TPCH_SF1`
- [x] Python via Anaconda: `/opt/anaconda3/bin/python`
- [ ] New packages (install in Step 1 below)

---

## Phase 2A: Install Deep Agents (30 minutes)

Open terminal:

```bash
cd ~/ai-sql-test

# Use Anaconda Python (your PATH fix)
/opt/anaconda3/bin/python -m pip install deepagents langgraph langchain langchain-aws snowflake-connector-python
```

**What each package does:**

| Package | Role |
|---------|------|
| `deepagents` | `create_deep_agent()` — planning, tools, file tools |
| `langgraph` | Runtime under Deep Agents (agent loop) |
| `langchain-aws` | `ChatBedrock` for Nova Pro |
| `snowflake-connector-python` | Same as today |

Verify Bedrock still works:

```bash
/opt/anaconda3/bin/python diagnose_bedrock.py
```

---

## Phase 2B: Add schema file (15 minutes)

Create `~/ai-sql-test/schema/tpch_sf1.md` — move the schema out of Python so the agent can read it:

```markdown
# TPCH_SF1 Schema (Snowflake sample data)

## CUSTOMER
- C_CUSTKEY: customer ID
- C_NAME: customer name
- C_NATIONKEY: links to NATION
- C_ACCTBAL: account balance
- C_MKTSEGMENT: BUILDING, AUTOMOBILE, etc.

## ORDERS
- O_ORDERKEY: order ID
- O_CUSTKEY: links to CUSTOMER
- O_TOTALPRICE: order total in dollars
- O_ORDERDATE: order date
- O_ORDERSTATUS: F, O, P
- O_ORDERPRIORITY: 1-URGENT, 3-MEDIUM, etc.

## NATION
- N_NATIONKEY: nation ID
- N_NAME: UNITED STATES, CANADA, etc.

Rules:
- Always use fully qualified names: TPCH_SF1.CUSTOMER, etc.
- Snowflake SQL syntax only
- SELECT only (no INSERT/UPDATE/DELETE/DROP)
```

---

## Phase 2C: Build SQL tools (1 hour)

Create `~/ai-sql-test/tools/snowflake_tools.py`:

```python
"""Tools the Deep Agent can call to query Snowflake."""
import re
import snowflake.connector
from langchain.tools import tool
from snowflake_config import account, user, password, warehouse, database, schema

FORBIDDEN = re.compile(r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|GRANT|REVOKE)\b", re.I)

def _connect():
    return snowflake.connector.connect(
        account=account,
        user=user,
        password=password,
        warehouse=warehouse,
        database=database,
        schema=schema,
    )

@tool
def execute_snowflake_sql(sql: str) -> str:
    """Run a read-only SELECT query on Snowflake TPCH_SF1. Returns columns and up to 20 rows as text."""
    sql = sql.strip().rstrip(";")
    if FORBIDDEN.search(sql):
        return "ERROR: Only SELECT queries are allowed in the sandbox."
    if not sql.upper().lstrip().startswith("SELECT"):
        return "ERROR: Query must start with SELECT."

    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("USE SCHEMA TPCH_SF1")
        cur.execute(sql)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchmany(20)
        return f"Columns: {cols}\nRows ({len(rows)} shown):\n{rows}"
    except Exception as e:
        return f"SNOWFLAKE ERROR: {e}\nFix the SQL and try again."
    finally:
        conn.close()

@tool
def get_schema_summary() -> str:
    """Return a short summary of available tables and columns."""
    return open("schema/tpch_sf1.md").read()
```

**Security note:** This is a personal sandbox. Production will add Snowflake RLS + stricter validation.

---

## Phase 2D: Create the Deep Agent script (1 hour)

Create `~/ai-sql-test/ask_deep_agent.py`:

```python
"""Interactive NL→SQL using LangChain Deep Agents + Snowflake tools."""
from langchain_aws import ChatBedrock
from deepagents import create_deep_agent
from tools.snowflake_tools import execute_snowflake_sql, get_schema_summary

SYSTEM_PROMPT = """You are a Snowflake SQL analyst for the TPCH_SF1 sample dataset.

Workflow:
1. Understand the user's question.
2. Call get_schema_summary if you need table/column names.
3. Write a SELECT query using fully qualified table names (TPCH_SF1.CUSTOMER, etc.).
4. Call execute_snowflake_sql to run it.
5. If Snowflake returns an error, fix the SQL and retry (max 3 attempts).
6. Reply with: (a) plain-English answer, (b) final SQL, (c) key numbers from results.

Never run INSERT, UPDATE, DELETE, or DDL.
"""

# Nova Pro via inference profile (same as your working script)
model = ChatBedrock(
    model_id="us.amazon.nova-pro-v1:0",
    region_name="us-east-1",
)

agent = create_deep_agent(
    model=model,
    tools=[execute_snowflake_sql, get_schema_summary],
    system_prompt=SYSTEM_PROMPT,
)

def ask(question: str) -> str:
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    return result["messages"][-1].content

if __name__ == "__main__":
    print("Deep Agent SQL Assistant (type 'quit' to exit)\n")
    while True:
        q = input("Question: ").strip()
        if q.lower() in {"quit", "exit", "q"}:
            break
        if not q:
            continue
        print("\n" + ask(q) + "\n")
```

Run from `~/ai-sql-test`:

```bash
cd ~/ai-sql-test
/opt/anaconda3/bin/python ask_deep_agent.py
```

---

## Phase 2E: Compare baseline vs Deep Agent (1 hour)

Create `~/ai-sql-test/compare_harnesses.py` using the same 8 questions from `ask_questions.py`:

| # | Question | Baseline (`ask_ai`) | Deep Agent |
|---|----------|---------------------|------------|
| 1 | How many customers are there? | | |
| 2 | What is the total revenue from all orders? | | |
| 3 | Which customer has the highest account balance? | | |
| 4 | What is the average order amount? | | |
| 5 | Show me all pending orders | | |
| 6 | How many customers are in the BUILDING segment? | | |
| 7 | What is the total price of urgent orders? | | |
| 8 | Which nation has the most customers? | | |

Track for each:

| Metric | How to measure |
|--------|----------------|
| SQL correct on first try? | Yes / No |
| Needed retry after Snowflake error? | Yes / No |
| Answer makes sense? | Yes / No |
| End-to-end seconds | `time` command |

**Decision rule:**

- Deep Agent **wins** on multi-step or error-recovery questions → keep it for CTA POC Harness #1
- Baseline **wins** on simple questions with **much** lower latency → use Deep Agent only for complex queries (hybrid)

---

## Phase 2F: Optional observability (30 minutes)

If you want to *see* the agent plan and tool calls:

1. Sign up for free LangSmith: https://smith.langchain.com
2. Set env vars:

```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY="your-key"
export LANGCHAIN_PROJECT="ai-sql-deep-agent-poc"
```

3. Re-run one question — open the trace in LangSmith UI

This aligns with meeting prep recommendation (Langfuse is an alternative; LangSmith is native to LangChain/Deep Agents).

---

## Troubleshooting

### `ModuleNotFoundError: deepagents`

```bash
/opt/anaconda3/bin/python -m pip install deepagents
```

### Agent loops forever / very slow

- Nova Pro + tool calling is slower than single-shot (expect 10–30s vs 3–5s)
- Cap retries in system prompt ("max 3 attempts")
- Start with simple questions only

### `Tool calling not supported` or empty tool calls

- Deep Agents require a model that supports tool calling
- Nova Pro via Bedrock Converse generally works; if not, try `init_chat_model` with `model_provider="bedrock_converse"` per [Deep Agents Bedrock docs](https://docs.langchain.com/oss/python/deepagents/customization)

### Inference profile errors

Keep using `us.amazon.nova-pro-v1:0` — same as `test_ai_sql.py`. Direct model IDs without `us.` prefix will fail in your company account.

### Schema file not found

Run scripts from `~/ai-sql-test` so relative path `schema/tpch_sf1.md` resolves.

---

## File layout after Phase 2

```
~/ai-sql-test/
├── test_ai_sql.py              # Phase 1 baseline (keep for comparison)
├── ask_questions.py            # Phase 1 interactive
├── ask_deep_agent.py           # Phase 2 Deep Agent interactive
├── compare_harnesses.py        # Phase 2 evaluation
├── snowflake_config.py         # credentials (never commit)
├── schema/
│   └── tpch_sf1.md             # schema the agent reads
└── tools/
    └── snowflake_tools.py      # execute_snowflake_sql, get_schema_summary
```

Optional: copy this folder into `personal_build` on branch `langchain-ai-sql-poc` once stable (without secrets).

---

## Success criteria

| Test | Pass? | Evidence |
|------|-------|----------|
| Deep Agent answers 6/8 sample questions | | `compare_harnesses.py` results |
| Agent recovers from at least 1 bad SQL | | Snowflake error → retry → success in trace or console |
| Only SELECT queries run | | `FORBIDDEN` regex blocks destructive SQL |
| You can explain agent vs baseline | | Can describe tools + retry loop to Katherine |

---

## What comes next (Phase 3+)

| Phase | From | What |
|-------|------|------|
| **3** | Simple plan Days 3–5 | Amplify web UI wrapping `ask_deep_agent` logic |
| **4** | Full POC plan | CTA Snowflake sandbox, read-only role, YAML semantic layer |
| **5** | Architecture doc | Aurora pgvector RAG, feedback → tribal knowledge capture |

---

## Time estimate

| Step | Activity | Time |
|------|----------|------|
| 2A | Install packages | 30 min |
| 2B | Schema file | 15 min |
| 2C | Snowflake tools | 1 hr |
| 2D | Deep Agent script | 1 hr |
| 2E | Compare harnesses | 1 hr |
| 2F | LangSmith (optional) | 30 min |
| **Total** | | **~4 hours** |

---

## References

- [Deep Agents overview](https://docs.langchain.com/oss/python/deepagents/overview)
- [Deep Agents quickstart](https://docs.langchain.com/oss/python/deepagents/quickstart)
- [Deep Agents customization (Bedrock section)](https://docs.langchain.com/oss/python/deepagents/customization)
- Simple POC baseline: `docs/plans/2026-05-28-002-feat-simple-ai-nl2sql-poc-plan.md`
- Harness evaluation context: `docs/brainstorms/2026-05-27-ai-data-analysis-poc-meeting-prep.md`

---

*Phase 1 proved NL→SQL works. Phase 2 proves an agent can plan, tool-call, and recover — the pattern CTA needs for production.*
