#!/usr/bin/env bash
# Full working-tree sweep, run at push time.
# pre-commit only ever sees staged content, so anything that landed before the
# hooks existed is invisible to it. This is the net for that.
set -euo pipefail

# Anchor on the repository root, never the caller's cwd. `gitleaks dir .` scans
# whatever directory it is run from: measured here, that is 2.02 MB from the
# root and 42.52 KB from specimens/11-mutation-check — and both print the same
# clean result. Same failure as a shallow CI checkout, which leak-check.yml
# already guards with fetch-depth: 0. A scan that looked at almost nothing is
# this repository's own eleventh pattern, inside its own guard.
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "BLOCKED - not inside a git repository, so there is no tree to scan."
  exit 1
}
cd "$ROOT"

CONFIG="${RE_DENYLIST:-$HOME/.config/re-denylist.toml}"
if [ ! -f "$CONFIG" ]; then
  echo "BLOCKED - forbidden-token config not found at ${CONFIG}"
  exit 1
fi

exec gitleaks dir . --redact --no-banner --config "$CONFIG"
