"""Tests for the corpus and the two sanitisers.

Run: python3 test_sanitize.py   (or: python3 -m pytest test_sanitize.py -q)

No network, no dependencies. The claim is about data, and the data is generated
in process, so everything asserted here is local and reproducible.

Several of these tests assert properties of the *corpus* rather than of the
code — that projects share magnitude tiers, that one point is not enough. Those
are load-bearing. Every number this specimen publishes is a function of how much
entropy the fleet has, and a change that quietly spread the projects further
apart would inflate the headline result without breaking anything else.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import corpus
import sanitize
from sanitize import naive_sanitize, resynthesize

HERE = Path(__file__).parent


# ── the corpus ───────────────────────────────────────────────────────────────

def test_fleet_is_deterministic():
    """Two builds must be byte-identical, or nothing downstream is reproducible."""
    assert corpus.build_fleet() == corpus.build_fleet()


def test_fleet_has_the_advertised_shape():
    fleet = corpus.build_fleet()
    assert len(fleet) == corpus.N_PROJECTS
    assert all(len(p.series) == corpus.SERIES_POINTS for p in fleet)
    assert len({p.name for p in fleet}) == len(fleet)
    assert len({p.run_id for p in fleet}) == len(fleet)


def test_projects_overlap_in_magnitude():
    """The tiers exist so that a single measurement is not a giveaway.

    Without collisions the k=1 row of the curve would read 100% and the whole
    measurement would be an artefact of having generated sixty obviously
    different projects.
    """
    fleet = corpus.build_fleet()
    owners: dict[int, set[int]] = {}
    for i, project in enumerate(fleet):
        for value in project.series:
            owners.setdefault(value, set()).add(i)
    shared = [v for v, who in owners.items() if len(who) > 1]
    assert shared, "no measurement is shared by two projects — the fleet is too spread out"


def test_the_peak_day_is_visible():
    """Each project has one distinctly slow build. Part of what makes a shape."""
    fleet = corpus.build_fleet()
    for project in fleet:
        assert max(project.series) > 1.5 * corpus.median(project.series)


def test_percentile_is_nearest_rank():
    assert corpus.percentile([1, 2, 3, 4], 50) == 2
    assert corpus.percentile([1, 2, 3, 4], 100) == 4
    assert corpus.percentile([5], 50) == 5


# ── the naive sanitiser ──────────────────────────────────────────────────────

def test_naive_sanitize_removes_every_name():
    fleet = corpus.build_fleet()
    release = naive_sanitize(fleet)
    blob = repr(release.records)
    for project in fleet:
        assert project.name not in blob
        assert project.owner not in blob


def test_naive_sanitize_keeps_every_measurement_verbatim():
    """The finding of cell 1, asserted. This is the operation as performed."""
    fleet = corpus.build_fleet()
    release = naive_sanitize(fleet)
    published = {r.series for r in release.records}
    assert published == {p.series for p in fleet}


def test_naive_sanitize_shuffles_the_rows():
    """Otherwise position alone re-links and the specimen proves nothing."""
    fleet = corpus.build_fleet()
    release = naive_sanitize(fleet)
    assert list(release.truth) != list(range(len(fleet)))


def test_truth_maps_each_original_to_its_own_row():
    fleet = corpus.build_fleet()
    release = naive_sanitize(fleet)
    assert sorted(release.truth) == list(range(len(fleet)))
    for entity, project in enumerate(fleet):
        assert release.series_of(release.truth[entity]) == project.series


def test_naive_sanitize_keeps_the_provenance_line():
    """Not an oversight in the specimen — it is the specimen."""
    fleet = corpus.build_fleet()
    release = naive_sanitize(fleet)
    assert all(r.provenance for r in release.records)
    assert fleet[0].run_id in " ".join(r.provenance for r in release.records)


# ── the real sanitiser ───────────────────────────────────────────────────────

def test_scale_multiplies_every_value():
    fleet = corpus.build_fleet()
    release = resynthesize(fleet, label="scaled", scale=2.0)
    for entity, project in enumerate(fleet):
        got = release.series_of(release.truth[entity])
        assert got == tuple(v * 2 for v in project.series)


def test_jitter_moves_almost_every_value():
    fleet = corpus.build_fleet()
    release = resynthesize(fleet, label="jittered", jitter=0.25)
    moved = same = 0
    for entity, project in enumerate(fleet):
        for before, after in zip(project.series, release.series_of(release.truth[entity])):
            moved += before != after
            same += before == after
    assert moved > 10 * same, f"{same} values survived unchanged out of {moved + same}"


def test_quantum_rounds_every_value():
    fleet = corpus.build_fleet()
    release = resynthesize(fleet, label="rounded", quantum=60)
    assert all(v % 60 == 0 for r in release.records for v in r.series)


def test_per_project_regeneration_keeps_the_magnitude():
    """The finding behind the last table: 'synthetic' that preserves per-entity
    statistics preserves the thing the attack uses."""
    fleet = corpus.build_fleet()
    release = resynthesize(fleet, label="entity", regenerate="entity")
    kept = 0
    for entity, project in enumerate(fleet):
        internal = corpus.median(project.series)
        published = corpus.median(release.series_of(release.truth[entity]))
        kept += abs(published / internal - 1.0) <= 0.25
    assert kept > 0.7 * len(fleet), f"only {kept}/{len(fleet)} medians survived"


def test_per_project_regeneration_invents_new_values():
    fleet = corpus.build_fleet()
    release = resynthesize(fleet, label="entity", regenerate="entity")
    for entity, project in enumerate(fleet):
        assert release.series_of(release.truth[entity]) != project.series


def test_fleet_regeneration_destroys_the_magnitude():
    fleet = corpus.build_fleet()
    release = resynthesize(fleet, label="fleet", regenerate="fleet")
    kept = 0
    for entity, project in enumerate(fleet):
        internal = corpus.median(project.series)
        published = corpus.median(release.series_of(release.truth[entity]))
        kept += abs(published / internal - 1.0) <= 0.10
    assert kept < 0.4 * len(fleet), f"{kept}/{len(fleet)} medians survived a pooled model"


def test_strip_provenance_flag_removes_it():
    fleet = corpus.build_fleet()
    release = resynthesize(fleet, label="stripped", strip_provenance=True)
    assert all(r.provenance is None for r in release.records)


def test_strip_provenance_helper_removes_it_after_the_fact():
    fleet = corpus.build_fleet()
    stripped = sanitize.strip_provenance(naive_sanitize(fleet))
    assert all(r.provenance is None for r in stripped.records)
    assert stripped.truth == naive_sanitize(fleet).truth


def test_resynthesis_is_deterministic():
    fleet = corpus.build_fleet()
    a = resynthesize(fleet, label="x", regenerate="entity")
    b = resynthesize(fleet, label="x", regenerate="entity")
    assert a.records == b.records


def test_different_labels_draw_differently():
    """Each configuration must get its own stream, or two rows of the last table
    would be the same experiment reported twice."""
    fleet = corpus.build_fleet()
    a = resynthesize(fleet, label="x", regenerate="entity")
    b = resynthesize(fleet, label="y", regenerate="entity")
    assert a.records != b.records


def test_output_does_not_depend_on_the_hash_seed():
    """`hash()` on a str is salted per process. Seeding anything with it would
    make the corpus reproducible only within a single run — the failure this
    repository exists to catch, in the code that measures it."""
    script = (
        "import corpus, sanitize;"
        "f = corpus.build_fleet();"
        "r = sanitize.resynthesize(f, label='fleet model', regenerate='fleet');"
        "print(sum(v for rec in r.records for v in rec.series))"
    )
    digests = set()
    for seed in ("0", "1", "12345"):
        proc = subprocess.run(
            [sys.executable, "-c", script],
            cwd=HERE,
            env={"PATH": "/usr/bin:/bin", "PYTHONHASHSEED": seed},
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, proc.stderr
        digests.add(proc.stdout.strip())
    assert len(digests) == 1, f"output varied with PYTHONHASHSEED: {digests}"


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
