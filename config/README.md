# Config

| File | Committed? | Purpose |
|------|------------|---------|
| `snowflake_config.example.py` | Yes | Template — copy and rename |
| `snowflake_config.py` | **No** (gitignored) | Your real Snowflake credentials |

```bash
cp config/snowflake_config.example.py config/snowflake_config.py
# Edit snowflake_config.py with your credentials
```

AWS credentials use the standard AWS CLI setup (`aws configure sso` + `aws sso login`), not this folder.

**Brainforge (company account):** profile `Brainfore-Team-Set-654654461736`, region `us-east-1`, access portal — not IAM user sign-in. Full steps: [docs/PHASE3-AMPLIFY-GETTING-STARTED.md](../docs/PHASE3-AMPLIFY-GETTING-STARTED.md).
