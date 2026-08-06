---
pattern: 05
name: "The Judge Cannot Share a Family"
status: draft          # draft | field-tested | superseded-by: NN
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

**But bias is not the only thing that invalidates a judge,** and — see below — it may not even be
the most common. A judge can be perfectly unbiased and still useless.

## The Refusal

**A judge that gates a promotion must not share a model family with the system it is judging — and
before you trust any judge, prove it produces a signal.**

Three checks, in this order. The first two are cheap and catch more in practice than the third.

1. **Does the judge discriminate?** Score your candidates and look at the distribution of raw
   verdicts. A judge that returns the same score for everything has produced no measurement, and its
   equal means are the *absence* of a result, not a considered tie. Report it as no-signal and stop.
2. **Is the verdict stable under reordering?** For any pairwise comparison, run both orders. A judge
   that picks whichever answer came first has expressed a position preference. Combine the orders;
   count the flips; treat a high flip rate as a disqualification, not a footnote.
3. **Does the choice of judge change the winner?** This is the **ranking-flip test**. Rank your
   candidates under each judge and under the panel. If the winner depends on who judged, judge
   independence is decision-critical for that comparison and no single-judge promotion can stand.

The flip test is the decisive one because it is binary, cheap, and runs on data you already have. It
converts an abstract argument about bias into a result.

**And the asymmetry that gets missed:** cross-family is a property of an *ordered pair*, not a pair.
A judge can be free of self-preference toward a subject and still be systematically lenient. Trust is
earned per direction — A judging B may be authoritative while B judging A stays advisory.

## Consequences

**You need a validated judge per subject family,** and onboarding a new subject family means
validating a new judge before it can gate anything. That is real work and it is the cost of the rule.

**Panel diversity beats panel size.** Aggregation gains collapse when panellists share error
structure; three variants of one lineage re-vote the same bias. Buy family diversity, not headcount —
and expect a latency and cost multiplier per panellist, which is why panels belong in audit runs
rather than every CI run.

**A judge change is a production change.** If the eval gates promotion, the eval's own configuration
is production-critical. Roll a new judge shadow → canary → authoritative, with the incumbent as
default until the numbers earn the swap. A judge that wrongly passes an unsafe answer is an incident
with no alarm attached.

**Agreement is reliability, not validity.** A panel can be reliably wrong. Establishing validity needs
a hand-labelled reference set — agreement between judges only tells you they fail the same way.

## The naive approach it beats

**"Use the same family, one tier down."** Cheap, available, and the single worst option: shared
tokeniser, shared lineage, shared stylistic priors. It maximises exactly the familiarity that drives
self-preference. It is the mitigation most likely to be chosen and least likely to work.

**And the one this pattern's own specimen caught: trusting a judge that never discriminated.** Two of
three judges in that run scored every answer identically, and the harness reported a winner from them
anyway because equal means look like a tie. They were not a tie. They were nothing. A saturated judge
and an unbiased judge produce output that is indistinguishable at the aggregate — which is the same
failure as [pattern 11](11-green-is-not-evidence.md), in a different costume.

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

**The specimen did not confirm this pattern's central claim, and says so.** Across two families and
three judges there was no ranking flip: every judge that resolved a winner picked the same candidate,
and an apparent +1.00 self-preference in absolute scoring dissolved once cross-family judges agreed
with it.

What the run did establish is checks 1 and 2 above, neither of which was in this entry's first draft:
two of three judges were saturated and produced no signal, and one flipped its verdict on half the
items depending on answer order. Those are the failures that showed up first, and the entry was
rewritten around them.

The status stays `draft` for that reason. The cross-family rule remains well-supported in the
literature and unproven here.
