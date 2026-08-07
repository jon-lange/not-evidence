---
type: Attested Computation
title: Specimen 07 · Gate Over-Refusal Separately
description: The measurement behind pattern 07.
resource: https://github.com/jon-lange/not-evidence/tree/main/specimens/07-over-refusal
tags: [specimen, measurement, live]
runtime: python
executor:
  resource: https://github.com/jon-lange/not-evidence/blob/main/specimens/07-over-refusal/probe.py
  receipt: [results_jsonl, stdout, exit_code]
attester:
  resource: https://github.com/jon-lange/not-evidence/blob/main/scripts/check-consistency.py
adjudication: central-claim-failed
generated: { by: human:jon-lange, at: 2026-08-06T13:51:25-05:00 }
verified:
  - { by: process:emit-okf/0.1, at: 2026-08-06T13:51:25-05:00 }
  - { by: human:jon-lange, at: 2026-08-06T13:51:25-05:00 }
---

# Specimen 07 · Gate Over-Refusal Separately

Measures [pattern 07](../patterns/07-gate-over-refusal-separately.md).

# Computation

```bash
cd specimens/07-over-refusal
python3 probe.py            # live: needs credentials, costs money
```

**Adjudication:** `central-claim-failed` — whether the pattern's central claim survived measurement.

# What would falsify this

**Reproduce 07(b):** any run where a newer model in a family shows a materially higher sensitive-bucket
refusal rate than an older one from the same family, on items the older model answered. The harness is
built for it — widen the item set toward the boundary (strip the defensive framing), or add a heavily
safety-tuned checkpoint, and re-run. `results.jsonl` makes the comparison a re-classification, not a
re-spend.

**Falsify 07's measurement stance:** show that a blended quality-with-refusal score would have caught
what a separate refusal metric caught here. It would not have — with quality high and refusal zero, a
composite is dominated by quality and reports the same "all green" either way. The separation earns
its keep on the run where refusal moves and quality does not; this run is not that run, and says so.

# Full record

- [RESULTS.md](https://github.com/jon-lange/not-evidence/blob/main/specimens/07-over-refusal/RESULTS.md) — what was run, what came back, the scope, and the falsification condition
- [Specimen source](https://github.com/jon-lange/not-evidence/tree/main/specimens/07-over-refusal)
