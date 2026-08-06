"""Tests for the prober, and for the numbers it produces.

Run: python3 test_prober.py   (or: python3 -m pytest test_prober.py -q)

The suite has three jobs. It checks the prober's parts. It pins the claim that
the prober reads codes as opaque labels — because if it were secretly reading
their meaning, the measured advantage would be an artefact of how this
specimen's error strings happen to be spelled. And it pins the published
numbers inside bands, so a change that moves them cannot pass while RESULTS.md
goes on quoting the old ones.
"""

from __future__ import annotations

import statistics

import probe
import prober
import validator as V
from prober import Box, Oracle, characterise, descend, neighbours
from validator import ACCRETED, CARVE_OUT, CLASS, Ref, Validator

SEEDS = range(6)


def completes(boundary, uniform, seeds=SEEDS, **kwargs):
    truth = V.accepted_set(boundary)
    return [characterise(Validator(boundary, uniform=uniform), truth, seed=s, **kwargs)
            for s in seeds]


# ── parts ────────────────────────────────────────────────────────────────────

def test_the_oracle_counts_distinct_references_only():
    oracle = Oracle(Validator(ACCRETED, uniform=False))
    ref = V.SPACE[0]
    for _ in range(5):
        oracle.query(ref)
    oracle.query(V.SPACE[1])
    assert oracle.probes == 2


def test_neighbours_differ_in_exactly_one_field():
    ref = Ref("https", "docs.example.com", "png", 64, "ok")
    got = list(neighbours(ref))
    assert len(got) == sum(len(V.VALUES[d]) - 1 for d in V.DIMS) == 40
    for other in got:
        assert sum(getattr(ref, d) != getattr(other, d) for d in V.DIMS) == 1
    assert len(set(got)) == len(got)


def test_descent_reports_the_values_that_keep_a_reference_accepted():
    validator = Validator(ACCRETED, uniform=False)
    oracle = Oracle(validator)
    accepted = Ref("", "", "md", 1, "ok")
    assert validator(accepted).ok
    box = descend(accepted, oracle.query)
    values = dict(box.values)
    assert values["scheme"] == frozenset({""})
    assert values["form"] == frozenset({"ok"})
    assert "png" in values["kind"] and "zip" not in values["kind"]


def test_a_box_enumerates_exactly_its_own_size():
    box = Box((("scheme", frozenset({"", "https"})), ("host", frozenset({""})),
               ("kind", frozenset({"md", "png"})), ("size_kb", frozenset({1})),
               ("form", frozenset({"ok"}))))
    points = list(box.points())
    assert len(points) == box.size() == 4
    assert len(set(points)) == 4


def test_coordinate_descent_over_claims_and_the_prober_checks_it():
    """Descent proposes a box; the region around a corner is not always one.

    Measured, not assumed: this reference sits where the per-field answers
    combine into a region containing rejected points, which is why the prober
    confirms a box point by point instead of trusting it.
    """
    validator = Validator(ACCRETED, uniform=False)
    oracle = Oracle(validator)
    corner = Ref("https", "docs.example.com", "png", 1, "ok")
    assert validator(corner).ok
    box = descend(corner, oracle.query)
    rejected = [p for p in box.points() if not validator(p).ok]
    assert rejected, "the over-claim this guard exists for is gone"


# ── the model it produces ────────────────────────────────────────────────────

def test_the_model_never_claims_a_rejected_reference():
    for boundary in (ACCRETED, CARVE_OUT, CLASS):
        truth = V.accepted_set(boundary)
        for uniform in (False, True):
            run = characterise(Validator(boundary, uniform=uniform), truth, seed=1)
            assert run.model <= truth


def test_the_model_ends_up_exactly_right():
    for run in completes(CLASS, False):
        assert run.probes_to_complete is not None
        assert run.model == V.accepted_set(CLASS)


def test_the_prober_respects_its_budget():
    truth = V.accepted_set(CARVE_OUT)
    run = characterise(Validator(CARVE_OUT, uniform=True), truth, seed=0, budget=300)
    assert run.probes <= 300
    assert run.probes_to_complete is None


def test_the_prober_reads_codes_as_opaque_labels():
    """Rename every error code and nothing may change.

    If the probe counts moved, the measured advantage of helpful errors would
    be an artefact of what this specimen's strings say rather than of the fact
    that they differ from each other.
    """
    truth = V.accepted_set(ACCRETED)
    renamed = {code: f"zz-{i}" for i, code in enumerate(sorted(set(ACCRETED.codes())))}
    plain = characterise(Validator(ACCRETED, uniform=False), truth, seed=3)
    scrambled = characterise(
        Validator(ACCRETED, uniform=False), truth, seed=3,
        label_of=lambda ref, verdict: renamed.get(verdict.code, verdict.code))
    assert plain.probes_to_complete == scrambled.probes_to_complete
    assert plain.model == scrambled.model


def test_collapsing_the_codes_is_what_costs_the_prober():
    """The same validator, the same seed, codes merged into one by relabelling
    rather than by a different validator. Nothing else in the run differs."""
    truth = V.accepted_set(CARVE_OUT)
    distinct = characterise(Validator(CARVE_OUT, uniform=False), truth, seed=0)
    merged = characterise(
        Validator(CARVE_OUT, uniform=False), truth, seed=0,
        label_of=lambda ref, verdict: V.ACCEPT_CODE if verdict.ok else V.UNIFORM_CODE)
    assert merged.probes_to_complete > 5 * distinct.probes_to_complete


# ── the published numbers ────────────────────────────────────────────────────

def test_uniform_errors_cost_the_prober_more_on_both_boundaries():
    for boundary, floor in ((ACCRETED, 2.0), (CARVE_OUT, 5.0)):
        helpful = statistics.median(r.probes_to_complete for r in completes(boundary, False))
        uniform = statistics.median(r.probes_to_complete for r in completes(boundary, True))
        assert uniform > floor * helpful, f"{boundary.name}: {uniform} vs {helpful}"


def test_the_gradient_walk_stays_cheap():
    """Pins the numerator of the published ratio, in both directions.

    The ratio alone does not defend it: a change that made the helpful prober
    wasteful would lower the ratio without breaking a band on the ratio, while
    RESULTS.md went on quoting the old numerator. The mutation check found
    exactly that hole — 'the climb does not stop on an accepted reference'
    survived the first pass — and this is the assertion that closes it.
    """
    accreted = statistics.median(r.probes_to_complete for r in completes(ACCRETED, False))
    carve = statistics.median(r.probes_to_complete for r in completes(CARVE_OUT, False))
    assert 200 < accreted < 2_500, accreted
    assert 100 < carve < 1_200, carve


def test_the_isolated_boundary_pays_more_than_the_adjacent_one():
    """The finding that pattern 02 does not state: the multiplier is geometry.

    A band rather than a floor. If the carve-out advantage ever collapsed to
    the accreted one, the geometry claim would be wrong and RESULTS.md would
    need rewriting rather than re-quoting.
    """
    def ratio(boundary):
        helpful = statistics.median(r.probes_to_complete for r in completes(boundary, False))
        uniform = statistics.median(r.probes_to_complete for r in completes(boundary, True))
        return uniform / helpful

    accreted, carve = ratio(ACCRETED), ratio(CARVE_OUT)
    assert 3 < accreted < 40, accreted
    assert 15 < carve < 400, carve
    assert carve > 2 * accreted


def test_the_class_refusal_is_mapped_identically_either_way():
    """It has one code already, so 'uniform errors' is not a change to it —
    which is the point of half one, asserted."""
    helpful = completes(CLASS, False)
    uniform = completes(CLASS, True)
    assert [r.probes_to_complete for r in helpful] == [r.probes_to_complete for r in uniform]


def test_the_class_refusal_is_cheap_to_map_and_that_is_fine():
    """Its accepted set is one contiguous region, so blind sampling finds it.
    A boundary whose map is 'local files only' loses nothing by being mapped."""
    uniform = statistics.median(r.probes_to_complete for r in completes(CLASS, True))
    accreted = statistics.median(r.probes_to_complete for r in completes(ACCRETED, True))
    assert uniform < accreted


# ── timing ───────────────────────────────────────────────────────────────────

def test_short_circuit_latency_orders_the_rules():
    """The side channel, asserted on the clock rather than on the code."""
    grouped = probe.refs_by_code(ACCRETED)
    validator = Validator(ACCRETED, uniform=True, costly=True)
    medians = probe.calibrate(validator, grouped, 3, 8)
    ordered = [medians[code] for code in ACCRETED.codes()]
    assert ordered == sorted(ordered), ordered
    assert ordered[-1] > 20 * ordered[0]


def test_constant_work_flattens_the_latency():
    grouped = probe.refs_by_code(ACCRETED)
    validator = Validator(ACCRETED, uniform=True, costly=True, constant_work=True)
    medians = probe.calibrate(validator, grouped, 3, 8)
    assert max(medians.values()) / min(medians.values()) < 1.3


def test_the_classifier_recovers_the_rule_from_latency_alone():
    grouped = probe.refs_by_code(ACCRETED)
    validator = Validator(ACCRETED, uniform=True, costly=True)
    centroids = probe.calibrate(validator, grouped, 3, 8)
    hits = total = 0
    for code, refs in grouped.items():
        for ref in refs[8:16]:
            hits += probe.classify(centroids, probe.latency(validator, ref, 3)) == code
            total += 1
    assert hits / total > 0.9, f"{hits}/{total}"


def test_dominance_is_a_coin_toss_for_identical_samples():
    assert probe.dominance([1, 2, 3], [3, 2, 1]) == 1 / 3
    assert probe.dominance([5, 5], [1, 1]) == 1.0
    assert probe.dominance([1, 1], [5, 5]) == 0.0


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
            except Exception as exc:  # noqa: BLE001 — a crash is a failure, not a stop
                failures += 1
                print(f"  ERROR {name}: {type(exc).__name__}: {exc}")
    print(f"\n{failures} failure(s)")
    raise SystemExit(1 if failures else 0)
