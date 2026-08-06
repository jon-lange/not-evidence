# Observed results

**Run 2026-08-05.** Fully offline — no models, no network, no keys. Deterministic: the matrix below
reproduces byte-for-byte on any machine.

## The matrix

One absence assertion, held constant across every row:

```
assert SECRET_VALUE not in capture(variant).text()
```

```
Specimen 11 — green is not evidence
==========================================================================================
The assertion under study, unchanged in every row below:

    assert SECRET_VALUE not in capture(variant).text()

==========================================================================================
 cell variant                   redact() lines leak  test  verdict
------------------------------------------------------------------------------------------
 1    correct                   intact     1    no   PASS  earned — cell 3 proves it
 2a   opt-in flag defaults off  intact     0    no   PASS  VACUOUS — log is empty
 2b   token dropped upstream    intact     1    no   PASS  VACUOUS — no token in the event
 3    correct                   BROKEN     1    YES  FAIL  caught — the assertion is live
 4a   opt-in flag defaults off  BROKEN     0    no   PASS  NOT CAUGHT
 4b   token dropped upstream    BROKEN     1    no   PASS  NOT CAUGHT
==========================================================================================

What mutate() says about each variant:

  LIVE     redact -> no-op, against 'correct'
           assertion failed: (no message)
  VACUOUS  redact -> no-op, against 'opt-in flag defaults off'
           mutated code still passed
  VACUOUS  redact -> no-op, against 'token dropped upstream'
           mutated code still passed

==========================================================================================
Cells 1, 2a and 2b are the same green. Read the report, run the suite,
look at the dashboard — there is no observable difference between an
assertion that held a property down and one that was never reached.

Cell 3 is what makes cell 1 a result. Redaction is broken, the token
reaches the log, and the assertion goes red. That red is the evidence;
the green in cell 1 is only a summary of it.

Cells 4a and 4b are cell 3 run against the refactors, and they stay
green. The code is broken, the guard is gone, and the suite reports
success — because the assertion is looking at a log the broken code
never wrote to, or for a field the event no longer carries.

Note the difference between the two vacuums. 4a writes zero lines, so a
witness assertion — 'and the log is not empty' — catches it. 4b writes a
full, plausible line and sails straight through that witness; catching
4b needs a different witness ('and the line contains [redacted]').

That is the argument for mutation, not against it. Every vacuum has some
positive assertion that would have caught it. What you do not have is the
list in advance — you would be writing the witness for the refactor that
has not happened yet. Requiring the assertion to be breakable does not
need the list.

Neither vacuum is a live leak. The token stays out of the log in every
row of this matrix. What is gone is the evidence, and evidence is the
thing that has to still be there the next time somebody edits redact().
```

## What this shows

**Cells 2a and 2b are the demonstration.** The assertion passes, and it proves nothing. In 2a a
rollout flag defaults off so the log is empty; in 2b a schema change stopped carrying the field, so a
full, plausible, correctly-shaped log line is written that simply has no token in it. Both are
refactors that pass code review. Neither is a live leak — what was destroyed is the *evidence*, not
the property.

**Cell 3 is what earns cell 1.** Break redaction against the correct implementation and the assertion
fails. That is the only reason to believe cell 1 meant anything.

**Cells 4a and 4b are the point.** The same mutation against either refactor still passes. A green
tick in cell 1 and a green tick in cell 4 are indistinguishable from outside the process.

**Two vacuums, not one, deliberately.** A single vacuum invites the objection that `assert log.lines`
would catch it — true for 2a, and 2b sails straight through that witness.

## Scope and limits

1. **Both vacuums are constructed, not discovered.** This shows the shape is real and catchable. It
   says nothing about how often it occurs, and no number here could honestly.
2. **The mutation is hand-chosen.** `mutate()` requires you to already name the breakage that
   matters. Pick the wrong one and you get a green liveness proof for an assertion that is live
   against something else — weaker than a tool that enumerates mutations, far stronger than nothing.
3. **The helper cannot distinguish two outcomes.** `swapped()` rebinds a module attribute, so it
   misses call sites holding their own reference. Then the test passes and `mutate()` reports
   VACUOUS — but the truth may be "the mutation never landed." From inside the helper those look
   identical.
4. **Substring absence only.** The sharper case — *the mock was never called* — is the same failure
   and is not demonstrated here.
5. **One overclaim was removed mid-build.** The probe originally said this class cannot be fixed by
   adding another assertion. That is false: each vacuum has *some* positive witness that catches it.
   The honest version is that you do not have the list in advance, because you would be writing the
   witness for the refactor nobody has written yet. Mutation does not need the list.

## What would falsify pattern 11

A refactor-induced vacuum that some ordinary, generally-recommended assertion reliably catches
without anyone having anticipated that specific refactor. Cell 2b was built to be exactly that
counter-example and it survives the obvious witness — but the search was not exhaustive.

## Reproducing

```bash
python3 probe.py          # the matrix
python3 test_subject.py   # the suite, including tests of the mutation helper itself
```
