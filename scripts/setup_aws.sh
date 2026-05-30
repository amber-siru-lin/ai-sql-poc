#!/bin/bash
# AWS Setup Helper for the AI SQL POC
#
# Most company accounts use AWS SSO (keys start with ASIA).
# Personal AWS accounts often use long-lived keys (start with AKIA).
#
# Run from repo root:  bash scripts/setup_aws.sh

set -euo pipefail

echo "============================================"
echo "AWS CREDENTIALS SETUP HELPER"
echo "============================================"
echo ""
echo "This POC needs AWS Bedrock in us-east-1."
echo ""
echo "Which setup matches your situation?"
echo ""
echo "  1) Company AWS with SSO  (recommended — keys often start with ASIA)"
echo "  2) Personal AWS account  (long-lived keys start with AKIA)"
echo "  3) Temporary keys CSV      (ASIA + secret + session token — all 3 values)"
echo "  4) Test current setup      (run aws sts get-caller-identity)"
echo "  5) Exit"
echo ""
read -p "Choose 1-5: " choice

case "$choice" in
  1)
    echo ""
    echo "--- AWS SSO (company account) ---"
    echo ""
    echo "SSO is the normal path for work accounts."
    echo "You log in through the browser; AWS CLI stores temporary credentials."
    echo ""
    echo "First time only — create an SSO profile:"
    echo "  aws configure sso"
    echo ""
    echo "You will need from IT:"
    echo "  - SSO start URL (e.g. https://your-company.awsapps.com/start)"
    echo "  - SSO region (often us-east-1)"
    echo "  - AWS account ID and role name"
    echo ""
    read -p "Have you already run 'aws configure sso'? (yes/no): " sso_done

    if [[ "$sso_done" != "yes" && "$sso_done" != "YES" ]]; then
      echo ""
      echo "Run this now in your terminal (interactive wizard):"
      echo "  aws configure sso"
      echo ""
      echo "When done, run this script again and choose option 1."
      exit 0
    fi

    echo ""
    echo "Profiles on this machine:"
    aws configure list-profiles 2>/dev/null | sed 's/^/  - /' || echo "  (none)"
    echo ""
    echo "Profile name = what YOU typed during 'aws configure sso'"
    echo "  (e.g. company, work, cta — NOT your email username)"
    echo ""
    read -p "SSO profile name: " profile

    if [[ -z "$profile" ]]; then
      echo "❌ Profile name required."
      exit 1
    fi

    if ! aws configure list-profiles 2>/dev/null | grep -qx "$profile"; then
      echo ""
      echo "❌ Profile '$profile' not found in ~/.aws/config"
      echo ""
      echo "Run the SSO wizard first (creates the profile):"
      echo "  aws configure sso"
      echo ""
      echo "At the end it asks 'CLI profile name' — remember that name and use it here."
      exit 1
    fi

    echo ""
    echo "Logging in (browser will open)..."
    aws sso login --profile "$profile"

    echo ""
    echo "Add this to your shell profile (~/.zshrc) so every terminal uses SSO:"
    echo "  export AWS_PROFILE=$profile"
    echo ""
    read -p "Set AWS_PROFILE=$profile for this session now? (yes/no): " set_profile
    if [[ "$set_profile" == "yes" || "$set_profile" == "YES" ]]; then
      export AWS_PROFILE="$profile"
      echo "AWS_PROFILE=$profile"
    fi
    ;;

  2)
    echo ""
    echo "--- Personal AWS (long-lived AKIA keys) ---"
    echo ""
    read -p "AWS Access Key ID (starts with AKIA): " access_key
    read -p "AWS Secret Access Key: " secret_key
    read -p "AWS Region [us-east-1]: " region
    region=${region:-us-east-1}

    if [[ ! "$region" =~ ^[a-z]{2}-[a-z]+-[0-9]+$ ]]; then
      echo "❌ '$region' is not a valid region. Use something like us-east-1."
      exit 1
    fi

    mkdir -p ~/.aws
    cat > ~/.aws/credentials << EOF
[default]
aws_access_key_id = $access_key
aws_secret_access_key = $secret_key
EOF
    cat > ~/.aws/config << EOF
[default]
region = $region
output = json
EOF
    chmod 600 ~/.aws/credentials ~/.aws/config
    echo "✅ Wrote ~/.aws/credentials and ~/.aws/config"
    ;;

  3)
    echo ""
    echo "--- Temporary credentials (ASIA + session token) ---"
    echo ""
    echo "If IT gave you 3 values, enter each in the RIGHT box:"
    echo "  Access Key ID     → starts with ASIA"
    echo "  Secret Access Key → short-ish random string"
    echo "  Session Token     → VERY long string (starts with IQoJ...)"
    echo "  Region            → us-east-1  (NOT the session token!)"
    echo ""
    read -p "AWS Access Key ID (ASIA...): " access_key
    read -p "AWS Secret Access Key: " secret_key
    read -p "AWS Session Token (long IQoJ... string): " session_token
    read -p "AWS Region [us-east-1]: " region
    region=${region:-us-east-1}

    if [[ "$access_key" != ASIA* ]]; then
      echo "⚠️  Expected access key to start with ASIA for temporary creds."
    fi
    if [[ ! "$region" =~ ^[a-z]{2}-[a-z]+-[0-9]+$ ]]; then
      echo "❌ Region looks wrong: '$region'"
      echo "   Region must be like us-east-1 — do NOT paste the session token here."
      exit 1
    fi
    if [[ -z "$session_token" ]]; then
      echo "❌ Temporary ASIA keys require a session token."
      exit 1
    fi

    mkdir -p ~/.aws
    cat > ~/.aws/credentials << EOF
[default]
aws_access_key_id = $access_key
aws_secret_access_key = $secret_key
aws_session_token = $session_token
EOF
    cat > ~/.aws/config << EOF
[default]
region = $region
output = json
EOF
    chmod 600 ~/.aws/credentials ~/.aws/config
    echo "✅ Wrote temporary credentials (they expire — use SSO when possible)"
    ;;

  4)
    echo ""
    echo "--- Testing current AWS setup ---"
    ;;

  5)
    exit 0
    ;;

  *)
    echo "Invalid choice."
    exit 1
    ;;
esac

echo ""
echo "Testing connection..."
if aws sts get-caller-identity; then
  echo ""
  echo "✅ AWS connection successful!"
  echo ""
  echo "Next: test Bedrock"
  echo "  python scripts/diagnose_bedrock.py"
else
  echo ""
  echo "❌ AWS connection failed."
  echo ""
  echo "Common fixes:"
  echo "  • Company SSO:  aws sso login --profile YOUR_PROFILE"
  echo "                  export AWS_PROFILE=YOUR_PROFILE"
  echo "  • Expired ASIA keys: log in again (SSO) or get fresh temporary creds"
  echo "  • Wrong region in ~/.aws/config: must be us-east-1, not a session token"
  echo ""
  echo "Key prefixes (both can be valid):"
  echo "  AKIA = long-lived personal IAM key"
  echo "  ASIA = temporary SSO/role key (needs aws_session_token)"
fi
