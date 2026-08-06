#!/usr/bin/env bash
# Scan staged content against the private forbidden-token list.
# The list lives outside every git tree; publishing it would be worse than the
# leak it prevents. Missing config is a hard failure, never a skip.
set -euo pipefail

# The staged scan reads the index, which git already resolves upward from any
# subdirectory, so scope is not at risk here the way it is in scan-tree.sh.
# Anchored anyway: outside a repository this would otherwise fail somewhere
# further down with a less obvious message.
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "BLOCKED - not inside a git repository, so there is no index to scan."
  exit 1
}
cd "$ROOT"

CONFIG="${RE_DENYLIST:-$HOME/.config/re-denylist.toml}"
if [ ! -f "$CONFIG" ]; then
  echo "BLOCKED - forbidden-token config not found at ${CONFIG}"
  echo "This scan is not optional. Restore the config before committing."
  exit 1
fi

exec gitleaks git --pre-commit --staged --redact --no-banner --config "$CONFIG"
