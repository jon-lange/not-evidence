"""Require that an assertion has been proven live. Standard library only.

This is the reusable artefact of the specimen, and it is small on purpose.
Break something the assertion claims to guard, run the assertion, and demand
that it fails. An assertion that survives its own mutation never observed the
thing it names.

Not a mutation-testing framework. There is no operator catalogue, no AST
rewriting, no coverage integration, and no attempt to find mutations for you.
Those tools answer "which of my assertions are weak?" — a question you ask
occasionally. This answers "is *this* assertion, the one guarding *this*
property, actually watching it?" — a question worth answering in the suite
itself, at every run, next to the assertion it is about.

Usage:

    require_live(subject, "redact", lambda e: dict(e), the_absence_test)

Read that as: with redaction reduced to a no-op, the absence test must fail. If
it does not, the test is not evidence and this raises.

**Its own failure mode is the one it detects.** The swap rebinds a name on a
module object, so it only reaches call sites that look the name up through that
module at call time. A caller that did `from subject import redact` holds its
own reference and never sees the replacement — and then the test passes, and
this reports the assertion as vacuous, because a mutation that never landed and
an assertion that was never live are indistinguishable from here. Treat a
surviving mutation as "one of two things is wrong" and check which.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Iterator


class MutationSurvived(AssertionError):
    """The mutated code still passed. The assertion was never load-bearing.

    Deliberately an AssertionError subclass: a surviving mutation is a failed
    test, and it should be reported by whatever runner you already use rather
    than surfacing as an infrastructure error nobody triages.
    """


@dataclass(frozen=True)
class MutationReport:
    name: str
    caught: bool
    detail: str


@contextmanager
def swapped(target: Any, attr: str, replacement: Any) -> Iterator[None]:
    """Temporarily replace `target.attr`.

    The restore lives in a finally block because the test being run is expected
    to fail — that is the whole point — and a mutation left in place after a
    failure poisons every test that runs after it. The failure mode is a suite
    where the first mutation check makes the rest of the run meaningless.
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
    """Break `target.attr`, run `test`, and report whether the test noticed.

    `caught=False` is the finding this specimen exists for: the code was broken
    and the test still said everything was fine.

    An exception that is not an AssertionError also counts as caught, but the
    two are not equivalent and the report says which happened. A crash proves
    the mutated code *ran*, which is enough to rule out vacuity. It does not
    prove your assertion was the thing watching — the mutation may simply have
    been ill-formed for the code it landed in. Read the detail line.
    """
    label = name or f"{getattr(target, '__name__', target)}.{attr}"
    with swapped(target, attr, replacement):
        try:
            test()
        except AssertionError as exc:
            # A bare `assert x not in y` carries no message, which is the common
            # case for exactly the assertions this helper exists to check.
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

    This is the form that belongs in a test suite. `mutate` reports; this one
    has an opinion, and the opinion is that a green absence-test which cannot be
    made to go red is not a result you are entitled to record.
    """
    report = mutate(target, attr, replacement, test, name=name)
    if not report.caught:
        raise MutationSurvived(
            f"mutation {report.name!r} survived — the assertion under it passed "
            f"with the code broken, so it is not evidence of anything"
        )
    return report
