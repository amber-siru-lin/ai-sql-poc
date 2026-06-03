# shellcheck shell=bash
# Helpers to read/update KEY=value lines in .env-style files.

env_get() {
  local file="$1" key="$2"
  [[ -f "$file" ]] || return 1
  grep -E "^${key}=" "$file" 2>/dev/null | tail -1 | cut -d= -f2- | sed 's/^["'\'' ]*//; s/["'\'' ]*$//'
}

env_set() {
  local file="$1" key="$2" value="$3"
  touch "$file"
  if grep -qE "^${key}=" "$file" 2>/dev/null; then
    local tmp
    tmp="$(mktemp)"
    awk -v k="$key" -v v="$value" '
      $0 ~ "^" k "=" { print k "=" v; next }
      { print }
    ' "$file" >"$tmp"
    mv "$tmp" "$file"
  else
    echo "${key}=${value}" >>"$file"
  fi
}

env_uncomment_or_set() {
  local file="$1" key="$2" value="$3"
  touch "$file"
  if grep -qE "^#?[[:space:]]*${key}=" "$file" 2>/dev/null; then
    local tmp
    tmp="$(mktemp)"
    awk -v k="$key" -v v="$value" '
      $0 ~ "^#?[[:space:]]*" k "=" { print k "=" v; next }
      { print }
    ' "$file" >"$tmp"
    mv "$tmp" "$file"
  else
    echo "${key}=${value}" >>"$file"
  fi
}
