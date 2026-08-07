---
type: Attested Computation
title: Specimen 06 · Refuse to Score Unratified Weights
description: The measurement behind pattern 06.
resource: https://github.com/langej117/not-evidence/tree/main/specimens/06-unratified-weights
tags: [specimen, measurement, offline]
runtime: python
executor:
  resource: https://github.com/langej117/not-evidence/blob/main/specimens/06-unratified-weights/probe.py
  receipt: [results_jsonl, stdout, exit_code]
attester:
  resource: https://github.com/langej117/not-evidence/blob/main/scripts/check-consistency.py
adjudication: narrowed
generated: { by: human:langej117, at: 2026-08-06T13:51:25-05:00 }
verified:
  - { by: process:emit-okf/0.1, at: 2026-08-06T13:51:25-05:00 }
  - { by: human:langej117, at: 2026-08-06T13:51:25-05:00 }
---

# Specimen 06 · Refuse to Score Unratified Weights

Measures [pattern 06](../patterns/06-refuse-unratified-weights.md).

# Computation

```bash
cd specimens/06-unratified-weights
python3 probe.py            # offline, no key, no network
```

**Adjudication:** `narrowed` — whether the pattern's central claim survived measurement.

# What would falsify this

**A domain where winners are robustly weight-independent.** If real evaluation scorecards mostly look
like `docgen-dominant` — one candidate ahead on every dimension — then the weighting never decides
anything, and refusing to score without a ratification is ceremony with a real cost and no benefit.
The specimen supplies the shape of that counterexample and measures it at exactly zero. What it
cannot supply is how common that shape is.

**A demonstration that provenance survives the trip.** The pattern rests on emitted numbers arriving
stripped of their origin. If an evaluation artefact can be shown to carry its weighting, its owner,
and its ratification state all the way to the decision — and to be read there — then warn-and-proceed
is sufficient and the refusal is over-engineering.

**A ratification record that is routinely rubber-stamped.** The control produces a named owner. If
the name is reliably supplied by whoever is least inconvenienced, the pattern has bought a signature
rather than a decision, and the failure it prevents has moved rather than gone.

# Full record

- [RESULTS.md](https://github.com/langej117/not-evidence/blob/main/specimens/06-unratified-weights/RESULTS.md) — what was run, what came back, the scope, and the falsification condition
- [Specimen source](https://github.com/langej117/not-evidence/tree/main/specimens/06-unratified-weights)
