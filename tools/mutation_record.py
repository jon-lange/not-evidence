#!/usr/bin/env python3
"""Mutation-check mutcheck. Standard library only.

    python3 mutation_record.py

Break one behaviour of the tool, run its suite, count the tests that notice,
restore. A mutation nothing catches means the suite passes for a reason other
than the one it names — which is the tool's own subject, so shipping it
unchecked would be the joke this repository exists to prevent.

The record this produces is in README.md.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE / "mutcheck.py"
SUITE = HERE / "test_mutcheck.py"

MUTATIONS: dict[str, tuple[str, str]] = {
    "a survivor no longer raises": (
        "    if not report.caught:",
        "    if False:",
    ),
    "every mutation reports as caught": (
        '    return MutationReport(label, False, "mutated code still passed")',
        '    return MutationReport(label, True, "mutated code still passed")',
    ),
    "a crash is reported as an assertion failure": (
        '            return MutationReport(label, True, f"crashed: {type(exc).__name__}: {exc}")',
        '            return MutationReport(label, True, f"assertion failed: {exc}")',
    ),
    "the original is never restored": (
        "        setattr(target, attr, original)",
        "        pass",
    ),
    "a missing attribute is tolerated": (
        "    original = getattr(target, attr)",
        "    original = getattr(target, attr, None)",
    ),
    "an empty assertion message renders blank": (
        "f\"assertion failed: {str(exc) or '(no message)'}\"",
        'f"assertion failed: {exc}"',
    ),
    "the label is dropped": (
        "    label = name or f\"{getattr(target, '__name__', target)}.{attr}\"",
        '    label = ""',
    ),
}


def run_suite() -> int:
    proc = subprocess.run([sys.executable, str(SUITE)], capture_output=True, text=True)
    found = re.search(r"(\d+) failure\(s\)", proc.stdout)
    return int(found.group(1)) if found else -1


def main() -> int:
    original = TOOL.read_text()
    baseline = run_suite()
    print(f"baseline: {baseline} failure(s)")
    if baseline != 0:
        print("the suite is not green — a mutation score against a red suite is meaningless")
        return 1

    print()
    print(f"  {'mutation':<46} tests broken")
    print(f"  {'-' * 46} ------------")
    survivors = []
    try:
        for name, (old, new) in MUTATIONS.items():
            if old not in original:
                print(f"  {name:<46} ANCHOR NOT FOUND")
                survivors.append(f"{name} (anchor missing)")
                continue
            TOOL.write_text(original.replace(old, new, 1))
            broken = run_suite()
            print(f"  {name:<46} {broken}")
            if broken == 0:
                survivors.append(name)
    finally:
        TOOL.write_text(original)

    print()
    if survivors:
        print("SURVIVED — no test defends these:")
        for s in survivors:
            print(f"  - {s}")
        return 1
    print(f"no mutation survived — {len(MUTATIONS)} breakages, all caught")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
