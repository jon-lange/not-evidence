---
type: Attested Computation
title: Specimen 08 · A Remembered Figure Is Never a Current Figure
description: The measurement behind pattern 08.
resource: https://github.com/jon-lange/not-evidence/tree/main/specimens/08-remembered-is-not-current
tags: [specimen, measurement, live]
runtime: python
executor:
  resource: https://github.com/jon-lange/not-evidence/blob/main/specimens/08-remembered-is-not-current/probe.py
  receipt: [results_jsonl, stdout, exit_code]
attester:
  resource: https://github.com/jon-lange/not-evidence/blob/main/scripts/check-consistency.py
adjudication: central-claim-failed
generated: { by: human:jon-lange, at: 2026-08-06T13:51:25-05:00 }
verified:
  - { by: process:emit-okf/0.1, at: 2026-08-06T13:51:25-05:00 }
  - { by: human:jon-lange, at: 2026-08-06T13:51:25-05:00 }
---

# Specimen 08 · A Remembered Figure Is Never a Current Figure

Measures [pattern 08](../patterns/08-remembered-is-not-current.md).

# Computation

```bash
cd specimens/08-remembered-is-not-current
python3 probe.py            # live: needs credentials, costs money
```

**Adjudication:** `central-claim-failed` — whether the pattern's central claim survived measurement.

# What would falsify this

**Restore it:** a system where memory and a live tool are pooled into one retrieval step, ranked by
similarity, and a stale figure is served as current under ordinary framing — no discouragement, no
removed freshness cue. That is the configuration the pattern's *naive approach* section describes,
and this specimen did **not** build it: the tool here is a first-class function call, not a retrieved
passage competing with a transcript for rank. Building the shared-index version is the obvious next
experiment, and the one most likely to reproduce the claim.

**Falsify it further:** a run where the `discouraged` condition also produces 0/10. That would say
the effect measured here is an artefact of two older models rather than a live failure mode.

# Full record

- [RESULTS.md](https://github.com/jon-lange/not-evidence/blob/main/specimens/08-remembered-is-not-current/RESULTS.md) — what was run, what came back, the scope, and the falsification condition
- [Specimen source](https://github.com/jon-lange/not-evidence/tree/main/specimens/08-remembered-is-not-current)
