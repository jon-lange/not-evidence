"""The scoring engine, and the geometry of the weight space it lives in.

Three synthetic scorecards over the same six dimensions, each comparing two
documentation generators. Per-dimension scores are given; the aggregate is a
weighted mean, which is the only place a weighting enters and the only thing
this specimen argues about.

There is deliberately no default weighting anywhere in this module. `equal()`
exists and is spelled out at every call site, because "equal weights" is a
claim about what matters and it should be readable as one.

The second half is weight-space geometry. Given the per-dimension differences
between two candidates, what fraction of possible weightings picks each winner?
That has an exact answer, not an estimate: the winner is decided by the sign of
`delta . w`, so the question is what share of the simplex falls on each side of
a hyperplane through it. `share_below_zero` computes it in closed form and
`monte_carlo_share` re-derives it by sampling, so the exact routine is checked
against something that shares none of its reasoning.

No network. Standard library only — the claim here is about scoring governance,
not about a model, so nothing needs to be asked of one.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

DIMENSIONS = (
    "api_coverage",
    "cross_reference_accuracy",
    "output_accessibility",
    "build_time",
    "incremental_rebuild",
    "theme_customisation",
)


@dataclass(frozen=True)
class Scorecard:
    """Per-dimension results for two candidates. Scores are 0–10, higher better.

    `left` and `right` are an ordering for printing, not a ranking. Nothing in
    this class knows which candidate is better, because nothing in this class
    has been told what matters.
    """

    name: str
    left: str
    right: str
    scores: dict[str, dict[str, float]] = field(default_factory=dict)
    dimensions: tuple[str, ...] = DIMENSIONS

    def delta(self, dimension: str) -> float:
        return self.scores[self.left][dimension] - self.scores[self.right][dimension]

    def deltas(self) -> list[float]:
        """left minus right, per dimension, in `dimensions` order.

        The whole comparison reduces to this vector. A weighting picks `left`
        exactly when its dot product with these differences is positive, which
        is why the flip analysis never needs the scores themselves.
        """
        return [self.delta(d) for d in self.dimensions]

    def candidates(self) -> tuple[str, str]:
        return (self.left, self.right)


# ── the three scorecards ─────────────────────────────────────────────────────
#
# Synthetic, and constructed rather than measured. What is constructed is the
# *shape* of each: a genuine trade-off, a lopsided trade-off, and no trade-off
# at all. The third exists so the specimen reports its own boundary condition
# instead of only the case that flatters the pattern.

CLOSE = Scorecard(
    name="docgen-close",
    left="alder",
    right="birch",
    scores={
        "alder": {
            "api_coverage": 8.4,
            "cross_reference_accuracy": 9.1,
            "output_accessibility": 7.5,
            "build_time": 5.2,
            "incremental_rebuild": 6.0,
            "theme_customisation": 7.0,
        },
        "birch": {
            "api_coverage": 6.3,
            "cross_reference_accuracy": 7.7,
            "output_accessibility": 6.9,
            "build_time": 8.0,
            "incremental_rebuild": 7.9,
            "theme_customisation": 7.5,
        },
    },
)

LOPSIDED = Scorecard(
    name="docgen-lopsided",
    left="cedar",
    right="dogwood",
    scores={
        "cedar": {
            "api_coverage": 9.0,
            "cross_reference_accuracy": 8.5,
            "output_accessibility": 8.0,
            "build_time": 3.0,
            "incremental_rebuild": 7.5,
            "theme_customisation": 7.0,
        },
        "dogwood": {
            "api_coverage": 6.0,
            "cross_reference_accuracy": 6.0,
            "output_accessibility": 6.0,
            "build_time": 7.0,
            "incremental_rebuild": 6.0,
            "theme_customisation": 6.0,
        },
    },
)

DOMINANT = Scorecard(
    name="docgen-dominant",
    left="elm",
    right="fir",
    scores={
        "elm": {
            "api_coverage": 8.0,
            "cross_reference_accuracy": 8.6,
            "output_accessibility": 7.4,
            "build_time": 7.1,
            "incremental_rebuild": 8.2,
            "theme_customisation": 6.9,
        },
        "fir": {
            "api_coverage": 6.5,
            "cross_reference_accuracy": 7.9,
            "output_accessibility": 6.1,
            "build_time": 6.8,
            "incremental_rebuild": 7.0,
            "theme_customisation": 6.4,
        },
    },
)

SCORECARDS = (CLOSE, LOPSIDED, DOMINANT)


# ── weightings ───────────────────────────────────────────────────────────────

def equal(dimensions: tuple[str, ...] = DIMENSIONS) -> dict[str, float]:
    """The weighting that gets used when nobody has been asked.

    Named `equal` rather than `default` on purpose. It asserts that a
    cross-reference that points at the wrong symbol and a theme that cannot be
    customised are the same size of problem, which is a claim somebody should
    have to make out loud.
    """
    return {d: 1.0 / len(dimensions) for d in dimensions}


def normalised(weights: dict[str, float]) -> dict[str, float]:
    total = sum(weights.values())
    if total <= 0:
        raise ValueError("weights must sum to something positive")
    return {d: w / total for d, w in weights.items()}


# Two weightings a real team would produce, from two people who both work on
# the thing. Neither is unreasonable; neither has been ratified by anybody.

CORRECTNESS_FIRST = normalised({
    "api_coverage": 0.25,
    "cross_reference_accuracy": 0.25,
    "output_accessibility": 0.15,
    "build_time": 0.15,
    "incremental_rebuild": 0.15,
    "theme_customisation": 0.05,
})

ITERATION_FIRST = normalised({
    "api_coverage": 0.15,
    "cross_reference_accuracy": 0.15,
    "output_accessibility": 0.05,
    "build_time": 0.30,
    "incremental_rebuild": 0.25,
    "theme_customisation": 0.10,
})


def weighted_total(card: Scorecard, candidate: str, weights: dict[str, float]) -> float:
    """No default for `weights`. Supplying one is the failure this specimen is about."""
    if set(weights) != set(card.dimensions):
        raise ValueError("weighting does not cover exactly the scorecard's dimensions")
    return sum(weights[d] * card.scores[candidate][d] for d in card.dimensions)


def margin(card: Scorecard, weights: dict[str, float]) -> float:
    """Weighted total for `left` minus weighted total for `right`."""
    return sum(weights[d] * card.delta(d) for d in card.dimensions)


def winner(card: Scorecard, weights: dict[str, float]) -> str | None:
    m = margin(card, weights)
    if m == 0:
        return None
    return card.left if m > 0 else card.right


def per_dimension_rows(card: Scorecard) -> list[tuple[str, float, float, float]]:
    """The un-collapsed result: dimension, left, right, difference.

    Always available, and deliberately not behind the ratification gate. This
    table carries no endorsement, because nobody mistakes six numbers for a
    verdict. Only the collapse into one number needs an owner.
    """
    return [(d, card.scores[card.left][d], card.scores[card.right][d], card.delta(d))
            for d in card.dimensions]


# ── weight-space geometry ────────────────────────────────────────────────────

def share_below_zero(values: list[float], *, floor: float = 0.0, concentration: int = 1) -> float:
    """Exact share of the weight simplex where `sum(values[i] * w[i]) < 0`.

    `values` are the per-dimension differences; the share below zero is the
    share of weightings that pick the right-hand candidate.

    Three declared measures over the simplex, all handled here:

      floor=0, concentration=1   uniform over every weighting that sums to 1,
                                 including the degenerate ones that put 99% on
                                 one dimension
      floor=f                    uniform over weightings that give every
                                 dimension at least f — no dimension silently
                                 deleted, which is what a real weighting looks
                                 like
      concentration=k            Dirichlet(k), concentrated near equal weights;
                                 k=8 is "small deviations from the default"

    Method: with w uniform on the simplex, sign(values . w) has the same
    distribution as sign(sum values[i] * E[i]) for E[i] iid Exp(1), because the
    normalising constant is positive. That turns a volume into a probability
    and gives an exact recursion over the negative and positive entries:

        D[k][j] = ( -a[k] * D[k][j-1] + b[j] * D[k-1][j] ) / ( b[j] - a[k] )

    with a the negative values and b the positive ones. Every denominator is a
    positive minus a negative, so it is never zero — repeated values and zeros
    cost nothing, which is why this is preferred over the partial-fraction
    closed form that divides by differences between like-signed entries.

    A floor shifts the threshold: w = f*1 + (1 - n*f)*u for u uniform, so
    values . w < 0 becomes (values - t) . u < 0 with t = -f*sum(values)/(1-n*f).
    Dirichlet(k) is Gamma(k) in place of Exp(1), and Gamma(k) is a sum of k
    exponentials, so it is the same recursion with every value repeated k times.
    """
    n = len(values)
    if n == 0:
        raise ValueError("no dimensions")
    if concentration < 1:
        raise ValueError("concentration must be a positive integer")
    if floor < 0 or floor * n >= 1:
        raise ValueError("floor must be in [0, 1/n)")

    shift = -floor * sum(values) / (1 - n * floor)
    expanded = [v - shift for v in values for _ in range(concentration)]

    negative = [v for v in expanded if v < 0]
    positive = [v for v in expanded if v > 0]
    if not negative:
        return 0.0
    if not positive:
        return 1.0

    # D[k] holds the share for the first k negatives against the positives
    # processed so far. D[k][0] = 1 (no positives, the sum is negative).
    d = [1.0] * (len(negative) + 1)
    for b in positive:
        d[0] = 0.0  # no negatives and at least one positive: never below zero
        for k in range(1, len(negative) + 1):
            a = negative[k - 1]
            d[k] = (-a * d[k] + b * d[k - 1]) / (b - a)
    return d[len(negative)]


def monte_carlo_share(
    values: list[float],
    *,
    floor: float = 0.0,
    concentration: int = 1,
    trials: int = 40_000,
    seed: int = 6,
) -> float:
    """The same share by sampling, as a check on `share_below_zero`.

    Shares no reasoning with the exact routine — it draws weightings and counts.
    Gamma(k) is built as a sum of k exponentials from `random.random()` alone,
    so the result is reproducible from the seed across interpreter versions in a
    way `random.gammavariate` does not promise.
    """
    rng = random.Random(seed)
    n = len(values)
    spread = 1.0 - n * floor
    hits = 0
    for _ in range(trials):
        gammas = [
            -sum(math.log(1.0 - rng.random()) for _ in range(concentration))
            for _ in range(n)
        ]
        total = sum(gammas)
        if sum(v * (floor + spread * g / total) for v, g in zip(values, gammas)) < 0:
            hits += 1
    return hits / trials


def flip_share(card: Scorecard, reference: dict[str, float], **measure) -> float:
    """Share of weightings that disagree with `reference` about the winner.

    A tie under the reference weighting has no winner to disagree with, and this
    raises rather than picking one — a scorecard that cannot separate its
    candidates at all is a different result, not a 100% flip.
    """
    decided = winner(card, reference)
    if decided is None:
        raise ValueError("the reference weighting produced a tie; there is no winner to flip")
    below = share_below_zero(card.deltas(), **measure)
    return below if decided == card.left else 1.0 - below


def minimum_flip_shift(card: Scorecard) -> tuple[float, str, str] | None:
    """Smallest move of weight away from equal weights that changes the winner.

    Returns (fraction, from_dimension, to_dimension), or None if no move within
    the simplex can do it. The cheapest move is always the same shape: take
    weight off the dimension where the losing candidate is strongest and put it
    on the dimension where it is weakest.

    This is the number that makes the flip share concrete. A share is a property
    of a measure nobody voted on; a shift is "move this many points of weight
    from build time to API coverage and the procurement decision reverses".
    """
    deltas = card.deltas()
    n = len(deltas)
    base = sum(deltas) / n
    if base == 0:
        return None
    hi = max(range(n), key=lambda i: deltas[i])
    lo = min(range(n), key=lambda i: deltas[i])
    span = deltas[hi] - deltas[lo]
    if span == 0:
        return None
    donor, receiver = (lo, hi) if base < 0 else (hi, lo)
    needed = abs(base) / span
    if needed > 1.0 / n:  # the donor dimension does not hold that much weight
        return None
    return needed, card.dimensions[donor], card.dimensions[receiver]
