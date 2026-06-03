#!/usr/bin/env bash
# Guided onboarding — run from repo root:  ./scripts/onboard.sh
#
# Flags:
#   --quick     Install deps + scaffold config only (same as setup.sh)
#   --check     Run verification checks only (no install)
#   --no-run    Skip "start the app now?" prompt at the end
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# shellcheck source=scripts/lib/env_file.sh
source "$ROOT/scripts/lib/env_file.sh"

QUICK=0
CHECK_ONLY=0
NO_RUN=0
for arg in "$@"; do
  case "$arg" in
    --quick) QUICK=1 ;;
    --check) CHECK_ONLY=1 ;;
    --no-run) NO_RUN=1 ;;
    -h | --help)
      cat <<'EOF'
AI SQL POC — guided onboarding

  ./scripts/onboard.sh           Interactive walkthrough (recommended)
  ./scripts/onboard.sh --quick   Install only (non-interactive)
  ./scripts/onboard.sh --check   Verify AWS/Snowflake/API config only
  ./scripts/onboard.sh --no-run  Guide without offering to start dev servers

After setup:
  ./scripts/dev.sh               Start API (:8000) + UI (:5173)

Docs: ONBOARDING.md · SETUP.md · docs/CLIENT-CREDENTIALS.md
EOF
      exit 0
      ;;
    *)
      echo "Unknown option: $arg (try --help)"
      exit 1
      ;;
  esac
done

step() {
  echo
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Step $1 — $2"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo
}

press_enter() {
  local msg="${1:-Press Enter when ready to continue…}"
  read -r -p "$msg " _
}

snowflake_needs_edit() {
  local f="config/snowflake_config.py"
  [[ ! -f "$f" ]] && return 0
  grep -q 'your-account-id\|your_username\|your_password\|YOUR_DATABASE\|YOUR_SCHEMA' "$f" 2>/dev/null
}

run_checks() {
  local aws_ok=0 sf_ok=0 bedrock_ok=0

  echo "Running verification checks…"
  echo

  if aws sts get-caller-identity >/dev/null 2>&1; then
    echo "  ✓ AWS credentials active ($(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo ok))"
    aws_ok=1
  else
    echo "  ✗ AWS — run: aws sso login --profile \"\${AWS_PROFILE}\""
  fi

  if [[ -f config/snowflake_config.py ]] && ! snowflake_needs_edit; then
    if "$ROOT/scripts/py" "$ROOT/scripts/verify_tpch_setup.py" >/dev/null 2>&1; then
      echo "  ✓ Snowflake — schema reachable"
      sf_ok=1
    else
      echo "  ✗ Snowflake — check config/snowflake_config.py (warehouse, database, schema, password)"
    fi
  else
    echo "  ✗ Snowflake — edit config/snowflake_config.py (still has placeholder values)"
  fi

  if [[ "$aws_ok" -eq 1 ]]; then
    if "$ROOT/scripts/py" "$ROOT/scripts/diagnose_bedrock.py" 2>&1 | grep -q "SUCCESS"; then
      echo "  ✓ Bedrock — model responds"
      bedrock_ok=1
    else
      echo "  ✗ Bedrock — check BEDROCK_MODEL_ID in .env and model access in AWS"
    fi
  else
    echo "  − Bedrock — skipped (AWS not configured)"
  fi

  if curl -sf http://localhost:8000/api/status >/dev/null 2>&1; then
    echo "  ✓ API already running at http://localhost:8000"
  else
    echo "  − API not running yet (start with ./scripts/dev.sh)"
  fi

  echo
  if [[ "$aws_ok" -eq 1 && "$sf_ok" -eq 1 && "$bedrock_ok" -eq 1 ]]; then
    echo "All core checks passed. You are ready to use the app."
    return 0
  fi
  echo "Some checks failed — fix the items above and re-run:  ./scripts/onboard.sh --check"
  return 1
}

if [[ "$CHECK_ONLY" -eq 1 ]]; then
  # Load AWS_PROFILE from .env for check
  if [[ -f .env ]]; then
    profile="$(env_get .env AWS_PROFILE || true)"
    [[ -n "$profile" ]] && export AWS_PROFILE="$profile"
  fi
  run_checks
  exit $?
fi

if [[ "$QUICK" -eq 1 ]]; then
  exec "$ROOT/scripts/setup.sh"
fi

cat <<'BANNER'

  AI SQL POC — guided setup
  ─────────────────────────
  This walkthrough will:
    1. Check prerequisites and install dependencies
    2. Create config templates (if missing)
    3. Help you set AWS + Snowflake credentials
    4. Verify Bedrock and Snowflake connectivity
    5. Optionally start the app (API + UI)

  Active stack:  api/  +  ui/  (CopilotKit chat)
  Parked:        web/  (Amplify — not needed for daily dev)

BANNER
press_enter "Press Enter to start…"

# ── Step 1: Install ──────────────────────────────────────────────────────────
step 1 "Install dependencies"
echo "Running ./scripts/setup.sh (idempotent — safe to re-run)…"
echo
bash "$ROOT/scripts/setup.sh"

# ── Step 2: AWS ──────────────────────────────────────────────────────────────
step 2 "AWS credentials (Bedrock)"
echo "Bedrock needs AWS CLI credentials. Most teams use SSO."
echo
echo "  First time?  aws configure sso"
echo "  Each session: aws sso login --profile YOUR_PROFILE"
echo

current_profile="$(env_get .env AWS_PROFILE 2>/dev/null || true)"
if [[ -n "${AWS_PROFILE:-}" ]]; then
  echo "  Shell already has AWS_PROFILE=${AWS_PROFILE}"
elif [[ -n "$current_profile" ]]; then
  export AWS_PROFILE="$current_profile"
  echo "  Loaded AWS_PROFILE=${AWS_PROFILE} from .env"
fi

read -r -p "AWS SSO profile name [.env AWS_PROFILE, or enter new]: " input_profile
input_profile="${input_profile:-${AWS_PROFILE:-$current_profile}}"
if [[ -n "$input_profile" ]]; then
  env_uncomment_or_set .env AWS_PROFILE "$input_profile"
  export AWS_PROFILE="$input_profile"
  echo "  Saved AWS_PROFILE=$input_profile to .env"
fi

read -r -p "AWS region [us-east-1]: " input_region
input_region="${input_region:-us-east-1}"
env_uncomment_or_set .env AWS_REGION "$input_region"

read -r -p "Bedrock model ID [us.amazon.nova-pro-v1:0]: " input_model
input_model="${input_model:-us.amazon.nova-pro-v1:0}"
env_uncomment_or_set .env BEDROCK_MODEL_ID "$input_model"

if [[ -n "${AWS_PROFILE:-}" ]]; then
  read -r -p "Run aws sso login now? [Y/n]: " do_login
  do_login="${do_login:-Y}"
  if [[ "$do_login" =~ ^[Yy] ]]; then
    aws sso login --profile "$AWS_PROFILE" || true
  fi
fi

read -r -p "Audit S3 bucket (optional — Enter to skip): " audit_bucket
if [[ -n "$audit_bucket" ]]; then
  env_uncomment_or_set .env AUDIT_S3_BUCKET "$audit_bucket"
  env_uncomment_or_set .env AUDIT_DESTINATION "s3"
  echo "  Saved AUDIT_S3_BUCKET=$audit_bucket"
else
  echo "  Skipped audit bucket (audit log features stay disabled until set)"
fi

# ── Step 3: Snowflake ───────────────────────────────────────────────────────
step 3 "Snowflake credentials"
echo "Edit config/snowflake_config.py with your client Snowflake settings."
echo
echo "  Required fields:"
echo "    account, user, password (or key-pair)"
echo "    warehouse, database, schema"
echo
echo "  Recommended:"
echo "    dataset_label = \"Your dataset name\"   # shown in the UI"
echo "    schema_markdown_path = \"schema/….md\"    # Off-mode schema doc"
echo
echo "  File: $ROOT/config/snowflake_config.py"
echo

if snowflake_needs_edit; then
  read -r -p "Open in default editor now? [y/N]: " open_editor
  if [[ "$open_editor" =~ ^[Yy] ]]; then
    "${EDITOR:-nano}" "$ROOT/config/snowflake_config.py" || true
  fi
  press_enter "Press Enter after you have saved snowflake_config.py…"
else
  echo "  Existing config/snowflake_config.py looks filled in."
  read -r -p "Re-edit anyway? [y/N]: " reedit
  if [[ "$reedit" =~ ^[Yy] ]]; then
    "${EDITOR:-nano}" "$ROOT/config/snowflake_config.py" || true
  fi
fi

# ── Step 4: Optional extras ─────────────────────────────────────────────────
step 4 "Optional features"
echo "  Wren semantic layer:  pip install \"wrenai[snowflake,memory]\""
echo "                        scripts/py scripts/sync_wren_profile.py"
echo "                        cd wren/tpch && wren context build"
echo
echo "  Postgres checkpoints: docker compose up -d"
echo "                        uncomment DATABASE_URL in .env"
echo
read -r -p "Start local Postgres now? [y/N]: " start_pg
if [[ "$start_pg" =~ ^[Yy] ]]; then
  if command -v docker >/dev/null 2>&1; then
    docker compose up -d
    env_uncomment_or_set .env DATABASE_URL "postgresql://ai_sql:ai_sql_dev@localhost:5432/ai_sql_poc"
    echo "  Postgres started; DATABASE_URL set in .env"
  else
    echo "  Docker not found — skip or install Docker Desktop"
  fi
fi

# ── Step 5: Verify ──────────────────────────────────────────────────────────
step 5 "Verify setup"
run_checks || true

# ── Step 6: Run ─────────────────────────────────────────────────────────────
step 6 "Start the app"
echo "  API:  http://localhost:8000/api/status"
echo "  UI:   http://localhost:5173"
echo
echo "  ./scripts/dev.sh          Start both servers (Ctrl+C stops both)"
echo "  Or two terminals — see SETUP.md"
echo

if [[ "$NO_RUN" -eq 1 ]]; then
  echo "Done. Run ./scripts/dev.sh when ready."
  exit 0
fi

read -r -p "Start the app now? [Y/n]: " start_app
start_app="${start_app:-Y}"
if [[ "$start_app" =~ ^[Yy] ]]; then
  exec "$ROOT/scripts/dev.sh"
fi

echo
echo "Setup complete. When ready:  ./scripts/dev.sh"
echo "Reference:  ONBOARDING.md · docs/CLIENT-CREDENTIALS.md"
