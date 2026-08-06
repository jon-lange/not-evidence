#!/usr/bin/env bash
# Assert this repo commits under the intended personal identity.
#
# Deliberately an ALLOW-list. A deny-list of employer domains would mean
# committing those domain names into a public repository — the exact class of
# leak this repo guards against. Asserting the expected address is also
# stronger: it catches every wrong identity, not two anticipated ones.
set -euo pipefail

# Anchor on the repository root. Run outside a repository, `git config
# user.email` silently answers from global config — so the check would pass
# while asserting nothing about this repository. A guard that reports success
# without having looked is the thing this repository is named for.
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "BLOCKED - not inside a git repository, so there is no identity to assert."
  exit 1
}
cd "$ROOT"

EXPECTED_EMAIL="langej117@gmail.com"

actual="$(git config user.email || true)"
if [ "$actual" != "$EXPECTED_EMAIL" ]; then
  echo "BLOCKED - git user.email is '${actual:-<unset>}', expected '${EXPECTED_EMAIL}'"
  echo "Fix with:  git config --local user.email ${EXPECTED_EMAIL}"
  exit 1
fi
