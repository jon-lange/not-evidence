#!/usr/bin/env bash
# Advisory scan. Prints findings for human review and ALWAYS exits 0.
#
# Separate from scan-tree.sh on purpose. Numbers and ambiguous product words
# need eyes, not a gate: a specimen recording its own measurements is the point
# of this repo, and a rule that blocks those teaches people to bypass the hook.
set -uo pipefail

CONFIG="${RE_REVIEW:-$HOME/.config/re-review.toml}"
[ -f "$CONFIG" ] || { echo "advisory config not found at ${CONFIG} — skipping"; exit 0; }

echo "Advisory review (not a gate):"
gitleaks dir . --config "$CONFIG" --redact --no-banner --exit-code 0 -v 2>&1 \
  | grep -vE "^\s*$" || true
exit 0
