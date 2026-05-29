# AI SQL Test - Natural Language to SQL
#
# SETUP:
#   1. cp snowflake_config.template.py snowflake_config.py
#   2. Edit snowflake_config.py with your Snowflake credentials
#   3. Run: aws configure (set up AWS credentials for Bedrock)
#   4. Run setup_demo_data.sql in Snowflake (if using custom data)
#   5. Run: python test_ai_sql.py

from langchain_aws import ChatBedrock
import snowflake.connector

try:
    from snowflake_config import account, user, password, warehouse, database, schema
except ImportError:
    print("=" * 60)
    print("  Missing Snowflake configuration!")
    print("=" * 60)
    print()
    print("  Create snowflake_config.py from the template:")
    print("    cp snowflake_config.template.py snowflake_config.py")
    print()
    print("  Then edit snowflake_config.py with your credentials.")
    print()
    print("  (snowflake_config.py is in .gitignore - safe locally)")
    print("=" * 60)
    exit(1)

# Schema description - teaches the AI what tables exist in SNOWFLAKE_SAMPLE_DATA
# This is Snowflake's built-in sample database with realistic data
SCHEMA = """
Schema: TPCH_SF1 (this is where the tables are located)

Table: CUSTOMER
- C_CUSTKEY: customer ID (integer)
- C_NAME: customer name (text)
- C_ADDRESS: customer address (text)
- C_NATIONKEY: nation ID (integer)
- C_PHONE: phone number (text)
- C_ACCTBAL: account balance (number)
- C_MKTSEGMENT: market segment like 'BUILDING', 'AUTOMOBILE', etc. (text)

Table: ORDERS
- O_ORDERKEY: order ID (integer)
- O_CUSTKEY: customer ID who placed order (integer)
- O_ORDERSTATUS: status like 'F' (fulfilled), 'O' (open), 'P' (pending) (text)
- O_TOTALPRICE: total order amount in dollars (number)
- O_ORDERDATE: order date (date)
- O_ORDERPRIORITY: priority like '1-URGENT', '3-MEDIUM', etc. (text)

Table: NATION
- N_NATIONKEY: nation ID (integer)
- N_NAME: nation name like 'UNITED STATES', 'CANADA', etc. (text)
- N_REGIONKEY: region ID (integer)
"""

def ask_ai(question):
    """Send question to Claude via Bedrock, get SQL back"""
    print(f"🤖 Asking AI: {question}")
    
    # Create the AI client (uses your AWS credentials automatically)
    # Using Amazon Nova Pro (works without Anthropic use case approval)
    llm = ChatBedrock(
        model_id="us.amazon.nova-pro-v1:0",
        region_name="us-east-1"
    )
    
    # Build the prompt for Nova model
    prompt = f"""You are a SQL expert. Here is the database schema:

{SCHEMA}

Write a SQL query to answer this question: {question}

Requirements:
- Return ONLY the SQL query, no explanation, no markdown
- Use Snowflake SQL syntax
- Use schema: TPCH_SF1
- Use fully qualified table names: TPCH_SF1.CUSTOMER, TPCH_SF1.ORDERS, etc.
- Do not include any text before or after the SQL
"""
    
    # Send to Nova
    response = llm.invoke(prompt)
    
    # Extract SQL from response
    sql = response.content
    
    # Clean up (remove markdown formatting if present)
    sql = sql.replace("```sql", "").replace("```", "").strip()
    
    return sql

def run_sql(sql):
    """Execute SQL and return results"""
    print(f"🔍 Running SQL: {sql}")
    
    # Connect to Snowflake
    conn = snowflake.connector.connect(
        account=account,
        user=user,
        password=password,
        warehouse=warehouse,
        database=database,
        schema=schema
    )
    
    # Use TPCH_SF1 schema (where the sample data tables live)
    cursor = conn.cursor()
    cursor.execute("USE SCHEMA TPCH_SF1")
    
    # Run the actual query
    cursor.execute(sql)
    results = cursor.fetchall()
    
    # Get column names
    columns = [desc[0] for desc in cursor.description] if cursor.description else []
    
    # Clean up
    cursor.close()
    conn.close()
    
    return columns, results

def main():
    # Test question - relevant to TPC-H sample data
    question = "What is the total amount of all orders?"
    # Other test questions you can try:
    # question = "How many customers are there in the BUILDING market segment?"
    # question = "What is the average account balance of all customers?"
    # question = "List all orders with URGENT priority"
    
    print("=" * 60)
    print("AI SQL ASSISTANT - POC TEST")
    print("=" * 60)
    print(f"\n📝 Question: {question}")
    print("-" * 60)
    
    try:
        # Step 1: Ask AI to write SQL
        sql = ask_ai(question)
        print(f"\n📋 Generated SQL:\n{sql}")
        print("-" * 60)
        
        # Step 2: Run SQL on Snowflake
        columns, results = run_sql(sql)
        
        # Step 3: Display results
        print(f"\n📊 Results:")
        if columns:
            print(f"Columns: {', '.join(columns)}")
        for row in results:
            print(f"  {row}")
        
        print("\n" + "=" * 60)
        print("✅ SUCCESS! AI wrote SQL and we got an answer.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nTroubleshooting:")
        print("1. Check snowflake_config.py has correct credentials")
        print("2. Run 'aws configure' to set up AWS credentials")
        print("3. Make sure demo_users table exists (run setup_demo_data.sql)")
        print("4. Check that Claude model is available in your AWS region")

if __name__ == "__main__":
    main()
