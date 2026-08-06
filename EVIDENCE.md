# Evidence

Every claim in this catalogue was put in front of a specimen before it was published. This page is
the short version: one line per pattern, the figure that came back, and a link to the working.

**Nothing here was measured anywhere but in this repository.** No figure is quoted from a system I
did not build for this catalogue — that rule is absolute and the reasoning is in
[METHOD.md](METHOD.md). Each specimen ships its harness, so every row is reproducible.

Where a row reports a **null** — nothing happened, nobody confabulated, the rate was flat — that is
the result, not a failed experiment. Three of the most useful rows below are nulls that contradicted
the pattern they were built to confirm.

| # | Pattern | What was measured | Result | Working |
|---|---|---|---|---|
| 01 | Grounded or Refuse | Confabulation under the naive *"say you don't know"* fix, 4 models, 148 completions | `0 out of 36` — the predicted failure never occurred | [RESULTS](specimens/01-grounded-or-refuse/RESULTS.md) |
| 02 | Refuse the Class, Not the Case | Three boundaries over a reference space of `48,000` items, accepted sets compared | Class refusal: 2 predicates, 0 table entries, 0 unintended accepts | [RESULTS](specimens/02-refuse-the-class/RESULTS.md) |
| 03 | Deterministic Over Prompted | A six-rung prompt-defence ladder against one poison document, 5 models, 140 calls | Converged to `0/20` at rung 4 — the ladder *did* close | [RESULTS](specimens/03-deterministic-over-prompted/RESULTS.md) |
| 04 | Meta-Injection Is Not Content-Relay | One good guardrail against two poison classes, 3 models | Meta-injection REFUSED; content-relay `RELAYED` by every model | [RESULTS](specimens/04-injection-classes/RESULTS.md) |
| 05 | The Judge Cannot Share a Family | 3 judges, 12 items, absolute then pairwise in both orders | Two judges produced `NO SIGNAL`; one flipped on 6 of 12 by position alone | [RESULTS](specimens/05-judge-family/RESULTS.md) |
| 06 | Refuse to Score Unratified Weights | The share of the weight simplex that reverses a real scorecard verdict | `40.6%` of defensible weightings pick the other candidate | [RESULTS](specimens/06-unratified-weights/RESULTS.md) |
| 07 | Gate Over-Refusal Separately | False-refusal rate across 5 models, 2 vendors, 25 items, oldest to newest | `flat — no difference`; the "newer models refuse more" claim did not reproduce | [RESULTS](specimens/07-over-refusal/RESULTS.md) |
| 08 | A Remembered Figure Is Never a Current Figure | Stale reuse of a remembered value across 6 conditions, 5 models, 117 calls | `3/10` — and only under the adversarial condition; the default was to call the tool | [RESULTS](specimens/08-remembered-is-not-current/RESULTS.md) |
| 09 | Keep New Modalities Off the Reasoning Path | Specimen 04's byte-identical payloads delivered as images, 4 vision models | `62/63` relay cells relayed; the guardrail refused every meta-injection in both channels | [RESULTS](specimens/09-modality-surface/RESULTS.md) |
| 10 | Never Auto-Commit a Lossy Transducer | Three transcription models against three inputs containing no speech | Invented content from silence, including `Merci d'avoir regardé!` | [RESULTS](specimens/10-lossy-transducer/RESULTS.md) |
| 11 | Green Is Not Evidence | One absence assertion across six variants, two of them silently broken | Two `NOT CAUGHT` cells — the test passed while the thing it guarded was broken | [RESULTS](specimens/11-mutation-check/RESULTS.md) |
| 12 | Distrust the Sanitization Label | Re-identification of a correctly-sanitised release, 60 projects, 62,700 trials | `60 / 60 rows re-linked, 0 wrong` from the numbers alone | [RESULTS](specimens/12-sanitization-label/RESULTS.md) |

## The four that contradicted their own pattern

These carry `revised-by-specimen`. The entry now states what the evidence supports; the original
prediction, and what happened to it, is in the specimen.

- **01** predicted that the naive fix confabulates. It did not — not once in 36 opportunities, across
  every model and both vendors. The entry now argues something different from what it set out to.
- **05** predicted a same-family judge would favour its own lineage. No ranking flip occurred, and
  the one signal that looked like self-preference dissolved when cross-family judges agreed with it.
  What *did* disqualify two of three judges was saturation and position instability — neither about
  lineage. The refusal was rewritten around those.
- **07** predicted that newer models within a family refuse more. Flat across both vendors, every
  vintage. The pattern's remaining claim is about measurement discipline, not about a trend.
- **08** predicted that agents substitute remembered figures for live ones. They called the tool
  instead — in 57 of 60 items. Only an explicitly adversarial condition produced stale reuse.

**This is the most useful thing in the repository.** A catalogue that only reports its confirmations
is telling you about its author's confidence, not about the world.

## Where a specimen cannot reach

Several patterns also make **architectural** commitments — claims about how a system should be
structured rather than predictions about how a model will behave. A specimen cannot test those, and
each `RESULTS.md` states which of its pattern's claims it exercised and which it did not.

Three specimens (04, 05, 10) do not yet carry an explicit falsification condition. That is a known
gap, not an oversight being hidden.

## Reproducing

```bash
make test     # every suite — no network, no keys
make demo     # every offline demonstration
```

Live probes are per-specimen, need credentials, and cost money. Each specimen's `RESULTS.md` ends
with exactly what to run.
