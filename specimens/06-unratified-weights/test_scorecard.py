"""Tests for the scoring engine and the weight-space geometry.

Run: python3 test_scorecard.py   (or: python3 -m pytest test_scorecard.py -q)

The exact share routine is the load-bearing piece — it produces the headline
number — so it is pinned three ways: against closed forms worked out by hand,
against its own structural identities (sign symmetry, zeros are inert, a
concentration of k is the same as repeating each value k times), and against a
Monte Carlo estimate that shares none of its reasoning.

No network, no dependencies.
"""

from __future__ import annotations

import inspect
import math
import random

import scorecard as sc

# ── closed forms, worked out by hand ─────────────────────────────────────────
#
# With w uniform on the simplex, sign(v . w) matches sign(sum v_i E_i) for E
# iid Exp(1). Each case below is that probability, computed directly.

def test_two_opposite_values_split_the_simplex():
    """P(E1 < E2) = 1/2."""
    assert sc.share_below_zero([1.0, -1.0]) == 0.5


def test_an_asymmetric_pair():
    """P(E1 - 2 E2 < 0) = P(E1 < 2 E2) = 1 - 1/(1+2) = 2/3."""
    assert math.isclose(sc.share_below_zero([1.0, -2.0]), 2 / 3)


def test_one_negative_against_two_positives():
    """P(E1 + E2 < Z) = E[e^-(E1+E2)] = (1/2)^2 = 1/4."""
    assert math.isclose(sc.share_below_zero([-1.0, 1.0, 1.0]), 0.25)


def test_two_negatives_against_one_positive():
    """P(Y < Z1 + Z2) = 1 - (1/2)^2 = 3/4. The complement of the case above."""
    assert math.isclose(sc.share_below_zero([-1.0, -1.0, 1.0]), 0.75)


def test_unequal_negatives_against_one_positive():
    """P(Y < Z1 + 2 Z2) = 1 - (1/2)(1/3) = 5/6."""
    assert math.isclose(sc.share_below_zero([-1.0, -2.0, 1.0]), 5 / 6)


def test_a_floor_restricts_the_simplex_to_a_known_interval():
    """v = (1, -3) with every weight at least 0.1: w1 ranges over [0.1, 0.9]
    and the sum is negative for w1 < 0.75, so the share is 0.65/0.8."""
    assert math.isclose(sc.share_below_zero([1.0, -3.0], floor=0.1), 0.8125)


# ── structural identities ────────────────────────────────────────────────────

def test_one_sided_scorecards_have_no_flip_region():
    assert sc.share_below_zero([1.0, 2.0, 3.0]) == 0.0
    assert sc.share_below_zero([-1.0, -2.0, -3.0]) == 1.0


def test_identical_candidates_produce_no_share_either_way():
    """Every delta zero: the margin is exactly zero for every weighting, and
    zero is not below zero. No weighting can separate them."""
    assert sc.share_below_zero([0.0, 0.0, 0.0]) == 0.0


def test_zero_deltas_are_inert():
    """A dimension the candidates tie on cannot move the winner, whatever
    weight it gets — wherever it sits in the dimension order.

    The trailing case was the whole test until the mutation check showed that a
    zero at the end of the recursion is inert even when it is wrongly filed as a
    negative. Leading and interleaved zeros are what catch that."""
    baseline = sc.share_below_zero([1.0, -1.0])
    assert sc.share_below_zero([1.0, -1.0, 0.0, 0.0]) == baseline
    assert sc.share_below_zero([0.0, 0.0, 1.0, -1.0]) == baseline
    assert sc.share_below_zero([0.0, 1.0, 0.0, -1.0]) == baseline


def test_flipping_every_sign_flips_the_share():
    values = [2.1, 1.4, 0.6, -2.8, -1.9, -0.5]
    mirrored = [-v for v in values]
    assert math.isclose(sc.share_below_zero(values) + sc.share_below_zero(mirrored), 1.0)


def test_repeated_values_do_not_break_the_recursion():
    """The reason for the negative/positive recursion rather than the partial
    fraction form: every denominator here is a positive minus a negative."""
    assert math.isclose(sc.share_below_zero([1.0, 1.0, -1.0, -1.0]), 0.5)
    # P(E1 + E2 + E3 < Z) = E[e^-Gamma(3)] = (1/2)^3.
    assert math.isclose(sc.share_below_zero([2.0, 2.0, 2.0, -2.0]), 0.125)


def test_concentration_is_repetition():
    """Dirichlet(k) is Gamma(k) per dimension, and Gamma(k) is k exponentials."""
    values = [2.1, -1.4, 0.6, -0.3]
    for k in (2, 3, 5):
        repeated = [v for v in values for _ in range(k)]
        assert math.isclose(sc.share_below_zero(values, concentration=k),
                            sc.share_below_zero(repeated), abs_tol=1e-12), k


def test_bad_measures_are_rejected():
    for kwargs in ({"floor": -0.1}, {"floor": 0.5}, {"concentration": 0}):
        try:
            sc.share_below_zero([1.0, -1.0], **kwargs)
        except ValueError:
            continue
        raise AssertionError(f"accepted {kwargs}")
    try:
        sc.share_below_zero([])
    except ValueError:
        return
    raise AssertionError("accepted an empty scorecard")


# ── the exact routine against sampling ───────────────────────────────────────

def test_the_exact_share_matches_monte_carlo():
    """Twelve random delta vectors, three measures each. The estimator shares
    no reasoning with the recursion, so agreement is evidence rather than a
    tautology. Tolerance is four standard errors of the estimate."""
    rng = random.Random(1789)
    trials = 20_000
    for _ in range(12):
        n = rng.randint(2, 7)
        values = [round(rng.uniform(-3, 3), 2) for _ in range(n)]
        for measure in ({}, {"floor": 0.05}, {"concentration": 3}):
            exact = sc.share_below_zero(values, **measure)
            estimate = sc.monte_carlo_share(values, trials=trials, seed=rng.randint(0, 10**6),
                                            **measure)
            se = math.sqrt(max(exact * (1 - exact), 1e-6) / trials)
            assert abs(exact - estimate) < 4 * se + 0.002, (values, measure, exact, estimate)


def test_monte_carlo_is_reproducible_from_its_seed():
    values = [2.1, 1.4, 0.6, -2.8, -1.9, -0.5]
    first = sc.monte_carlo_share(values, trials=2_000, seed=99)
    assert first == sc.monte_carlo_share(values, trials=2_000, seed=99)
    assert first != sc.monte_carlo_share(values, trials=2_000, seed=100)


# ── the scorecards ───────────────────────────────────────────────────────────

def test_the_close_scorecard_is_a_genuine_trade_off():
    """The data invariant the specimen rests on. If this ever becomes one-sided
    the flip result stops meaning anything, and it should fail loudly here."""
    deltas = sc.CLOSE.deltas()
    assert any(d > 0 for d in deltas) and any(d < 0 for d in deltas)


def test_the_dominant_scorecard_really_dominates():
    """The boundary condition. One candidate better on every dimension."""
    assert all(d > 0 for d in sc.DOMINANT.deltas())


def test_three_defensible_weightings_produce_two_winners():
    """The headline. Same measurements, same candidates, different verdict."""
    winners = {label: sc.winner(sc.CLOSE, w) for label, w in (
        ("equal", sc.equal()),
        ("correctness", sc.CORRECTNESS_FIRST),
        ("iteration", sc.ITERATION_FIRST),
    )}
    assert winners == {"equal": "birch", "correctness": "alder", "iteration": "birch"}


def test_equal_weights_are_not_a_tie():
    """They pick a winner, decisively enough to be quoted, and by 2.5% of the
    scale — which is what makes the flip cheap."""
    margin = sc.margin(sc.CLOSE, sc.equal())
    assert margin < 0
    assert 0.1 < abs(margin) < 0.3


def test_the_flip_share_is_substantial_where_there_is_a_trade_off():
    reference = sc.equal()
    close = sc.flip_share(sc.CLOSE, reference)
    lopsided = sc.flip_share(sc.LOPSIDED, reference)
    assert 0.3 < close < 0.5
    assert 0.05 < lopsided < 0.2
    assert sc.flip_share(sc.DOMINANT, reference) == 0.0


def test_concentrating_near_equal_weights_shrinks_the_flip_region():
    """As the measure concentrates on the equal-weight point the flip share has
    to fall toward zero, because that point is not in the flip region."""
    reference = sc.equal()
    wide = sc.flip_share(sc.CLOSE, reference)
    mid = sc.flip_share(sc.CLOSE, reference, concentration=8)
    tight = sc.flip_share(sc.CLOSE, reference, concentration=64)
    assert wide > mid > tight > 0.0


def test_flip_share_refuses_a_reference_that_did_not_decide():
    """A weighting that ties has no winner, and reporting 100% flipped would be
    a claim about a comparison that never happened."""
    tied = sc.Scorecard(name="tied", left="a", right="b", dimensions=("x", "y"),
                        scores={"a": {"x": 5.0, "y": 5.0}, "b": {"x": 5.0, "y": 5.0}})
    try:
        sc.flip_share(tied, sc.equal(("x", "y")))
    except ValueError:
        return
    raise AssertionError("flip_share invented a winner")


def test_the_minimum_shift_actually_flips_the_winner():
    """Applying the reported move plus a hair changes the verdict; a hair less
    does not. Without both halves this is a number nobody has checked."""
    shift = sc.minimum_flip_shift(sc.CLOSE)
    assert shift is not None
    size, donor, receiver = shift
    assert (donor, receiver) == ("build_time", "api_coverage")
    assert 0.03 < size < 0.04

    for nudge, expected in ((1e-6, "alder"), (-1e-6, "birch")):
        weights = dict(sc.equal())
        weights[donor] -= size + nudge
        weights[receiver] += size + nudge
        assert sc.winner(sc.CLOSE, weights) == expected, nudge


def test_no_shift_helps_when_one_candidate_dominates():
    assert sc.minimum_flip_shift(sc.DOMINANT) is None


# ── the scoring engine ───────────────────────────────────────────────────────

def test_weighted_total_rejects_a_weighting_of_the_wrong_shape():
    partial = {d: 0.2 for d in sc.DIMENSIONS[:5]}
    try:
        sc.weighted_total(sc.CLOSE, "alder", partial)
    except ValueError:
        return
    raise AssertionError("scored against a weighting that ignored a dimension")


def test_there_is_no_default_weighting_anywhere():
    """The pattern's second clause, asserted against the source. A default
    parameter here would be the whole failure, shipped."""
    for fn in (sc.weighted_total, sc.margin, sc.winner):
        parameter = inspect.signature(fn).parameters["weights"]
        assert parameter.default is inspect.Parameter.empty, fn.__name__


def test_equal_weights_sum_to_one_and_cover_every_dimension():
    weights = sc.equal()
    assert set(weights) == set(sc.DIMENSIONS)
    assert math.isclose(sum(weights.values()), 1.0)


def test_the_two_authored_weightings_are_normalised():
    for weights in (sc.CORRECTNESS_FIRST, sc.ITERATION_FIRST):
        assert math.isclose(sum(weights.values()), 1.0)
        assert set(weights) == set(sc.DIMENSIONS)


def test_normalised_rescales_a_weighting_that_does_not_sum_to_one():
    """Added after the mutation check: both authored weightings were written
    already summing to 1, so `normalised` returning its input unchanged passed
    the test above and every other test in this file. The test was checking the
    literals, not the function."""
    assert sc.normalised({"a": 2.0, "b": 6.0}) == {"a": 0.25, "b": 0.75}
    try:
        sc.normalised({"a": 0.0, "b": 0.0})
    except ValueError:
        return
    raise AssertionError("normalised a weighting with nothing in it")


def test_the_per_dimension_table_needs_nothing():
    """It is not behind the gate, and it carries the differences that the
    aggregate throws away."""
    rows = sc.per_dimension_rows(sc.CLOSE)
    assert [r[0] for r in rows] == list(sc.DIMENSIONS)
    assert all(math.isclose(r[3], r[1] - r[2]) for r in rows)


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS  {name}")
            except AssertionError as exc:
                failures += 1
                print(f"  FAIL  {name}: {exc}")
            except Exception as exc:  # noqa: BLE001 — a crash is a failure, keep counting
                failures += 1
                print(f"  ERROR {name}: {type(exc).__name__}: {exc}")
    print(f"\n{failures} failure(s)")
    raise SystemExit(1 if failures else 0)
