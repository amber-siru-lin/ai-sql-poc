"""Phase 1 baseline test: one question end-to-end."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.check_setup import check_all
from src.nl2sql import ask_ai, run_sql

check_all()


def main() -> None:
    question = "What is the total amount of all orders?"

    print("=" * 60)
    print("AI SQL ASSISTANT - POC TEST (Phase 1 baseline)")
    print("=" * 60)
    print(f"\n📝 Question: {question}")
    print("-" * 60)

    try:
        sql = ask_ai(question)
        print(f"\n📋 Generated SQL:\n{sql}")
        print("-" * 60)

        columns, results = run_sql(sql)
        print("\n📊 Results:")
        if columns:
            print(f"Columns: {', '.join(columns)}")
        for row in results:
            print(f"  {row}")

        print("\n" + "=" * 60)
        print("✅ SUCCESS! AI wrote SQL and we got an answer.")
        print("=" * 60)
    except Exception as exc:
        print(f"\n❌ ERROR: {exc}")
        print("\nTroubleshooting:")
        print("1. Copy config/snowflake_config.example.py → config/snowflake_config.py")
        print("2. Run: aws sso login  (or aws configure)")
        print("3. Run: python scripts/diagnose_bedrock.py")


if __name__ == "__main__":
    main()
