---
type: Attested Computation
title: Specimen 11 · Green Is Not Evidence
description: The measurement behind pattern 11.
resource: https://github.com/jon-lange/not-evidence/tree/main/specimens/11-mutation-check
tags: [specimen, measurement, offline]
runtime: python
executor:
  resource: https://github.com/jon-lange/not-evidence/blob/main/specimens/11-mutation-check/probe.py
  receipt: [results_jsonl, stdout, exit_code]
attester:
  resource: https://github.com/jon-lange/not-evidence/blob/main/scripts/check-consistency.py
adjudication: confirmed
generated: { by: human:jon-lange, at: 2026-08-06T13:51:25-05:00 }
verified:
  - { by: process:emit-okf/0.1, at: 2026-08-06T13:51:25-05:00 }
  - { by: human:jon-lange, at: 2026-08-06T13:51:25-05:00 }
---

# Specimen 11 · Green Is Not Evidence

Measures [pattern 11](../patterns/11-green-is-not-evidence.md).

# Computation

```bash
cd specimens/11-mutation-check
python3 probe.py            # offline, no key, no network
```

**Adjudication:** `confirmed` — whether the pattern's central claim survived measurement.

# What would falsify this

A refactor-induced vacuum that some ordinary, generally-recommended assertion reliably catches
without anyone having anticipated that specific refactor. Cell 2b was built to be exactly that
counter-example and it survives the obvious witness — but the search was not exhaustive.

# Full record

- [RESULTS.md](https://github.com/jon-lange/not-evidence/blob/main/specimens/11-mutation-check/RESULTS.md) — what was run, what came back, the scope, and the falsification condition
- [Specimen source](https://github.com/jon-lange/not-evidence/tree/main/specimens/11-mutation-check)
