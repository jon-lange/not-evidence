---
type: Attested Computation
title: Specimen 05 · The Judge Cannot Share a Family
description: The measurement behind pattern 05.
resource: https://github.com/jon-lange/not-evidence/tree/main/specimens/05-judge-family
tags: [specimen, measurement, live]
runtime: python
executor:
  resource: https://github.com/jon-lange/not-evidence/blob/main/specimens/05-judge-family/probe.py
  receipt: [results_jsonl, stdout, exit_code]
attester:
  resource: https://github.com/jon-lange/not-evidence/blob/main/scripts/check-consistency.py
adjudication: central-claim-failed
generated: { by: human:jon-lange, at: 2026-08-06T14:00:52-05:00 }
verified:
  - { by: process:emit-okf/0.1, at: 2026-08-06T14:00:52-05:00 }
  - { by: human:jon-lange, at: 2026-08-06T14:00:52-05:00 }
---

# Specimen 05 · The Judge Cannot Share a Family

Measures [pattern 05](../patterns/05-judge-cannot-share-a-family.md).

# Computation

```bash
cd specimens/05-judge-family
python3 probe.py            # live: needs credentials, costs money
```

**Adjudication:** `central-claim-failed` — whether the pattern's central claim survived measurement.

# What would falsify this

The entry was rewritten around what actually disqualified two of three judges: **saturation and
position instability**. So falsification is now about those two checks, not about lineage.

**Falsify the current claim:** a judge that passes both checks — it discriminates between candidates
and its ranking survives an order swap — and is *still* systematically wrong, measured against a
reference the run trusts more than the judge. That would show the two checks are not the ones worth
gating on, which is the claim the entry now makes.

**Also falsifying:** a run where the two checks reject a judge whose verdicts turn out to be correct.
Screening out good judges is a cost the entry does not currently price.

**Restore the original lineage claim:** a comparison where a same-family judge picks one winner and a
cross-family judge picks the other, on a task set where both judges discriminate and are order-stable.
The confound this run hit was saturation — absolute scoring on a task set where both candidates are
strong. Swap the task set for one that separates them, keep the three judges, and re-run; the harness
is built for it. A flip that survives those controls puts lineage back.

**What this run cannot settle:** twelve items, one rubric, one day. A null on twelve items is weak
evidence of absence, and the entry says so rather than reading it as a refutation of self-preference
in general.

# Full record

- [RESULTS.md](https://github.com/jon-lange/not-evidence/blob/main/specimens/05-judge-family/RESULTS.md) — what was run, what came back, the scope, and the falsification condition
- [Specimen source](https://github.com/jon-lange/not-evidence/tree/main/specimens/05-judge-family)
