"""Interactive Phase 1 demo — ask your own questions."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.check_setup import check_all
from src.nl2sql import ask_ai, run_sql

check_all()


def show_help() -> None:
    print("\n" + "=" * 70)
    print("AVAILABLE TABLES & COLUMNS")
    print("=" * 70)
    print("""
Table: TPCH_SF1.CUSTOMER
  - C_CUSTKEY: customer ID
  - C_NAME: customer name
  - C_NATIONKEY: nation ID
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
4. What is the average order amount?
5. Show me all pending orders
6. How many customers are in the BUILDING market segment?
7. What is the total price of urgent orders?
8. Which nation has the most customers?
    """)
    print("=" * 70)
    print("Type 'help' to see this again, 'quit' to exit")
    print("=" * 70 + "\n")


def ask_single_question(question: str) -> bool:
    print(f"\n📝 Question: {question}")
    print("-" * 70)

    try:
        print("🤖 AI is thinking...")
        sql = ask_ai(question)
        print(f"📋 Generated SQL:\n{sql}")
        print("-" * 70)

        print("🔍 Running on Snowflake...")
        columns, results = run_sql(sql)

        print("\n📊 Results:")
        if columns:
            print(f"Columns: {', '.join(columns)}")

        if results:
            for row in results[:10]:
                print(f"  {row}")
            if len(results) > 10:
                print(f"  ... and {len(results) - 10} more rows")
        else:
            print("  No results found")

        print("\n✅ Success!")
        return True
    except Exception as exc:
        print(f"\n❌ Error: {exc}")
        return False


def main() -> None:
    print("=" * 70)
    print("AI SQL ASSISTANT - Interactive Demo (Phase 1)")
    print("=" * 70)
    print("\nAsk questions about the Snowflake sample data!")
    show_help()

    while True:
        try:
            question = input("❓ Your question (or 'help', 'quit'): ").strip()
            if not question:
                continue
            if question.lower() in {"quit", "exit", "q"}:
                print("\n👋 Goodbye!")
                break
            if question.lower() in {"help", "h"}:
                show_help()
                continue
            ask_single_question(question)
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break


if __name__ == "__main__":
    main()
