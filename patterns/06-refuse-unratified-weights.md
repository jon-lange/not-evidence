---
pattern: 06
name: "Refuse to Score Unratified Weights"
status: field-tested   # draft | field-tested | superseded-by: NN
refuses: "to produce a number the domain owner never endorsed"
specimen: 06-unratified-weights
---

# 06 · Refuse to Score Unratified Weights

> **Refuses to produce a number the domain owner never endorsed.**

## Context

An evaluation produces results per dimension — correctness, completeness, format compliance, tone.
Then something collapses them into a single score, because decisions consume single numbers.

That collapse requires weights, and the weights are the whole of the sentence *"this is good
enough"*: that a formatting failure is survivable and a factual one is not. None of it is knowable
from the harness. It is known by whoever owns the quality bar — the person who will be asked to
defend an output when it turns out to be wrong.

## Forces

**The score is needed before the owner is available.** The gap between *we need a number today* and
*the owner has an hour next week* is what a placeholder fills.

**Weights look like configuration.** Same file as batch size and retry count, same syntax, same
reviewers. Nothing marks one field as an engineering parameter and another as a policy decision
wearing a float.

**A number, once produced, travels** — into a summary, a review, a slide — stripped of its
provenance and carrying the system's authority.

**Ratification is slow and socially expensive.** Endorsing a weighting means owning its consequences,
which is why it is worth doing and why it gets deferred.

## The Refusal

**If the weighting has not been ratified by the person who owns the quality bar, the scoring run
fails. It does not warn, and it does not fall back to a default.**

Three parts, all load-bearing:

1. **Fails, not warns.** The difference is not severity, it is *audience*: a warning reaches the
   engineer reading the log, who already knows and cannot fix it. Only the narrower half is
   demonstrable — a warning **cannot** reach the right audience, because it emits an artefact
   byte-identical to the clean one and names nobody. That a failure reliably *does* reach them is a
   claim about people this entry does not evidence.
2. **No default weighting.** Downstream, a default is indistinguishable from a considered weighting.
   Equal weights are not neutral: they claim every dimension matters identically, which is rarely
   true and has never once been argued.
3. **Ratified against a specific version.** Sign-off is a claim about particular numbers, not the
   concept of weighting. Record who ratified what; any edit invalidates the record and re-fails the
   run.

Consulting the domain owner is a practice, and practices degrade under deadline. A stopped run is a
fact, and it gets resolved by the person who should have been consulted.

## Consequences

**The weighting acquires a named owner** — the actual deliverable; the number is a by-product. Asked
*who decided completeness was worth double?*, there is an answer other than "the harness".

**You are visibly blocked on someone else's calendar,** and teams will experience the tool as
obstructive. It is, and that is the design.

**The argument happens before the number exists.** Disagreement about weights is cheap while the
score is hypothetical and expensive once it is quoted in decisions.

**You lose the casual exploratory run** — unless you split the outputs: emit per-dimension results
freely, refuse only the aggregate. Nobody mistakes a table of dimensions for a verdict.

**The control buys nothing where there is no trade-off.** Where one candidate is better on every
dimension, no weighting flips the winner — and you cannot know which kind of scorecard you have
without computing the flip share first. That computation, not the gate, is what to reach for on day
one.

## The naive approach it beats

**Ship a plausible default weighting with a `TODO: confirm with the domain owner`.**

Genuinely attractive: it unblocks the run, it is honest in the source, and it feels provisional. But
**the number is immediately useful, so it is immediately used**, and use fixes it in place. Revising
the weights would mean revising every decision already justified by the old ones, so "we'll tune them
later" grows more expensive until it is abandoned.

The second failure is endorsement: a default is read as a choice, and the more polished the reporting
the less provisional it looks. A variant fails the same way — show the domain owner the *scores* and
ask them to confirm the weights afterwards, which is negotiation with a result rather than
ratification of a quality bar.

The tell: ask three people who chose the weights. Three answers, or a shrug, and the number in
circulation has no owner and never did.

## Prior art

- Keeney & Raiffa, *Decisions with Multiple Objectives: Preferences and Value Tradeoffs* (Wiley,
  1976) — weights in a multi-attribute score are *elicited value judgements* belonging to the
  decision maker, not parameters for the analyst to assume
- *Software Engineering at Google*, ch. 20, "Static Analysis" —
  [abseil.io/resources/swe-book/html/ch20.html](https://abseil.io/resources/swe-book/html/ch20.html).
  "We have found repeatedly that developers ignore compiler warnings," so: error and break the
  build, or don't show it at all.
- Johnson & Goldstein, *Do Defaults Save Lives?*, Science 302 (2003), 1338–1339 —
  [doi:10.1126/science.1091721](https://doi.org/10.1126/science.1091721). Defaults dominate outcomes
  and are read as implicit recommendations.

## Specimen

[`specimens/06-unratified-weights/`](../specimens/06-unratified-weights/) — **built.**
Measured output in [`RESULTS.md`](../specimens/06-unratified-weights/RESULTS.md).

Offline and exact rather than sampled: the winner is the sign of `delta·w`, so the flip share has a
closed form. Monte Carlo agrees within 1.7 standard errors across nine cells.

**On a realistic scorecard with genuine trade-offs, 40.6% of the weight simplex picks the candidate
equal weights reject.** Concretely: move **3.7 points of weight** from one dimension to another and
the decision reverses.

The gate refuses five ways and the warning version emits a byte-identical clean artefact in all five:
no ratification record, weights edited by 0.01 since sign-off, the dimension set changed, and an
engineer ratifying their own weighting.

**The boundary the entry did not state:** where one candidate dominates every dimension, the flip
share is exactly zero and the control is worthless. And the flip share is not a property of the
scorecard alone — it is scorecard × measure, ranging 40.6% to 1.9% across plausible priors. Choosing
that measure is the same unargued act one level up, and the specimen has no principled measure to
recommend.
