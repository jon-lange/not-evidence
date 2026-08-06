"""Tests for mutcheck. Standard library only.

Run: python3 test_mutcheck.py   (or: python3 -m pytest -q)

A tool whose subject is "prove the assertion would have failed" has no business
shipping tests nobody proved. So this file is mutation-checked by
`mutation_record.py` beside it, and the record is in README.md.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import mutcheck  # noqa: E402
from mutcheck import MutationSurvived, mutate, require_live, swapped  # noqa: E402


class Subject:
    """Minimal stand-in for a module: something with a swappable attribute."""

    __name__ = "Subject"

    def __init__(self) -> None:
        self.seen: list[str] = []

    def redact(self, text: str) -> str:
        return text.replace("SECRET", "***")

    def emit(self, text: str) -> None:
        self.seen.append(self.redact(text))


def live_test(s: Subject) -> object:
    def check() -> None:
        s.seen.clear()
        s.emit("password=SECRET")
        assert "SECRET" not in "".join(s.seen)
    return check


# ------------------------------------------------------------- the core claim


def test_a_live_assertion_catches_its_mutation():
    s = Subject()
    report = mutate(s, "redact", lambda t: t, live_test(s))
    assert report.caught
    assert "assertion failed" in report.detail


def test_a_vacuous_assertion_survives_its_mutation():
    """The finding the tool exists for: broken code, green test."""
    s = Subject()
    s.emit = lambda text: None  # nothing is ever written, so nothing can leak
    report = mutate(s, "redact", lambda t: t, live_test(s))
    assert not report.caught
    assert "still passed" in report.detail


def test_require_live_raises_on_a_survivor():
    s = Subject()
    s.emit = lambda text: None
    try:
        require_live(s, "redact", lambda t: t, live_test(s))
    except MutationSurvived as exc:
        assert "not evidence" in str(exc)
    else:
        raise AssertionError("a surviving mutation did not raise")


def test_require_live_returns_the_report_when_the_mutation_is_caught():
    s = Subject()
    assert require_live(s, "redact", lambda t: t, live_test(s)).caught


# ------------------------------------------------------------- the edge cases


def test_a_crash_counts_as_caught_but_is_reported_distinctly():
    """A crash proves the mutated code ran, which rules out vacuity. It does not
    prove the assertion was watching, so the two must not read the same."""
    s = Subject()

    def boom() -> None:
        raise RuntimeError("kaboom")

    report = mutate(s, "redact", lambda t: t, boom)
    assert report.caught
    assert "crashed" in report.detail and "RuntimeError" in report.detail
    assert "assertion failed" not in report.detail


# Restoration is asserted by behaviour, not identity. `s.redact` is a bound
# method and every attribute access builds a new object, so an `is` comparison
# fails against a correctly restored attribute — a test that would report a
# working restore as broken, which is this repository's subject in miniature.


def test_the_original_is_restored_after_a_failing_test():
    """A mutation left in place after a failure poisons every later test — the
    failure mode is a suite where the first check makes the rest meaningless."""
    s = Subject()
    mutate(s, "redact", lambda t: t, live_test(s))
    assert s.redact("password=SECRET") == "password=***"


def test_the_original_is_restored_after_a_crashing_test():
    s = Subject()

    def boom() -> None:
        raise RuntimeError("kaboom")

    mutate(s, "redact", lambda t: t, boom)
    assert s.redact("password=SECRET") == "password=***"


def test_swapped_restores_even_when_the_body_raises():
    s = Subject()
    try:
        with swapped(s, "redact", lambda t: t):
            assert s.redact("password=SECRET") == "password=SECRET"
            raise ValueError("inner")
    except ValueError:
        pass
    assert s.redact("password=SECRET") == "password=***"


def test_a_bare_assertion_with_no_message_still_reports_readably():
    """The assertions this tool is aimed at are usually bare `assert x not in y`,
    which carry no message. An empty detail line would be useless."""
    s = Subject()
    report = mutate(s, "redact", lambda t: t, live_test(s))
    assert "(no message)" in report.detail


def test_the_label_defaults_to_something_identifiable():
    s = Subject()
    assert mutate(s, "redact", lambda t: t, live_test(s)).name == "Subject.redact"
    named = mutate(s, "redact", lambda t: t, live_test(s), name="custom")
    assert named.name == "custom"


def test_a_missing_attribute_fails_loudly_rather_than_silently_passing():
    """Swapping an attribute that does not exist must not read as a clean run."""
    s = Subject()
    try:
        mutate(s, "no_such_attribute", lambda t: t, live_test(s))
    except AttributeError:
        pass
    else:
        raise AssertionError("mutating a nonexistent attribute did not raise")


# ----------------------------------------------------------------- the demo


def test_the_demo_runs_and_reproduces_the_specimen_result():
    """The demo is the sixty-second path, so it has to actually work — and its
    matrix must still match specimen 11's recorded result: one live assertion,
    two vacuums."""
    proc = subprocess.run(
        [sys.executable, str(HERE / "mutcheck.py"), "--demo"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.count("NOT CAUGHT") == 2
    assert proc.stdout.count("CAUGHT") == 3  # 'NOT CAUGHT' contains 'CAUGHT'


def test_running_with_no_arguments_explains_itself():
    proc = subprocess.run(
        [sys.executable, str(HERE / "mutcheck.py")], capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "--demo" in proc.stdout


# -------------------------------------------------------------- anti-drift


def test_it_agrees_with_the_specimen_it_was_extracted_from():
    """Two copies of the same idea drift. specimens/11-mutation-check/mutation.py
    is the reference and its recorded results must stay reproducible, so this
    asserts the shared API behaves identically rather than trusting that it does.

    Skips rather than fails if the specimen is absent: this file is meant to be
    copied out of the repository, where it will be."""
    specimen = HERE.parent / "specimens" / "11-mutation-check"
    if not (specimen / "mutation.py").is_file():
        return

    sys.path.insert(0, str(specimen))
    try:
        import mutation  # noqa: PLC0415
    finally:
        sys.path.remove(str(specimen))

    for emit, expected in [(None, True), (lambda text: None, False)]:
        a, b = Subject(), Subject()
        if emit is not None:
            a.emit = emit
            b.emit = emit
        ra = mutate(a, "redact", lambda t: t, live_test(a))
        rb = mutation.mutate(b, "redact", lambda t: t, live_test(b))
        assert ra.caught == rb.caught == expected
        assert ra.detail == rb.detail

    assert issubclass(mutcheck.MutationSurvived, AssertionError)
    assert issubclass(mutation.MutationSurvived, AssertionError)


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
                # A crash is a failure. A runner counting only AssertionError
                # scores a mutation that raises as a pass.
                failures += 1
                print(f"  ERROR {name}: {type(exc).__name__}: {exc}")
    print(f"\n{failures} failure(s)")
    raise SystemExit(1 if failures else 0)
