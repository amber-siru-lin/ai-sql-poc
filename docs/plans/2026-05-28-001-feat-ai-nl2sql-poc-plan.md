---
title: AI NL-to-SQL POC Implementation Plan
type: feat
status: active
date: 2026-05-28
origin: docs/brainstorms/2026-05-28-ai-data-analysis-poc-requirements.md
---

# AI NL-to-SQL POC Implementation Plan

## Overview

Build a **modular, swappable POC** that tests 4 NL→SQL harnesses against CTA's Snowflake data. Begin with LangChain (beginner-friendly), then add WrenAI, SuperSonic, and custom Claude SDK. The POC proves we can generate valid SQL from natural language questions and execute it safely.

**Scope:** 1-2 week implementation. Beginner-safe approach with local SQLite testing before touching Snowflake.

**Audience:** AI implementation agent / junior developer with 0 experience.

---

## Problem Frame

CTA staff ask business questions in English, but only SQL experts can query Snowflake. We need to test which AI harness best translates English → SQL for CTA's specific data.

**User:** Non-technical CTA staff (membership coordinators, event planners, finance staff)
**Pain:** "I need to know Q1 revenue but I don't know SQL"
**Success:** User types "What was Q1 revenue?" → gets correct answer in < 15 seconds

---

## Requirements Trace

- **R1:** Generate valid SQL from natural language questions (from origin: Section 1)
- **R2:** Execute SQL safely against Snowflake (read-only, no data modification) (from origin: Section 5)
- **R3:** Compare 4 harness approaches with same test data (from origin: Section 2)
- **R4:** Beginner-safe implementation (no production damage, easy rollback) (from origin: Section 1, Safety Rules)
- **R5:** SQLite-first testing before Snowflake (from origin: Section 1, Rule #3)
- **R6:** Modular architecture — swap harnesses via config change (from origin: Section 2)

---

## Scope Boundaries

- **In scope:** 4 harness adapters, SQLite testing, Snowflake read-only queries, comparison report
- **Out of scope:** React UI, Cambria integration, SSO/auth, production deployment, teach mode, cost optimization, multi-tenant isolation
- **Deferred to MVP:** Aurora PostgreSQL vector store, API Gateway, Cognito, CDK/IaC, ECS hosting

---

## Context & Research

### Technology Stack
- **Language:** Python 3.11+
- **Primary Harness:** LangChain (starter) with AWS Bedrock (Claude 3.5 Sonnet)
- **Local Testing:** SQLite (no AWS needed for initial dev)
- **Production Testing:** Snowflake (read-only service account)
- **Containerization:** Docker (only for WrenAI/SuperSonic phases)
- **Version Control:** Git with branch-per-experiment strategy

### Institutional Learnings
- CTA is a nonprofit with audit/compliance requirements (from origin: Section 1)
- Existing AWS infrastructure in us-east-2 (from origin: Section 3)
- 4-person DataOps team, limited AWS access (from origin: Section 3)
- Test corpus received from Katherine (from origin: Section 10)

---

## Key Technical Decisions

1. **Starter Harness:** LangChain — best docs, community, built-in Snowflake support (from origin: Section 4.1)
2. **Gateway:** AWS Bedrock default — IAM auth, CloudTrail, consolidated billing (from origin: Section 11)
3. **Testing Order:** SQLite first → Snowflake second — prevents accidental data damage (from origin: Section 1, Rule #3)
4. **Repository:** New separate repo (not existing CTA repo) — zero risk to production (from origin: Appendix A)
5. **Branch Strategy:** One branch per harness experiment — easy rollback (from origin: Appendix A)

---

## Open Questions

### Resolved During Planning
- **Repository location:** New separate repo recommended (from origin: Request #6)
- **Starter harness:** LangChain (from origin: Section 4.1, 7)
- **Testing strategy:** SQLite first, then Snowflake (from origin: Section 1, Rule #3)

### Deferred to Implementation
- **Exact Snowflake schema:** Need Katherine to provide table names and column definitions
- **Bedrock model availability in us-east-2:** Need CTA AWS admin confirmation
- **Docker availability:** Need IT approval for WrenAI/SuperSonic phases
- **Budget approval:** $100 estimated POC cost (from origin: Request #5)

---

## Output Structure

```
cta-ai-poc/                          <-- Main project folder (new repo)
│
├── .git/                             <-- Git history (auto-generated)
├── .gitignore                        <-- Password protection (CRITICAL)
│
├── README.md                         <-- "What is this and how do I run it?"
├── requirements.txt                  <-- Python packages to install
│
├── config/                           <-- Settings and secrets
│   ├── poc.yaml                      <-- Which harness to use
│   └── snowflake.yaml                <-- Database login (NEVER commit this!)
│
├── src/                              <-- ALL your code
│   ├── __init__.py                   <-- "This is a Python package"
│   ├── main.py                       <-- "Run me to start the app"
│   ├── adapters/                     <-- 4 harness connectors
│   │   ├── __init__.py
│   │   ├── langchain_adapter.py      <-- Phase 1: Starter
│   │   ├── wrenai_adapter.py         <-- Phase 2: Pre-built system
│   │   ├── supersonic_adapter.py     <-- Phase 3: Enterprise system
│   │   └── custom_adapter.py         <-- Phase 4: Hand-built
│   ├── gateway/                      <-- Bedrock translator
│   │   ├── __init__.py
│   │   └── bedrock_gateway.py        <-- Talks to AWS Bedrock
│   ├── semantic_layer/               <-- "Recipe book" for AI
│   │   ├── __init__.py
│   │   └── schema_definitions.py     <-- "Member = table X"
│   └── security/                     <-- Safety checks
│       ├── __init__.py
│       └── sql_validator.py          <-- "Does this contain DROP?"
│
├── tests/                            <-- Test questions
│   ├── test_corpus.yaml              <-- Katherine's 5-10 questions
│   └── test_runner.py                <-- "Grade my homework" script
│
├── notebooks/                        <-- Experimental scratch paper
│   └── experiments.ipynb             <-- Try things without breaking code
│
└── docs/                             <-- Notes and diagrams
    └── architecture_diagrams/
```

---

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification. The implementing agent should treat it as context, not code to reproduce.*

### Data Flow (Happy Path)

```
User Question → Adapter (LangChain/WrenAI/etc.) → Gateway → Bedrock → Claude → SQL
                                                                    ↓
User ← Results ← SQLite/Snowflake ← SQL Validator ← (safe check) ← SQL
```

### Adapter Pattern

All 4 harnesses implement the same interface:
- **Input:** `question: str`, `schema_context: str`
- **Output:** `sql: str`, `confidence: float`, `explanation: str`

This lets us swap harnesses by changing one config line without touching the rest of the code.

### Safety Layers

1. **SQLite first:** Test on local fake database before touching real data
2. **Read-only Snowflake:** Dedicated service account with zero write permissions
3. **SQL Validator:** Keyword blacklist blocks DROP, DELETE, INSERT, etc.
4. **Branch isolation:** Each experiment is on its own Git branch
5. **Config isolation:** Passwords in config files, never in code, added to .gitignore

---

## Implementation Units

### Phase 1: Foundation & LangChain (Days 1-3)

- [ ] **Unit 1: Project Setup & Repository Creation**

**Goal:** Create the project structure and initialize Git safely

**Requirements:** R4 (beginner-safe), R5 (SQLite-first)

**Dependencies:** None

**Files:**
- Create: `cta-ai-poc/README.md`
- Create: `cta-ai-poc/requirements.txt`
- Create: `cta-ai-poc/.gitignore`
- Create: `cta-ai-poc/config/poc.yaml`
- Create: `cta-ai-poc/src/__init__.py`
- Create: `cta-ai-poc/src/main.py`

**Approach:**
1. Create new folder `cta-ai-poc` (NOT inside existing CTA repo)
2. Run `git init` to start version control
3. Create `.gitignore` with these CRITICAL lines:
   ```
   config/snowflake.yaml
   config/*.env
   *.key
   *.pem
   __pycache__/
   *.pyc
   venv/
   ```
4. Create `README.md` explaining what the project does
5. Create `requirements.txt` with initial packages: `langchain`, `langchain-aws`, `snowflake-sqlalchemy`
6. Create empty `src/__init__.py` and `src/main.py`

**Patterns to follow:** Standard Python project structure (from origin: Appendix A)

**Test scenarios:**
- Happy path: `git status` shows clean repo, no uncommitted files
- Edge case: Verify `.gitignore` works by creating `config/snowflake.yaml` and confirming `git status` ignores it

**Verification:**
- `git status` shows only tracked files (README.md, requirements.txt, src/)
- `config/snowflake.yaml` does NOT appear in `git status`

---

- [ ] **Unit 2: SQLite Test Database**

**Goal:** Create fake data for safe local testing

**Requirements:** R5 (SQLite-first testing)

**Dependencies:** Unit 1

**Files:**
- Create: `cta-ai-poc/tests/test_database.db` (auto-generated)
- Create: `cta-ai-poc/tests/setup_sqlite.py`

**Approach:**
1. Create a simple SQLite database with 2-3 fake tables that mirror CTA's structure:
   - `members` (id, name, join_date, status)
   - `events` (id, name, date, revenue)
   - `attendance` (member_id, event_id)
2. Insert 10-20 fake rows of data
3. This is your "sandbox" — you can break it without consequences

**Execution note:** Start with a failing test — try to query the SQLite database before it exists to prove the test setup works.

**Test scenarios:**
- Happy path: `SELECT COUNT(*) FROM members` returns a number > 0
- Edge case: Query a table that doesn't exist → should get error (verify error handling)
- Integration: Python script connects to SQLite, runs query, prints results

**Verification:**
- Run `python tests/setup_sqlite.py` → creates `test_database.db`
- Run `SELECT * FROM members` → shows fake data

---

- [ ] **Unit 3: Common Interface & Adapter Base**

**Goal:** Define the contract all 4 harnesses must follow

**Requirements:** R6 (modular architecture)

**Dependencies:** Unit 1

**Files:**
- Create: `cta-ai-poc/src/adapters/__init__.py`
- Create: `cta-ai-poc/src/adapters/base_adapter.py`

**Approach:**
1. Create abstract base class `NLToSQLAdapter` with methods:
   - `generate_sql(question, schema_context)` → returns `SQLResult` object
   - `get_name()` → returns harness name
2. Create `SQLResult` dataclass with fields: sql, confidence, explanation, model_used, latency_ms
3. This is your "contract" — every harness must implement these exact methods

**Technical design:**
```python
# Directional guidance only
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class SQLResult:
    sql: str
    confidence: float
    explanation: str
    model_used: str
    latency_ms: float

class NLToSQLAdapter(ABC):
    @abstractmethod
    def generate_sql(self, question: str, schema_context: str) -> SQLResult:
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        pass
```

**Test scenarios:**
- Happy path: Create a fake adapter that implements the interface → should work
- Error path: Create an adapter that misses a required method → should fail immediately with clear error

**Verification:**
- Python can import `base_adapter` without errors
- A test fake adapter passes interface validation

---

- [ ] **Unit 4: SQL Validator (Safety Guard)**

**Goal:** Block dangerous SQL before execution

**Requirements:** R2 (safe execution), R4 (beginner-safe)

**Dependencies:** Unit 1

**Files:**
- Create: `cta-ai-poc/src/security/__init__.py`
- Create: `cta-ai-poc/src/security/sql_validator.py`

**Approach:**
1. Create validator that checks for forbidden keywords: DROP, DELETE, INSERT, UPDATE, ALTER, CREATE, TRUNCATE
2. Case-insensitive check (convert SQL to uppercase first)
3. Returns `True` if safe, `False` if dangerous
4. Log blocked queries for debugging

**Execution note:** Test-first — write tests that pass dangerous SQL and verify they get blocked BEFORE implementing the validator.

**Test scenarios:**
- Happy path: `SELECT * FROM members` → passes (safe)
- Error path: `DROP TABLE members` → blocked (dangerous)
- Error path: `delete from members` → blocked (case-insensitive)
- Edge case: `SELECT "How to delete" FROM help` → passes (keyword in string, not command)
- Integration: Validator called before every SQL execution

**Verification:**
- `SELECT` queries pass
- `DROP`, `DELETE`, `INSERT` queries are blocked with clear error message

---

- [ ] **Unit 5: Semantic Layer (Recipe Book)**

**Goal:** Teach the AI what CTA's tables mean

**Requirements:** R1 (generate valid SQL)

**Dependencies:** Unit 1

**Files:**
- Create: `cta-ai-poc/src/semantic_layer/__init__.py`
- Create: `cta-ai-poc/src/semantic_layer/schema_definitions.py`
- Create: `cta-ai-poc/config/schema.yaml`

**Approach:**
1. Create YAML file with table definitions (from Katherine's schema):
   ```yaml
   tables:
     members:
       description: "CTA members"
       columns:
         - id: "Unique identifier"
         - name: "Member full name"
         - join_date: "When they joined"
         - status: "active, inactive, pending"
     events:
       description: "CTA events like CES"
       columns:
         - id: "Event identifier"
         - name: "Event name (e.g., CES 2026)"
         - date: "Event date"
         - revenue: "Total revenue from event"
   ```
2. Create Python loader that reads YAML and formats it for AI prompts
3. This is the "recipe book" that translates business terms to database terms

**Test scenarios:**
- Happy path: Load YAML → get structured schema object
- Edge case: Missing YAML file → clear error message
- Integration: Schema formatted into text that looks good in an AI prompt

**Verification:**
- `python src/semantic_layer/schema_definitions.py` loads schema without errors
- Output looks like: "Table: members (id, name, join_date, status)"

---

- [ ] **Unit 6: Bedrock Gateway (AWS Translator)**

**Goal:** Connect to AWS Bedrock to use Claude

**Requirements:** R1 (generate SQL)

**Dependencies:** Unit 1

**Files:**
- Create: `cta-ai-poc/src/gateway/__init__.py`
- Create: `cta-ai-poc/src/gateway/bedrock_gateway.py`

**Approach:**
1. Use `langchain-aws` package (easier than raw boto3 for beginners)
2. Configure with AWS credentials (from environment or ~/.aws/credentials)
3. Create simple method: `ask_claude(prompt)` → returns response text
4. Handle common errors: no credentials, model not available, rate limits

**Execution note:** If AWS credentials not available, create a "mock gateway" that returns fake SQL for testing. This lets you continue development without AWS access.

**Test scenarios:**
- Happy path: Valid AWS credentials → Claude responds with SQL
- Error path: No AWS credentials → clear error: "Set up AWS credentials first"
- Error path: Model not available → error: "Claude 3.5 Sonnet not available in us-east-2"
- Mock mode: Without credentials, returns `SELECT 1 as test` for testing

**Verification:**
- `python src/gateway/bedrock_gateway.py` connects and gets a response
- Response contains SQL-like text

---

- [ ] **Unit 7: LangChain Adapter (Starter Harness)**

**Goal:** First working NL→SQL harness using LangChain

**Requirements:** R1 (generate SQL), R6 (modular)

**Dependencies:** Units 3, 4, 5, 6

**Files:**
- Create: `cta-ai-poc/src/adapters/langchain_adapter.py`

**Approach:**
1. Implement `NLToSQLAdapter` interface
2. Use LangChain's `create_sql_query_chain` (simpler than building from scratch)
3. Flow: Question + Schema → LangChain → Bedrock → Claude → SQL
4. Add timing (latency_ms) for comparison later
5. Return `SQLResult` with all fields

**Execution note:** Start with SQLite only. Do NOT connect to Snowflake yet. Test with local database first.

**Test scenarios:**
- Happy path: "How many members?" → generates `SELECT COUNT(*) FROM members`
- Happy path: "What is revenue by event?" → generates `SELECT name, revenue FROM events`
- Edge case: Nonsense question → returns error or invalid SQL (test error handling)
- Integration: Full flow from question → SQL → SQLite execution → results

**Verification:**
- `python src/main.py` asks "How many members?" and prints a number
- SQL is valid and executes successfully on SQLite

---

- [ ] **Unit 8: Snowflake Connector (Read-Only)**

**Goal:** Connect to real CTA data (safely)

**Requirements:** R2 (Snowflake execution)

**Dependencies:** Unit 7, AWS/Snowflake credentials

**Files:**
- Create: `cta-ai-poc/config/snowflake.yaml` (add to .gitignore!)
- Modify: `cta-ai-poc/src/main.py` (add Snowflake option)

**Approach:**
1. Add Snowflake connection config (username, password, account, warehouse, database)
2. Use `snowflake-sqlalchemy` or `snowflake-connector-python`
3. CRITICAL: Verify read-only permissions before first query
4. Add command-line flag: `python src/main.py --database sqlite` vs `--database snowflake`
5. Default to SQLite (safe), require explicit flag for Snowflake

**Execution note:** BEFORE first Snowflake query:
1. Run `SHOW GRANTS TO USER poc_readonly;` to verify permissions
2. Verify no INSERT, UPDATE, DELETE, DROP privileges
3. Test with `SELECT 1` first
4. Only then run real queries

**Test scenarios:**
- Happy path: `python src/main.py --database snowflake --question "How many members?"` → returns real count
- Safety: Attempt to run `DROP TABLE` → blocked by SQL Validator (Unit 4)
- Safety: Verify Snowflake user has no write permissions
- Error path: Wrong credentials → clear error message

**Verification:**
- Snowflake query returns same results as manual SQL query
- SQL Validator blocks dangerous queries before they reach Snowflake

---

### Phase 2: WrenAI Testing (Days 4-5) — SUPERSEDED

> **Use [2026-06-01-004 Phase 4 plan](2026-06-01-004-feat-wren-ai-phase-4-plan.md) instead.** Wren `main` (CLI/SDK, no Docker UI) + Snowflake Cortex Analyst comparison. The Docker/`wren-ui` steps below are **`legacy/v1` only** — out of scope.

- [ ] **Unit 9: WrenAI Installation & Setup** *(deprecated — see Phase 4 Unit 1)*

**Goal:** ~~Run WrenAI locally via Docker~~ → Install `wrenai` Python package + Snowflake profile

**Approach (historical v1 — do not use):**
1. ~~Install Docker Desktop~~
2. ~~Run: `docker run -p 3000:3000 wrenai/wrenai`~~
3. ~~Open browser to `http://localhost:3000`~~

**Current approach:** See Phase 4 plan Units 1–5.

---

- [ ] **Unit 10: WrenAI Adapter**

**Goal:** Connect our test framework to WrenAI

**Requirements:** R3 (compare harnesses), R6 (modular)

**Dependencies:** Unit 9, Unit 3

**Files:**
- Create: `cta-ai-poc/src/adapters/wrenai_adapter.py`

**Approach:**
1. Implement `NLToSQLAdapter` interface
2. Use `requests` library to call WrenAI REST API
3. Method: POST `http://localhost:3000/api/ask` with question
4. Parse response JSON to extract SQL
5. Return `SQLResult` with same format as LangChain

**Test scenarios:**
- Happy path: "How many members?" → calls WrenAI → returns SQL
- Happy path: Same question returns similar SQL to LangChain
- Error path: WrenAI not running → clear error: "Start WrenAI with: docker run..."
- Integration: Same test corpus runs through both LangChain and WrenAI

**Verification:**
- `python tests/test_runner.py --harness wrenai` runs test corpus
- Results comparable to LangChain

---

### Phase 3: SuperSonic Testing (Days 6-7)

- [ ] **Unit 11: SuperSonic Installation & Setup**

**Goal:** Run SuperSonic locally via Docker

**Requirements:** R3 (compare harnesses)

**Dependencies:** Docker installed, Unit 1

**Files:**
- Create: `cta-ai-poc/src/adapters/supersonic_adapter.py`

**Approach:**
1. Similar to WrenAI but requires more RAM (8GB+)
2. Run SuperSonic container (check their docs for exact command)
3. Configure via web UI
4. Note: If laptop struggles, SKIP this phase

**Execution note:** Document in comparison report if skipped due to resource constraints.

**Test scenarios:**
- Happy path: SuperSonic container starts (if sufficient RAM)
- Error path: Insufficient RAM → clear skip message

**Verification:**
- SuperSonic web UI loads (if attempted)

---

- [ ] **Unit 12: SuperSonic Adapter**

**Goal:** Connect test framework to SuperSonic

**Requirements:** R3 (compare harnesses), R6 (modular)

**Dependencies:** Unit 11, Unit 3

**Files:**
- Create: `cta-ai-poc/src/adapters/supersonic_adapter.py`

**Approach:**
1. Implement `NLToSQLAdapter` interface
2. Call SuperSonic API (similar to WrenAI)
3. Parse response for SQL

**Test scenarios:**
- Happy path: Same test corpus runs through SuperSonic
- Comparison: Results vs LangChain and WrenAI

**Verification:**
- Test corpus executes successfully (if SuperSonic available)

---

### Phase 4: Custom Claude SDK (Days 8-9)

- [ ] **Unit 13: Custom Claude SDK Adapter**

**Goal:** Build NL→SQL from scratch (no LangChain)

**Requirements:** R3 (compare harnesses), R6 (modular)

**Dependencies:** Unit 3, Unit 4, Unit 5, Unit 6

**Files:**
- Create: `cta-ai-poc/src/adapters/custom_adapter.py`
- Create: `cta-ai-poc/prompts/custom_sql.txt`

**Approach:**
1. Implement `NLToSQLAdapter` interface
2. Use `anthropic.AnthropicBedrock()` client directly
3. Write custom prompt template (text file):
   ```
   You are a SQL expert. Here is the database schema:
   {schema}
   
   Write SQL to answer: {question}
   
   Return ONLY the SQL, no explanation.
   ```
4. Parse SQL from Claude's response (simple regex: look for ```sql ... ```)
5. Validate with SQL Validator (Unit 4)
6. Execute on database

**Test scenarios:**
- Happy path: "How many members?" → Claude generates `SELECT COUNT(*) FROM members`
- Happy path: Compare results with LangChain on same questions
- Edge case: Claude returns explanation + SQL → parser extracts only SQL
- Error path: Claude returns no SQL → clear error message

**Verification:**
- Custom adapter passes same tests as LangChain
- SQL quality comparable or better

---

### Phase 5: Comparison & Decision (Day 10)

- [ ] **Unit 14: Test Runner & Comparison Report**

**Goal:** Run all harnesses against same questions, generate comparison

**Requirements:** R3 (compare harnesses)

**Dependencies:** All previous units

**Files:**
- Create: `cta-ai-poc/tests/test_runner.py`
- Create: `cta-ai-poc/tests/comparison_report.md`

**Approach:**
1. Load test corpus (Katherine's 5-10 questions)
2. For each harness:
   - Run each question
   - Record: SQL generated, execution success, latency, correctness
3. Generate comparison table:
   | Harness | Accuracy | Avg Latency | Setup Time | Debuggability | Your Rating |
   |---------|----------|-------------|-----------|---------------|-------------|
   | LangChain | 80% | 2.5s | 3 hours | Easy | 4/5 |
   | WrenAI | 75% | 4.0s | 1 hour | Hard | 3/5 |
   | ... | ... | ... | ... | ... | ... |
4. Write 1-page recommendation with rationale

**Test scenarios:**
- Happy path: All 4 harnesses run same 5 questions
- Integration: Report shows side-by-side results
- Edge case: One harness fails → still generate report for others

**Verification:**
- `python tests/test_runner.py --all` runs complete comparison
- `tests/comparison_report.md` exists with clear recommendation

---

## System-Wide Impact

- **No production systems touched:** POC runs in completely separate repo
- **SQLite default:** Even if Snowflake config is wrong, tests run safely on local data
- **Branch isolation:** Each experiment is on separate branch — cannot break other work
- **Read-only Snowflake:** Even if SQL validator fails, Snowflake account has no write permissions

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| **AWS Bedrock not available** | Use mock gateway for development, switch to real when available |
| **Snowflake credentials delayed** | Test entirely on SQLite, add Snowflake later |
| **Docker not approved** | Skip WrenAI/SuperSonic, compare LangChain vs Custom SDK only |
| **Laptop insufficient RAM** | Skip SuperSonic (requires 8GB+), test LangChain + WrenAI only |
| **SQL generated is wrong** | SQL Validator blocks dangerous queries; read-only account prevents damage |
| **Beginner gets stuck** | Each unit has "Verification" section with simple test; commit after each unit |

---

## Documentation / Operational Notes

- **README.md:** "How to run this POC" — step by step for beginners
- **Comparison report:** Share with Katherine and senior engineering
- **Decision doc:** Clear recommendation for MVP harness
- **.gitignore:** CRITICAL — ensures passwords never committed

---

## Sources & References

- **Origin document:** [docs/brainstorms/2026-05-28-ai-data-analysis-poc-requirements.md](docs/brainstorms/2026-05-28-ai-data-analysis-poc-requirements.md)
- **Meeting prep:** [docs/brainstorms/2026-05-27-ai-data-analysis-poc-meeting-prep.md](docs/brainstorms/2026-05-27-ai-data-analysis-poc-meeting-prep.md)
- **Requirements consolidated:** [docs/brainstorms/2026-05-18-ai-data-analysis-app-consolidated-requirements.md](docs/brainstorms/2026-05-18-ai-data-analysis-app-consolidated-requirements.md)
- **External docs:** LangChain docs, WrenAI GitHub, SuperSonic GitHub, AWS Bedrock docs

---

*Plan prepared for AI implementation agent. Last updated: 2026-05-28*