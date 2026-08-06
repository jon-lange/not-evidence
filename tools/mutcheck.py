#!/usr/bin/env python3
"""Prove an assertion would have failed, before trusting that it passed.

One file, standard library only, nothing imported from the repository it ships
in. Copy it next to your tests and use it, or run it directly to watch the
failure it detects:

    python3 mutcheck.py --demo

The question it answers is narrow on purpose: **is this assertion, guarding this
property, actually watching it?** Break what the assertion claims to guard, run
the assertion, and demand that it fails. One that survives its own mutation
never observed the thing it names.

    require_live(subject, "redact", lambda e: dict(e), the_absence_test)

Read that as: with redaction reduced to a no-op, the absence test must fail. If
it passes, the test is not evidence, and this raises.

NOT a mutation-testing framework. No operator catalogue, no AST rewriting, no
coverage integration, and no attempt to find mutations for you. mutmut and
cosmic-ray do that and do it better — they answer "which of my assertions are
weak?" across a whole suite, which is a question you ask occasionally. This
answers "is *this* one live?", which belongs in the suite, on the line below the
assertion it is about, running every time.

**Its own failure mode is the one it detects.** The swap rebinds a name on a
module object, so it reaches only call sites that look the name up through that
module at call time. A caller holding its own reference — `from subject import
redact` — never sees the replacement. Then the test passes, and this reports the
assertion as vacuous, because from here a mutation that never landed and an
assertion that was never live are indistinguishable. Treat a surviving mutation
as "one of two things is wrong" and find out which.
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Iterator

__all__ = ["MutationSurvived", "MutationReport", "swapped", "mutate", "require_live"]


class MutationSurvived(AssertionError):
    """The mutated code still passed. The assertion was never load-bearing.

    Deliberately an AssertionError subclass: a surviving mutation is a failed
    test, and belongs in whatever runner you already use rather than surfacing
    as an infrastructure error nobody triages.
    """


@dataclass(frozen=True)
class MutationReport:
    name: str
    caught: bool
    detail: str


@contextmanager
def swapped(target: Any, attr: str, replacement: Any) -> Iterator[None]:
    """Temporarily replace `target.attr`.

    The restore is in a finally block because the test being run is *expected*
    to fail — that is the whole point — and a mutation left in place after a
    failure poisons every test that runs after it.
    """
    original = getattr(target, attr)
    setattr(target, attr, replacement)
    try:
        yield
    finally:
        setattr(target, attr, original)


def mutate(
    target: Any,
    attr: str,
    replacement: Any,
    test: Callable[[], None],
    *,
    name: str | None = None,
) -> MutationReport:
    """Break `target.attr`, run `test`, report whether the test noticed.

    `caught=False` is the finding: the code was broken and the test still said
    everything was fine.

    A non-assertion exception also counts as caught, but the two are not
    equivalent and the report says which. A crash proves the mutated code *ran*,
    which rules out vacuity. It does not prove your assertion was the thing
    watching — the mutation may have been ill-formed for the code it landed in.
    Read the detail line.
    """
    label = name or f"{getattr(target, '__name__', target)}.{attr}"
    with swapped(target, attr, replacement):
        try:
            test()
        except AssertionError as exc:
            # A bare `assert x not in y` carries no message, which is the common
            # case for exactly the assertions this exists to check.
            return MutationReport(label, True, f"assertion failed: {str(exc) or '(no message)'}")
        except Exception as exc:  # noqa: BLE001 — a crash is still detection
            return MutationReport(label, True, f"crashed: {type(exc).__name__}: {exc}")
    return MutationReport(label, False, "mutated code still passed")


def require_live(
    target: Any,
    attr: str,
    replacement: Any,
    test: Callable[[], None],
    *,
    name: str | None = None,
) -> MutationReport:
    """`mutate`, but raise if the mutation survived.

    This is the form that belongs in a suite. `mutate` reports; this one has an
    opinion, and the opinion is that a green absence-test which cannot be made
    to go red is not a result you are entitled to record.
    """
    report = mutate(target, attr, replacement, test, name=name)
    if not report.caught:
        raise MutationSurvived(
            f"mutation {report.name!r} survived — the assertion under it passed "
            f"with the code broken, so it is not evidence of anything"
        )
    return report


# --------------------------------------------------------------------- demo
# A worked example, so the failure can be watched rather than described. It is
# under __main__ rather than in a docstring because a demonstration that is
# never executed is the same category of thing this tool exists to refuse.

_DEMO = '''
A logging module redacts a secret before writing. One absence test guards it:

    assert SECRET not in log.written()

Three implementations. The assertion passes against all three.
'''

SECRET = "hunter2"


class _Log:
    """Three redaction behaviours and one absence test over all of them."""

    def __init__(self, mode: str) -> None:
        self.mode, self.lines = mode, []

    def redact(self, event: str) -> str:
        return event.replace(SECRET, "***")

    def write(self, event: str) -> None:
        if self.mode == "correct":
            self.lines.append(self.redact(event))
        elif self.mode == "flag-off":
            pass                       # a rollout flag defaults off: nothing logged
        elif self.mode == "field-gone":
            self.lines.append("event=login user=alice")   # schema dropped the field

    def written(self) -> str:
        return "\n".join(self.lines)


def _absence_test(log: _Log) -> Callable[[], None]:
    def check() -> None:
        log.write(f"event=login user=alice password={SECRET}")
        assert SECRET not in log.written()
    return check


def _demo() -> int:
    print(_DEMO)
    rows = []
    for mode, label in [
        ("correct", "redaction works"),
        ("flag-off", "rollout flag off — nothing is logged"),
        ("field-gone", "schema change — field no longer carried"),
    ]:
        log = _Log(mode)
        test = _absence_test(log)
        test()  # the assertion passes in all three. That is the problem.
        report = mutate(log, "redact", lambda e: e, test, name=f"redact→no-op [{mode}]")
        rows.append((label, report.caught, report.detail))

    width = max(len(r[0]) for r in rows)
    print(f"  {'implementation'.ljust(width)}   mutation caught?")
    print(f"  {'-' * width}   ----------------")
    for label, caught, detail in rows:
        mark = "CAUGHT" if caught else "NOT CAUGHT"
        print(f"  {label.ljust(width)}   {mark:<11} {detail}")

    vacuous = [r[0] for r in rows if not r[1]]
    print()
    print(
        f"The assertion passed in all three. With redaction reduced to a no-op it\n"
        f"failed in {len(rows) - len(vacuous)} of {len(rows)} — so in the other "
        f"{len(vacuous)} it was never watching\nredaction at all. Neither is a live "
        f"leak. What was destroyed is the evidence,\nnot the property, and a green "
        f"tick looks identical either way.\n"
    )
    print("Drop this file beside your tests and wrap one absence assertion:\n")
    print('    require_live(subject, "redact", lambda e: e, my_absence_test)\n')
    return 0


def main(argv: list[str]) -> int:
    if "--demo" in argv:
        return _demo()
    print(__doc__)
    print("Run `python3 mutcheck.py --demo` to watch the failure it detects.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
