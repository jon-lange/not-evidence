"""Specimen 11 — green is not evidence.

Runs one absence-test against three variants of the same recorder, twice: once
with redaction intact, once with redaction deliberately broken.

  1   correct code, redaction intact          -> PASS, and it means something
  2   refactored code, redaction intact       -> PASS, and it means nothing
  3   correct code, redaction BROKEN          -> FAIL, which is what proves 1
  4   refactored code, redaction BROKEN       -> PASS, which is what damns 2

Cells 2 and 4 are the demonstration. The refactors are not bugs and not
leaks — the token really does stay out of the log in every row. What they
destroy is the *evidence*. A test that cannot be made to fail is not covering
the surface it is filed under, and the surface stays recorded as covered until
the day someone re-adds the field.

No network, no API key, no dependencies. This specimen is about a property of
test suites, not a property of a model, so everything it needs is local.

Usage:
    python3 probe.py

Reference implementation. Not maintained.
"""

from __future__ import annotations

import argparse
from contextlib import nullcontext
from dataclasses import dataclass

import mutation
import subject
from subject import CORRECT, VACUUM_DEAD_FIELD, VACUUM_FLAG, Variant


def redact_nothing(event: dict) -> dict:
    """The mutation: redaction reduced to a copy that masks nothing.

    Defined once, here, and imported by the test suite. Two definitions of "the
    deliberate breakage" would drift, and a mutation check is only worth as much
    as the mutation being the one you think it is.
    """
    return dict(event)


@dataclass(frozen=True)
class Row:
    cell: str
    label: str
    broken: bool
    lines: int
    leaked: bool
    passed: bool
    verdict: str


def observe(cell: str, variant: Variant, broken: bool, verdict: str) -> Row:
    """Record one matrix row: what got written, and what the assertion said."""
    swap = mutation.swapped(subject, "redact", redact_nothing) if broken else nullcontext()
    with swap:
        log = subject.capture(variant)
        try:
            subject.absence_check(variant)
            passed = True
        except AssertionError:
            passed = False
    return Row(cell, variant.label, broken, len(log.lines), subject.SECRET_VALUE in log.text(),
               passed, verdict)


ROWS = [
    ("1", CORRECT, False, "earned — cell 3 proves it"),
    ("2a", VACUUM_FLAG, False, "VACUOUS — log is empty"),
    ("2b", VACUUM_DEAD_FIELD, False, "VACUOUS — no token in the event"),
    ("3", CORRECT, True, "caught — the assertion is live"),
    ("4a", VACUUM_FLAG, True, "NOT CAUGHT"),
    ("4b", VACUUM_DEAD_FIELD, True, "NOT CAUGHT"),
]

RULE = "=" * 90
FMT = " {cell:<5}{label:<26}{redact:<9}{lines:^6}{leak:^5}{result:^6} {verdict}"


def header() -> str:
    return FMT.format(cell="cell", label="variant", redact="redact()", lines="lines",
                      leak="leak", result="test", verdict="verdict")


def render(row: Row) -> str:
    return FMT.format(
        cell=row.cell,
        label=row.label,
        redact="BROKEN" if row.broken else "intact",
        lines=str(row.lines),
        leak="YES" if row.leaked else "no",
        result="PASS" if row.passed else "FAIL",
        verdict=row.verdict,
    )


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()

    print("Specimen 11 — green is not evidence")
    print(RULE)
    print("The assertion under study, unchanged in every row below:\n")
    print("    assert SECRET_VALUE not in capture(variant).text()\n")
    print(RULE)
    print(header())
    print("-" * 90)
    for cell, variant, broken, verdict in ROWS:
        print(render(observe(cell, variant, broken, verdict)))
    print(RULE)

    # The same four states again, this time through the reusable helper — which
    # is the form you would actually commit. mutate() reports; require_live()
    # raises. Cells 4a and 4b are what it is for.
    print("\nWhat mutate() says about each variant:\n")
    for variant in (CORRECT, VACUUM_FLAG, VACUUM_DEAD_FIELD):
        report = mutation.mutate(
            subject, "redact", redact_nothing,
            lambda v=variant: subject.absence_check(v),
            name=f"redact -> no-op, against {variant.label!r}",
        )
        mark = "LIVE   " if report.caught else "VACUOUS"
        print(f"  {mark}  {report.name}")
        print(f"           {report.detail}")

    print("\n" + RULE)
    print(
        "Cells 1, 2a and 2b are the same green. Read the report, run the suite,\n"
        "look at the dashboard — there is no observable difference between an\n"
        "assertion that held a property down and one that was never reached.\n"
        "\n"
        "Cell 3 is what makes cell 1 a result. Redaction is broken, the token\n"
        "reaches the log, and the assertion goes red. That red is the evidence;\n"
        "the green in cell 1 is only a summary of it.\n"
        "\n"
        "Cells 4a and 4b are cell 3 run against the refactors, and they stay\n"
        "green. The code is broken, the guard is gone, and the suite reports\n"
        "success — because the assertion is looking at a log the broken code\n"
        "never wrote to, or for a field the event no longer carries.\n"
        "\n"
        "Note the difference between the two vacuums. 4a writes zero lines, so a\n"
        "witness assertion — 'and the log is not empty' — catches it. 4b writes a\n"
        "full, plausible line and sails straight through that witness; catching\n"
        "4b needs a different witness ('and the line contains [redacted]').\n"
        "\n"
        "That is the argument for mutation, not against it. Every vacuum has some\n"
        "positive assertion that would have caught it. What you do not have is the\n"
        "list in advance — you would be writing the witness for the refactor that\n"
        "has not happened yet. Requiring the assertion to be breakable does not\n"
        "need the list.\n"
        "\n"
        "Neither vacuum is a live leak. The token stays out of the log in every\n"
        "row of this matrix. What is gone is the evidence, and evidence is the\n"
        "thing that has to still be there the next time somebody edits redact()."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
