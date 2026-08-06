---
pattern: 11
name: "Green Is Not Evidence"
status: field-tested   # draft | field-tested | superseded-by: NN
refuses: "to trust an absence-test that was never mutation-checked"
specimen: 11-mutation-check
---

# 11 · Green Is Not Evidence

> **Refuses to trust an absence-test that was never mutation-checked.**

## Context

Presence tests and absence tests fail differently, and only one of them fails loudly.

A presence test says *the response contains the resolved display name*. Break the code that produces
the name and the assertion has nothing to match — it is coupled to the behaviour it checks.

An absence test says *the credential does not appear in the log*, *the forged token is rejected*,
*the payload is not in the trace*. It passes by finding nothing, and it finds nothing in two
different worlds: the one where the guard works, and the one where the code that would have produced
the forbidden thing never ran. From outside the process, both emit the same green tick.

## Forces

**Absence is how you state the properties you care most about.** Security and privacy requirements
are almost always negative: must not leak, must not accept, must not persist. The requirements with
the worst consequences produce the test class with the weakest evidence.

**Every other test class earns trust honestly,** which is why the habit of reading green as evidence
transfers intact into the one place it doesn't hold. And nobody investigates a passing test: red
demands attention, green closes the tab.

**Refactors remove code paths quietly.** A call gets inlined, wrapped, flagged off, or dropped in a
diff about something else. That never surfaces as a failing absence test. It surfaces as an absence
test that got easier to pass.

## The Refusal

**An absence assertion is not evidence until you have watched it fail. Break the guarded behaviour
on purpose, confirm the test goes red for the reason you expect, restore it — and record that you
did.**

1. **Break the guard, not the test.** Remove the redaction. Let the expired token through. If the
   suite stays green, that assertion never checked anything.
2. **Fail for the right reason.** Red is not sufficient. A test that errors because the fixture
   stopped building has told you nothing about the property.
3. **Record it,** and require a check before the next absence assertion counts. Unrecorded
   verification decays to folklore.

**"The test passed" is a fact about this run. "The test would have failed" is a fact about the
test.** Only the second is evidence, and only the second survives the refactor that hasn't happened
yet.

### The worked example

A service logs request metadata. A test drives one request, captures the log stream, and asserts the
API key does not appear in it. Green from the day it was written.

Months later a refactor moves logging behind a new abstraction and drops the call site in that
handler — one line, in a diff about something else. The handler now logs nothing, the stream is
empty, and the assertion is trivially true. The suite reports the property as covered; what it
reports is that there was no output to search. Reintroduce logging later without the redaction and
the test is still green — it has been green throughout, and nothing marks the moment it stopped
meaning anything.

### The stronger version

Mutation-checking makes an absence assertion trustworthy. It does not make the absence guaranteed:
you are verifying a behaviour a later change can remove.

Put the absence in the type instead. Give credentials a wrapper whose unwrapping is explicit and
audited, and let the logging interface accept only values that render — a trait the wrapper does not
implement. **A test says the leak did not occur in the cases you ran; a type says the code expressing
the leak does not compile.** One is a promise, the other a guarantee. Where the type system cannot
reach, the mutation check is the fallback, not the ideal.

### Past the test suite

Any all-clear produced by the same code path as *not configured* has this defect: a scanner whose
credential expired and now returns zero findings, a policy engine that permits everything because
its ruleset failed to load. The healthy signal and the broken signal are the same signal, and the
broken one is quieter. **An alert you have never seen fire is an alert you have not tested.**

## Consequences

**You find dead assertions immediately** — negative tests that cannot fail, each previously counted
as coverage of a high-stakes property.

**Writing negative tests gets slower,** by one manual step producing no artifact but a line in a
record. Mutation frameworks automate part of it and not the important part: the mutants that matter
are semantic — *drop the redaction*, *accept the expired token* — and those come from someone who
knows what the guard is for.

**The record becomes the reviewable artifact.** "We test that it doesn't leak" is not checkable.
"These four assertions are mutation-checked as of this date, these two are not" is.

## The naive approach it beats

**Line coverage over the guarded path.** The sophisticated version of the mistake, attractive for
good reasons: quantitative, automated, trended, genuinely useful everywhere else.

It fails precisely. **Coverage records that a line executed, not that any assertion depended on it.**
In the worked example, coverage of the handler stays high throughout — the handler runs, the test
exercises it, the lines are hit. The line that vanished was not an assertion, and no coverage number
is computed over assertions. Coverage answers *did this code run*. The question was *would this test
have noticed*.

The tell: someone can describe what the test asserts, and nobody can say when it last failed.

## Prior art

- DeMillo, Lipton & Sayward, *Hints on Test Data Selection: Help for the Practicing Programmer* —
  IEEE *Computer*, April 1978. The origin of mutation testing, and still the clearest statement of
  why a test that no fault can break is not a test
- Just et al., *Are Mutants a Valid Substitute for Real Faults in Software Testing?* — FSE 2014.
  Mutant detection tracks real faults where coverage does not
- Petrović, Ivanković, Fraser & Just, *Practical Mutation Testing at Scale* —
  [arXiv:2102.11378](https://arxiv.org/abs/2102.11378)
- Sabelfeld & Myers, *Language-based information-flow security* (IEEE JSAC, 2003), and Alexis King,
  *[Parse, Don't Validate](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/)* —
  illegal states made unrepresentable rather than asserted against

## Specimen

[`specimens/11-mutation-check/`](../specimens/11-mutation-check/) — **built.** Runs offline on the
standard library alone.

One absence assertion — *the secret does not appear in the log* — held constant across six cells. The
same mutation (redaction becomes a no-op) is applied to a correct implementation and to two
**refactors that pass code review**: a rollout flag defaulting off, and a schema change that stopped
carrying the field. Against the correct code the assertion fails, proving it live. Against either
refactor it still passes, proving it was never evidence.

Two vacuums rather than one, deliberately: the first writes nothing, so a reviewer can object that
`assert log.lines` would catch it. The second writes a full, plausible, correctly-shaped log line and
sails through that same witness.

The reusable artefact is `mutate()` — apply a named breakage, run the assertion, and require that it
*fails*. That is what converts "the test passed" into "the test would have failed."

**The specimen found a vacuous test inside its own suite.** A test of the restore mechanism read its
baseline from live module state; under the mutation that broke restoration, an earlier test left that
state poisoned, so the test compared the poisoned value to itself and passed. A test of the restore
mechanism, defeated by the restore mechanism being broken. It now asserts against a private sentinel.
