# Snowflake Configuration Template
#
# INSTRUCTIONS:
# 1. Copy this file: cp snowflake_config.template.py snowflake_config.py
# 2. Fill in your real Snowflake credentials
# 3. NEVER commit snowflake_config.py to Git (it's in .gitignore)

account = "your-org-your-account"  # e.g. "wzqidsn-ib45431"
user = "your_username"
password = "your_password"
warehouse = "COMPUTE_WH"
database = "SNOWFLAKE_SAMPLE_DATA"
schema = "PUBLIC"
