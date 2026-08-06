"""Tests for the recorder, and tests for the mutation helper that checks them.

Run: python3 test_subject.py   (or: python3 -m pytest test_subject.py -q)

No network, no dependencies. Everything this specimen claims is local and
reproducible, because the claim is about test suites rather than about anything
a service could tell you.

Two of these tests document a failure rather than a guarantee:
test_a_vacuum_passes_the_absence_test and its dead-field twin assert that the
absence-test passes on refactors where it means nothing. They exist so that a
future change which accidentally FIXES the demonstration is caught, and so a
reader can see the fraud asserted rather than only described.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import mutation
import subject
from mutation import MutationSurvived, mutate, require_live, swapped
from probe import redact_nothing  # one definition of the breakage, shared with the matrix
from subject import CORRECT, VACUUM_DEAD_FIELD, VACUUM_FLAG


# ── redaction ────────────────────────────────────────────────────────────────

def test_redact_masks_every_secret_field():
    out = subject.redact({"auth_token": "t", "password": "p", "private_key": "k"})
    assert set(out.values()) == {subject.REDACTION}


def test_redact_leaves_ordinary_fields_alone():
    """Points the other way: a redactor that masks everything is not a redactor.

    Without this, 'mask the whole dict' passes the suite — and a telemetry
    pipeline that emits nothing but [redacted] fails silently as surely as one
    that emits secrets loudly.
    """
    out = subject.redact({"job": "nightly-reindex", "attempt": 2})
    assert out == {"job": "nightly-reindex", "attempt": 2}


def test_redact_does_not_mutate_its_input():
    """The event is shared downstream; redaction is for the log copy only."""
    event = {"auth_token": subject.SECRET_VALUE}
    subject.redact(event)
    assert event["auth_token"] == subject.SECRET_VALUE


# ── the recorder ─────────────────────────────────────────────────────────────

def test_the_correct_recorder_writes_the_event():
    """The witness. Absence of a secret means nothing without presence of a line."""
    log = subject.capture(CORRECT)
    assert len(log.lines) == 1
    assert subject.JOB_NAME in log.text()


def test_the_absence_check_passes_on_correct_code():
    subject.absence_check(CORRECT)


def test_the_absence_check_fails_when_redaction_is_broken():
    """The plain, un-helpered version of cell 3. This is what 'live' means."""
    try:
        with swapped(subject, "redact", redact_nothing):
            subject.absence_check(CORRECT)
    except AssertionError:
        return
    raise AssertionError("broken redaction did not reach the log")


# ── the two vacuums ──────────────────────────────────────────────────────────

def test_a_vacuum_passes_the_absence_test():
    """Cell 2a. Green, and worth nothing — nothing was recorded at all."""
    subject.absence_check(VACUUM_FLAG)
    assert subject.capture(VACUUM_FLAG).lines == []


def test_the_dead_field_vacuum_survives_a_witness_assertion():
    """Cell 2b, and the reason the specimen ships a second vacuum.

    A full line is written, so 'and the log is not empty' passes too. The cheap
    fix for 2a does not reach this one.
    """
    log = subject.capture(VACUUM_DEAD_FIELD)
    subject.absence_check(VACUUM_DEAD_FIELD)
    assert len(log.lines) == 1
    assert subject.JOB_NAME in log.text()
    assert "auth_token" not in log.text()


def test_neither_vacuum_actually_leaks():
    """The honest caveat, asserted. These refactors are safe and unevidenced."""
    for variant in (VACUUM_FLAG, VACUUM_DEAD_FIELD):
        assert subject.SECRET_VALUE not in subject.capture(variant).text()


# ── the mutation helper ──────────────────────────────────────────────────────

def test_mutate_reports_caught_when_the_assertion_is_live():
    report = mutate(subject, "redact", redact_nothing, lambda: subject.absence_check(CORRECT))
    assert report.caught
    assert "assertion failed" in report.detail


def test_mutate_reports_survived_against_each_vacuum():
    """Cells 4a and 4b, through the helper. caught=False is the whole finding."""
    for variant in (VACUUM_FLAG, VACUUM_DEAD_FIELD):
        report = mutate(subject, "redact", redact_nothing,
                        lambda v=variant: subject.absence_check(v))
        assert not report.caught, variant.label
        assert "still passed" in report.detail


def test_mutate_counts_a_crash_as_caught_and_says_so():
    """A crash proves the path ran. The detail line must not claim more."""

    def explodes():
        raise TypeError("boom")

    report = mutate(subject, "redact", redact_nothing, explodes)
    assert report.caught
    assert "crashed: TypeError" in report.detail


def test_swapped_restores_the_original_after_a_failure():
    """A mutation left in place would poison every test that runs after it.

    Asserted against a private sentinel rather than against subject.redact. An
    earlier version read the original off the live module, and a broken restore
    elsewhere in the suite meant this test compared a poisoned value to itself
    and passed — the same vacuity the specimen is about, found by running the
    mutation check on the mutation checker.
    """
    holder = SimpleNamespace(value="original")
    try:
        with swapped(holder, "value", "mutated"):
            raise AssertionError("the test under mutation failed, as intended")
    except AssertionError:
        pass
    assert holder.value == "original"


def test_require_live_raises_when_the_mutation_survives():
    try:
        require_live(subject, "redact", redact_nothing,
                     lambda: subject.absence_check(VACUUM_FLAG))
    except MutationSurvived as exc:
        assert "survived" in str(exc)
        return
    raise AssertionError("require_live accepted a vacuous assertion")


def test_mutation_survived_is_an_assertion_error():
    """So an unproven assertion is reported as a test failure, not as infra noise."""
    assert issubclass(MutationSurvived, AssertionError)


def test_require_live_returns_the_report_when_caught():
    report = require_live(subject, "redact", redact_nothing,
                          lambda: subject.absence_check(CORRECT), name="named-check")
    assert report.caught
    assert report.name == "named-check"


def test_default_mutation_name_identifies_the_target():
    report = mutate(subject, "redact", redact_nothing, lambda: subject.absence_check(CORRECT))
    assert report.name == "subject.redact"


# ── the assertion this suite is actually here to defend ──────────────────────

def test_the_absence_check_is_mutation_checked():
    """The reusable artefact, in the position it is meant to occupy.

    Every other test in this file asserts something about the subject. This one
    asserts that the security test above is capable of failing — which is the
    only claim that distinguishes cell 1 from cell 2, and it is a claim no
    amount of additional green can supply.
    """
    require_live(subject, "redact", redact_nothing,
                 lambda: subject.absence_check(CORRECT),
                 name="redaction is a no-op")


# ── entry point ──────────────────────────────────────────────────────────────

def test_probe_runs_and_prints_the_matrix():
    proc = subprocess.run(
        [sys.executable, "probe.py"],
        cwd=Path(__file__).parent,
        env={"PATH": "/usr/bin:/bin"},  # no key, no network, nothing to configure
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "Traceback" not in proc.stderr
    assert "NOT CAUGHT" in proc.stdout
    assert "VACUOUS" in proc.stdout


def test_module_imports_leave_no_mutation_in_place():
    """Cheap guard: importing this file must not have swapped anything out."""
    assert subject.redact.__module__ == "subject"
    assert mutation.mutate.__module__ == "mutation"


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS  {name}")
            except AssertionError as exc:
                failures += 1
                print(f"  FAIL  {name}: {exc}")
            except Exception as exc:  # noqa: BLE001
                # A crash is a failure, not a reason to stop counting. The
                # mutation checks in the README are produced by breaking this
                # module on purpose, and a runner that aborts on the first
                # non-assertion exception would under-report every one of them.
                failures += 1
                print(f"  ERROR {name}: {type(exc).__name__}: {exc}")
    print(f"\n{failures} failure(s)")
    raise SystemExit(1 if failures else 0)
