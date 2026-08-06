---
pattern: 01
name: "Grounded or Refuse"
status: draft          # draft | field-tested | superseded-by: NN
refuses: "to answer without evidence"
specimen: 01
---

# 01 · Grounded or Refuse

> **Refuses to answer without evidence.**

## Context

A system answers questions over a corpus, a set of tools, or both. The generator can always produce
fluent, well-formed, plausible text — that capability is unconditional. Whether the text is
*entailed by anything the system actually retrieved this turn* is a separate question, and nothing
on the output surface distinguishes the two cases.

This matters wherever being wrong has a consequence beyond disappointment: someone acts on it,
files it, forwards it, or gets audited on it.

## Forces

**Answering is measured; grounding is not.** Coverage is trivial to instrument. Groundedness needs
a judgement per claim. Whichever you measure is the one that gets optimised.

**Model confidence carries no information about grounding.** Fluency and confidence are properties
of generation. They are produced identically whether the context supported the claim or not. There
is no signal in the output that says *this clause came from the document*.

**Users prefer a wrong answer to no answer** — right up until it costs them, at which point the
preference reverses, retroactively, and in public.

## The Refusal

**Answer only from evidence retrieved this turn, and cite it. When retrieval returns nothing
sufficient, decline — and say what was missing.**

Three parts, all load-bearing:

1. **This turn.** Evidence from an earlier turn is a fact about that turn. See pattern 08.
2. **Cite it.** An uncited answer is unfalsifiable. The citation is what lets someone who does not
   trust the system check it — the only kind of checking that counts.
3. **Decline explicitly.** Not a hedge; not a confident general answer with the specifics quietly
   omitted. Those are this failure mode wearing a disguise.

**Refusal is a success outcome.** If your telemetry files it under errors, the team will optimise it
away — correctly, given what you told them to measure.

## Consequences

**You get a checkable system.** Every answer carries its own audit trail, and failures become
countable events instead of silent ones.

**You get a real refusal rate,** higher than anyone expects. It is politically awkward and
diagnostically excellent: it measures corpus coverage rather than model quality, and it points
directly at where to invest.

**You take on an obligation.** The moment refusal is a first-class outcome, it becomes something the
system can overproduce. Pattern 07 exists because of this one.

**You give up graceful vagueness.** Questions the system used to half-answer it now declines
outright. That is the trade, stated plainly.

## The naive approach it beats

> *"If you're not sure, say you don't know."*

The argument against it is that **it asks the model to report on a state it doesn't have.** There is
no calibrated internal sense of whether retrieved context supports a given clause — only a
distribution over plausible continuations, in which "I don't know" competes against fluent
completions that score better. So the check has to be **structural** — did retrieval return
anything, does the answer cite it, does the cited span actually contain the claim.

**Specimen 01 tested that prediction and it did not hold.** Four models across two vendors, thirteen
questions, including a class where retrieval returns a document that names the concept and never
states the value. The bare attitudinal prompt confabulated **0 out of 36 times**, and refused while
naming what was missing. The structural check's forced-refusal path never fired, because nothing
arrived that needed catching.

The scope is narrow and friendly to the naive fix: a few hundred words of context, lookup-shaped
questions, no competing instruction to be helpful, one sample per cell, current-generation models.
It rules out a large effect on that shape, not a small one, and says nothing about long assembled
contexts or answers reached by synthesis. But the honest statement today is that **on easy shapes,
recent post-training does much of what this pattern says only structure can do** — and that a claim
this section made confidently was, when measured, wrong.

What survives the result is the reason to prefer structure anyway: a cited, verifiable span is
*checkable by someone who does not trust the system*, and an attitudinal prompt that happens to
behave well is not. Groundedness you cannot audit is a property you are taking on faith, whatever
the refusal rate looks like.

A subtler version of the original error is untouched: measuring groundedness by asking a model
whether its own answer was grounded. That inherits everything above, plus pattern 05.

## Prior art

- Lewis et al., *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks* —
  [arXiv:2005.11401](https://arxiv.org/abs/2005.11401)
- Rashkin et al., *Measuring Attribution in Natural Language Generation Models* —
  [arXiv:2112.12870](https://arxiv.org/abs/2112.12870). The split between *plausible* and
  *attributable* is the whole pattern.
- NIST AI Risk Management Framework (AI 100-1) — on documenting system limits rather than obscuring them

## Specimen

**[01-grounded-or-refuse](../specimens/01-grounded-or-refuse/)** — the naive fix, tested head-on
against four models on two vendors over an authored corpus with a class of questions whose answers
are adjacent to the retrieved documents but absent from them.

**It measured 0/36 confabulations for the attitudinal prompt and contradicted this entry's
prediction.** The result and its six scope limits are in
[RESULTS.md](../specimens/01-grounded-or-refuse/RESULTS.md); `status` stays `draft` because of it.
