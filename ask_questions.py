# Interactive AI SQL Test - Ask Your Own Questions!
#
# SETUP:
#   1. cp snowflake_config.template.py snowflake_config.py
#   2. Edit snowflake_config.py with your Snowflake credentials
#   3. Run: aws configure (set up AWS credentials for Bedrock)
#   4. Run: python ask_questions.py
# Then type your questions and see the AI write SQL!

from test_ai_sql import ask_ai, run_sql

def show_help():
    """Show available tables and sample questions"""
    print("\n" + "=" * 70)
    print("AVAILABLE TABLES & COLUMNS")
    print("=" * 70)
    print("""
Table: TPCH_SF1.CUSTOMER
  - C_CUSTKEY: customer ID
  - C_NAME: customer name
  - C_ADDRESS: address
  - C_NATIONKEY: nation ID
  - C_PHONE: phone number
  - C_ACCTBAL: account balance
  - C_MKTSEGMENT: market segment (BUILDING, AUTOMOBILE, etc.)

Table: TPCH_SF1.ORDERS
  - O_ORDERKEY: order ID
  - O_CUSTKEY: customer ID (links to CUSTOMER)
  - O_ORDERSTATUS: status (F=fulfilled, O=open, P=pending)
  - O_TOTALPRICE: total order amount
  - O_ORDERDATE: order date
  - O_ORDERPRIORITY: priority (1-URGENT, 3-MEDIUM, etc.)

Table: TPCH_SF1.NATION
  - N_NATIONKEY: nation ID
  - N_NAME: nation name (UNITED STATES, CANADA, etc.)
    """)
    print("=" * 70)
    print("SAMPLE QUESTIONS YOU CAN ASK")
    print("=" * 70)
    print("""
1. How many customers are there?
2. What is the total revenue from all orders?
3. Which customer has the highest account balance?
4. How many orders were placed in 2024?
5. What is the average order amount?
6. Show me all pending orders
7. How many customers are in the BUILDING market segment?
8. What is the total price of urgent orders?
    """)
    print("=" * 70)
    print("Type 'help' to see this again, 'quit' to exit")
    print("=" * 70 + "\n")

def ask_single_question(question):
    """Ask one question and show results"""
    print(f"\n📝 Question: {question}")
    print("-" * 70)
    
    try:
        # Get SQL from AI
        print("🤖 AI is thinking...")
        sql = ask_ai(question)
        print(f"📋 Generated SQL:\n{sql}")
        print("-" * 70)
        
        # Run SQL
        print("🔍 Running on Snowflake...")
        columns, results = run_sql(sql)
        
        # Show results
        print(f"\n📊 Results:")
        if columns:
            print(f"Columns: {', '.join(columns)}")
        
        if results:
            for i, row in enumerate(results[:10]):  # Show first 10 rows
                print(f"  {row}")
            
            if len(results) > 10:
                print(f"  ... and {len(results) - 10} more rows")
        else:
            print("  No results found")
        
        print("\n✅ Success!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nPossible issues:")
        print("  - The question might be too complex for the AI")
        print("  - Try rephrasing your question")
        print("  - Or ask about a specific table/column")
        return False

def main():
    print("=" * 70)
    print("AI SQL ASSISTANT - Interactive Demo")
    print("=" * 70)
    print("\nAsk questions about the Snowflake sample data!")
    print("The AI will write SQL and run it for you.\n")
    
    show_help()
    
    while True:
        try:
            # Get user input
            question = input("❓ Your question (or 'help', 'quit'): ").strip()
            
            if not question:
                continue
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye! Thanks for testing.")
                break
            
            if question.lower() in ['help', 'h']:
                show_help()
                continue
            
            # Ask the question
            ask_single_question(question)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            print("Try asking a different question.")

if __name__ == "__main__":
    main()
