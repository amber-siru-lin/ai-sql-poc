"""Core NL→SQL logic: Bedrock (Nova Pro) + Snowflake."""

from __future__ import annotations

import sys
from pathlib import Path

from langchain_aws import ChatBedrock
import snowflake.connector

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from config.snowflake_config import (
        account,
        database,
        password,
        schema,
        user,
        warehouse,
    )
except ImportError as exc:
    raise SystemExit(
        "Missing config/snowflake_config.py\n"
        "Run: cp config/snowflake_config.example.py config/snowflake_config.py\n"
        "Then fill in your Snowflake credentials."
    ) from exc

SCHEMA_PATH = REPO_ROOT / "schema" / "tpch_sf1.md"
BEDROCK_MODEL_ID = "us.amazon.nova-pro-v1:0"
BEDROCK_REGION = "us-east-1"
SNOWFLAKE_SCHEMA = "TPCH_SF1"


def load_schema() -> str:
    return SCHEMA_PATH.read_text(encoding="utf-8")


def ask_ai(question: str, *, verbose: bool = True) -> str:
    """Send a question to Bedrock and return generated SQL."""
    if verbose:
        print(f"🤖 Asking AI: {question}")

    llm = ChatBedrock(model_id=BEDROCK_MODEL_ID, region_name=BEDROCK_REGION)
    prompt = f"""You are a SQL expert. Here is the database schema:

{load_schema()}

Write a SQL query to answer this question: {question}

Requirements:
- Return ONLY the SQL query, no explanation, no markdown
- Use Snowflake SQL syntax
- Use schema: {SNOWFLAKE_SCHEMA}
- Use fully qualified table names: {SNOWFLAKE_SCHEMA}.CUSTOMER, {SNOWFLAKE_SCHEMA}.ORDERS, etc.
- Do not include any text before or after the SQL
"""

    response = llm.invoke(prompt)
    sql = response.content
    return sql.replace("```sql", "").replace("```", "").strip()


def run_sql(sql: str, *, verbose: bool = True):
    """Execute SQL on Snowflake and return column names + rows."""
    if verbose:
        print(f"🔍 Running SQL: {sql}")

    conn = snowflake.connector.connect(
        account=account,
        user=user,
        password=password,
        warehouse=warehouse,
        database=database,
        schema=schema,
    )
    try:
        cursor = conn.cursor()
        cursor.execute(f"USE SCHEMA {SNOWFLAKE_SCHEMA}")
        cursor.execute(sql)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        return columns, results
    finally:
        conn.close()
