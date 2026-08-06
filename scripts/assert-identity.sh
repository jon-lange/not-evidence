#!/usr/bin/env bash
# Assert this repo commits under the intended personal identity.
#
# Deliberately an ALLOW-list. A deny-list of employer domains would mean
# committing those domain names into a public repository — the exact class of
# leak this repo guards against. Asserting the expected address is also
# stronger: it catches every wrong identity, not two anticipated ones.
set -euo pipefail

EXPECTED_EMAIL="langej117@gmail.com"

actual="$(git config user.email || true)"
if [ "$actual" != "$EXPECTED_EMAIL" ]; then
  echo "BLOCKED - git user.email is '${actual:-<unset>}', expected '${EXPECTED_EMAIL}'"
  echo "Fix with:  git config --local user.email ${EXPECTED_EMAIL}"
  exit 1
fi
