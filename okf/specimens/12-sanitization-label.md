---
type: Attested Computation
title: Specimen 12 · Distrust the Sanitization Label
description: The measurement behind pattern 12.
resource: https://github.com/jon-lange/not-evidence/tree/main/specimens/12-sanitization-label
tags: [specimen, measurement, offline]
runtime: python
executor:
  resource: https://github.com/jon-lange/not-evidence/blob/main/specimens/12-sanitization-label/probe.py
  receipt: [results_jsonl, stdout, exit_code]
attester:
  resource: https://github.com/jon-lange/not-evidence/blob/main/scripts/check-consistency.py
adjudication: narrowed
generated: { by: human:jon-lange, at: 2026-08-06T13:51:25-05:00 }
verified:
  - { by: process:emit-okf/0.1, at: 2026-08-06T13:51:25-05:00 }
  - { by: human:jon-lange, at: 2026-08-06T13:51:25-05:00 }
---

# Specimen 12 · Distrust the Sanitization Label

Measures [pattern 12](../patterns/12-distrust-the-sanitization-label.md).

# Computation

```bash
cd specimens/12-sanitization-label
python3 probe.py            # offline, no key, no network
```

**Adjudication:** `narrowed` — whether the pattern's central claim survived measurement.

# What would falsify this

Any of the following, measured on a corpus generated the way this one was:

1. **A naive release that does not re-link.** If substituting names and shuffling rows left the
   published records un-joinable to their originals by exact numeric match, cell 1 is wrong. Observed:
   60/60.
2. **A partial series that stays ambiguous.** If a fragment amounting to a fifth of a series matched
   many entities rather than one — say, uniqueness below 50% at k = 4 in a fleet of sixty — the claim
   that a series is a fingerprint is unsupported. Observed: 100% at k = 4, 96% at k = 2.
3. **A noisy adversary at chance.** If holding an *independently measured* fragment gave no advantage
   — that is, if only verbatim values re-linked — then cell 2 would be a statement about exact
   duplicates rather than about series, and the pattern's second section would be a tautology dressed
   as a finding. Observed: 82% at k = 4, holding no value present in the release.
4. **Provenance that is not a key.** If retained provenance strings were categorical rather than
   1:1 — an environment name shared by hundreds of rows — cell 3 is a much weaker claim. Observed:
   60 distinct run ids in 60 rows, re-linking a fully regenerated release at 100%.
5. **A configuration that defeated the attack while preserving per-project utility.** This is the one
   that would most change the advice, because it would mean the trade-off in the last table is an
   artefact of the four sanitisers tried rather than a real cost. Not observed here — but four
   sanitisers is not a search, and this is the falsification I would most expect someone to deliver.

# Full record

- [RESULTS.md](https://github.com/jon-lange/not-evidence/blob/main/specimens/12-sanitization-label/RESULTS.md) — what was run, what came back, the scope, and the falsification condition
- [Specimen source](https://github.com/jon-lange/not-evidence/tree/main/specimens/12-sanitization-label)
