---
name: weight-flip-share
description: Measure how much of a weighted decision was made by the weighting rather than the evidence, and refuse to emit the score until someone owns the weighting. Use when collapsing per-dimension results into one number that decides something — a model comparison, a vendor choice, a launch gate, a scorecard — or when a weights file is about to be written, edited, or quoted. Also use when a score is already circulating and nobody can say who chose the weights.
pattern: 06
status: field-tested
---

# Weight flip share

A weighted score is two things welded together: what was measured, and what was decided to matter.
Only the first is evidence. **The flip share is how much of the verdict came from the second.**

It answers one question with an exact number: *what fraction of plausible weightings would pick the
other candidate?* If that fraction is large, the weighting made the decision, and whoever owns the
quality bar has to ratify it before the number is quoted anywhere.

## When to run this

Before any weighted aggregate leaves the harness. Specifically:

- Per-dimension results — correctness, latency, cost, tone — about to be collapsed into one number
- A `weights` field being filled in or edited, in a config file that also holds batch size and retries
- Any single score already being quoted in a decision, review, or slide
- Equal weights, because they are the case that most looks like no decision was made

Equal weights are not neutral. They assert that a cross-reference pointing at the wrong symbol and an
uncustomisable theme are the same size of problem — a claim two in five weightings disagree with on
the measured scorecard, and one that has never once been argued.

## The procedure

**1. Compute per-dimension deltas.** `delta[i] = left[i] − right[i]`. The whole comparison reduces to
this vector — the flip analysis never needs the scores themselves.

**2. Compute the flip share.** The winner is the sign of `delta·w`, so the flip region is the simplex
cut by a hyperplane. That is a volume, and it has a closed form. Do not sample.

**3. Report the cheapest flip.** A share is a property of a measure nobody voted on; a *shift* is
"move this many points of weight from build time to API coverage and the procurement decision
reverses." Take weight off the dimension where the loser is strongest and put it where it is weakest:
`needed = |mean(delta)| / (max(delta) − min(delta))`, infeasible if it exceeds `1/n`.

**4. If the share is meaningful, refuse to emit a score** until a ratification record exists. Fail —
do not warn, do not fall back to a default. A warning is addressed to the engineer reading the log,
who already knew and does not own the quality bar.

**5. Emit the un-collapsed table regardless.** Six numbers side by side carry no endorsement. Gate
only the collapse, and the exploratory run survives.

```python
def share_below_zero(deltas):
    """Exact share of the weight simplex where delta·w < 0 — the share picking the
    right-hand candidate. With w uniform on the simplex, sign(delta·w) has the same
    distribution as sign(sum delta_i * E_i) for E_i iid Exp(1), which turns a volume
    into a probability and gives a recursion over the negative and positive entries."""
    neg = [d for d in deltas if d < 0]
    pos = [d for d in deltas if d > 0]
    if not neg:
        return 0.0                      # left dominates: no weighting flips it
    if not pos:
        return 1.0                      # right dominates
    s = [1.0] * (len(neg) + 1)          # s[k]: first k negatives vs the positives so far
    for b in pos:
        s[0] = 0.0                      # no negatives, one positive: never below zero
        for k in range(1, len(neg) + 1):
            a = neg[k - 1]
            s[k] = (-a * s[k] + b * s[k - 1]) / (b - a)   # positive minus negative: never 0
    return s[-1]

# Flip share = share_below_zero(deltas) if the quoted winner is `left`, else 1 − it.
# A floor ("every dimension gets at least 5%") is a shift of the deltas; Dirichlet(k)
# concentration toward equal weights is the same recursion with each delta repeated k
# times. Both are in the specimen, along with a Monte Carlo cross-check.
```

Runnable reference implementation:
[`../../specimens/06-unratified-weights/`](../../specimens/06-unratified-weights/).

## What this measured

One realistic scorecard, six dimensions, two documentation generators, genuine trade-offs. Exact
rather than sampled; Monte Carlo agrees within 1.7 standard errors across nine cells.

| Finding | Number |
|---|---|
| **Weightings that pick the candidate equal weights reject** | **40.6%** |
| Weight transfer that reverses the decision | **3.7 points**, from one dimension to another |
| Three defensible weightings a real team would write | two winners between them |
| Where one candidate dominates every dimension | **exactly 0%** — nothing flips |
| Same share under a Dirichlet(64) prior near equal weights | 1.9% |

Nobody reviewing a weights file flags a 3.7-point difference, and nobody reading the winner downstream
can see it at all.

**The gate refuses five ways; the warning version emits a byte-identical clean artefact in all five** —
no record at all, weights nudged by 0.01 after sign-off, a seventh dimension added, the engineer
ratifying their own weighting. Two of those warned runs name *different winners*. Adding a provenance
field does not help: the warned path writes some value into it and the summary downstream drops it.

## The ratification record

Minimal shape, and nothing more is needed:

```
scorecard    which comparison this endorses — a record does not transfer between cards
dimensions   the sorted dimension set, so adding a seventh invalidates it
weights_hash sha256 of the canonical normalised weighting; any edit invalidates it
owner, role  a name, and what makes them the person who owns the quality bar
date         when
```

**The gate deliberately cannot tell a real owner from a plausible string.** `owner="TODO"` passes, and
a test pins that in place. A denylist of placeholder-looking names would be worse than nothing — it
would pass everything not on the list while looking like it checked, which is
[pattern 02](../../patterns/02-refuse-the-class.md)'s failure mode. What is actually enforced: *some*
name is attached, it is bound to one version, and editing the version invalidates it.

## Honest limits

**Where one candidate dominates, this buys exactly zero.** The dominant scorecard flips under no
weighting in any measure, and the cheapest-shift search returns nothing. The gate then protects a
decision that was never at risk. You cannot know which kind of scorecard you have without computing
the flip share — which is the argument for computing it first, not for the gate.

**There is no measure-free flip fraction.** The share is a property of the scorecard *and* a measure
over weightings: 40.6% under a uniform simplex, 1.9% under Dirichlet(64), and raising a floor from 5%
to 14% took one card's region to exactly 0. Declaring "uniform over the simplex" says a weighting
putting 99% on theme customisation is as likely as any other — the same unargued act, one level up.
No principled measure is on offer here. Report several and show the spread.

**Re-ratification is cheap.** The hash makes an edit *visible*, not expensive. Anyone who wants the
other winner can nudge a weight and request a fresh signature.

**The sharpest failure is undefended.** Show an owner the scores and then ask them to confirm the
weights, and they are reasoning backwards from an outcome they can already see — negotiation with a
result, not ratification of a quality bar. Nothing here prevents that, and probably nothing can.

**Closeness is not the mechanism.** A card winning by 5.5× the close card's margin still flipped
13.6% of the time. What produces a flip region is mixed-sign deltas, and under the unfloored simplex
*any* mixed-sign delta vector has one, however large the margin.

## Prior art

- Keeney & Raiffa, *Decisions with Multiple Objectives: Preferences and Value Trade-Offs* — Wiley
  1976; CUP reissue [doi:10.1017/CBO9781139174084](https://doi.org/10.1017/CBO9781139174084). Weights
  in a multi-attribute score are elicited value judgements belonging to the decision maker, not
  parameters for the analyst to assume.
- Johnson & Goldstein, *Do Defaults Save Lives?* — *Science* 302 (2003), 1338–1339,
  [doi:10.1126/science.1091721](https://doi.org/10.1126/science.1091721). Defaults dominate outcomes
  and are read as implicit recommendations, which is why a placeholder weighting is not a neutral act.
- *Software Engineering at Google*, ch. 20, "Static Analysis" —
  [abseil.io/resources/swe-book/html/ch20.html](https://abseil.io/resources/swe-book/html/ch20.html).
  "We have found repeatedly that developers ignore compiler warnings." Break the build or don't emit
  the finding at all.
