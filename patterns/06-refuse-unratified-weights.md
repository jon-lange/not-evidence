---
pattern: 06
name: "Refuse to Score Unratified Weights"
status: draft          # draft | field-tested | superseded-by: NN
refuses: "to produce a number the domain owner never endorsed"
specimen: none
---

# 06 · Refuse to Score Unratified Weights

> **Refuses to produce a number the domain owner never endorsed.**

## Context

An evaluation produces results per dimension — correctness, completeness, format compliance, tone.
Then something collapses those dimensions into a single score, because a decision has to be made and
decisions consume single numbers.

That collapse requires weights, and the weights are the whole of the sentence *"this is good
enough."* They say completeness matters more than tone; that a formatting failure is survivable and a
factual one is not. None of that is knowable from the harness. It is known by whoever owns the
quality bar for the domain — the person who will be asked to defend an output when it turns out to be
wrong.

Engineers build the harness. Engineers are therefore the ones sitting in front of the field labelled
`weights` when the pipeline needs a value there.

## Forces

**The score is needed before the owner is available.** Reviews get scheduled; runs do not wait, and
the gap between *we need a number today* and *the owner has an hour next week* is exactly the gap a
placeholder fills.

**Weights look like configuration.** Same file as batch size and retry count, same syntax, same
reviewers. Nothing about the artefact signals that one field is an engineering parameter and another
is a policy decision wearing a float.

**A number, once produced, travels** — into a summary, a review, a slide — arriving each time
stripped of its provenance and carrying the authority of the system that emitted it.

**Ratification is slow and socially expensive.** Asking someone to endorse a weighting is asking them
to own its consequences. That is why it is worth doing and why it gets deferred.

## The Refusal

**If the weighting has not been ratified by the person who owns the quality bar, the scoring run
fails. It does not warn, and it does not fall back to a default.**

Three parts, all load-bearing:

1. **Fails, not warns.** A warning is addressed to whoever reads the log — the engineer, who already
   knows and cannot fix it. A failure is addressed to whoever can unblock it. The difference is not
   severity, it is *audience*.
2. **No default weighting.** A default is worse than no weighting, because downstream it is
   indistinguishable from a considered one. Equal weights are not neutral: they are a strong claim
   that every dimension matters identically, which is rarely true and has never once been argued.
3. **Ratified against a specific version.** Sign-off is a claim about particular numbers, not about
   the concept of weighting. Record who ratified what, and make any edit invalidate the record and
   re-fail the run.

This is an organisational control enforced by a tool, and that is the mechanism, not an awkwardness
to apologise for. Consulting the domain owner from memory is a practice, and practices degrade under
deadline. A run that will not complete is a fact, and it gets resolved by the person who should have
been consulted in the first place.

## Consequences

**The weighting acquires a named owner,** which is the actual deliverable — the number is a
by-product. Asked *who decided completeness was worth double?*, there is now an answer, and it is not
"the harness".

**You are visibly blocked on someone else's calendar.** Some teams will experience this as the tool
being obstructive. It is, and that is the design.

**The argument happens before the number exists.** Disagreement about weights is cheap while the
score is hypothetical and expensive once it is being quoted in decisions. Forcing it early is most of
the value.

**You lose the casual exploratory run** — unless you split the outputs. Emit per-dimension results
freely and refuse only the aggregate. Un-collapsed results carry no false endorsement, because nobody
mistakes a table of dimensions for a verdict.

## The naive approach it beats

**Ship a plausible default weighting with a `TODO: confirm with the domain owner`.**

Genuinely attractive: it unblocks the run, it is honest in the source, and it feels provisional. It
fails through a specific mechanism — **the number is immediately useful, so it is immediately used**,
and being used is what fixes it in place. Once a score is circulating, revising the weights means
revising every decision already justified by the old one. "We'll tune them later" is not an intention
that fails; it is an intention that grows steadily more expensive to act on until it is abandoned,
leaving the comment behind as evidence that someone knew.

The second failure is endorsement. A default is read as a choice. Nobody downstream of a dashboard
asks whether the weighting was ratified, because emitted numbers do not look provisional — and the
more polished the reporting, the less provisional they look.

A subtler variant fails the same way: show the domain owner the *scores* and ask them to confirm the
weights afterwards. They are now reasoning backwards from an outcome they can already see, which is
not ratification of a quality bar but negotiation with a result.

The tell: ask three people who chose the weights. Three answers, or a shrug, and the number in
circulation has no owner and never did.

## Prior art

- Keeney & Raiffa, *Decisions with Multiple Objectives: Preferences and Value Tradeoffs* (Wiley,
  1976) — the foundational statement that weights in a multi-attribute score are *elicited value
  judgements* belonging to the decision maker, not parameters for the analyst to assume
- *Software Engineering at Google*, ch. 20, "Static Analysis" —
  [abseil.io/resources/swe-book/html/ch20.html](https://abseil.io/resources/swe-book/html/ch20.html).
  "We have found repeatedly that developers ignore compiler warnings," and therefore: enable the
  check as an error and break the build, or don't show it at all. The same reasoning, applied to a
  different kind of finding.
- Johnson & Goldstein, *Do Defaults Save Lives?*, Science 302 (2003), 1338–1339 —
  [doi:10.1126/science.1091721](https://doi.org/10.1126/science.1091721). Defaults dominate outcomes
  and are read as implicit recommendations, which is why a placeholder weighting is not a neutral act.

## Specimen

None — prose is sufficient. The enforcement is a few lines of validation; the hard part is convincing
a team that failing their own pipeline on a governance condition is correct behaviour.
