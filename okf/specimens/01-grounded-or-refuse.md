---
type: Attested Computation
title: Specimen 01 · Grounded or Refuse
description: The measurement behind pattern 01.
resource: https://github.com/langej117/not-evidence/tree/main/specimens/01-grounded-or-refuse
tags: [specimen, measurement, live]
runtime: python
executor:
  resource: https://github.com/langej117/not-evidence/blob/main/specimens/01-grounded-or-refuse/probe.py
  receipt: [results_jsonl, stdout, exit_code]
attester:
  resource: https://github.com/langej117/not-evidence/blob/main/scripts/check-consistency.py
adjudication: central-claim-failed
generated: { by: human:langej117, at: 2026-08-06T13:51:25-05:00 }
verified:
  - { by: process:emit-okf/0.1, at: 2026-08-06T13:51:25-05:00 }
  - { by: human:langej117, at: 2026-08-06T13:51:25-05:00 }
---

# Specimen 01 · Grounded or Refuse

Measures [pattern 01](../patterns/01-grounded-or-refuse.md).

# Computation

```bash
cd specimens/01-grounded-or-refuse
python3 probe.py            # live: needs credentials, costs money
```

**Adjudication:** `central-claim-failed` — whether the pattern's central claim survived measurement.

# What would falsify this

The direction of the falsification claim is now reversed, and that is the honest way to state it.

**This result would be overturned by a corpus and question shape where configuration A0 confabulates
and configuration B does not.** The specific untested conditions above are where to look first —
long assembled contexts, questions answerable by synthesis rather than lookup, and a competing
instruction to be helpful. Anyone finding such a shape has restored pattern 01's prediction, and
this specimen should record that.

**This result would be overturned in the other direction** by a run at n≥20 samples per cell that
finds a non-zero tail. n=1 per cell cannot see one.

**What this run does not touch.** Pattern 01 has four claims. This specimen tests only the fourth —
that the attitudinal fix fails. The other three (answer from evidence retrieved *this turn*, cite
it, treat refusal as a success outcome) are architectural commitments, not behavioural predictions,
and no result here bears on them.

# Full record

- [RESULTS.md](https://github.com/langej117/not-evidence/blob/main/specimens/01-grounded-or-refuse/RESULTS.md) — what was run, what came back, the scope, and the falsification condition
- [Specimen source](https://github.com/langej117/not-evidence/tree/main/specimens/01-grounded-or-refuse)
