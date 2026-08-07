---
type: Attested Computation
title: Specimen 10 · Never Auto-Commit a Lossy Transducer
description: The measurement behind pattern 10.
resource: https://github.com/langej117/not-evidence/tree/main/specimens/10-lossy-transducer
tags: [specimen, measurement, live]
runtime: python
executor:
  resource: https://github.com/langej117/not-evidence/blob/main/specimens/10-lossy-transducer/probe.py
  receipt: [results_jsonl, stdout, exit_code]
attester:
  resource: https://github.com/langej117/not-evidence/blob/main/scripts/check-consistency.py
adjudication: narrowed
generated: { by: human:langej117, at: 2026-08-06T14:00:52-05:00 }
verified:
  - { by: process:emit-okf/0.1, at: 2026-08-06T14:00:52-05:00 }
  - { by: human:langej117, at: 2026-08-06T14:00:52-05:00 }
---

# Specimen 10 · Never Auto-Commit a Lossy Transducer

Measures [pattern 10](../patterns/10-never-auto-commit-a-transducer.md).

# Computation

```bash
cd specimens/10-lossy-transducer
python3 probe.py            # live: needs credentials, costs money
```

**Adjudication:** `narrowed` — whether the pattern's central claim survived measurement.

# What would falsify this

The entry's claim is that a lossy transducer's output must reach a review buffer rather than an
execution path, and the revised specimen claim is that a hint gives the transducer material to emit
when there is nothing to transcribe.

**Falsify the invention result:** a transcription model that returns empty for all three non-speech
inputs, bare *and* hinted, reproduced across runs. One such model does not overturn the pattern —
`gpt-4o-mini-transcribe` already returns empty when unprompted and stops the moment a hint arrives —
but a model that holds empty under a hint would show the failure is a vendor defect rather than a
property of generative transduction. If most current models did that, the pattern is arguing about a
fixed bug.

**Falsify the auto-commit refusal, which is the load-bearing claim:** a gate that reliably separates
invented output from real transcription without a human in the path. This run measured a level gate
as necessary and not sufficient — the speech-level tone cleared −40 dBFS and still produced
`'Mise en place.'`. A confidence score, a logprob threshold, or a second transducer used as a check,
shown to catch the invented cells while passing genuine speech, would make auto-commit defensible at
some risk tier and narrow the pattern to the tiers above it.

**What would not falsify it:** better average accuracy. The pattern is about the consequence of the
single wrong commit, not about the rate, and `'Mise en place.'` is the cell that matters precisely
because it is short, fluent, grammatical, on-topic, and indistinguishable from a real result.

**Not runnable from the recorded data.** Both conditions above need new calls — a different model set
for the first, and a scoring signal this harness does not currently capture for the second. Unlike
07's, this falsification cannot be re-derived from `results.jsonl` by re-classifying.

# Full record

- [RESULTS.md](https://github.com/langej117/not-evidence/blob/main/specimens/10-lossy-transducer/RESULTS.md) — what was run, what came back, the scope, and the falsification condition
- [Specimen source](https://github.com/langej117/not-evidence/tree/main/specimens/10-lossy-transducer)
