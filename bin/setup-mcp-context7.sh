#!/usr/bin/env sh
set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CURSOR_DIR="$REPO_ROOT/.cursor"
OUT_FILE="$CURSOR_DIR/mcp-config.json"

# Load from .env if present (best-effort, avoids executing arbitrary code)
load_from_dotenv() {
  [ -f "$REPO_ROOT/.env" ] || return 1
  # Extract the first matching KEY=VALUE line (no quotes handling; keep it simple)
  val=$(grep -E '^[[:space:]]*CONTEXT7_API_KEY=' "$REPO_ROOT/.env" | head -n 1 | sed -E 's/^[[:space:]]*CONTEXT7_API_KEY=//')
  [ -n "$val" ] || return 1
  printf '%s' "$val"
}

get_key() {
  if [ "${CONTEXT7_API_KEY:-}" != "" ]; then
    printf '%s' "$CONTEXT7_API_KEY"
    return 0
  fi

  if key_from_env=$(load_from_dotenv 2>/dev/null); then
    printf '%s' "$key_from_env"
    return 0
  fi

  if [ "${OP_CONTEXT7_API_KEY_REF:-}" != "" ]; then
    if command -v op >/dev/null 2>&1; then
      # 1Password secret reference, e.g. op://Vault/Item/CONTEXT7_API_KEY
      op read "$OP_CONTEXT7_API_KEY_REF"
      return 0
    fi
  fi

  return 1
}

KEY="$(get_key || true)"

if [ "$KEY" = "" ]; then
  echo "ERROR: Could not find CONTEXT7_API_KEY." >&2
  echo "Set one of:" >&2
  echo "  - export CONTEXT7_API_KEY=..." >&2
  echo "  - add CONTEXT7_API_KEY=... to .env" >&2
  echo "  - export OP_CONTEXT7_API_KEY_REF=op://... and install/sign-in to 1Password CLI (op)" >&2
  exit 1
fi

mkdir -p "$CURSOR_DIR"

cat > "$OUT_FILE" <<JSON
{
  "mcpServers": {
    "context7": {
      "httpUrl": "https://mcp.context7.com/mcp",
      "headers": {
        "CONTEXT7_API_KEY": "$KEY"
      }
    }
  }
}
JSON

# Best-effort permissions hardening
chmod 600 "$OUT_FILE" 2>/dev/null || true

echo "Wrote $OUT_FILE (gitignored)."
