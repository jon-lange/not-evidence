#!/usr/bin/env bash
# Prove the repository does not depend on where it lives.
#
# The catalogue was renamed once, and the working directory moved with it. That
# is the moment a hard-coded path fails, and the failure is quiet: a script that
# resolves the wrong tree does not crash, it reports clean. So this does not
# assert portability, it measures it — the tracked tree is exported to a fresh
# location and the checks are run there.
#
# The destination deliberately contains a space and a different depth. Both are
# ordinary on a real machine and both break naive quoting.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "BLOCKED - not inside a git repository, so there is nothing to export."
  exit 1
}
cd "$ROOT"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
DEST="$TMP/a deeper/path with spaces/not-evidence"
mkdir -p "$DEST"

# Tracked content only. Untracked venvs are excluded on purpose: a venv holds
# absolute shebangs by construction and recreating it is a documented step, so
# including one would test Python's packaging, not this repository's code.
git archive HEAD | tar -x -C "$DEST"

echo "exported tracked tree to:"
echo "  $DEST"
echo

cd "$DEST"
# The export is not a git repository, so `git init` is needed by anything that
# resolves the root through git. That is exactly the path resilience under test.
git init --quiet .
git add -A && git -c user.email=langej117@gmail.com \
  -c user.name=portability commit --quiet -m "portability probe" --no-verify

fail=0

echo "── metadata consistency, from the new location ──"
python3 scripts/check-consistency.py || fail=1
echo

echo "── specimen suites, from the new location ──"
# No venvs here, so this runs on the system interpreter. Specimens whose
# dependencies are absent report SKIPPED, which the Makefile already refuses to
# read as coverage. Portability is about paths resolving, not packages existing.
make test || fail=1
echo

echo "── guard scripts, from the new location ──"
# Both directions, and with the identity set locally on the export. Reading the
# ambient global config instead would test this machine, not this repository —
# and the first run of this script did exactly that, passing the wrong address
# through to a guard that then looked broken when it was working.
git config --local user.email langej117@gmail.com
if bash scripts/assert-identity.sh >/dev/null 2>&1; then
  echo "  assert-identity PASSES on the correct identity, from the new path"
else
  echo "  assert-identity blocked a correct identity"; fail=1
fi

git config --local user.email wrong-identity@example.invalid
if bash scripts/assert-identity.sh >/dev/null 2>&1; then
  echo "  assert-identity PASSED a wrong identity — the guard is not live"; fail=1
else
  echo "  assert-identity BLOCKS a wrong identity, from the new path"
fi

# The scan is only meaningful with the private config, which is absent in CI and
# on any machine but the author's. Skip loudly rather than silently.
if [ -f "${RE_DENYLIST:-$HOME/.config/re-denylist.toml}" ]; then
  if bash scripts/scan-tree.sh >/dev/null 2>&1; then
    echo "  scan-tree resolved and scanned the exported tree"
  else
    echo "  scan-tree failed on the exported tree"; fail=1
  fi
else
  echo "  scan-tree SKIPPED — no denylist config on this machine"
fi

if [ "$fail" -ne 0 ]; then
  echo
  echo "PORTABILITY FAILED - something in this repository depends on where it lives."
  exit 1
fi

echo
echo "portable — the tree passes from a different name, depth, and a path with spaces"
