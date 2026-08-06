"""Analysis over per-item verdicts.

Everything here operates on the persisted record rather than on aggregates. That
ordering is deliberate: a harness that only writes dimension-level means has
permanently discarded what is needed for paired comparison, agreement, and
interval estimation, and retrofitting it means re-running everything.

No network. Standard library only, so the analysis is testable without spending
a cent.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import dataclass

Verdict = dict  # {item, candidate, judge, dimension -> int}

DIMENSIONS = ("accuracy", "mechanism", "commitment")

# Paired two-sided t-test, alpha = .05, power = .80. The 2.8 is
# (z_{1-a/2} + z_{1-B}) = 1.96 + 0.84, rounded. Adequate for sizing; this is a
# sanity bound, not a substitute for a real power calculation.
MDE_CONSTANT = 2.8


@dataclass(frozen=True)
class JudgeView:
    judge: str
    means: dict[str, float]          # candidate -> mean total score
    winner: str | None               # None for a tie OR for a judge with no signal
    gap: float
    mde: float
    n_paired: int
    n_discordant: int
    discriminating: bool             # did this judge ever separate the candidates?
    note: str = ""


def _total(v: Verdict) -> int:
    return sum(int(v[d]) for d in DIMENSIONS)


def paired_scores(verdicts: list[Verdict], judge: str, a: str, b: str) -> list[tuple[int, int]]:
    """Per-item (a_score, b_score) for items this judge scored for BOTH candidates.

    Items where either side is missing are dropped rather than imputed. An
    imputed score is indistinguishable from a real one once it reaches a mean.
    """
    by_item: dict[str, dict[str, int]] = defaultdict(dict)
    for v in verdicts:
        if v["judge"] == judge:
            by_item[v["item"]][v["candidate"]] = _total(v)
    return [
        (scores[a], scores[b])
        for scores in by_item.values()
        if a in scores and b in scores
    ]


def minimum_detectable_effect(pairs: list[tuple[int, int]]) -> float:
    """Smallest mean difference this many items could resolve.

    A gap below this is a tie. Reporting the number next to the result is the
    point — it converts 'no significant difference' from an excuse into a
    statement about the experiment's resolution.
    """
    n = len(pairs)
    if n < 2:
        return float("inf")
    diffs = [x - y for x, y in pairs]

    if all(d == 0 for d in diffs):
        # The judge scored both candidates identically on every item. There is no
        # variance AND no difference — the run carries no information about which
        # is better. Reporting a tiny MDE here would imply enormous precision;
        # the honest value is that nothing is resolvable.
        return float("inf")

    sd = statistics.stdev(diffs)
    if sd == 0:
        # A perfectly consistent non-zero difference on every item.
        return 0.0
    return MDE_CONSTANT * sd / (n ** 0.5)


def discordant(pairs: list[tuple[int, int]]) -> int:
    """Items where the candidates actually differ.

    Power in a paired comparison comes from these, not from the total. Two runs
    with identical marginal means can be easy or hard to separate depending on
    how much of the agreement is item-level coincidence.
    """
    return sum(1 for x, y in pairs if x != y)


def judge_view(verdicts: list[Verdict], judge: str, a: str, b: str) -> JudgeView:
    pairs = paired_scores(verdicts, judge, a, b)
    if not pairs:
        return JudgeView(judge, {}, None, 0.0, float("inf"), 0, 0, False, "no verdicts")

    mean_a = statistics.fmean(x for x, _ in pairs)
    mean_b = statistics.fmean(y for _, y in pairs)
    gap = mean_a - mean_b
    mde = minimum_detectable_effect(pairs)
    n_disc = discordant(pairs)

    # A judge that never separated the candidates on any item has produced no
    # signal about which is better. Its equal means are not a considered tie —
    # they are the absence of a measurement, and the two must not be reported
    # the same way. This is the refusal: no winner from a judge that never
    # discriminated, however confident the aggregate looks.
    if n_disc == 0:
        return JudgeView(judge, {a: mean_a, b: mean_b}, None, gap, mde,
                         len(pairs), 0, False,
                         "no signal — scored both candidates identically on every item")

    if gap == 0:
        winner, note = None, "exact tie"
    elif abs(gap) < mde:
        winner, note = None, "below the minimum detectable effect"
    else:
        winner, note = (a if gap > 0 else b), ""

    return JudgeView(judge, {a: mean_a, b: mean_b}, winner, gap, mde,
                     len(pairs), n_disc, True, note)


def ranking_flipped(views: list[JudgeView]) -> bool:
    """Did the choice of judge change which candidate wins?

    Ties are excluded. A flip requires two judges that both resolved a winner and
    disagreed about who it is — that is the decisive observation, and it turns an
    abstract argument about bias into a binary result.
    """
    decided = {v.winner for v in views if v.winner is not None}
    return len(decided) > 1


def self_preference(views: list[JudgeView], generators: dict[str, str]) -> list[tuple[str, float]]:
    """For each judge that also generated a candidate, its margin for its own output.

    Positive means the judge scored its own generation above the other's. This is
    the mechanism the cross-family rule exists to remove: self-recognition, not
    quality, moving the number.
    """
    out = []
    for v in views:
        own = generators.get(v.judge)
        if own is None or not v.means:
            continue
        other = next((c for c in v.means if c != own), None)
        if other is None:
            continue
        out.append((v.judge, v.means[own] - v.means[other]))
    return out
