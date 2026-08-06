---
pattern: 05
name: "The Judge Cannot Share a Family"
status: revised-by-specimen   # draft | field-tested | revised-by-specimen | superseded-by: NN
refuses: "to let a same-lineage judge gate a promotion"
specimen: 05-judge-family
---

# 05 · The Judge Cannot Share a Family

> **Refuses to let a same-lineage judge gate a promotion.**

## Context

You are using one model to score another's output, and the score gates something — a prompt change
ships or it doesn't, a model swap is approved or it isn't, a release is blocked or cleared.

The judge is a component of your release process. It has the authority of a test suite and none of
the determinism.

## Forces

**Judging with a related model is the path of least resistance.** Same SDK, same key, same latency
profile, same billing relationship. Often the same model with a different prompt.

**"Use a smaller model of the same family" feels like the responsible compromise.** It's cheap, it
sounds neutral, and it looks like you have thought about cost.

**Self-preference is mechanistically real.** There is evidence that evaluator models recognise their
own generations and rate them more favourably, and the effect is tied to that self-recognition rather
than to quality.

**But bias is not the only thing that invalidates a judge, and rarely the first.** A judge can be
perfectly unbiased and still useless — saturated, or unstable under reordering, or both.

## The Refusal

**Before a judge may gate anything, prove it produces a signal and that its verdict survives
reordering. Only then does whose lineage it shares become the question.**

Three checks, in this order — and the order is the pattern. The first two are cheap, and in practice
they disqualify judges long before bias does.

1. **Does the judge discriminate?** Score your candidates and look at the distribution of raw
   verdicts. A judge that returns the same score for everything has produced no measurement, and its
   equal means are the *absence* of a result, not a considered tie. Report it as no-signal and stop.
2. **Is the verdict stable under reordering?** For any pairwise comparison, run both orders. A judge
   that picks whichever answer came first has expressed a position preference. Combine the orders;
   count the flips; treat a high flip rate as a disqualification, not a footnote.
3. **Does the choice of judge change the winner?** This is the **ranking-flip test**. Rank your
   candidates under each judge and under the panel. If the winner depends on who judged, judge
   independence is decision-critical for that comparison and no single-judge promotion can stand.

**Then, and only then, lineage.** A judge sharing a model family with its subject can favour it —
evaluator models recognise their own generations and rate them more favourably. Exclude the subject's
lineage from the judge set that gates promotion.

The asymmetry that gets missed: cross-family is a property of an *ordered pair*, not a pair. A judge
can be free of self-preference toward a subject and still be systematically lenient. Trust is earned
per direction — A judging B may be authoritative while B judging A stays advisory.

**A saturated judge and an unbiased judge produce identical aggregates.** Equal means are the absence
of a measurement, not a considered tie, and no amount of care about lineage recovers a run where the
judge never discriminated. That is why checks 1 and 2 come first.

## Consequences

**You need a validated judge per subject family.** Onboarding a new subject means validating a new
judge before it can gate anything — real work, and the cost of the rule.

**Panel diversity beats panel size.** Aggregation gains collapse when panellists share error
structure; three variants of one lineage re-vote the same bias. Buy family diversity, not headcount,
and expect a cost multiplier per panellist — which is why panels belong in audit runs, not every CI run.

**A judge change is a production change.** Roll a new judge shadow → canary → authoritative, with the
incumbent as default until the numbers earn the swap. A judge that wrongly passes an unsafe answer is
an incident with no alarm attached.

**Agreement is reliability, not validity.** A panel can be reliably wrong. Validity needs a
hand-labelled reference set; agreement between judges only tells you they fail the same way.

## The naive approach it beats

**"Use the same family, one tier down."** Cheap, available, and the single worst option: shared
tokeniser, shared lineage, shared stylistic priors. It maximises exactly the familiarity that drives
self-preference. It is the mitigation most likely to be chosen and least likely to work.

**And the more common one: reading equal means as a considered tie.** A judge that scored every
candidate identically has produced no measurement, but it emits the same aggregate a careful tie
would. Harnesses report a winner from it, because nothing in the mean says which it was. That is
[pattern 11](11-green-is-not-evidence.md) in a different costume — a result whose healthy form and
broken form are the same number.

## Prior art

- Panickssery et al., *LLM Evaluators Recognize and Favor Their Own Generations* —
  [arXiv:2404.13076](https://arxiv.org/abs/2404.13076). The self-recognition mechanism the rule exists
  to remove.
- Zheng et al., *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena* —
  [arXiv:2306.05685](https://arxiv.org/abs/2306.05685). Position bias in LLM judges, and why both
  orders must be run.

## Specimen

[`specimens/05-judge-family/`](../specimens/05-judge-family/) — **built.**
Measured output in [`RESULTS.md`](../specimens/05-judge-family/RESULTS.md).

Two candidates from different model families, twelve questions, three judges — two from one family,
one from the other. Absolute scoring, then pairwise in both orders.

**Checks 1 and 2 disqualified two of three judges before lineage was reachable.** Both judges from
one family awarded a perfect score to all 24 answers — one distinct value across the entire run, no
measurement at all. A third flipped its verdict on half the items depending purely on answer order,
while another flipped on none.

**Absolute scoring saturates; pairwise cannot.** On a competent task set every answer earns full
marks and the judge stops carrying information. Forcing a choice removes the ceiling — and introduces
position bias, which is why both orders must be run.

**One pass is not enough to read the result.** Absolute scoring showed a judge rating its own family
higher, the shape of self-preference. Pairwise showed both cross-family judges preferring the same
candidate, unanimously — so the simplest reading consistent with all six measurements is that those
answers were better and everyone noticed.

Scope in RESULTS.md: twelve items, one rubric, one day, no hand-labelled reference set.
