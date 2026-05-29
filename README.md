# AI SQL POC — Natural Language to SQL

Ask questions in English, get SQL queries run against Snowflake using Amazon Bedrock (Nova Pro).

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up Snowflake credentials
cp snowflake_config.template.py snowflake_config.py
# Edit snowflake_config.py with your real credentials

# 3. Configure AWS (for Bedrock access)
aws configure

# 4. Run the interactive demo
python ask_questions.py
```

## What it does

- You type a question like *"What is the total amount of all orders?"*
- AI (Amazon Nova Pro via Bedrock) writes a SQL query
- Query runs against Snowflake sample data
- Results print to your terminal

## Files

| File | What it does |
|------|-------------|
| `test_ai_sql.py` | Core POC — AI → SQL → Snowflake pipeline |
| `ask_questions.py` | Interactive CLI — keep asking questions |
| `snowflake_config.template.py` | Template for credentials (copy to `snowflake_config.py`) |
| `setup_demo_data.sql` | Creates sample tables if needed |
| `create_inference_profile.py` | Helper for Bedrock inference profiles |
| `diagnose_bedrock.py` | Debug Bedrock model access |
| `setup_aws.sh` | Interactive AWS credential setup |

## Security

- `snowflake_config.py` is in `.gitignore` — never commit credentials
- AWS credentials go in `~/.aws/credentials` (managed by `aws configure`)

## Requirements

- Python 3.10+
- Snowflake account (free trial works)
- AWS account with Bedrock access (Nova Pro or Claude)
