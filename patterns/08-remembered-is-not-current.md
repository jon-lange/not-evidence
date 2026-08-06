---
pattern: 08
name: "A Remembered Figure Is Never a Current Figure"
status: revised-by-specimen   # draft | field-tested | revised-by-specimen | superseded-by: NN
refuses: "to let a stored value stand in for a live one"
specimen: 08-remembered-is-not-current
---

# 08 · A Remembered Figure Is Never a Current Figure

> **Refuses to let a stored value stand in for a live one.**

## Context

A system accumulates context about its user: preferences, prior answers, a document attached three
weeks ago. It also answers from live sources, under pattern 01. Both ship together, described
the same way — *we give the model more context*.

Then someone asks how many nodes are in the staging pool. The answer was given last Tuesday, and it is
sitting in the history.

## Forces

**Reuse is the whole value proposition, and it is right for some things and wrong for others.** Reusing
a preference is the feature working; reusing a *figure* substitutes an old world-state for the current
one.

**Memory and grounding feel like allies.** Both are arrows into the prompt, so the boundary between
them is never designed — it emerges from whichever retrieval path ran first.

**Staleness is invisible at the output.** The sentence reads identically whether the number came from a
live call or a transcript written in March.

## The Refusal

**A remembered or document-derived value may shape presentation and may supply tool parameters. It may
never substitute for a live value.**

The line is what the stored item is *doing*:

- **Shaping presentation** — this user wants terse output. It changes the frame, not the fact.
- **Supplying parameters** — "the usual pool" means a specific one; the call still happens.
- **Standing in for the fact** — the node count from last Tuesday's transcript. Forbidden, however
  recent.

**A number read from a stored artefact is a fact about that artefact, not a fact about the world.**
*"The report says the pool holds forty nodes"* is checkable; *"the pool holds forty nodes"* is a claim
about now, which no document can support.

Combined questions show this. *"Show me the queue depth the way you showed me last time"*: format from
memory, depth from a call. If the call fails, refuse the value and honour the format.

**What drives substitution is the cost of the live path, not the convenience of memory.** A stale
figure one line above the question is ignored when the tool is cheap; describe it as slow, rate-limited
and billed, and reuse appears immediately. Retry budgets and "prefer cached" hints are where this is
violated.

**A third outcome sits between substituting a figure and attributing it: silently discarding it.** The
system answers correctly and never mentions that the user's document said otherwise — the majority
behaviour when measured, splitting by vendor. Surfacing that divergence is a separate requirement.

### The second refusal: inferred facts may be suggested, never silently saved

A stated preference — *"always give me the short version"* — can be stored, with a visible, reversible
record. One the system *inferred* is different: **anything inferred about the user is surfaced for
confirmation before storage, whatever the classifier's confidence.** Confidence is not consent; a
high-confidence wrong inference is the worse one, applied more readily and shaping every answer while
the user never sees the premise.

## Consequences

**Some answers get slower, and some unavailable when the source is down.** An unreachable source means
an unknown value, and pattern 01 says what to do with one.

**Every stored item needs a type** — preference, parameter, or claim-about-an-artefact — carried in the
storage layer, because a model reading a string cannot recover it at read time. The payoff is a memory
with a provenance per line.

**You lose the better demo.** The instant answer beats the pause to check, until the number is stale
and someone acts on it.

## The naive approach it beats

**One retrieval step that pools memory, attachments, and live sources into a single ranked context, and
lets the model decide** — one code path instead of three, and the shape every tutorial builds.

**Ranking is by similarity, and a stale figure is maximally similar to the question that asks for it.**
A transcript saying *"the pool holds forty nodes"* often matches *"how many nodes are in the pool?"*
better than the tool schema that would fetch the true answer. Retrieval has no notion of freshness to
rank on, and downstream every item is text with a score.

The tell: memory store and document store sharing an embedding index. If they do, the substitution is
the design, working as specified.

## Prior art

- Vu et al., *FreshLLMs: Refreshing Large Language Models with Search Engine Augmentation* —
  [arXiv:2310.03214](https://arxiv.org/abs/2310.03214). The gap between what a system holds and what is
  currently true.
- Amershi et al., *Guidelines for Human-AI Interaction*, CHI 2019 —
  [doi:10.1145/3290605.3300233](https://dl.acm.org/doi/10.1145/3290605.3300233). G12 (*remember recent
  interactions*) and G17 (*provide global controls*): the two halves this pattern ships together.
- Nissenbaum, *Privacy as Contextual Integrity*, 79 Wash. L. Rev. 119 (2004) — why a fact learned in
  one context is not thereby available in another. The basis of the second refusal.

## Specimen

[`specimens/08-remembered-is-not-current/`](../specimens/08-remembered-is-not-current/) — **built.**
Measured output in [`RESULTS.md`](../specimens/08-remembered-is-not-current/RESULTS.md).

Five models, two vendors, six conditions, 60 items. Ground truth is the tool's own invocation log,
not a judge.

**With a cheap, obvious tool, substitution does not happen: 0 of 50 across five conditions.** A dated
figure for exactly the thing asked, one line above the question, changed nothing. Combined questions
were split correctly, unprompted, 10 out of 10.

**Make the tool look expensive and it appears immediately.** A sixth condition described the tool as
slow, rate-limited and billed and dropped the "right now" cue: reuse at 3 of 10, entirely in the two
oldest models.

**Scope.** The agent had a first-class tool with an enum naming the metric — the arrangement most
favourable to calling it. This measures *remembered figure versus obvious tool*, not *remembered figure
versus ranked passage*, which remains unmeasured.
