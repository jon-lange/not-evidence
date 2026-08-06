"""The system under test — a job-runner telemetry recorder, and two refactors of it.

The property worth asserting here is a negative one: *a recorded event never
contains an authentication token*. Negative properties are the ones you test by
absence, and absence is the assertion shape that can pass for the wrong reason.

Three ways to record one event live in this module. They are not one correct
implementation and two bugs. They are one correct implementation and two
**refactors**, each of which would pass code review, and each of which leaves
the absence-test green while emptying it of meaning:

  Recorder + build_event
      Correct. The token is redacted before the line is written.

  DroppingRecorder + build_event
      Telemetry became opt-in per deployment. The flag defaults off, so record()
      returns before it reaches the log. Nothing is written, so nothing leaks.

  Recorder + build_event_after_migration
      A schema change stopped putting the token into the event at all. A full,
      normal-looking line is written; the redactor never has anything to do.

The first vacuum is catchable by additionally asserting the log is non-empty.
The second sails through that same witness — it writes a plausible line — and
needs a different one. That is why both ship here: the point is not that a
witness assertion is useless, it is that you would need the right witness for a
refactor nobody has written yet.

Note that neither vacuum is a live leak. The system is safe in all three rows.
What is gone in rows two and three is the *evidence*, and evidence is what stops
the property rotting the next time someone touches the code.

Generic domain on purpose: a job runner, a token, a log. Nothing here belongs to
any product, and the mechanism is the same wherever a negative property is
asserted by looking for a string that is not there.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable

# Field names whose values must never reach the log. A frozenset rather than a
# list because membership is the only operation, and because a mutable module
# global is a footgun in a module that gets monkeypatched by mutation.py.
SECRET_FIELDS = frozenset({"auth_token", "password", "private_key"})

REDACTION = "[redacted]"

# The canary. Deliberately not secret-shaped — it is a marker whose whole job is
# to be searched for. A realistic-looking token here would make the specimen a
# worse neighbour in a repository that scans itself for credentials.
SECRET_VALUE = "canary-DO-NOT-PERSIST"

JOB_NAME = "nightly-reindex"
ATTEMPT = 2


def redact(event: dict) -> dict:
    """Return a copy of `event` with secret-named fields masked.

    A copy, not an in-place edit: the caller's event object is shared with the
    rest of the pipeline, and a redactor that mutates its input silently
    destroys the token for everything downstream that legitimately needs it.
    """
    return {k: (REDACTION if k in SECRET_FIELDS else v) for k, v in event.items()}


def serialize(event: dict) -> str:
    """One event, one line. Sorted keys so the output is byte-stable."""
    return json.dumps(event, sort_keys=True)


def build_event(job: str, attempt: int, token: str) -> dict:
    """The event as originally specified — the token travels with it."""
    return {"job": job, "attempt": attempt, "auth_token": token, "worker": "w-04"}


def build_event_after_migration(job: str, attempt: int, token: str) -> dict:
    """The same event after a schema change dropped the token.

    Signature unchanged, so every call site still compiles and every caller
    still passes the token. It simply stops arriving in the payload. This is the
    shape of change that turns a redactor into dead code without anyone noticing
    — including the test suite, which goes on reporting the surface as covered.
    """
    return {"job": job, "attempt": attempt, "worker": "w-04"}


@dataclass
class EventLog:
    """The sink the absence-test reads. In a real system, a file or a stream."""

    lines: list[str] = field(default_factory=list)

    def write(self, line: str) -> None:
        self.lines.append(line)

    def text(self) -> str:
        return "\n".join(self.lines)


@dataclass
class Recorder:
    """The correct recorder. Redacts, then writes."""

    log: EventLog

    def record(self, event: dict) -> None:
        self.log.write(serialize(redact(event)))


@dataclass
class DroppingRecorder:
    """The same recorder after telemetry became opt-in per deployment.

    Nothing about this is wrong. A staged rollout defaults its flag off, and a
    reviewer reading the diff sees a correct feature flag. The consequence is
    invisible from here: every caller that constructs a recorder with defaults —
    which includes the test suite — now exercises a code path that returns
    before it ever reaches the redactor.
    """

    log: EventLog
    enabled: bool = False

    def record(self, event: dict) -> None:
        if not self.enabled:
            return
        self.log.write(serialize(redact(event)))


@dataclass(frozen=True)
class Variant:
    """A (recorder, event builder) pairing — one row of the probe's matrix."""

    label: str
    recorder: Callable[[EventLog], Recorder | DroppingRecorder]
    builder: Callable[[str, int, str], dict]


CORRECT = Variant("correct", Recorder, build_event)
VACUUM_FLAG = Variant("opt-in flag defaults off", DroppingRecorder, build_event)
VACUUM_DEAD_FIELD = Variant("token dropped upstream", Recorder, build_event_after_migration)


def capture(variant: Variant) -> EventLog:
    """Wire the variant to a fresh log, record one event, hand back the log."""
    log = EventLog()
    variant.recorder(log).record(variant.builder(JOB_NAME, ATTEMPT, SECRET_VALUE))
    return log


# ── the assertion under study ────────────────────────────────────────────────
#
# A test-shaped function in the subject module looks out of place, and it is
# here deliberately. The probe and the test suite must run the *same* assertion,
# not two copies of it — a mutation check performed against a copy proves that
# the copy is live and tells you nothing about the one that guards the build.


def absence_check(variant: Variant) -> None:
    """The security assertion: the token never appears in the log.

    Raises AssertionError when it does. This is the entire contract, and it is
    also every one of the ways this specimen shows it can be worthless.
    """
    assert SECRET_VALUE not in capture(variant).text()
