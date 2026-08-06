---
pattern: 01
name: "Grounded or Refuse"
status: revised-by-specimen   # draft | field-tested | revised-by-specimen | superseded-by: NN
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

**Answer only from evidence retrieved this turn, and cite it so the answer is checkable by someone
who does not trust the system. When retrieval returns nothing sufficient, decline — and say what was
missing.**

The reason is auditability, not distrust of the model. Current models decline well on
straightforward lookups: measured across four models on questions whose answers were absent from the
corpus, none confabulated. **That is a property of this year's post-training, not of your system.**
It is not visible in your logs, does not transfer to longer contexts or answers reached by
synthesis, and can change with the next model you deploy.

A cited span is *checkable*. Behaviour that happens to be good is being taken on faith.

Three parts, all load-bearing:

1. **This turn.** Evidence from an earlier turn is a fact about that turn. See pattern 08.
2. **Cite it.** An uncited answer is unfalsifiable, however correct it happens to be.
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

**Not because it fails to produce refusals** — on straightforward lookups it produces them reliably.
Because it produces them *unaccountably*.

An attitudinal prompt asks the model to report on a state it does not have: there is no calibrated
internal sense of whether retrieved context supports a clause, only a distribution over plausible
continuations. When it declines correctly, that is a fact about the model's training, not about your
system. You cannot see it in a log, cannot point a reviewer at it, and cannot tell whether it still
holds after a model upgrade. **The failure mode is not confabulation. It is that you would not know.**

The structural check — did retrieval return anything, does the answer cite it, does the cited span
contain the claim — produces the same refusals *and* an artefact. That artefact is the entire
difference.

Two related errors worth naming:

- **Measuring groundedness by asking a model whether its own answer was grounded.** Inherits
  everything above, plus pattern 05.
- **Treating a low confabulation rate as coverage.** It measures the questions you asked, on the
  context lengths you tested, against the model you tested. Longer assembled contexts and answers
  reached by synthesis are a different regime, and nothing about a good rate on lookups predicts it.

## Prior art

- Lewis et al., *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks* —
  [arXiv:2005.11401](https://arxiv.org/abs/2005.11401)
- Rashkin et al., *Measuring Attribution in Natural Language Generation Models* —
  [arXiv:2112.12870](https://arxiv.org/abs/2112.12870). The split between *plausible* and
  *attributable* is the whole pattern.
- NIST AI Risk Management Framework (AI 100-1) — on documenting system limits rather than obscuring them

## Specimen

[`specimens/01-grounded-or-refuse/`](../specimens/01-grounded-or-refuse/) — **built.**
Measured output in [`RESULTS.md`](../specimens/01-grounded-or-refuse/RESULTS.md).

Four models across two vendors, thirteen questions over an authored corpus, including a class where
retrieval returns a document that names the concept and never states the value. Two configurations:
an attitudinal prompt, and a structural check that verifies the cited span contains the claim.

**Confabulation was 0 of 36 in both.** On lookup-shaped questions with short context, current models
decline correctly without being made to — which is why this entry argues auditability rather than
confabulation risk. The structural check's forced-refusal path never fired: it was not needed, and
it was not therefore proven to work.

Six scope limits are recorded in RESULTS.md. The binomial upper bound on 0/36 is about 8%, which
rules out a large effect on this shape and not a small one.
