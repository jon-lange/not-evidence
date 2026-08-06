---
name: judge-independence-check
description: Prove an LLM judge produced a signal before trusting its verdict. Use when a model-graded score gates a decision — a prompt change ships, a model swap is approved, a release is cleared — or when choosing which model will judge an eval. Also use when two candidates came out equal and the harness called it a tie, when a judge shares a model family with what it is scoring, or when a pairwise comparison was run in one order only.
pattern: 05
status: revised-by-specimen
---

# Judge independence check

A judge's verdict is a fact about the judge. **"The verdict would have been different"** — under a
different order, under a different judge — is a fact about the measurement. Only the second tells you
whether the number you are about to promote on means anything.

Three checks, **in this order**. The first two are cheap and catch more in practice than the third.
Run them before arguing about lineage, because a saturated judge and an unbiased judge produce
aggregate output that is indistinguishable.

## When to run this

Any model-graded score that gates something. Also:

- A judge that shares a model family with the system it is scoring
- A pairwise comparison run in a single answer order
- A result reported as a tie, equal means, or "no significant difference"
- A panel assembled from one vendor, however many members it has

**Equal means are the absence of a result, not a considered tie.** That distinction is the whole
skill, and no amount of staring at the aggregate will recover it.

## The procedure

**1. Does the judge discriminate at all?** Before comparing anything, look at the raw distribution of
that judge's verdicts. Count the distinct values. Count the items where the candidates actually
differ. One distinct value across the run means the judge carried no information — report **NO
SIGNAL** and stop. Do not name a winner from it, and do not let it vote on a panel.

**2. Is the verdict stable under reordering?** For any pairwise comparison, run every (item, judge)
pair twice with the answers swapped. Count the items where the verdict changed. A judge picking
whichever answer came first has expressed a position preference, not a quality preference. **A high
flip rate is a disqualification, not a footnote** — combine the orders, and report the rate next to
the result.

**3. Does the choice of judge change the winner?** The **ranking-flip test**. Rank the candidates
under each judge that resolved a winner. If the winner depends on who judged, judge independence is
decision-critical for that comparison and no single-judge promotion can stand. Binary, cheap, and it
runs on data you already have.

Only then apply the family rule: **a judge that gates a promotion must not share a model family with
the system it is judging.**

```python
# The three checks. Not a framework.
def discriminates(totals):           # 1 — run this first, on ONE judge's raw scores
    """totals: {item: (score_a, score_b)}. Returns False when the judge never separated them."""
    return any(a != b for a, b in totals.values())

def flip_rate(pairwise):             # 2 — needs BOTH orders, or it cannot be computed
    """pairwise: {item: (winner_in_order_AB, winner_in_order_BA)}."""
    return sum(ab != ba for ab, ba in pairwise.values()) / len(pairwise)

def ranking_flipped(winners):        # 3 — ties and no-signal judges excluded, not counted as agreement
    """winners: one resolved winner per judge, or None."""
    return len({w for w in winners if w is not None}) > 1
```

Note what check 3 excludes. A judge that produced no signal is not a judge that agreed with you.
Feeding its `None` into the panel as consensus is how a no-measurement becomes a unanimous result.

Runnable reference implementation: [`../../specimens/05-judge-family/`](../../specimens/05-judge-family/),
measured output in [`RESULTS.md`](../../specimens/05-judge-family/RESULTS.md).

## What this repeatedly finds

From that specimen's run — two candidates from different families, twelve items, three judges,
absolute scoring then pairwise in both orders:

| Finding | What it looked like from the aggregate |
|---|---|
| **Two of three judges produced no signal.** Both scored a perfect 15/15 on all 24 answers — one distinct value across the entire run. | Two judges "rating the candidates equal." The harness reported a winner from them anyway. |
| **One judge flipped on half the items.** `gpt-4o` preferred whichever answer came first on 6 of 12; the Anthropic judge flipped on 0 of 12. | A clean single-order pairwise result. Position bias is large, judge-specific, and invisible until you run the swap. |
| **An apparent +1.00 self-preference dissolved.** Absolute scoring showed a judge rating its own family a full point higher — textbook self-preference. Pairwise showed *both* cross-family judges preferring the same answers, unanimously. | A confident, publishable, wrong finding. Stopping after check 1 would have produced it. |
| **No ranking flip.** Every judge that resolved a winner picked the same candidate. | The decisive test did not fire. See *Honest limits* — this is not a clean bill of health. |

**Judge quality varied more than judge bias did.** The differences that mattered were saturation and
position sensitivity. Neither is about lineage. Both would have invalidated a promotion decision.

## Absolute scoring versus pairwise

**Absolute scoring saturates.** On a task set where both candidates are competent, every answer earns
full marks and the judge stops carrying information. This is the ordinary case, not the pathological
one — it is what happened above.

**Pairwise cannot saturate**, because it forces a choice. It buys that by introducing position bias,
which is why check 2 exists and why single-order pairwise is not a measurement. Run both orders or
report neither.

## The asymmetry that gets missed

**Cross-family is a property of an *ordered pair*, not a pair.** A judge can be entirely free of
self-preference toward a subject and still be systematically lenient, or systematically harsh, or
saturated. Trust is earned per direction: A judging B may be authoritative while B judging A stays
advisory. Validating one direction licenses exactly one direction.

The same asymmetry sinks panels bought by headcount. Aggregation gains collapse when panellists share
error structure — three variants of one lineage re-vote the same bias. **Buy family diversity, not
members.**

## Honest limits

**Agreement is reliability, not validity.** Judges agreeing tells you they fail the same way. A
unanimous panel can be unanimously wrong, and nothing in this procedure can tell the difference.
Establishing validity needs a hand-labelled reference set — which is more expensive than every check
here combined, and is the only thing that actually grounds the scale.

**The flip test is one-directional evidence.** It tells you when you *have* a problem. It cannot tell
you that you do not. No flip is consistent with judge independence and equally consistent with three
judges sharing one blind spot.

**This repo's own run did not demonstrate the cross-family claim.** There was no ranking flip, and the
one signal that looked like self-preference dissolved once cross-family judges agreed with it. The
cross-family rule remains well-supported in the literature and unproven here; the pattern stays
`draft`, and so does this skill. What the run established was checks 1 and 2, neither of which was in
the pattern's first draft.

**Checks 1 and 2 are properties of a judge on a task set, not of a judge.** A judge that
discriminates on an adversarial set may saturate on an easy one. Re-run them when the task set
changes — including when it changes because your candidates got better.

**Persist per-item verdicts before aggregating.** None of these checks are computable from dimension
means. A harness storing only aggregates has discarded what they need, and retrofitting it means
re-running the whole eval. Both analysis defects in the specimen were fixed and recomputed from
persisted records without re-spending a cent.

## Prior art

- Panickssery, Bowman & Feng, *LLM Evaluators Recognize and Favor Their Own Generations* —
  [arXiv:2404.13076](https://arxiv.org/abs/2404.13076). Self-recognition, and its linear correlation
  with self-preference strength — the mechanism the family rule exists to remove.
- Zheng et al., *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena* —
  [arXiv:2306.05685](https://arxiv.org/abs/2306.05685). Position bias in LLM judges, and why both
  orders must be run.
