"""Tests for the re-identification attack, and for the probe that reports it.

Run: python3 test_reidentify.py   (or: python3 -m pytest test_reidentify.py -q)

Three of these pin *numbers* rather than behaviours —
test_one_point_is_usually_not_enough, test_four_points_identify_every_project,
and test_shape_matching_collapses_under_jitter. They are the ones that would
break if the corpus were retuned, which is the point: the headline results in
RESULTS.md are properties of a fleet with a chosen amount of entropy, and a
change that quietly made re-identification easier should fail the suite rather
than improve the write-up.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import corpus
import reidentify as attack
import sanitize
from reidentify import (
    build_index,
    candidate_windows,
    exact_candidates,
    link_by_provenance,
    link_by_values,
    nearest_row,
    perturb,
    rate,
    run_trials,
    windows,
)
from sanitize import naive_sanitize, resynthesize

HERE = Path(__file__).parent
TRIALS = HERE / "_generated" / "trials.jsonl"

SMALL = dict(n=20, points=10)


def small_fleet():
    return corpus.build_fleet(**SMALL)


# ── the mechanics ────────────────────────────────────────────────────────────

def test_windows_covers_every_offset():
    got = list(windows((1, 2, 3, 4), 2))
    assert got == [(0, (1, 2)), (1, (2, 3)), (2, (3, 4))]


def test_windows_of_full_length_is_the_whole_series():
    assert list(windows((1, 2, 3), 3)) == [(0, (1, 2, 3))]


def test_index_maps_a_window_to_the_rows_containing_it():
    fleet = small_fleet()
    release = naive_sanitize(fleet)
    index = build_index(release, 3)
    for entity, project in enumerate(fleet):
        assert release.truth[entity] in exact_candidates(project.series[:3], index)


def test_exact_candidates_is_empty_for_a_fragment_nobody_has():
    release = naive_sanitize(small_fleet())
    assert exact_candidates((-1, -2, -3), build_index(release, 3)) == set()


def test_nearest_row_finds_an_exact_window():
    fleet = small_fleet()
    release = naive_sanitize(fleet)
    flat = candidate_windows(release, 4)
    for entity, project in enumerate(fleet):
        row, distance = nearest_row(project.series[2:6], flat)
        assert row == release.truth[entity]
        assert distance == 0


def test_shape_matching_ignores_a_constant_scale():
    """The rescale defence, defeated in one assertion."""
    fleet = small_fleet()
    release = resynthesize(fleet, label="scaled", scale=attack.UNIT_SCALE)
    flat = candidate_windows(release, 5, normalise=True)
    hits = sum(
        nearest_row(p.series[0:5], flat, normalise=True)[0] == release.truth[e]
        for e, p in enumerate(fleet)
    )
    assert hits >= 0.8 * len(fleet), f"only {hits}/{len(fleet)} matched by shape"


def test_raw_matching_does_not_survive_a_rescale():
    """The counterpart: without normalisation the same attack fails, which is
    what makes the previous test a statement about shape rather than luck."""
    fleet = small_fleet()
    release = resynthesize(fleet, label="scaled", scale=attack.UNIT_SCALE)
    flat = candidate_windows(release, 5)
    hits = sum(
        nearest_row(p.series[0:5], flat)[0] == release.truth[e] for e, p in enumerate(fleet)
    )
    assert hits <= 0.25 * len(fleet)


def test_perturb_moves_every_point_but_only_a_little():
    fragment = (300, 305, 298, 310)
    noisy = perturb(fragment, entity=3, offset=1)
    assert noisy != fragment
    for before, after in zip(fragment, noisy):
        assert abs(after / before - 1.0) <= attack.NOISE_FRACTION + 1e-9


def test_perturb_is_deterministic():
    assert perturb((100, 200), 1, 2) == perturb((100, 200), 1, 2)
    assert perturb((100, 200), 1, 2) != perturb((100, 200), 2, 2)


def test_adversary_quantum_rounds_the_fragment():
    """A coarsened release is scored against an adversary who noticed. Without
    this the coarsening column would measure the adversary's carelessness."""
    fleet = small_fleet()
    release = resynthesize(fleet, label="rounded", quantum=60)
    blind = rate(run_trials(fleet, release, "exact", 4))
    aware = rate(run_trials(fleet, release, "exact", 4, adversary_quantum=60))
    assert blind == 0.0
    assert aware > blind


# ── the curve ────────────────────────────────────────────────────────────────

def test_one_point_is_usually_not_enough():
    """Guards the corpus entropy, in a band rather than with a loose bound.

    A published k=1 rate of 21.9% is the reason the rest of the curve means
    anything. This test originally read `0 < r < 0.5`, and the mutation check
    found that a tenfold increase in per-project spread sailed through it — the
    suite would have accepted a materially different fleet while RESULTS.md went
    on quoting the old numbers. The band is tight on purpose.
    """
    fleet = corpus.build_fleet()
    trials = run_trials(fleet, naive_sanitize(fleet), "exact", 1)
    r, candidates = rate(trials), attack.mean_candidates(trials)
    assert 0.15 <= r <= 0.30, f"k=1 unique rate was {r:.3f}; the fleet was retuned"
    assert candidates >= 2.2, f"one point narrows sixty projects to {candidates:.2f}"


def test_four_points_identify_every_project():
    """The headline. Four consecutive build durations out of a twenty-point
    series pin one project in sixty, every trial, with no exceptions."""
    fleet = corpus.build_fleet()
    trials = run_trials(fleet, naive_sanitize(fleet), "exact", 4)
    assert rate(trials) == 1.0
    assert all(t.candidates == 1 for t in trials)


def test_the_curve_is_monotone_in_k():
    fleet = corpus.build_fleet()
    release = naive_sanitize(fleet)
    rates = [rate(run_trials(fleet, release, "exact", k)) for k in (1, 2, 3, 4)]
    assert rates == sorted(rates)


def test_a_noisy_adversary_beats_chance_without_verbatim_values():
    """No value the adversary holds appears in the release, and they still win."""
    fleet = small_fleet()
    release = naive_sanitize(fleet)
    trials = run_trials(fleet, release, "noisy", 4, max_offsets=3)
    assert rate(trials) > 5.0 / len(fleet)


def test_fragments_come_from_the_fleet_not_from_the_release():
    """If the attack sampled its fragment out of the published artefact it would
    always succeed, and the measurement would be a self-join."""
    fleet = small_fleet()
    release = resynthesize(fleet, label="jittered", jitter=0.25)
    assert rate(run_trials(fleet, release, "exact", 4)) == 0.0


def test_shape_matching_collapses_under_jitter():
    """The honest counterweight to the shape result.

    Discarding magnitude beats an exact rescale and then falls apart under a
    perturbation the magnitude-using adversary shrugs off. Pattern 12's 'the
    shape is the fingerprint' is true in a narrower sense than it sounds.
    """
    fleet = corpus.build_fleet()
    release = resynthesize(fleet, label="jittered", jitter=0.03)
    shape = rate(run_trials(fleet, release, "shape", 4, max_offsets=4))
    noisy = rate(run_trials(fleet, release, "noisy", 4, max_offsets=4))
    assert shape < noisy / 2, f"shape {shape:.3f} vs magnitude-using {noisy:.3f}"


def test_pooled_regeneration_reaches_chance():
    fleet = corpus.build_fleet()
    release = resynthesize(fleet, label="fleet model", regenerate="fleet")
    r = rate(run_trials(fleet, release, "noisy", 4, max_offsets=3))
    assert r <= 3.0 / len(fleet), f"pooled model still re-identified at {r:.3f}"


def test_per_project_regeneration_does_not():
    """Reported because it is the uncomfortable one: 'synthetic' data that
    preserves per-project statistics stays well above chance."""
    fleet = corpus.build_fleet()
    release = resynthesize(fleet, label="entity model", regenerate="entity")
    r = rate(run_trials(fleet, release, "noisy", 4, max_offsets=3))
    assert r > 2.0 / len(fleet), f"per-project model reached chance at {r:.3f}"


def test_rate_and_mean_candidates_agree_with_the_trials():
    fleet = small_fleet()
    trials = run_trials(fleet, naive_sanitize(fleet), "exact", 4)
    assert rate(trials) == sum(t.unique_and_correct for t in trials) / len(trials)
    assert attack.mean_candidates(trials) >= 1.0


def test_run_trials_rejects_an_unknown_mode():
    try:
        run_trials(small_fleet(), naive_sanitize(small_fleet()), "vibes", 2)
    except ValueError:
        return
    raise AssertionError("an unknown match mode was accepted")


# ── whole-record joins ───────────────────────────────────────────────────────

def test_link_by_values_recovers_the_entire_naive_release():
    """Cell 1: sixty of sixty, on numbers alone, after names and order are gone."""
    fleet = corpus.build_fleet()
    release = naive_sanitize(fleet)
    links = link_by_values(fleet, release)
    assert attack.correct_links(links, release) == len(fleet)


def test_link_by_values_fails_once_the_values_move():
    fleet = corpus.build_fleet()
    release = resynthesize(fleet, label="jittered", jitter=0.03)
    assert attack.correct_links(link_by_values(fleet, release), release) == 0


def test_provenance_re_identifies_a_fully_regenerated_release():
    """Cell 3, and the sharpest result in the specimen. Not one number in this
    release is a real measurement, and it is still 100% re-identifiable."""
    fleet = corpus.build_fleet()
    release = resynthesize(fleet, label="fleet model", regenerate="fleet")
    assert attack.correct_links(link_by_values(fleet, release), release) == 0
    assert attack.correct_links(link_by_provenance(fleet, release), release) == len(fleet)


def test_stripping_provenance_defeats_that_join():
    fleet = corpus.build_fleet()
    release = resynthesize(
        fleet, label="fleet model stripped", regenerate="fleet", strip_provenance=True
    )
    assert link_by_provenance(fleet, release) == {}


def test_run_ids_are_a_one_to_one_key():
    """What makes the provenance line a join key rather than a category label."""
    fleet = corpus.build_fleet()
    assert len({p.run_id for p in fleet}) == len(fleet)


# ── the probe ────────────────────────────────────────────────────────────────

def _run_probe():
    return subprocess.run(
        [sys.executable, "probe.py"],
        cwd=HERE,
        env={"PATH": "/usr/bin:/bin"},  # no key, no network, nothing to configure
        capture_output=True,
        text=True,
    )


def test_probe_runs_and_prints_all_three_cells():
    proc = _run_probe()
    assert proc.returncode == 0, proc.stderr
    assert "Traceback" not in proc.stderr
    for marker in ("CELL 1", "CELL 2", "CELL 3", "WHAT RE-SYNTHESIS ACTUALLY REQUIRES"):
        assert marker in proc.stdout, marker


def test_probe_persists_per_trial_rows_before_aggregating():
    """A harness that stores only the rates has thrown away the entity and
    offset columns, and with them every question the author did not think of."""
    _run_probe()
    rows = [json.loads(line) for line in TRIALS.read_text().splitlines()]
    assert len(rows) > 10_000
    assert set(rows[0]) == {
        "release", "mode", "k", "entity", "offset", "candidates", "correct",
        "unique_and_correct",
    }
    assert {r["mode"] for r in rows} == set(attack.MATCH_MODES)
    assert len({r["entity"] for r in rows}) == corpus.N_PROJECTS


def test_probe_quick_mode_produces_the_same_shape():
    proc = subprocess.run(
        [sys.executable, "probe.py", "--quick"],
        cwd=HERE,
        env={"PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "CELL 3" in proc.stdout


def test_sanitize_module_is_not_monkeypatched():
    """Cheap guard: importing this file must not have swapped anything out."""
    assert sanitize.naive_sanitize.__module__ == "sanitize"
    assert attack.run_trials.__module__ == "reidentify"


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
