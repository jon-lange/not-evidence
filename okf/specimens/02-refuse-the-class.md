---
type: Attested Computation
title: "Specimen 02 · Refuse the Class, Not the Case"
description: The measurement behind pattern 02.
resource: https://github.com/langej117/not-evidence/tree/main/specimens/02-refuse-the-class
tags: [specimen, measurement, offline]
runtime: python
executor:
  resource: https://github.com/langej117/not-evidence/blob/main/specimens/02-refuse-the-class/probe.py
  receipt: [results_jsonl, stdout, exit_code]
attester:
  resource: https://github.com/langej117/not-evidence/blob/main/scripts/check-consistency.py
adjudication: narrowed
generated: { by: human:langej117, at: 2026-08-06T13:51:25-05:00 }
verified:
  - { by: process:emit-okf/0.1, at: 2026-08-06T13:51:25-05:00 }
  - { by: human:langej117, at: 2026-08-06T13:51:25-05:00 }
---

# Specimen 02 · Refuse the Class, Not the Case

Measures [pattern 02](../patterns/02-refuse-the-class.md).

# Computation

```bash
cd specimens/02-refuse-the-class
python3 probe.py            # offline, no key, no network
```

**Adjudication:** `narrowed` — whether the pattern's central claim survived measurement.

# What would falsify this

Measured on a boundary and space of this kind:

1. **A uniform-error boundary that is no more expensive to map.** If the ratio came out at or below
   1, the second half would be decoration. Observed: 10.7× and 55.1×, with the uniform run more
   expensive in 92.8% and 99.7% of seed pairs.
2. **A distinct-error boundary mapped in roughly the number of error classes.** This is what the
   pattern's "for free" implies, and it is the claim that did *not* survive. Observed: 2,298 probes
   against 6 error classes.
3. **A class refusal that is not smaller than the allowlist it replaces.** If refusing the class took
   as many rules and entries as filtering the cases, the first half would be a preference rather
   than an argument. Observed: 2 predicates and 0 entries against 6 and 18.
4. **An allowlist with no unintended acceptances.** The enumeration argument rests on the claim that
   a list of values plus a matcher admits things nobody listed. Observed: 36 of 166, from one
   `endswith`.
5. **A timing channel that is materially weaker than the message channel.** If constant messages with
   short-circuit evaluation had degraded the attack, "same string, same code" would be sufficient
   advice. Observed: identical probe counts, seed for seed.

# Full record

- [RESULTS.md](https://github.com/langej117/not-evidence/blob/main/specimens/02-refuse-the-class/RESULTS.md) — what was run, what came back, the scope, and the falsification condition
- [Specimen source](https://github.com/langej117/not-evidence/tree/main/specimens/02-refuse-the-class)
