#!/usr/bin/env bash
# Idempotent local bootstrap for api/ + ui/. Run from repo root: ./scripts/setup.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PASS=0
FAIL=0
WARN=0

ok() { echo "  OK  $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL $1"; FAIL=$((FAIL + 1)); }
warn() { echo "  WARN $1"; WARN=$((WARN + 1)); }

echo "=== AI SQL POC setup ==="
echo

# --- Prerequisites ---
echo "Prerequisites"
if command -v node >/dev/null 2>&1 && [[ "$(node -p 'process.versions.node.split(".")[0]')" -ge 18 ]]; then
  ok "Node $(node -v)"
else
  fail "Node.js >= 18 required"
fi

if command -v npm >/dev/null 2>&1; then
  ok "npm $(npm -v)"
else
  fail "npm required"
fi

if [[ -x "$ROOT/scripts/py" ]] || command -v python3 >/dev/null 2>&1; then
  ok "Python ($( "$ROOT/scripts/py" --version 2>/dev/null || python3 --version ))"
else
  fail "Python 3 required (use scripts/py or python3)"
fi

if command -v aws >/dev/null 2>&1; then
  ok "AWS CLI $(aws --version 2>&1 | head -1)"
else
  warn "AWS CLI not found — install for Bedrock"
fi

if command -v docker >/dev/null 2>&1; then
  ok "Docker available (optional Postgres)"
else
  warn "Docker not found — skip Postgres checkpoints or install Docker Desktop"
fi

echo
echo "Config files"
if [[ -f config/snowflake_config.py ]]; then
  ok "config/snowflake_config.py"
else
  cp config/snowflake_config.example.py config/snowflake_config.py
  warn "Created config/snowflake_config.py — edit with client Snowflake credentials"
fi

if [[ -f .env ]]; then
  ok ".env"
else
  cp .env.example .env
  warn "Created .env — set AWS_PROFILE, BEDROCK_MODEL_ID, AUDIT_S3_BUCKET"
fi

if [[ -f ui/.env.local ]]; then
  ok "ui/.env.local"
else
  if [[ -f ui/.env.example ]]; then
    cp ui/.env.example ui/.env.local
    warn "Created ui/.env.local"
  fi
fi

echo
echo "Installing dependencies"
"$ROOT/scripts/py" -m pip install -r requirements.txt -q
ok "Python requirements"

(cd ui && npm ci --silent)
ok "ui/ npm ci"

echo
echo "Optional checks"
if [[ -n "${AWS_PROFILE:-}" ]] || aws sts get-caller-identity >/dev/null 2>&1; then
  if "$ROOT/scripts/py" "$ROOT/scripts/diagnose_bedrock.py" 2>&1 | grep -q "SUCCESS"; then
    ok "Bedrock model reachable"
  else
    warn "Bedrock check failed — run: aws sso login --profile \$AWS_PROFILE"
  fi
else
  warn "AWS credentials not active — export AWS_PROFILE and aws sso login"
fi

if [[ -f config/snowflake_config.py ]]; then
  if "$ROOT/scripts/py" "$ROOT/scripts/verify_tpch_setup.py" >/dev/null 2>&1; then
    ok "Snowflake connectivity"
  else
    warn "Snowflake check failed — edit config/snowflake_config.py"
  fi
fi

echo
echo "=== Summary: ${PASS} passed, ${WARN} warnings, ${FAIL} failed ==="
if [[ "$FAIL" -gt 0 ]]; then
  echo "Fix failures above, then re-run ./scripts/setup.sh"
  exit 1
fi
echo
echo "Next: ./scripts/onboard.sh   (guided setup)  or  ./scripts/dev.sh   (start app)"
echo "Docs: ONBOARDING.md · SETUP.md"
