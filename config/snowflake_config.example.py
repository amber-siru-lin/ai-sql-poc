# Snowflake Configuration — EXAMPLE ONLY
#
# Setup:
#   1. Copy this file:  cp config/snowflake_config.example.py config/snowflake_config.py
#   2. Fill in your real values in snowflake_config.py
#   3. NEVER commit snowflake_config.py (it is in .gitignore)

# From Snowflake URL: https://app.snowflake.com/<org>/<account>/
account = "your-account-id"  # e.g. wzqidsn-ib45431
user = "your_username"
password = "your_password"
warehouse = "COMPUTE_WH"
database = "SNOWFLAKE_SAMPLE_DATA"
schema = "PUBLIC"
