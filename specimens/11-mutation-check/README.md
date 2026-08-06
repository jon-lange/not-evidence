# Specimen 11 — an absence-test that passes because nothing ran

Demonstrates [pattern 11 · Green Is Not Evidence](../../patterns/11-green-is-not-evidence.md).

One security assertion — *the recorded event never contains an authentication token* — run against
three variants of the same telemetry recorder, twice each: once with redaction intact and once with
redaction deliberately broken.

```
 cell variant                   redact() lines leak  test  verdict
 1    correct                   intact     1    no   PASS  earned — cell 3 proves it
 2a   opt-in flag defaults off  intact     0    no   PASS  VACUOUS — log is empty
 2b   token dropped upstream    intact     1    no   PASS  VACUOUS — no token in the event
 3    correct                   BROKEN     1    YES  FAIL  caught — the assertion is live
 4a   opt-in flag defaults off  BROKEN     0    no   PASS  NOT CAUGHT
 4b   token dropped upstream    BROKEN     1    no   PASS  NOT CAUGHT
```

**Cells 2 and 4 are the demonstration.** Rows 1, 2a and 2b are the same green. Nothing in a test
report, a CI badge, or a coverage number separates an assertion that held a property down from one
that was never reached.

## The finding

**An absence-test cannot distinguish "guarded" from "never ran."** It looks for a string that is not
there, and a string is not there when the code was correct, and also when the code did nothing at
all. The two outcomes are the same outcome.

Row 3 is what makes row 1 a result. Break redaction and the token reaches the log and the assertion
goes red — *that* red is the evidence, and the green in row 1 is a summary of it. Rows 4a and 4b are
row 3 run against the refactors, and they stay green: the code is broken, the guard is gone, and the
suite reports success.

**Neither refactor is a bug, and neither is a live leak.** The token really does stay out of the log
in every row of that matrix. `DroppingRecorder` is a correct feature flag for a staged rollout,
defaulting off. `build_event_after_migration` is a correct schema change that stopped carrying a
field. Both would pass review. What they destroy is not the property, it is the *evidence* — and
evidence is the thing that has to still be there the next time somebody edits `redact()`.

## Why there are two vacuums

The first one, 2a, is catchable cheaply: assert the log is not empty and 4a goes red.

That fix does not reach 2b, which writes a full, plausible, correctly-shaped line and would sail
straight through the same witness. Catching 2b needs a *different* witness — *and the line contains
`[redacted]`* — and that is the whole problem in one sentence. Every vacuum has some positive
assertion that would have caught it. You do not have the list in advance, because you would be
writing the witness for the refactor nobody has written yet.

Requiring that the assertion can be made to fail does not need the list.

## The reusable part

`mutation.py` is about seventy lines and is the only thing here worth taking:

```python
require_live(subject, "redact", redact_nothing, lambda: subject.absence_check(CORRECT))
```

Read as: *with redaction reduced to a no-op, this absence test must fail.* If it does not,
`MutationSurvived` is raised — deliberately an `AssertionError` subclass, so an unproven assertion is
reported by whatever runner you already have rather than surfacing as infrastructure noise nobody
triages.

It is not a mutation-testing framework and does not want to be. Those tools answer *which of my
assertions are weak?*, a question you ask occasionally, offline, over a whole suite. This answers *is
this assertion, guarding this property, actually watching it?* — which belongs in the suite, at every
run, on the line below the assertion it is about.

## Run it

```bash
python3 probe.py          # prints the matrix
python3 test_subject.py   # or: python3 -m pytest test_subject.py -q
```

No network, no key, no dependencies, no configuration. This specimen makes a claim about test
suites, not about a service, so everything it asserts is local and reproducible.

## Tests

Twenty tests. Two of them assert a *failure* rather than a guarantee —
`test_a_vacuum_passes_the_absence_test` and `test_the_dead_field_vacuum_survives_a_witness_assertion`
pin the fraud in place, so a later change that accidentally fixes the demonstration is caught.

**Mutation-checked.** Fifteen deliberate breakages, all caught, and every one of the twenty tests is
killed by at least one:

| Mutation | Tests failed |
|---|---|
| `Recorder.record()` returns before writing (a third vacuum) | 6 |
| `probe.py`'s `redact_nothing` actually redacts | 4 |
| `swapped()` never restores the original | 4 |
| `redact()` masks every field, not just secrets | 3 |
| `mutate()` reports survived unconditionally | 3 |
| `DroppingRecorder`'s opt-in flag defaults on | 3 |
| The schema migration nests the token instead of dropping it | 3 |
| `redact()` returns its input unchanged | 2 |
| `SECRET_FIELDS` is empty | 2 |
| `mutate()` reports caught unconditionally | 2 |
| `redact()` mutates the caller's event in place | 1 |
| `require_live()` never raises | 1 |
| `MutationSurvived` is a plain `Exception` | 1 |
| The crash branch is removed from `mutate()` | 1 |
| `mutate()` labels the mutation by attribute alone | 1 |

**The mutation check found a vacuous test in this specimen's own suite.**
`test_swapped_restores_the_original_after_a_failure` originally read the pre-mutation value off the
live `subject` module. Under *"`swapped()` never restores the original"* an earlier test in the same
run left `subject.redact` poisoned, so this test read the poisoned value as its baseline, compared it
to itself, and passed — a test of the restore mechanism, defeated by the restore mechanism being
broken. It now asserts against a private sentinel. That is the finding this specimen is about,
occurring in the code that demonstrates it, and it was caught by the technique rather than by
reading.

One test earns its place by pointing the other way: `test_redact_leaves_ordinary_fields_alone`. A
redactor that masks everything passes every absence-test ever written, and a telemetry pipeline that
emits nothing but `[redacted]` has failed as surely as one that emits secrets.

## Scope

One property, one assertion shape (substring absence), two vacuum mechanisms, one language. This
shows that the failure exists, that it survives the obvious fix, and that a seventy-line check
catches it.

**The result that would falsify the pattern** is a vacuous absence-test whose mutation check still
reports the assertion as live. If you find one, the pattern is wrong and I want to know.

## What this specimen deliberately does not do

**The vacuums are constructed, not discovered.** Both refactors were written to be vacuous. The
specimen establishes that the shape is real and that the check catches it; it does not establish how
often this occurs in the wild, and no number here would be honest about that.

**The mutation is chosen by hand, and a check is only as good as its mutation.** `require_live` asks
you to name the breakage that would matter. Name the wrong one and you get a green liveness proof for
an assertion that is live against something else. This is strictly weaker than a tool that enumerates
mutations for you — and strictly stronger than nothing, which is the alternative it is competing
with.

**The helper's own failure mode is the signal it exists to produce.** `swapped()` rebinds a name on a
module object, so it only reaches call sites that resolve that name through the module at call time.
A caller holding its own reference — `from subject import redact` — never sees the replacement, the
test passes, and `mutate()` reports *vacuous*. A mutation that never landed and an assertion that was
never live are indistinguishable from inside the helper. Treat a surviving mutation as *one of two
things is wrong* and go find out which.

**It does not run the check for you at build time.** There is no hook, no plugin, no gate. Wiring
`require_live` next to the assertions that matter is a decision about which properties are worth the
duplicated execution, and this specimen does not make it on anyone's behalf.

**Substring absence only.** Real absence-tests also take the shape of *no exception was raised*, *the
list is empty*, *the mock was never called* — and the last of those is the same failure with a
sharper edge, because a mock that was never called and a mock that was correctly never called are
recorded identically. The mechanism generalises; this specimen does not demonstrate the generalisation.

---

Reference implementation. Not maintained.
