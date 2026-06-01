---
title: Super Simple AI NL-to-SQL POC Plan
type: feat
status: active
date: 2026-05-28
origin: docs/brainstorms/2026-05-28-ai-data-analysis-poc-requirements.md
---

# Super Simple AI NL-to-SQL POC Plan

## Overview

Get ONE English question → SQL → Answer working in **2-3 days** using your own AWS account and a free Snowflake trial. No CTA permissions needed. No Docker. Just prove NL→SQL works.

**Goal:** Ask "How many users joined in 2025?" and get a real answer from Snowflake.

**Why this exists:** The main plan is for CTA production. This is a **personal sandbox** where you can break things safely and learn.

---

## What You Need (Check These Off)

- [ ] **Your own AWS account** (or company internal account) with Bedrock access
- [ ] **5 minutes** to sign up for Snowflake free trial
- [ ] **Your laptop** with Python installed
- [ ] **Katherine's test questions** (you already have these!)

**That's it.** No asking IT for permissions. No waiting for approvals.

---

## Architecture (Super Simple)

```
You (laptop)
  │
  ├──→ LangChain code (Python)
  │       ├──→ AWS Bedrock (your account)
  │       │       └──→ Claude AI
  │       └──→ SQL answer
  │
  └──→ Snowflake (free trial)
          └──→ Real data
```

**What we're NOT doing:**
- ❌ No Docker
- ❌ No WrenAI/SuperSonic (too complex for first test)
- ❌ No separate repo (just a folder on your laptop)
- ❌ No CI/CD
- ❌ No CloudWatch
- ❌ No S3
- ❌ No Lambda (run on your laptop)
- ❌ No read-only restrictions (it's YOUR demo data)

**What we ARE doing:**
- ✅ Install Python packages
- ✅ Write 1 Python script
- ✅ Sign up for Snowflake free trial
- ✅ Test 3-5 questions
- ✅ See if it works

---

## Day 1: Setup (2 Hours)

### Step 1: Create Project Folder (10 minutes)

Open terminal/command prompt:

```bash
# Mac/Linux
mkdir ~/ai-sql-test
cd ~/ai-sql-test

# Windows
mkdir %USERPROFILE%\ai-sql-test
cd %USERPROFILE%\ai-sql-test
```

### Step 2: Install Python Packages (5 minutes)

```bash
pip install langchain langchain-aws snowflake-connector-python
```

**What this does:** Installs 3 tools:
1. `langchain` - The LEGO toolkit for AI
2. `langchain-aws` - Connects LangChain to AWS Bedrock
3. `snowflake-connector-python` - Talks to Snowflake database

### Step 3: Sign Up for Snowflake Free Trial (5 minutes)

1. Go to: https://signup.snowflake.com/
2. Use your work email or personal email
3. Choose any company name (e.g., "AI Test")
4. Select AWS as cloud provider
5. Choose region closest to you (e.g., us-east-1)
6. **Important:** Choose "Enterprise" edition (free trial includes it)

**What you get:**
- $400 in free credits (lasts 30 days)
- Your own Snowflake account (not CTA's!)
- Full admin access (you can create/drop tables)

### Step 4: Create Demo Data (15 minutes)

Log into your Snowflake web interface and run this SQL:

```sql
-- Create a simple table
CREATE TABLE demo_users (
    id INTEGER,
    name STRING,
    join_date DATE,
    status STRING
);

-- Insert fake data
INSERT INTO demo_users VALUES
    (1, 'Alice Smith', '2024-03-15', 'active'),
    (2, 'Bob Jones', '2025-01-20', 'active'),
    (3, 'Carol White', '2025-06-10', 'inactive'),
    (4, 'David Brown', '2024-11-05', 'active'),
    (5, 'Eve Davis', '2025-02-28', 'pending');

-- Test it works
SELECT * FROM demo_users;
```

**What this does:** Creates a pretend "users" table with 5 people. This is YOUR data. You can break it.

### Step 5: Get Your Snowflake Connection Info (5 minutes)

In Snowflake web interface, click your username (top-right) → Account:

You'll see something like:
- **Account URL:** `xyz12345.us-east-1.snowflakecomputing.com`
- **Username:** Your email
- **Password:** The one you created

Save these in a file called `snowflake_config.txt` (DON'T share this):

```
Account: xyz12345
Username: your.email@company.com
Password: YourPassword123!
Database: YourDatabase
Schema: PUBLIC
Warehouse: COMPUTE_WH
```

---

## Day 1: Write the Code (1 Hour)

Create a file called `test_ai_sql.py`:

```python
# === SETUP ===
# 1. Install packages: pip install langchain langchain-aws snowflake-connector-python
# 2. Set AWS credentials: export AWS_ACCESS_KEY_ID=... (or use aws configure)
# 3. Update SNOWFLAKE_CONFIG below with your details

from langchain_aws import ChatBedrock
import snowflake.connector

# === YOUR SNOWFLAKE CONFIG ===
SNOWFLAKE_CONFIG = {
    "account": "xyz12345",  # CHANGE THIS
    "user": "your.email@company.com",  # CHANGE THIS
    "password": "YourPassword123!",  # CHANGE THIS
    "database": "DEMO_DATABASE",  # CHANGE THIS
    "schema": "PUBLIC",
    "warehouse": "COMPUTE_WH"
}

# === SIMPLE SCHEMA DESCRIPTION ===
# This teaches the AI what your tables mean
SCHEMA = """
Table: demo_users
- id: user number
- name: person's full name
- join_date: when they signed up
- status: active, inactive, or pending
"""

# === ASK THE AI TO WRITE SQL ===
def ask_ai(question):
    """Send question to Claude via Bedrock, get SQL back"""
    
    # Create the AI client
    llm = ChatBedrock(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        region_name="us-east-1"  # CHANGE if your AWS region is different
    )
    
    # Build the prompt (instructions for Claude)
    prompt = f"""
    You are a SQL expert. Here is the database schema:
    {SCHEMA}
    
    Write a SQL query to answer this question: {question}
    
    Return ONLY the SQL query, nothing else.
    The SQL should work in Snowflake.
    """
    
    # Send to Claude
    response = llm.invoke(prompt)
    
    # Extract SQL from response
    sql = response.content
    
    # Clean up (remove markdown formatting if present)
    sql = sql.replace("```sql", "").replace("```", "").strip()
    
    return sql

# === RUN SQL ON SNOWFLAKE ===
def run_sql(sql):
    """Execute SQL and return results"""
    
    # Connect to Snowflake
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    
    # Run the query
    cursor = conn.cursor()
    cursor.execute(sql)
    
    # Get results
    results = cursor.fetchall()
    
    # Clean up
    cursor.close()
    conn.close()
    
    return results

# === MAIN: ASK QUESTION AND GET ANSWER ===
if __name__ == "__main__":
    # Your test question
    question = "How many users joined in 2025?"
    
    print(f"Question: {question}")
    print("=" * 50)
    
    # Step 1: Ask AI to write SQL
    print("Asking Claude to write SQL...")
    sql = ask_ai(question)
    print(f"SQL: {sql}")
    print("-" * 50)
    
    # Step 2: Run SQL on Snowflake
    print("Running SQL on Snowflake...")
    results = run_sql(sql)
    print(f"Results: {results}")
    print("=" * 50)
    
    # Success!
    print("✅ It works! AI wrote SQL and we got an answer.")
```

### Test It (5 minutes)

```bash
python test_ai_sql.py
```

**Expected output:**
```
Question: How many users joined in 2025?
==================================================
Asking Claude to write SQL...
SQL: SELECT COUNT(*) FROM demo_users WHERE YEAR(join_date) = 2025
--------------------------------------------------
Running SQL on Snowflake...
Results: [(3,)]
==================================================
✅ It works! AI wrote SQL and we got an answer.
```

**If it fails:**
1. Check AWS credentials: `aws sts get-caller-identity`
2. Check Snowflake connection info is correct
3. Check Bedrock model ID is available in your region

---

## Day 2: Test Katherine's Questions (1 Hour)

Now test the real questions from Katherine. Create `test_katherine_questions.py`:

```python
from test_ai_sql import ask_ai, run_sql

# Katherine's questions
questions = [
    "How many active users do we have?",
    "Who joined in 2025?",
    "How many inactive users?",
    # Add more from Katherine's list
]

for question in questions:
    print(f"\nQuestion: {question}")
    print("-" * 50)
    
    try:
        # Get SQL from AI
        sql = ask_ai(question)
        print(f"SQL: {sql}")
        
        # Run on Snowflake
        results = run_sql(sql)
        print(f"Answer: {results}")
        
        # Is it correct? (You be the judge)
        print("✅ Query succeeded")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("SQL might be wrong or question is too complex")
```

Run it:
```bash
python test_katherine_questions.py
```

**For each question, ask yourself:**
1. Did the AI understand the question?
2. Is the SQL valid?
3. Does the answer make sense?
4. How long did it take?

**Write down your results:**

| Question | SQL Correct? | Answer Makes Sense? | Time (seconds) |
|----------|-------------|---------------------|----------------|
| How many active users? | Yes/No | Yes/No | 3.2 |
| ... | ... | ... | ... |

---

## Day 2-3: Wren / Cortex (optional — see Phase 4 plan)

> **Updated 2026-06-01:** The old `docker run -p 3000:3000 wrenai/wrenai` GenBI UI is on **`legacy/v1`**, not `main`. We do **not** use v1 or Wren’s product UI.

**Phase 4** compares:

1. **Wren `main`** — `pip install "wrenai[snowflake,memory]"`, MDL in git, CLI/SDK behind our UI  
2. **Snowflake Cortex Analyst** — Semantic View + REST API  

See: [docs/plans/2026-06-01-004-feat-wren-ai-phase-4-plan.md](2026-06-01-004-feat-wren-ai-phase-4-plan.md) and [docs/architecture/wren-vs-snowflake-cortex-analyst.md](../architecture/wren-vs-snowflake-cortex-analyst.md).

---

## Day 3-5: Add Amplify (Learn as You Go)

**Goal:** Put your working NL→SQL code behind a web interface

**Why now:** You proved the core concept works. Now learn Amplify by wrapping it around working code.

### Step 1: Set Up Amplify Project (1 hour)

```bash
# Install Amplify CLI
npm install -g @aws-amplify/cli

# Create new React app
npx create-react-app ai-sql-ui
cd ai-sql-ui

# Initialize Amplify
amplify init
# Choose: JavaScript, React, AWS profile

# Add API (REST endpoint)
amplify add api
# Choose: REST, API Gateway + Lambda
# Name: aiSqlApi
```

### Step 2: Create Lambda Function (30 minutes)

Amplify creates a Lambda function. Replace its code with:

```python
# amplify/backend/function/aiSqlApi/src/index.py
import json
from test_ai_sql import ask_ai, run_sql  # Your working code!

def handler(event, context):
    # Parse request
    body = json.loads(event['body'])
    question = body['question']
    
    # Call your working NL→SQL code
    sql = ask_ai(question)
    results = run_sql(sql)
    
    # Return response
    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({
            'question': question,
            'sql': sql,
            'results': results
        })
    }
```

**Key insight:** You're not rewriting your NL→SQL code. You're just wrapping it in a Lambda function that Amplify serves.

### Step 3: Create React UI (2 hours)

Create `src/App.js`:

```javascript
import React, { useState } from 'react';
import { API } from 'aws-amplify';

function App() {
  const [question, setQuestion] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const askQuestion = async () => {
    setLoading(true);
    try {
      const response = await API.post('aiSqlApi', '/ask', {
        body: { question }
      });
      setResults(response);
    } catch (error) {
      console.error(error);
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto' }}>
      <h1>AI SQL Assistant</h1>
      
      <input
        type="text"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask a question about your data..."
        style={{ width: '100%', padding: '10px', marginBottom: '10px' }}
      />
      
      <button onClick={askQuestion} disabled={loading}>
        {loading ? 'Thinking...' : 'Ask AI'}
      </button>

      {results && (
        <div style={{ marginTop: '20px' }}>
          <h3>SQL:</h3>
          <pre>{results.sql}</pre>
          
          <h3>Answer:</h3>
          <pre>{JSON.stringify(results.results, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default App;
```

### Step 4: Deploy (30 minutes)

```bash
# Deploy backend
amplify push

# Deploy frontend
npm run build
amplify hosting add
amplify publish
```

**What you get:** A URL like `https://abc123.cloudfront.net` where you can:
1. Type a question
2. Click "Ask AI"
3. See the SQL and answer

### What You Learned

- **Amplify CLI:** How to create projects, add APIs, deploy
- **Lambda:** How to run Python code in the cloud
- **API Gateway:** How to create HTTP endpoints
- **React:** Basic UI components (input, button, display)
- **CORS:** How browsers talk to APIs

---

## Success Criteria (Day 5)

| Test | Pass? | Evidence |
|------|-------|----------|
| AI writes valid SQL | ✅ | `test_ai_sql.py` runs without errors |
| SQL returns correct data | ✅ | Answer matches what you expect |
| Katherine's questions work | ✅ | 3+ questions answered correctly |
| You understand how it works | ✅ | Can explain to someone else |

**If all pass:** You're ready for the real POC with CTA infrastructure.

**If some fail:** That's fine! You learned what doesn't work. Adjust and try again.

---

## What You Learned

After 2-3 days, you should understand:

1. **How NL→SQL works:** Question → AI → SQL → Database → Answer
2. **LangChain basics:** How to connect AI to databases
3. **AWS Bedrock:** How to use Claude through AWS
4. **Snowflake connection:** How to query databases from Python
5. **What works/what doesn't:** Which questions AI answers well

---

## Transition to Real CTA POC

Once this works:

1. **Show Katherine:** "Look, I asked 'How many users?' and got an answer in 3 seconds!"
2. **Use CTA AWS account:** Swap your personal AWS credentials for CTA's
3. **Use CTA Snowflake:** Swap demo data for CTA's real data (read-only!)
4. **Add safety:** SQL validator, read-only account, etc. (from main plan)
5. **Scale up:** Test all 4 harnesses, build comparison report

---

## Troubleshooting

### "AWS Bedrock not working"
- Check: `aws configure list` (shows your credentials)
- Check: AWS region has Bedrock (us-east-1 and us-west-2 usually do)
- Check: You have permission to invoke Bedrock models

### "Snowflake connection refused"
- Check: Account name format (should be `xyz12345`, not full URL)
- Check: Password is correct (Snowflake passwords are case-sensitive)
- Check: Warehouse exists (`COMPUTE_WH` is default)

### "AI writes bad SQL"
- Add more schema details (column types, example values)
- Simplify question ("How many users?" vs "What's the retention cohort analysis?")
- Check: Is Claude 3.5 Sonnet available? (older models write worse SQL)

### "Results don't make sense"
- Check: Did AI use wrong table name?
- Check: Did AI use wrong column name?
- Check: Is the data in Snowflake what you expect?

---

## Files You Created

```
~/ai-sql-test/                      <-- Your test folder
    test_ai_sql.py                  <-- Main script (ask AI, run SQL)
    test_katherine_questions.py     <-- Test real questions
    snowflake_config.txt            <-- Passwords (KEEP SECRET!)
```

**Note:** This is just a test folder on your laptop. Not a Git repo. Not connected to CTA. Safe to delete when done.

---

## Time Estimate

| Day | Activity | Time |
|-----|----------|------|
| **Day 1** | Setup + First working query | 2-3 hours |
| **Day 2** | Test Katherine's questions + evaluate | 1-2 hours |
| **Day 2-3** | Try WrenAI (optional) | 1 hour |
| **Total** | | **3-6 hours** |

---

## Next Steps

1. **If this works:** Show results to Katherine, get CTA AWS/Snowflake access
2. **If this works well:** Use main POC plan for full 4-harness comparison
3. **If this is confusing:** Ask for help! The main plan has more detail.

---

*This is a sandbox. Break things. Learn. Have fun.*

*When ready for production, use the full plan: docs/plans/2026-05-28-001-feat-ai-nl2sql-poc-plan.md*