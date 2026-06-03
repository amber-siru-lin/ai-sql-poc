# Snowflake Configuration — EXAMPLE ONLY
#
# Setup:
#   1. Copy this file:  cp config/snowflake_config.example.py config/snowflake_config.py
#   2. Fill in your real values in snowflake_config.py
#   3. NEVER commit snowflake_config.py (it is in .gitignore)

# From Snowflake URL: https://app.snowflake.com/<org>/<account>/
account = "your-account-id"  # e.g. xy12345.us-east-1
user = "your_username"
password = "your_password"
warehouse = "COMPUTE_WH"
database = "YOUR_DATABASE"
schema = "YOUR_SCHEMA"

# Optional — override defaults used by the app and UI
dataset_label = "Your dataset name"  # shown in API /api/status and UI
schema_markdown_path = "schema/tpch_sf1.md"  # repo-relative markdown schema for Off mode
wren_profile_name = "default"  # active profile in ~/.wren/profiles.yml

# Optional — key-pair auth instead of password (uncomment one approach)
# private_key_path = "/path/to/rsa_key.p8"
# private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"
