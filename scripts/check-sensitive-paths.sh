#!/usr/bin/env bash
# Block committing secrets, credentials, and Wren/Snowflake profile files.
# Used by pre-commit (local) and .github/workflows/secret-scan.yml (CI).
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  check-sensitive-paths.sh --staged
  check-sensitive-paths.sh --ci <base-sha> <head-sha>
  check-sensitive-paths.sh --from-file <path-list-file>
EOF
}

is_allowed_example() {
  case "$1" in
    */snowflake_config.example.py | */.env.example) return 0 ;;
    *) return 1 ;;
  esac
}

is_sensitive_path() {
  local file="$1"

  if is_allowed_example "$file"; then
    return 1
  fi

  case "$file" in
    snowflake_config.py | */snowflake_config.py | \
    profiles.yml | */profiles.yml | \
    profiles.local.yml | */profiles.local.yml | \
    .env | */.env | \
    .aws/credentials | */.aws/credentials | \
    credentials.json | */credentials.json | \
    .wren/profiles.yml | */.wren/profiles.yml | \
    *.pem | \
    *.key)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

check_paths() {
  local failed=0

  while IFS= read -r file || [ -n "${file:-}" ]; do
    [ -z "$file" ] && continue
    if is_sensitive_path "$file"; then
      echo "Sensitive file must not be committed: $file" >&2
      failed=1
    fi
  done

  return "$failed"
}

mode="${1:-}"
case "$mode" in
  --staged)
    git diff --cached --name-only --diff-filter=ACMR | check_paths
    ;;
  --ci)
    base="${2:?base sha required}"
    head="${3:?head sha required}"
    git diff --name-only --diff-filter=ACMR "$base" "$head" | check_paths
    ;;
  --from-file)
    list_file="${2:?path list file required}"
    check_paths <"$list_file"
    ;;
  -h | --help)
    usage
    exit 0
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
