---
name: mutation-check
description: Prove a test would have failed before trusting that it passed. Use when writing or reviewing tests that assert an absence — that a secret is not logged, a forged token is rejected, a payload is not persisted, an alert would fire — or any check whose healthy signal and broken signal look identical. Also use when a suite is green and nobody can say when it last failed.
pattern: 11
status: field-tested
---

# Mutation check

A passing test is a fact about this run. **"The test would have failed" is a fact about the test.**
Only the second is evidence, and only the second survives the refactor that hasn't happened yet.

This matters most for **absence assertions** — the ones that pass by finding nothing. They find
nothing in two different worlds: the one where the guard works, and the one where the code that would
have produced the forbidden thing never ran. From outside the process both emit the same green tick.

## When to run this

Any assertion of the form *X does not appear*, *Y is rejected*, *Z is never called*. Also:

- A scanner, alert, or policy check whose "all clear" is produced by the same path as "not configured"
- A test nobody can date the last failure of
- Any suite you are about to cite as coverage of a security or privacy property

Security and privacy requirements are almost always negative — must not leak, must not accept, must
not persist. **The requirements with the worst consequences produce the test class with the weakest
evidence.**

## The procedure

**1. Name the breakage that matters.** Not a random mutation — the specific thing that would make the
guarded property false. *Redaction becomes a no-op. The expired token is accepted. The scrubber
returns its input.* If you cannot name it, you do not yet know what the test is for.

**2. Apply it and run the suite.**

**3. Require a failure, and read the reason.** Red is not sufficient. A test that errors because a
fixture stopped building has told you nothing about the property. It must fail *because the property
is now false*.

**4. Restore, and record it.** Which assertions have been mutation-checked, and on what date.
Unrecorded verification decays to folklore within a quarter.

**5. Count how many tests died.** A mutation that kills one test where you expected four has found
either a redundancy or a gap. Both are worth knowing.

```python
# The whole mechanism. Not a framework.
def require_live(break_it, run_tests, name):
    """Apply a deliberate breakage; require the suite to fail; restore."""
    with break_it():
        if run_tests():                       # still green?
            raise AssertionError(f"VACUOUS: {name} — suite passed with the guard broken")
    assert run_tests(), f"{name}: suite did not recover after restore"
```

Runnable reference implementation: [`../../specimens/11-mutation-check/`](../../specimens/11-mutation-check/).

## What this repeatedly finds

Run against this repository's own twelve specimen suites, mutation checking surfaced a defect in
**seven** of them — 01, 02, 03, 05, 06, 11 and 12. The other five caught every mutation cleanly.
Not one of the seven defects was visible from running the tests.

| Defect | How it hid |
|---|---|
| **Runner caught only `AssertionError`** | A mutation raising `KeyError` crashed the script, printed no FAIL line, and scored as *survived*. Found in four separate suites, including ones written to demonstrate this skill. |
| **Test compared a poisoned value to itself** | A test of a restore mechanism read its baseline from live module state that an earlier mutation had left poisoned. Defeated by the thing it was testing. |
| **Assertion checked literals, not behaviour** | A normalisation function returning its input unchanged passed everything, because the fixtures were already normalised. |
| **Test could not fail** | Asserted dict-order independence over code that never reads dict order. Deleted, along with the dead guard it defended. |
| **Guard was on the ratio, not the number** | A change moving a published median by 1.5× passed, because the suite only constrained a derived ratio. |
| **Mutation never landed** | Same-size edit within one second left a stale `.pyc`; the mutation silently un-applied and reported green. Clear `__pycache__` per run. |
| **Behaviourally dead branch** | A zero-gap check was subsumed by a threshold check. Removing it changed no outcome, only an explanatory note — so the test had to assert the note. |

**Read that last column, not the first.** Every one of these produced a green suite, and none would
have been found by any amount of running it.

## The stronger version

Mutation-checking makes an absence assertion trustworthy. It does not make the absence *guaranteed* —
you are verifying a behaviour a later change can remove.

Where the type system can reach, put the absence there instead. Give credentials a wrapper whose
unwrapping is explicit, and let the logging interface accept only values that render — a trait the
wrapper does not implement. **A test says the leak did not occur in the cases you ran. A type says the
code expressing the leak does not compile.** One is a promise; the other is a guarantee.

The mutation check is the fallback, not the ideal.

## Honest limits

**It requires you to already name the breakage.** Pick the wrong one and you get a green liveness
proof for an assertion that is live against something *else*. Weaker than a tool that enumerates
mutants; far stronger than nothing.

**It cannot always distinguish two outcomes.** If the mutation never actually landed — a rebound
module attribute a call site holds its own reference to, a stale bytecode cache — the suite passes and
the check reports VACUOUS. From inside the harness, *"the assertion is dead"* and *"the mutation
missed"* look identical. Verify the mutation took effect.

**It is not a coverage metric.** Coverage records that a line executed, not that any assertion
depended on it. Both numbers can be high while the property is unguarded.

**Adding another assertion is sometimes enough** — every vacuum has *some* positive witness that would
catch it. The problem is that you do not have the list in advance, because you would be writing the
witness for the refactor nobody has written yet. Mutation does not need the list.

## Prior art

- DeMillo, Lipton & Sayward, *Hints on Test Data Selection* — IEEE *Computer*, 1978
- Just et al., *Are Mutants a Valid Substitute for Real Faults in Software Testing?* — FSE 2014
- Petrović et al., *Practical Mutation Testing at Scale* — [arXiv:2102.11378](https://arxiv.org/abs/2102.11378)
