#!/usr/bin/env bash
# Full working-tree sweep, run at push time.
# pre-commit only ever sees staged content, so anything that landed before the
# hooks existed is invisible to it. This is the net for that.
set -euo pipefail

CONFIG="${RE_DENYLIST:-$HOME/.config/re-denylist.toml}"
if [ ! -f "$CONFIG" ]; then
  echo "BLOCKED - forbidden-token config not found at ${CONFIG}"
  exit 1
fi

exec gitleaks dir . --redact --no-banner --config "$CONFIG"
