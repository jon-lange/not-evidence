---
pattern: 08
name: "A Remembered Figure Is Never a Current Figure"
status: draft          # draft | field-tested | superseded-by: NN
refuses: "to let a stored value stand in for a live one"
specimen: 08-remembered-is-not-current
---

# 08 · A Remembered Figure Is Never a Current Figure

> **Refuses to let a stored value stand in for a live one.**

## Context

A system accumulates context about the person using it: stated preferences, prior answers, a document
they attached three weeks ago. The same system also answers from live sources, under the discipline of
pattern 01.

Both features ship in the same quarter, described the same way — *we give the model more context*. Then
someone asks how many nodes are in the staging pool. The answer was given last Tuesday, and it is
sitting right there in the history.

## Forces

**Memory's entire value proposition is reuse.** A memory you never reach for is storage; the feature
only justifies its complexity if the system uses what it kept.

**Reuse is exactly right for some things and exactly wrong for others.** Reusing a preference is the
feature working. Reusing a *figure* silently substitutes an old world-state for the current one.

**Memory and grounding feel like allies.** Both add context, and on a diagram both are arrows pointing
into the prompt. Nothing marks them as adversaries, so the boundary between them is never designed — it
emerges from whichever retrieval path ran first.

**The remembered value is free *relative to a live path that costs something*, and staleness is
invisible at the output** — the sentence reads identically whether the number came from a live call or
from a transcript written in March. The qualifier is load-bearing and was added after measurement:
when the live tool is cheap and obvious, models reach for it. Substitution appeared only once the tool
was described as slow, rate-limited and billed. It is the tool's apparent cost that moves this, not
memory's convenience.

## The Refusal

**A remembered or document-derived value may shape presentation and may supply tool parameters. It may
never substitute for a live value.**

The line is drawn by what the stored item is *doing*:

- **Shaping presentation** — that this user wants terse output, or a particular level of detail. Safe:
  it changes the frame, not the fact.
- **Supplying parameters** — that "the usual pool" means a specific one, so the call can be made without
  asking again. Safe: the call still happens.
- **Standing in for the fact** — reporting the node count from the earlier transcript. Forbidden,
  however recent it is.

The general form: **a number read from a stored artefact is a fact about that artefact, not a fact about
the world.** *"The report you attached says the pool holds forty nodes"* is checkable. *"The pool holds
forty nodes"* is a claim about now — one no document can support, not because the document is wrong but
because it is a document.

Combined questions are where this is most visible. *"Show me the queue depth the way you showed me
last time."* The format half comes from memory; the depth half requires a call. Split them — and if the
call fails, refuse the value half while still honouring the format.

This entry originally called combined questions the case "where this gets decided." Measured, every
model split them correctly without being asked, 10/10. They are the clearest illustration of the rule,
not the place it fails.

**And there is a third outcome this pattern did not name.** Between substituting the stored figure and
attributing it lies *silently discarding* it — answering correctly from the live source while never
telling the user their document said something different. That was the majority behaviour, 7 of 10, and
it splits by vendor. It avoids the error this pattern is about and still leaves the user unaware their
information is stale, which is most of what they wanted to know.

The same rule governs attachments. A user-supplied file is not a source of standing equal to a curated
corpus; it is a claim by one artefact of unknown provenance and age. Attribute it as one — *this
document states X* — never merged into the system's own voice beside sources that were vetted.

### The second refusal: inferred facts may be suggested, never silently saved

A user who says *"always give me the short version"* has stated a preference: store it, with a visible,
reversible record that you did. A system that *notices* they usually pick the short version has inferred
one, and inference changes the rule. **Anything the system inferred about the user is surfaced for
confirmation before it is stored, whatever the classifier's confidence.**

Confidence is not consent. A high-confidence wrong inference is worse than a low-confidence one: it is
applied more readily, to more answers, and it shapes every future response while the user sees the
outputs and never the premise.

## Consequences

**Some answers get slower, and some become unavailable when the source is down.** That is the correct
cost: an unreachable source means an unknown value, and pattern 01 says what to do with one.

**Every stored item needs a type** — preference, parameter, or claim-about-an-artefact — carried in the
storage layer, because a model reading a string that happens to contain a number cannot recover the
distinction at read time. The payoff is an auditable memory: everything the system believes about a
user, with a provenance per line.

**You lose the better demo,** and confirmation prompts cost real friction. The instant answer demos
better than the pause to check; the difference surfaces the day the remembered number is stale and
someone acts on it.

## The naive approach it beats

**One retrieval step that pools memory, attachments, and live sources into a single ranked context, and
lets the model decide what to use.**

Genuinely attractive: one code path instead of three, the shape every tutorial builds, and the model is
good at synthesis — so let it.

It fails at a precise point. **Ranking is by similarity, and a stale figure is maximally similar to the
question that asks for it.** A transcript containing *"the pool holds forty nodes"* is the best semantic
match for *"how many nodes are in the pool?"* — often a better match than the tool schema that would
fetch the true answer. Retrieval cannot rank on freshness because it has no notion of it, and the model
downstream cannot restore the distinction: by then every item is text with a score.

The tell: your memory store and your document store share an embedding index. If they do, the
substitution is not a bug review will catch — it is the design, working as specified.

## Prior art

- Vu et al., *FreshLLMs: Refreshing Large Language Models with Search Engine Augmentation* —
  [arXiv:2310.03214](https://arxiv.org/abs/2310.03214). On the gap between what a system holds and what
  is currently true.
- Amershi et al., *Guidelines for Human-AI Interaction*, CHI 2019 —
  [doi:10.1145/3290605.3300233](https://dl.acm.org/doi/10.1145/3290605.3300233). G12 (*remember recent
  interactions*) and G17 (*provide global controls*): the two halves this pattern insists on shipping
  together.
- Nissenbaum, *Privacy as Contextual Integrity*, 79 Wash. L. Rev. 119 (2004) — why a fact appropriately
  learned in one context is not thereby available in another. The basis of the second refusal.

## Specimen

[`specimens/08-remembered-is-not-current/`](../specimens/08-remembered-is-not-current/) — **built.**
Measured output in [`RESULTS.md`](../specimens/08-remembered-is-not-current/RESULTS.md).

The claim that this was "not a runtime behaviour a harness could stage" was wrong. A harness staged it,
and it fired.

**Five models, two vendors, six conditions, 60 items. Stale reuse across conditions 1–5: 0 of 50.**
Placing a plausible dated figure for exactly the thing asked one line above the question changed
nothing. Ground truth is the tool's own invocation log, not a judge.

Substitution appeared only in a sixth condition the specimen author added deliberately — *because a
detector that never fires is an untested detector*, which is pattern 11 applied to a harness. Making
the tool look expensive ("slow, rate-limited, billed, prefer what you already have") produced 3 of 10
reuse immediately, entirely in the two oldest models. That condition is what makes the null readable:
it proves the detector works end to end on real output.

**What was not tested, and it is the important gap.** This entry's naive-approach section describes
failure through *similarity ranking over a pooled memory-and-source index*. The specimen gave the agent
a first-class tool with an enum naming the metric — the arrangement most favourable to calling it. The
null measures *remembered figure versus obvious tool*, not *remembered figure versus ranked passage*.
The mechanism this pattern actually blames remains unmeasured.

`status` stays `draft` for that reason.
