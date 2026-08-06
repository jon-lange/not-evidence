---
pattern: 01
name: "Grounded or Refuse"
status: draft          # draft | field-tested | superseded-by: NN
refuses: "to answer without evidence"
specimen: none
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

In a system prompt this fails for a specific, non-obvious reason: **it asks the model to report on a
state it doesn't have.** There is no calibrated internal sense of whether retrieved context supports
a given clause — only a distribution over plausible continuations, in which "I don't know" competes
against fluent completions that score better.

The check has to be **structural** — did retrieval return anything, does the answer cite it, does the
cited span actually contain the claim — not **attitudinal**. You cannot instruct your way to
groundedness, for the same reason you cannot instruct your way past pattern 03.

A subtler version of the same error: measuring groundedness by asking a model whether its own answer
was grounded. That inherits everything above, plus pattern 05.

## Prior art

- Lewis et al., *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks* —
  [arXiv:2005.11401](https://arxiv.org/abs/2005.11401)
- Rashkin et al., *Measuring Attribution in Natural Language Generation Models* —
  [arXiv:2112.12870](https://arxiv.org/abs/2112.12870). The split between *plausible* and
  *attributable* is the whole pattern.
- NIST AI Risk Management Framework (AI 100-1) — on documenting system limits rather than obscuring them

## Specimen

None — prose is sufficient. The claim isn't contested. Treating refusal as a success outcome is the
part people skip.
