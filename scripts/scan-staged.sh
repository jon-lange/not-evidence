#!/usr/bin/env bash
# Scan staged content against the private forbidden-token list.
# The list lives outside every git tree; publishing it would be worse than the
# leak it prevents. Missing config is a hard failure, never a skip.
set -euo pipefail

CONFIG="${RE_DENYLIST:-$HOME/.config/re-denylist.toml}"
if [ ! -f "$CONFIG" ]; then
  echo "BLOCKED - forbidden-token config not found at ${CONFIG}"
  echo "This scan is not optional. Restore the config before committing."
  exit 1
fi

exec gitleaks git --pre-commit --staged --redact --no-banner --config "$CONFIG"
