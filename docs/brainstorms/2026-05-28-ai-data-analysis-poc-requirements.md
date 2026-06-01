---
date: 2026-05-28
topic: ai-data-analysis-poc-requirements
author: smooth-tinkerer-3703
status: draft
purpose: technical-requirements-for-poc-implementation
---

# AI Data Analysis POC — Technical Requirements

**Goal:** Build a modular, swappable POC that tests 4 NL→SQL harnesses against CTA's Snowflake data.
**Scope:** 1-2 week implementation. Begin with LangChain (beginner-friendly), then add WrenAI, SuperSonic, and custom Claude SDK.
**Audience:** AI planning agent / senior engineering review.

---

## 1. POC Scope

### What This POC Proves
- Can we generate valid SQL from natural language questions?
- Can we execute that SQL safely against Snowflake?
- Can we compare 4 different harness approaches with the same test data?
- Can a non-technical user (CTA staff) interact with it?

### What This POC Does NOT Build
- Full user interface (no React app, no Cambria integration)
- Production security (no SSO, no audit logging, no role-based access)
- Semantic model builder UI
- Teach mode / feedback loop
- Cost optimization
- Multi-tenant isolation

### Outputs
1. Working end-to-end pipeline: question → SQL → Snowflake results
2. Test harness comparison report (accuracy, latency, SQL quality)
3. Decision: which harness to use for MVP?

### Safety & Isolation Rules (CRITICAL FOR NEWBIES)

**Rule #1: NEVER touch CTA production code**
- This POC lives in a **completely separate folder** from CTA's existing repos
- We will create a new folder called `cta-ai-poc/` on your laptop
- No files will be modified in CTA's GitHub repos, Snowflake, or AWS accounts

**Rule #2: ALWAYS use a branch**
- Before writing ANY code, create a Git branch: `git checkout -b poc-langchain-test`
- This keeps your changes isolated from `main`
- If you break something, you can delete the branch and start over

**Rule #3: Test on a COPY first**
- We will use a **local SQLite database** (a file on your laptop) for initial testing
- Only connect to CTA's Snowflake AFTER everything works locally
- This prevents accidentally running bad SQL on real data

**Rule #4: Read-only everywhere**
- Even in Snowflake, we use an account that **cannot write, delete, or modify anything**
- SQL validation blocks all dangerous keywords before execution
- Think of it like "training wheels" — safe by default

---

## Appendix A: Repository Structure for Absolute Beginners

**What is a "repository"?** Think of it like a filing cabinet for your project. It's a folder on your computer where you keep all the code, organized neatly. Git (version control) watches this folder and remembers every change you make.

### If You Are Starting from Scratch (No Amplify Structure Provided)

Since you have 0 development experience, here is the EXACT folder structure you should create. This keeps everything organized and safe.

Create a folder on your computer called `cta-ai-poc` (or whatever name you choose). Inside it, create these sub-folders:

```
cta-ai-poc/                          <-- The main project folder (the "repo")
│
├── .git/                             <-- Git's memory (don't touch this!)
├── .gitignore                        <-- List of files Git should ignore (e.g., passwords)
│
├── README.md                         <-- The instruction manual for your project
│                                       (What is this? How do I run it?)
│
├── requirements.txt                  <-- A shopping list for your computer
│                                       ("Install these Python packages")
│
├── config/                           <-- Settings and secrets (passwords, API keys)
│   ├── poc.yaml                      <-- Which harness to use (LangChain, WrenAI, etc.)
│   └── snowflake.yaml                <-- Snowflake login info (keep secret!)
│
├── src/                              <-- ALL of your code lives here
│   ├── __init__.py                   <-- Tells Python "this is a code package"
│   ├── main.py                       <-- The front door (run this to start the app)
│   ├── adapters/                     <-- The 4 harness connectors
│   │   ├── __init__.py
│   │   ├── langchain_adapter.py      <-- Code for LangChain
│   │   ├── wrenai_adapter.py         <-- Code for WrenAI (simple API client)
│   │   ├── supersonic_adapter.py     <-- Code for SuperSonic (simple API client)
│   │   └── custom_adapter.py         <-- Code for hand-built Claude SDK
│   ├── gateway/                      <-- The translator to Bedrock (only for LangChain/Custom)
│   │   ├── __init__.py
│   │   └── bedrock_gateway.py        <-- How to talk to AWS Bedrock
│   ├── semantic_layer/               <-- The "recipe book" for the AI (only for LangChain/Custom)
│   │   ├── __init__.py
│   │   └── schema_definitions.py     <-- "Member = table X, Revenue = column Y"
│   └── security/                     <-- Safety checks
│       ├── __init__.py
│       └── sql_validator.py          <-- "Does this SQL contain DROP? Block it!"
│
├── tests/                            <-- Test questions and expected answers
│   ├── test_corpus.yaml              <-- Katherine's 5-10 questions
│   └── test_runner.py                <-- The script that runs tests automatically
│
├── notebooks/                        <-- Experimental scratch paper (optional)
│   └── experiments.ipynb             <-- Jupyter notebook for trying things out
│
└── docs/                             <-- Notes, decisions, meeting prep
    └── architecture_diagrams/        <-- Drawings of how it works
```

### What Each File Actually Does (For a Beginner)

| File/Folder | Analogy | What It Actually Contains |
|-------------|---------|---------------------------|
| `README.md` | Instruction manual | "This project generates SQL from English. To run it, type `python src/main.py`" |
| `requirements.txt` | Shopping list | A list of programs to install (like `pip install langchain`) |
| `config/poc.yaml` | Settings menu | `harness: langchain` (which engine to use) |
| `config/snowflake.yaml` | Login credentials | Username, password, database name (NEVER share this!) |
| `src/main.py` | Front door | The first code that runs when you start the app |
| `src/adapters/` | Different car engines | 4 different ways to generate SQL (LangChain, WrenAI, etc.) |
| `src/gateway/` | Phone translator | Converts your message into Bedrock's language |
| `src/semantic_layer/` | Recipe book | "When user says 'member', look in table `dim_member`" |
| `src/security/` | Security guard | Checks SQL for dangerous words like DROP before running |
| `tests/` | Exam questions | Questions you ask the AI to see if it gets them right |
| `.gitignore` | "Do not disturb" list | Tells Git: "Don't save passwords or temporary files" |

### The `.gitignore` File (CRITICAL for Beginners)

This file tells Git which files to IGNORE (don't save in history). **You MUST create this** to avoid accidentally committing passwords.

Create a file named `.gitignore` in your main folder with this exact content:

```
# Ignore files with passwords or secrets
config/snowflake.yaml
config/*.env
*.key
*.pem

# Ignore temporary files
__pycache__/
*.pyc
.ipynb_checkpoints/

# Ignore virtual environment (if you create one)
venv/
.env/
```

**Why this matters:** If you accidentally commit `snowflake.yaml` with your password to GitHub, that password is on the internet forever. This file prevents that mistake.

### How to Create This Structure (Step-by-Step)

**On Mac/Linux (Terminal):**
```bash
# 1. Create the main folder
mkdir cta-ai-poc
cd cta-ai-poc

# 2. Initialize Git (version control)
git init

# 3. Create the folder structure
mkdir -p src/adapters src/gateway src/semantic_layer src/security
mkdir -p config tests notebooks docs/architecture_diagrams

# 4. Create empty files (placeholders)
touch README.md requirements.txt .gitignore
touch src/__init__.py src/main.py
touch src/adapters/__init__.py
# ... etc for all folders

# 5. Verify it looks right
ls -R
```

**On Windows (Command Prompt or PowerShell):**
```cmd
:: Create the main folder
mkdir cta-ai-poc
cd cta-ai-poc

:: Initialize Git
git init

:: Create folders
mkdir src\adapters src\gateway src\semantic_layer src\security
mkdir config tests notebooks docs\architecture_diagrams

:: Create files
type nul > README.md
type nul > requirements.txt
type nul > .gitignore
:: ... etc
```

### If Amplify Provides a Structure

If CTA's Amplify setup creates a folder structure for you, **you don't need to do the above**. Instead:

1. Ask Katherine: "Does Amplify create folders automatically?"
2. If yes: Use their structure, but add these folders:
   - `src/adapters/` (for the 4 harnesses)
   - `config/` (for settings)
   - `tests/` (for test questions)
3. If no: Use the structure above.

### Golden Rules for Beginners

1. **Never put passwords directly in your code.** Always put them in `config/` and add `config/` to `.gitignore`.
2. **Commit often.** After every small working change, run:
   ```bash
   git add .
   git commit -m "I got the LangChain adapter working with SQLite"
   ```
3. **Never commit to the `main` branch.** Always create a branch:
   ```bash
   git checkout -b my-experiment-name
   ```
4. **If you mess up, don't panic.** You can always go back to the last commit:
   ```bash
   git checkout .          # Undo changes in current files
   git checkout main       # Go back to the safe starting point
   ```

---

## 2. Modular Architecture

### IMPORTANT CLARIFICATION: What Each Harness Actually Is

**LangChain = LEGO Toolkit**
- You build everything yourself using pre-made pieces
- You write the gateway code (how to talk to Bedrock)
- You write the semantic layer (business definitions)
- Best for learning, but more code to write

**WrenAI = Complete Kitchen (Pre-Built)**
- Already has a recipe book (semantic layer)
- Already has a waiter (gateway built-in)
- Already has a kitchen layout (database connector)
- You just load your recipes and turn it on
- Less code, but harder to customize/debug

**SuperSonic = Restaurant Franchise (Enterprise)**
- Even more pre-built than WrenAI
- Has multiple kitchens (database support)
- Has fancy menu builder UI
- Heaviest system, most "magic"

### Design Principle: Adapter Pattern
Every harness implements the same interface. Swap harnesses by changing config, not code.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                                   │
│                   (CLI or simple web form)                              │
└───────────────────────────┬───────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     COMMON INTERFACE (You Build This)                   │
│  Input:  {question: string, context: SemanticContext}                  │
│  Output: {sql: string, confidence: number, explanation: string}         │
└───────────────────────────┬───────────────────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┬────────────────┐
              ▼             ▼             ▼                ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │   ADAPTER    │ │   ADAPTER    │ │   ADAPTER    │ │   ADAPTER    │
    │  LangChain   │ │   WrenAI     │ │  SuperSonic  │ │  Custom SDK  │
    │   (Toolkit)  │ │ (Pre-Built)  │ │ (Enterprise) │ │  (Handbuilt) │
    └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
           │                │                │                │
           │                │                │                │
           │    ┌───────────┘                │                │
           │    │  (Built-in)                 │                │
           │    ▼                             │                │
           │ ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
           │ │ SEMANTIC │  │ SEMANTIC │  │ SEMANTIC │  │ SEMANTIC │
           │ │  LAYER   │  │  LAYER   │  │  LAYER   │  │  LAYER   │
           │ │ (You     │  │ (Built-  │  │ (Built-  │  │ (You     │
           │ │  Build)  │  │   in)    │  │   in)    │  │  Build)  │
           │ └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
           │      │            │            │            │
           │      │    ┌───────┘            │            │
           │      │    │  (Built-in)        │            │
           │      │    ▼                    │            │
           │ ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
           │ │ GATEWAY  │  │ GATEWAY  │  │ GATEWAY  │  │ GATEWAY  │
           │ │ (You     │  │ (Built-  │  │ (Built-  │  │ (You     │
           │ │  Build)  │  │   in)    │  │   in)    │  │  Build)  │
           │ └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
           │      │            │            │            │
           └──────┼────────────┴────────────┴────────────┘
                  │
                  ▼
    ┌─────────────────────────────────────────────────────────────┐
    │              AI PROVIDER (Same for All)                     │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
    │  │ AWS BEDROCK  │  │  ANTHROPIC   │  │    OTHER     │   │
    │  │  (Default)   │  │   (Direct)   │  │   PROVIDERS  │   │
    │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
    │         │                 │                 │           │
    │         └─────────────────┴─────────────────┘           │
    │                           │                             │
    │                           ▼                             │
    │                     ┌──────────┐                        │
    │                     │  CLAUDE  │                        │
    │                     │   (AI)   │                        │
    │                     └────┬─────┘                        │
    │                        Generates SQL                   │
    └────────────────────────┼────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │   SNOWFLAKE    │
                    │  (Database)    │
                    └────────────────┘
```

### What This Diagram Shows

**LangChain & Custom SDK:**
- YOU build the Semantic Layer (recipe book)
- YOU build the Gateway (waiter/translator)
- More work, but you understand every piece
- When it breaks, you know exactly where to look

**WrenAI & SuperSonic:**
- THEY provide the Semantic Layer
- THEY provide the Gateway
- Less code to write initially
- BUT: When it breaks, you don't know if it's:
  - Their semantic layer?
  - Their gateway?
  - The AI model?
  - Your database connection?
- Harder to debug as a beginner

**All paths lead to the same AI Provider (Bedrock/Anthropic) and same Database (Snowflake).**

### Why LangChain is Still Recommended for Beginners

Even though WrenAI seems "simpler" (less code), LangChain is actually BETTER for learning because:

1. **Better Error Messages**
   - LangChain: "Error in line 42 of your code: missing import"
   - WrenAI: "Internal server error" (hides where the problem is)

2. **More Tutorials**
   - LangChain: 10,000 StackOverflow questions, YouTube tutorials
   - WrenAI: 50 GitHub issues, mostly unanswered

3. **Step-by-Step Debugging**
   - LangChain: You can print what the AI receives at each step
   - WrenAI: Black box — you can't see inside

4. **Understand the Fundamentals**
   - LangChain forces you to learn how NL→SQL actually works
   - WrenAI hides the complexity (good later, confusing now)

5. **Easier to Get Help**
   - "My LangChain code gives error X" → 100 people can help
   - "My WrenAI Docker container won't start" → 5 people can help

### POC Strategy

**Phase 1: LangChain (Days 1-3)**
- Build the fundamentals
- Learn how NL→SQL works
- Debug issues and understand the system

**Phase 2-3: WrenAI/SuperSonic (Days 4-7)**
- Now that you understand the basics, try the pre-built options
- Compare: Is their "magic" better than your hand-built solution?
- If WrenAI works better, you'll understand WHY (because you built LangChain first)

**Phase 4: Decision (Day 10)**
- Pick the winner based on real data, not marketing promises
- You'll understand the tradeoffs because you tried both approaches

### Common Interface (All Adapters Must Implement)

```python
class NLToSQLAdapter(ABC):
    @abstractmethod
    async def generate_sql(
        self,
        question: str,
        schema_context: str,
        conversation_history: List[Dict] = None
    ) -> SQLGenerationResult:
        """
        Returns:
            sql: Generated SQL string
            confidence: 0.0-1.0 score
            explanation: Natural language explanation of the SQL
            model_used: Which model generated this
            latency_ms: How long generation took
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return harness name for logging/comparison"""
        pass
```

### Gateway Abstraction (For LangChain & Custom SDK Only)

**What is a gateway?** It's the code that translates your question into the format AWS Bedrock expects.

**Do you need to build it?**
- **LangChain:** Yes, you configure LangChain's built-in gateway (2 lines of code)
- **WrenAI:** No, WrenAI has its own built-in gateway (configure in web UI)
- **SuperSonic:** No, SuperSonic has its own built-in gateway (configure in admin panel)
- **Custom SDK:** Yes, you write direct API calls to Bedrock

**For LangChain (Starter):**
```python
from langchain_aws import ChatBedrock  # This IS the gateway!

# 2 lines = gateway is ready
llm = ChatBedrock(
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    region_name="us-east-1"  # Uses your AWS credentials automatically
)

# Now use it:
result = llm.invoke("Write SQL to count users")
```

**For Custom SDK:**
```python
import boto3  # AWS SDK = gateway

# Direct API call = you are the gateway
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

response = bedrock.invoke_model(
    modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
    body={"prompt": "Write SQL to count users", "max_tokens": 1000}
)
```

**For WrenAI:**
```python
# WrenAI handles ALL gateway logic internally
# You just use their REST API
response = requests.post("http://localhost:3000/api/ask", json={"question": "count users"})
# WrenAI internally: translates → calls Bedrock → gets SQL → returns to you
```

**Bottom Line:**
- LangChain = you write 2 lines to configure the gateway
- Custom SDK = you write 10-20 lines to build the gateway
- WrenAI/SuperSonic = they handle it, you don't write gateway code

### Version Control Strategy (So You Can Always Roll Back)

**What is Git?**
Think of Git like "Save History" in a video game. Every time you make progress, you create a "checkpoint" (called a **commit**). If you mess up, you can go back to any checkpoint.

**Beginner Workflow:**
```bash
# Step 1: Create a branch (isolated workspace)
git checkout -b poc-langchain-test

# Step 2: Make changes (edit code)
# ... write some code ...

# Step 3: Save checkpoint
git add .
git commit -m "LangChain adapter working with SQLite"

# Step 4: If something breaks, go back
git checkout main          # Return to safe starting point
git branch -D poc-langchain-test  # Delete broken branch
git checkout -b poc-langchain-test-v2  # Start fresh
```

**Branch Naming for This POC:**
- `poc-langchain-test` — Phase 1 (starter)
- `poc-wrenai-test` — Phase 2
- `poc-supersonic-test` — Phase 3
- `poc-custom-test` — Phase 4
- `poc-comparison` — Phase 5 (final comparison)

**Golden Rule:**
- NEVER work directly on `main` branch
- ALWAYS create a new branch for each experiment
- COMMIT often (every 30-60 minutes of progress)
- If stuck, ASK before trying random fixes

### Configuration-Driven Harness Selection

**For LangChain & Custom SDK (You Build the Adapter):**
```yaml
# config/poc.yaml
harness:
  active: "langchain"  # Change to "custom" 
  
providers:
  langchain:
    adapter: "adapters.langchain_adapter.LangChainAdapter"
    gateway: "bedrock"  # YOU configure this
    model: "anthropic.claude-3-5-sonnet-20241022-v2:0"
    snowflake: "config/snowflake.yaml"
    
  custom:
    adapter: "adapters.custom_adapter.CustomAdapter"
    gateway: "bedrock"  # YOU write this code
    model: "anthropic.claude-3-5-sonnet-20241022-v2:0"
    prompt_template: "prompts/custom_sql.txt"
    snowflake: "config/snowflake.yaml"
```

**For WrenAI & SuperSonic (They Are Complete Systems):**
```yaml
# config/poc.yaml
harness:
  active: "wrenai"  # or "supersonic"
  
providers:
  wrenai:
    # WrenAI runs as a separate application (Docker)
    # It has its OWN config files, its OWN gateway, its OWN semantic layer
    url: "http://localhost:3000"  # Where WrenAI is running
    semantic_model: "config/wrenai_semantic.yaml"  # Table definitions
    # Gateway is INSIDE WrenAI — you don't configure it here
    
  supersonic:
    # SuperSonic runs as a separate application (Docker)
    url: "http://localhost:8080"  # Where SuperSonic is running
    # Gateway is INSIDE SuperSonic — you don't configure it here
```

**Key Difference:**
- LangChain/Custom: Your code connects everything (gateway, database, prompts)
- WrenAI/SuperSonic: You launch a separate app, your code just calls its API

---

### Architecture Summary for Beginners

**The Big Picture:**

You are building a **translator** between English questions and SQL queries. The translator has 4 different "engines" you can swap between.

**What YOU build vs what is pre-built:**

| Component | LangChain | WrenAI | SuperSonic | Custom SDK |
|-----------|-----------|--------|------------|------------|
| **Your Code** | Adapter (20 lines) | API Client (5 lines) | API Client (5 lines) | EVERYTHING (200+ lines) |
| **Gateway** | LangChain provides | WrenAI has built-in | SuperSonic has built-in | YOU write it |
| **Semantic Layer** | YOU write YAML | WrenAI stores it | SuperSonic stores it | YOU write code |
| **SQL Parser** | LangChain handles | WrenAI handles | SuperSonic handles | YOU write regex |
| **SQL Validation** | YOU write it | WrenAI handles | SuperSonic handles | YOU write it |
| **Database Connection** | LangChain handles | WrenAI handles | SuperSonic handles | YOU write it |

**The Tradeoff:**
- **More pre-built (WrenAI/SuperSonic):** Less code, but harder to debug when things go wrong
- **Less pre-built (LangChain/Custom):** More code, but you understand every piece and can fix it

**Why LangChain first?** It's the middle ground — you write some code (learn how it works) but get help with the hard parts (gateway, SQL parsing).

---

## 3. AWS Services (Minimal, Limited Access)

### Assumption: Limited AWS Access
You can use existing AWS resources but cannot create new VPCs, IAM roles, or complex infrastructure.

### Required AWS Services

| Service | Purpose | Why Minimal |
|---------|---------|-------------|
| **AWS Bedrock** | Run Claude models | Already available in CTA's AWS account; no setup needed |
| **AWS Lambda** | Run the POC backend | Serverless, no servers to manage, fits in existing VPC |
| **Amazon S3** | Store semantic model YAML, test results | Simple storage, existing buckets likely available |
| **Amazon CloudWatch** | Basic logging and metrics | Already enabled for Lambda, no extra setup |

### NOT Using (To Keep It Simple)

| Service | Why Skip |
|---------|----------|
| **Amazon Aurora PostgreSQL** | POC can use S3 + in-memory caching; add Aurora for MVP |
| **AWS AppSync / API Gateway** | Use Lambda function URL or simple HTTP trigger; add API Gateway for MVP |
| **AWS Cognito** | No auth for POC; use simple API key or no auth |
| **AWS CDK / CloudFormation** | Manual Lambda deployment for POC; add IaC for MVP |
| **AWS ECS / EKS** | WrenAI/SuperSonic Docker containers run locally for POC; add ECS for MVP |

---

## 4. Adapter Requirements

### 4.1 LangChain Adapter (Starter / Phase 1)

**Why start here:** Best documentation, largest community, built-in Snowflake support, easiest for beginners.

**Implementation:**
```python
class LangChainAdapter(NLToSQLAdapter):
    def __init__(self, gateway: AIGateway):
        self.gateway = gateway
        self.llm = ChatBedrock(
            model_id=gateway.model,
            client=gateway.bedrock_client
        )
        self.db = SQLDatabase.from_uri("snowflake://...")
    
    async def generate_sql(self, question, schema_context, history=None):
        # Use LangChain's SQL generation chain
        chain = create_sql_query_chain(self.llm, self.db)
        result = await chain.ainvoke({"question": question})
        return SQLGenerationResult(
            sql=result["query"],
            confidence=0.85,  # LangChain doesn't provide this; estimate
            explanation="Generated by LangChain SQL chain",
            model_used=gateway.model,
            latency_ms=result["latency"]
        )
```

**Required Packages:**
```
langchain
langchain-community
langchain-aws
snowflake-sqlalchemy
```

**Test Cases:**
1. "How many members joined in 2025?" → Basic SELECT
2. "What is revenue by region?" → GROUP BY
3. "Show me active members who attended CES" → JOIN
4. "What does table X contain?" → Schema introspection

---

### 4.2 Wren AI (Phase 4) — OPEN CONTEXT LAYER (`main` only)

> **Supersedes (2026-06-01):** The sections below describing Docker + port 3000 + Wren web UI refer to **`legacy/v1` GenBI**, archived by Canner in May 2026. **Current POC uses `main` only** — no v1, no Wren product UI. See [Phase 4 plan](../plans/2026-06-01-004-feat-wren-ai-phase-4-plan.md) and [Wren vs Cortex Analyst](../architecture/wren-vs-snowflake-cortex-analyst.md). Also evaluate **Snowflake Cortex Analyst** (Semantic Views + REST) as the warehouse-native alternative.

**What it actually is (2026 `main`):** An OSS semantic **engine** for agents — MDL in git, `wren` CLI / Python SDK / `wren-langchain` tools. You bring the LLM (e.g. Bedrock) and **your** UI (CopilotKit/Amplify).

**Think of it as:** A governed semantic layer your Deep Agent calls — not a separate chat application.

**Implementation Strategy (current):**
- `pip install "wrenai[snowflake,memory]"` — no Docker required for POC
- Model TPCH in `wren/tpch/` MDL; `wren context build`; `wren memory index`
- Integrate via `wren-langchain` from Phase 2 Deep Agent or compare script
- **Do not** use `legacy/v1` or `docker run -p 3000:3000 wrenai/wrenai`

**Historical note (v1 — do not use):** The former GenBI app had its own web interface:

- Install Docker Desktop (like installing a virtual machine)
- Download WrenAI container: `docker run -p 3000:3000 wrenai/wrenai`
- Open browser to `http://localhost:3000` — WrenAI had its OWN web interface
- Upload your schema definitions (YAML file with table descriptions)
- WrenAI handles EVERYTHING internally:
  - Semantic layer (built-in)
  - Gateway to Bedrock (built-in)
  - SQL generation (uses its own prompts)
  - Result formatting
- YOUR adapter just calls WrenAI's REST API:
  ```python
  # Your adapter is just a simple HTTP client!
  response = requests.post("http://localhost:3000/api/ask", json={
      "question": "What was Q1 revenue?"
  })
  sql = response.json()["sql"]
  ```

**What YOU need to provide:**
- Semantic model YAML (table definitions, relationships)
- Snowflake connection details
- Bedrock API credentials (WrenAI connects directly)

**What WrenAI handles for you:**
- Gateway to Bedrock (no code needed)
- Semantic layer storage (no database needed)
- Prompt engineering (no templates needed)
- SQL parsing (no validation code needed)

**Required:**
- Docker Desktop installed locally
- CTA schema definitions in YAML format
- WrenAI supports Bedrock natively (just configure in UI)

---

### 4.3 SuperSonic (Phase 3) — ENTERPRISE PRE-BUILT SYSTEM

**What it actually is:** Like WrenAI but bigger and more complex, built for large companies.

**Think of it as:** WrenAI is a food truck; SuperSonic is a restaurant chain.

**Implementation Strategy:**
- Similar to WrenAI: Run in Docker locally
- Has web UI for building semantic models (drag-and-drop)
- Has multiple database connectors
- YOUR adapter calls its API:
  ```python
  response = requests.post("http://localhost:8080/api/chat", json={
      "query": "What was Q1 revenue?"
  })
  sql = response.json()["sql"]
  ```

**What YOU need to provide:**
- Schema definitions (via their web UI)
- Snowflake connection details
- Bedrock credentials (configure in their admin panel)

**What SuperSonic handles for you:**
- Everything WrenAI does, PLUS:
  - User management (multi-tenant)
  - Dashboard creation
  - Query history
  - Permission controls

**Required:**
- Docker Desktop installed locally
- More RAM than WrenAI (8GB+ recommended)
- Complex configuration files

---

### 4.4 Custom Claude SDK (Phase 4 / Fallback)

**What it actually is:** Writing ALL the code yourself — no frameworks, no pre-built systems.

**Think of it as:** Building a kitchen from raw lumber and nails.

**Implementation Strategy:**
- Use `anthropic.AnthropicBedrock()` client directly
- Build your OWN semantic layer (Python dictionaries)
- Build your OWN gateway (direct API calls)
- Write your OWN prompt templates
- Parse SQL from Claude's response manually
- Validate SQL before execution

**What YOU need to build:**
- Semantic layer (Python code with table definitions)
- Gateway (direct Bedrock API calls)
- Prompt templates (text files with instructions for Claude)
- SQL parser/extractor (regex or simple parser)
- SQL validator (keyword blacklist)
- Result formatter (convert to JSON)

**Required:**
```
anthropic[bedrock]        # Claude SDK with Bedrock support
snowflake-connector-python  # Direct Snowflake connection
```

**Best for:** Learning how everything works, maximum control

---

## 5. Data Access & Security

### Snowflake Connection

**Read-only service account.** POC should never write, delete, or modify data.

```python
# config/snowflake.yaml
snowflake:
  account: "cta.snowflakecomputing.com"
  user: "POC_READONLY"
  role: "POC_READER"
  warehouse: "POC_WH"
  database: "CTA_PROD"
  schema: "PUBLIC"
  readonly: true  # Enforce at connection level
```

### SQL Validation (Before Execution)

```python
class SQLValidator:
    FORBIDDEN_KEYWORDS = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']
    
    @staticmethod
    def validate(sql: str) -> bool:
        upper_sql = sql.upper()
        return not any(keyword in upper_sql for keyword in FORBIDDEN_KEYWORDS)
```

### Sandbox Warehouse

Use dedicated POC warehouse with auto-suspend after 1 minute to minimize costs.

---

## 6. Testing Strategy

### Test Corpus (From Katherine)

Need 5-10 real business questions. Example categories:
1. **Counting**: "How many active members?"
2. **Aggregation**: "Total revenue by quarter?"
3. **Joins**: "Members who attended events?"
4. **Time-based**: "New members last month?"
5. **Business terms**: "CES attendance vs. CES 2025?"

### Evaluation Script

```python
async def evaluate_harness(adapter: NLToSQLAdapter, test_cases: List[TestCase]):
    results = []
    for test in test_cases:
        start = time.time()
        result = await adapter.generate_sql(test.question, schema_context)
        latency = (time.time() - start) * 1000
        
        # Execute SQL (safely)
        sql_valid = SQLValidator.validate(result.sql)
        execution_success = False
        if sql_valid:
            try:
                df = snowflake.execute(result.sql)
                execution_success = True
            except Exception as e:
                execution_error = str(e)
        
        results.append({
            "harness": adapter.get_name(),
            "question": test.question,
            "sql": result.sql,
            "sql_valid": sql_valid,
            "execution_success": execution_success,
            "latency_ms": latency,
            "confidence": result.confidence
        })
    
    return results
```

### Comparison Report

Generate side-by-side comparison:
- Accuracy: % of questions with valid, successful SQL
- Latency: Average time per question
- SQL Quality: Readability, correctness, efficiency
- Coverage: Which harnesses handle which question types?

---

## 7. Implementation Phases (Beginner-Friendly)

### ⚠️ BEFORE YOU START: Safety Checklist
- [ ] Create a new branch: `git checkout -b poc-langchain-test`
- [ ] Confirm you have a LOCAL test database (SQLite file, not Snowflake)
- [ ] Verify you have read-only Snowflake credentials (never use admin account)
- [ ] Have Katherine's phone/Slack in case you need help

### Phase 1: LangChain Starter (Days 1-3)
**Goal:** Get ONE query working end-to-end (question → SQL → result)

**Day 1: Setup (No Coding Yet)**
- [ ] Install Python 3.11+ on your laptop
- [ ] Install VS Code (free code editor)
- [ ] Create project folder: `~/cta-ai-poc/`
- [ ] Create Git branch: `git checkout -b poc-langchain-test`
- [ ] Install required packages (see Section 4.1)
- [ ] Create a local SQLite test database with sample data
- [ ] Test: Can you run a simple Python script that prints "Hello World"?

**Day 2: First NL→SQL Pipeline**
- [ ] Implement the common interface (Section 2)
- [ ] Build LangChain adapter (copy code from Section 4.1)
- [ ] Configure it to use SQLite (NOT Snowflake yet)
- [ ] Test with question: "How many users are in the database?"
- [ ] Verify it generates SQL like: `SELECT COUNT(*) FROM users`
- [ ] If it breaks, check the error message, Google it, or ask for help

**Day 3: Add Snowflake (Carefully)**
- [ ] Create a NEW branch: `git checkout -b poc-langchain-snowflake`
- [ ] Add Snowflake connection (using read-only credentials)
- [ ] Add SQL validation (Section 5)
- [ ] Test with 3-5 basic questions from Katherine
- [ ] Compare results: Does the SQL return correct numbers?
- [ ] If wrong, debug: Is the table name correct? Are the JOINs right?

**Success:** You can type a question in English and get a correct answer from Snowflake in under 15 seconds.

---

### Phase 2: Test WrenAI (Days 4-5)
**Goal:** Test a pre-built system. See if it's easier/better than hand-built LangChain.

**IMPORTANT:** WrenAI is a COMPLETE APPLICATION, not a library. You don't "build an adapter" — you install it and use it.

**Day 4: Install and Configure WrenAI**
- [ ] Create branch: `git checkout -b poc-wrenai-test`
- [ ] Install Docker Desktop (if approved by IT)
- [ ] Download and run WrenAI container:
  ```bash
  docker run -p 3000:3000 wrenai/wrenai
  ```
- [ ] Open browser to `http://localhost:3000`
- [ ] You should see WrenAI's web interface!
- [ ] Upload CTA schema definitions (YAML file with table descriptions)
- [ ] Configure Snowflake connection (in WrenAI's web UI)
- [ ] Configure Bedrock credentials (in WrenAI's web UI)

**Day 5: Test and Compare**
- [ ] Ask WrenAI the SAME test questions you asked LangChain
- [ ] Write down the SQL it generates
- [ ] Compare: Is it better than LangChain? Easier to set up?
- [ ] Note problems: Does it misunderstand your tables? Is it slower?
- [ ] DECISION: Keep using WrenAI for MVP, or stick with LangChain?

**Debugging WrenAI:**
- Check WrenAI's logs: `docker logs <container_name>`
- Check if Bedrock is responding (in WrenAI's admin panel)
- If SQL is wrong, check if schema definitions are correct

---

### Phase 3: Test SuperSonic (Days 6-7)
**Goal:** Test the enterprise option. See if extra features are worth complexity.

**IMPORTANT:** SuperSonic is also a COMPLETE APPLICATION. Similar to WrenAI but bigger.

**Day 6-7: Install and Configure SuperSonic**
- [ ] Create branch: `git checkout -b poc-supersonic-test`
- [ ] Run SuperSonic container (command will be in their docs)
- [ ] Open browser to `http://localhost:8080`
- [ ] Use their web UI to build semantic model (drag-and-drop)
- [ ] Configure Snowflake and Bedrock in their admin panel
- [ ] Ask the SAME test questions
- [ ] Compare results with LangChain and WrenAI

**Note:** SuperSonic requires more RAM (8GB+) and more setup than WrenAI. If your laptop struggles, skip to Phase 4.

---

### Phase 4: Build Custom Claude SDK (Days 8-9)
**Goal:** Learn how NL→SQL works at the lowest level. Build everything from scratch.

**Day 8-9: Hand-Built Implementation**
- [ ] Create branch: `git checkout -b poc-custom-test`
- [ ] Install packages: `pip install anthropic[bedrock] snowflake-connector-python`
- [ ] Build EVERYTHING yourself (no LangChain helpers):
  - [ ] Write prompt template (text file telling Claude how to write SQL)
  - [ ] Write gateway code (direct boto3 calls to Bedrock)
  - [ ] Write SQL parser (extract SQL from Claude's response text)
  - [ ] Write SQL validator (check for dangerous keywords)
  - [ ] Write Snowflake connector (run SQL and get results)
- [ ] Test same questions
- [ ] Compare: Is hand-built better than LangChain? More work but more control?

**This is like:** Building a kitchen from scratch after working with a pre-built one. You'll understand every screw and nail.

---

### Phase 5: Comparison & Decision (Day 10)
**Goal:** Pick the winner for MVP

**What you're comparing:**
| Approach | What You Built vs What Came Pre-Built |
|----------|--------------------------------------|
| **LangChain** | You wrote adapter code, used LangChain's gateway |
| **WrenAI** | You wrote a simple API client, WrenAI did everything else |
| **SuperSonic** | You wrote a simple API client, SuperSonic did everything else |
| **Custom SDK** | You wrote EVERYTHING (gateway, parser, validator, etc.) |

**Comparison Criteria:**
- [ ] Create branch: `git checkout -b poc-comparison`
- [ ] Run ALL 4 approaches against the SAME 5-10 test questions
- [ ] Fill out comparison spreadsheet:
  | Harness | Accuracy | Latency | Setup Time | Debuggability | Your Rating |
  |---------|----------|---------|-----------|---------------|-------------|
  | LangChain | ?% | ? sec | ? hours | Easy/Hard | 1-5 |
  | WrenAI | ?% | ? sec | ? hours | Easy/Hard | 1-5 |
  | SuperSonic | ?% | ? sec | ? hours | Easy/Hard | 1-5 |
  | Custom SDK | ?% | ? sec | ? hours | Easy/Hard | 1-5 |
- [ ] Write 1-page recommendation: "We recommend [X] because..."
  - Include: Setup time comparison
  - Include: Debugging experience (which was easier to fix?)
  - Include: SQL quality comparison (which generated better SQL?)
  - Include: Your confidence maintaining each option
- [ ] Share with Katherine and senior engineering for review

---

## 8. Specific Client Requests (Copy-Paste Ready)

These are the **EXACT** questions to ask Katherine/CTA. Copy and paste these into an email or Slack message.

### Request #1: AWS Bedrock Access
**Send to:** CTA AWS Administrator (IT/Ops team)

```
Subject: POC Request - AWS Bedrock Access for AI Testing

Hi [Name],

I'm running a 1-2 week POC to test AI-generated SQL against our Snowflake data. 
I need the following AWS permissions:

1. Can you confirm AWS Bedrock is enabled in our account?
2. Which Bedrock models are available? (Ideally Claude 3.5 Sonnet)
3. Can I get an IAM user or role with these specific permissions?
   - bedrock:InvokeModel (to call Claude)
   - bedrock:ListFoundationModels (to see available models)
   - logs:CreateLogGroup (for CloudWatch logging)
   - logs:CreateLogStream (for CloudWatch logging)
   - logs:PutLogEvents (for CloudWatch logging)

4. Is there an existing S3 bucket I can use for POC files? If not, can you create one named:
   cta-ai-poc-[your-name]-dev

5. Can I create Lambda functions, or do I need you to create them?

This is read-only testing only. No production data will be modified.

Thanks!
[Your name]
```

### Request #2: Snowflake Read-Only Access
**Send to:** Katherine + Snowflake Administrator

```
Subject: POC Request - Snowflake Read-Only Account for AI Testing

Hi Katherine and [Snowflake Admin],

For the AI POC, I need a read-only Snowflake account with these specifics:

1. Username: POC_READONLY_USER
2. Role: POC_READER_ROLE
3. Warehouse: POC_WAREHOUSE (XS size, auto-suspend after 1 minute)
4. Database access: Read-only access to [production database name]
5. Schema access: [list specific schemas needed]

IMPORTANT: This account must NOT have permission to:
   - INSERT, UPDATE, DELETE any data
   - DROP tables or schemas
   - CREATE new objects
   - Grant permissions to others

The warehouse should be dedicated to POC use and auto-suspend immediately to save costs.

Can you provide:
- Account URL (e.g., cta.snowflakecomputing.com)
- Username and password (or better: key-pair authentication)
- Exact database and schema names I should connect to

I'll start with just 3-5 test queries, then scale up.

Thanks!
[Your name]
```

### Request #3: Business Questions for Testing
**Send to:** Katherine + CTA Business Users

```
Subject: Need 5-10 Real Business Questions for AI POC

Hi Katherine,

To test the AI SQL generator, I need real questions that CTA staff actually ask.

Can you and your team provide 5-10 questions like these examples?

Examples:
- "How many members joined in Q1 2025?"
- "What is total revenue by region for CES 2026?"
- "Which members attended both CES 2025 and CES 2026?"
- "How many new member applications are pending?"
- "What is the retention rate for members who joined in 2024?"

The questions should:
1. Be real questions someone at CTA asks regularly
2. Require data from our Snowflake database
3. Range from simple (one table) to medium (2-3 tables joined)

I'll use these to test if the AI generates correct SQL. No sensitive data will be shared outside CTA.

Thanks!
[Your name]
```

### Request #4: Docker Permission
**Send to:** Engineering Lead / DevOps

```
Subject: POC Request - Docker Installation Permission

Hi [Name],

For the POC, I need to run Docker Desktop locally to test two NL→SQL tools (WrenAI and SuperSonic).

Questions:
1. Can I install Docker Desktop on my laptop? (free download from docker.com)
2. Are there any company policies blocking Docker?
3. Is there a preferred version or installation method?
4. If Docker is blocked, can we get a temporary exception for 1-2 weeks?

Docker will only run locally on my machine. Nothing gets deployed to production.

Thanks!
[Your name]
```

### Request #5: Cost Approval
**Send to:** Katherine + Finance/Procurement

```
Subject: POC Budget - AWS Bedrock and Snowflake Costs

Hi Katherine,

Estimated costs for the 1-2 week POC:

AWS Bedrock:
- Claude 3.5 Sonnet: ~$3-5 per 1,000 queries
- Expected: 100-200 test queries = $5-15 total
- No monthly subscription, pay-per-use only

Snowflake:
- POC warehouse: XS size = ~$2-4 per hour when running
- Auto-suspend after 1 minute = usually $0 (suspended most of the time)
- Estimated: $10-50 for the entire POC

Total estimated cost: $15-65 for the entire 1-2 week POC.

Can we get approval for up to $100 to be safe?

Thanks!
[Your name]
```

### Request #6: Repository Location (Where Does Code Live?)
**Send to:** Katherine + Engineering Lead

```
Subject: POC Question - Where Should We Put the AI Experiment Code?

Hi Katherine and [Engineering Lead],

Quick question about the POC code location:

I see CTA's current DataOps repo (this one) has production dbt models, infrastructure, and pipelines. For the AI POC, I want to make sure I don't accidentally affect any production code.

Question: Should the POC live in:
1. A NEW GitHub repo (e.g., "cta-ai-poc") - completely separate from production
2. A subfolder in the existing repo (e.g., /poc-ai-sql/) - same repo, different folder
3. My personal GitHub account - isolated, but harder to share

My recommendation: Option 1 (new repo) to keep it completely separate from production dbt/infrastructure code and avoid any risk of accidentally triggering production CI/CD.

Can I get permission to create a new private repo under the CTA GitHub organization? Or should I use my personal account?

Also: What naming convention should we use? I was thinking:
- Repo name: cta-ai-nl2sql-poc
- Branch naming: poc/langchain-test, poc/wrenai-test, etc.

Let me know what works best for the team!

Thanks!
[Your name]
```

---

## 9. Success Criteria

| Criteria | Target | How Measured |
|----------|--------|--------------|
| **End-to-end working** | LangChain adapter generates and executes SQL | Manual test |
| **All 4 adapters built** | Each implements common interface | Code review |
| **Test corpus passed** | 70%+ of questions generate valid SQL | Evaluation script |
| **Comparison report** | Side-by-side metrics for all 4 | Automated report |
| **Decision made** | Clear recommendation for MVP | Team review |

---

## 10. Definition of Ready (for `/ce:plan`)

**DO NOT START CODING until ALL of these are checked off.**

### Pre-Coding Checklist

- [ ] **GitHub repo access**: You can create branches in the CTA repo (or a separate POC repo)
  - If NO: Ask Katherine for GitHub access or create a personal repo
  - DECISION NEEDED: Will POC live in new repo or existing repo? (See Request #6)
  
- [ ] **AWS Bedrock access confirmed**: 
  - You have an AWS account or IAM user
  - You can log into AWS Console
  - Bedrock service is visible (not grayed out)
  - Test: Can you see Claude models in the Bedrock console?
  
- [ ] **Snowflake read-only credentials in hand**:
  - You have the username, password, and account URL
  - You have tested logging into Snowflake web UI
  - You can see tables (but cannot modify them)
  - Test: Run `SELECT COUNT(*) FROM some_table` successfully
  
- [x] **Test corpus received**:
  - Katherine sent 5-10 real questions ✅
  - You understand what the correct answers should look like
  - You know which tables/columns are involved
  
- [ ] **Docker decision made**:
  - Docker is installed OR you have permission to install it
  - OR you know WrenAI/SuperSonic will be skipped
  
- [ ] **Budget approved**:
  - Katherine or finance approved up to $100 for POC costs
  - You know who to ask if costs exceed estimate

### Safety Verification (Before First Snowflake Query)

- [ ] You are on a branch (not `main`)
- [ ] SQL validation code is working (tested with a fake DROP command)
- [ ] You have confirmed the Snowflake user is read-only
- [ ] You have a local backup or know you can recreate everything

### If ANY item is missing:
- STOP and ask for help
- Do not "just try it anyway"
- Missing items usually take 1-3 days to resolve (permissions, access, etc.)

---

## 11. Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Starter harness** | LangChain | Best docs, community, built-in Snowflake support |
| **Gateway default** | AWS Bedrock | CTA already on AWS; IAM auth; CloudTrail |
| **Provider switch** | Anthropic direct via config | Gateway supports both; swap without code changes |
| **Hosting** | AWS Lambda | Serverless, fits existing VPC, minimal setup |
| **Storage** | Amazon S3 | Simple, available, no new infrastructure |
| **Auth** | None for POC | Focus on core NL→SQL; add auth for MVP |
| **Docker for WrenAI/SuperSonic** | Local Docker | POC only; move to ECS for production |
| **SQL validation** | Keyword blacklist | Simple, effective for POC; add query parsing for MVP |

## Appendix B: Glossary of Terms (For Beginners)

This document uses a lot of jargon. Here is what every term actually means in plain English.

### People & Roles

| Term | What It Means | Analogy |
|------|---------------|---------|
| **DataOps** | The team that manages data pipelines and databases | The plumbers and electricians of the data world |
| **CTA** | Consumer Technology Association (your client, a nonprofit) | The organization you're building this for |
| **Katherine** | Your main contact at CTA | Your "customer" who gives you requirements |
| **Senior Engineering** | Experienced developers who review your work | A teacher who checks your homework before you turn it in |
| **AWS Admin** | The person at CTA who manages AWS accounts | The building manager who has keys to every room |

### Technical Terms

| Term | What It Means | Analogy |
|------|---------------|---------|
| **Repository (Repo)** | A folder containing all your code, tracked by Git | A filing cabinet with a memory chip that remembers every change |
| **Git** | A program that remembers every change you make to files | A time machine for your code — you can go back to any point |
| **Branch** | A copy of your code where you can experiment safely | A sandbox — you can build castles without affecting the real playground |
| **Commit** | A saved "checkpoint" of your code | A save point in a video game |
| **Merge** | Combining your experimental code back into the main code | Merging two drafts of an essay into one final version |
| **AWS** | Amazon Web Services — cloud computers you rent | Renting a kitchen instead of building one in your house |
| **AWS Bedrock** | AWS's service that hosts AI models like Claude | A vending machine that dispenses AI brains |
| **Lambda** | AWS service that runs code without managing servers | A food delivery service — you order, they cook, you don't see the kitchen |
| **S3** | AWS's file storage service | An infinite filing cabinet in the cloud |
| **IAM Role** | A set of permissions assigned to a computer program | An employee badge that says "this person can enter these rooms" |
| **Docker** | A program that packages applications so they run anywhere | A shipping container for software |
| **Container** | A running instance of a packaged application | The actual shipping container, now on a truck, moving |
| **API** | A way for two computer programs to talk to each other | A waiter taking orders between a customer and a kitchen |
| **REST API** | A common way to build APIs using web addresses (URLs) | A standardized menu format every restaurant uses |
| **JSON** | A text format for storing data | A structured shopping list: `{ "item": "milk", "quantity": 2 }` |
| **YAML** | Another text format for storing config/settings | A cleaner shopping list without curly braces |
| **SQL** | A language for asking databases questions | A way to say "Show me all customers who bought milk" to a computer |
| **NL→SQL** | Natural Language to SQL — converting English to database queries | A translator who converts "What did I spend last month?" to database language |
| **Semantic Layer** | A document that translates business words to database tables | A dictionary that says "Member = table users, Revenue = column sales.amount" |
| **Schema** | The structure of a database (table names, column names, types) | The blueprint of a building showing where every room is |
| **Adapter** | Code that connects two different systems | A power adapter that lets you plug a US device into a European outlet |
| **Gateway** | Code that translates between your app and an external service | A universal translator in a sci-fi movie |
| **Harness** | A framework or tool for doing a specific job | A car engine — different engines (V6, electric, hybrid) that all make the car move |
| **LangChain** | A Python library for building AI applications | A LEGO set for building AI projects |
| **WrenAI / SuperSonic** | Complete applications (not libraries) that do NL→SQL | Pre-built kitchens you can rent — no construction needed |
| **Claude** | An AI model made by Anthropic that can write SQL | A very smart intern who writes database queries for you |
| **Prompt** | The instructions you give to an AI | The exact words you say to the intern: "Please write SQL to count users" |
| **Token** | A piece of text that AI models process (roughly 4 characters) | The "currency" AI uses — you pay per token processed |
| **Vector Store** | A database that finds similar text using math | A librarian who doesn't just find exact matches, but also "books like this one" |
| **RAG** | Retrieval-Augmented Generation — looking up facts before answering | A student who checks their notes before answering an exam question |
| **CI/CD** | Continuous Integration / Continuous Deployment — automated testing and deployment | A robot that automatically checks your homework and submits it |
| **MVP** | Minimum Viable Product — the simplest version that works | A skateboard before you build a car — gets you moving fast |
| **POC** | Proof of Concept — a quick experiment to prove something works | A science fair project — test if your idea works before building the real thing |

### Git Commands You'll Actually Use

| Command | What It Does | When to Use It |
|---------|--------------|----------------|
| `git status` | Shows which files you changed | Every time before committing |
| `git add .` | Prepares all changed files to be saved | Before committing |
| `git commit -m "message"` | Saves a checkpoint with a note | After each small working change |
| `git checkout -b new-branch` | Creates a new sandbox branch | Before starting any new experiment |
| `git checkout main` | Goes back to the safe main branch | When you want to start over |
| `git log` | Shows your save history | When you want to go back to an old version |
| `git diff` | Shows exactly what you changed | When you forget what you just did |

### Python Terms

| Term | What It Means |
|------|---------------|
| **Package** | A folder of code that does something specific (like `langchain`) |
| **Import** | Bringing someone else's code into your program (`import langchain`) |
| **Function** | A named block of code that does one thing (`def my_function():`) |
| **Class** | A blueprint for creating objects with data and behavior |
| **Method** | A function that belongs to a class |
| **Variable** | A named box that holds data (`x = 5`) |
| **List** | An ordered collection of items (`[1, 2, 3]`) |
| **Dictionary** | A collection of labeled items (`{"name": "Alice", "age": 30}`) |
| **String** | Text data (`"Hello world"`) |
| **Boolean** | True or False |
| **None** | Nothing, empty, null |
| **Exception / Error** | When something goes wrong in your code |
| **Try/Except** | "Try this code, and if it breaks, do this instead" |
| **Async / Await** | Running code that waits for slow things (like API calls) without freezing |

---

*Document prepared for AI planning agent. Last updated: 2026-05-28*
