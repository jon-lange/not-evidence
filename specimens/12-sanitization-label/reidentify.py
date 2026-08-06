"""The attack. Standard library only, and small enough to read in one sitting.

Three adversaries, in increasing order of how little they need to hold:

  exact   holds the counterpart values verbatim. Matches by exact contiguous
          subsequence. This is the vendor-ticket case: they have the internal
          copy, you published the 'sanitised' one, and a join is a dictionary
          lookup.

  noisy   holds an independently measured fragment — same builds, their own
          instrumentation, a few percent off. Matches by nearest window under
          mean absolute difference. This is the harder and more realistic case,
          and it is the one that says something about series in general.

  shape   holds the fragment in the original units, while the published values
          have been multiplied by a constant nobody disclosed. Matches on
          mean-normalised windows, so magnitude is discarded and only shape
          remains. This exists to test the pattern's actual claim — that the
          *shape* is the fingerprint — rather than the easier claim that
          identical numbers are identical.

A trial is one (entity, window offset) pair. Per-trial rows are what the probe
writes to JSONL; the curves are aggregates of them, computed afterwards, because
a harness that stores only the means has thrown away everything a later question
would need.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from sanitize import Release

MATCH_MODES = ("exact", "noisy", "shape")

# How far the noisy adversary's independent measurement is off, per point.
NOISE_FRACTION = 0.03

# The undisclosed constant in the 'we normalised the units' release.
UNIT_SCALE = 1.37


@dataclass(frozen=True)
class Trial:
    """One re-identification attempt. This is the row that reaches the JSONL."""

    release: str
    mode: str
    k: int
    entity: int
    offset: int
    candidates: int
    correct: bool
    unique_and_correct: bool


def windows(series: tuple[int, ...], k: int):
    """Every contiguous k-point window, as (offset, tuple)."""
    for offset in range(len(series) - k + 1):
        yield offset, series[offset : offset + k]


# ── exact subsequence matching ───────────────────────────────────────────────


def build_index(release: Release, k: int) -> dict[tuple[int, ...], set[int]]:
    """Map every published k-window to the rows containing it.

    The index is the whole point of the exact attack: once built, matching a
    fragment costs one dictionary lookup, so 'trivially re-linkable' is meant
    literally rather than rhetorically.
    """
    index: dict[tuple[int, ...], set[int]] = {}
    for row, record in enumerate(release.records):
        for _, window in windows(record.series, k):
            index.setdefault(window, set()).add(row)
    return index


def exact_candidates(fragment: tuple[int, ...], index) -> set[int]:
    return set(index.get(tuple(fragment), ()))


# ── nearest-window matching ──────────────────────────────────────────────────


def _l1(a, b) -> float:
    return sum(abs(x - y) for x, y in zip(a, b))


def _normalised(window):
    """Divide by the window mean. Discards magnitude, keeps shape."""
    mean = sum(window) / len(window)
    if mean == 0:
        return tuple(0.0 for _ in window)
    return tuple(v / mean for v in window)


def candidate_windows(release: Release, k: int, *, normalise: bool = False):
    """Flatten the release into (row, window) pairs, once per k."""
    out = []
    for row, record in enumerate(release.records):
        for _, window in windows(record.series, k):
            out.append((row, _normalised(window) if normalise else window))
    return out


def nearest_row(fragment, flat, *, normalise: bool = False) -> tuple[int, float]:
    """The published row whose closest window is nearest the fragment.

    Ties resolve to the lowest row index. That is a deliberate choice in the
    adversary's *disfavour* for this specimen's scoring — a tie counts as a
    single guess, not as a shortlist, so the numbers reported are what one
    guess buys.
    """
    probe = _normalised(fragment) if normalise else tuple(fragment)
    best_row, best_distance = -1, float("inf")
    for row, window in flat:
        distance = _l1(probe, window)
        if distance < best_distance:
            best_row, best_distance = row, distance
    return best_row, best_distance


# ── the adversary's fragment ─────────────────────────────────────────────────


def perturb(fragment: tuple[int, ...], entity: int, offset: int) -> tuple[int, ...]:
    """The noisy adversary's own measurement of the same builds.

    Deterministic given (entity, offset) so a rerun reproduces the trial
    exactly, and deliberately not centred noise-free: every point moves.
    """
    out = []
    for i, value in enumerate(fragment):
        # A fixed, seed-free hash mix. Reproducible on any interpreter.
        h = (entity * 7919 + offset * 104_729 + i * 15_485_863) % 1_000_003
        direction = (h / 1_000_003.0) * 2 - 1
        out.append(int(round(value * (1.0 + NOISE_FRACTION * direction))))
    return tuple(out)


# ── the measurement ──────────────────────────────────────────────────────────


def run_trials(
    fleet,
    release: Release,
    mode: str,
    k: int,
    *,
    max_offsets: int | None = None,
    adversary_quantum: int = 1,
) -> list[Trial]:
    """Every (entity, offset) trial at one fragment length, for one adversary.

    The adversary's fragment always comes from the *original* fleet, never from
    the published release. That is what makes this a re-identification
    measurement rather than a self-join: under a sanitiser that perturbs values,
    the fragment no longer appears in the release at all, and the attack is
    entitled to fail.

    `adversary_quantum` models the one thing coarsening does *not* hide: the
    published resolution is visible in the file, so an adversary attacking a
    release rounded to the minute rounds their own fragment to the minute too.
    Scoring coarsening against an adversary who did not notice would overstate
    it.
    """
    if mode not in MATCH_MODES:
        raise ValueError(f"unknown match mode {mode!r}")

    index = build_index(release, k) if mode == "exact" else None
    flat = None if mode == "exact" else candidate_windows(release, k, normalise=mode == "shape")

    trials: list[Trial] = []
    for entity, project in enumerate(fleet):
        offsets = [o for o, _ in windows(project.series, k)]
        if max_offsets is not None and len(offsets) > max_offsets:
            step = len(offsets) / max_offsets
            offsets = [offsets[int(i * step)] for i in range(max_offsets)]

        for offset in offsets:
            fragment = project.series[offset : offset + k]
            if mode == "noisy":
                fragment = perturb(fragment, entity, offset)
            if adversary_quantum > 1:
                fragment = tuple(
                    int(round(v / adversary_quantum)) * adversary_quantum for v in fragment
                )

            target = release.truth[entity]

            if mode == "exact":
                hits = exact_candidates(fragment, index)
                candidates = len(hits)
                correct = target in hits
                unique = candidates == 1 and correct
            else:
                row, _ = nearest_row(fragment, flat, normalise=mode == "shape")
                candidates = 1
                correct = row == target
                unique = correct

            trials.append(
                Trial(release.label, mode, k, entity, offset, candidates, correct, unique)
            )

    return trials


def rate(trials: list[Trial]) -> float:
    """Share of trials that pinned exactly one row, and the right one."""
    if not trials:
        return 0.0
    return sum(t.unique_and_correct for t in trials) / len(trials)


def mean_candidates(trials: list[Trial]) -> float:
    if not trials:
        return 0.0
    return sum(t.candidates for t in trials) / len(trials)


# ── whole-record joins, for cells 1 and 3 ────────────────────────────────────


def link_by_values(fleet, release: Release) -> dict[int, int]:
    """Join original to published on the exact full series. Cell 1."""
    by_series: dict[tuple[int, ...], int] = {}
    for row, record in enumerate(release.records):
        by_series.setdefault(record.series, row)
    return {i: by_series[p.series] for i, p in enumerate(fleet) if p.series in by_series}


def link_by_provenance(fleet, release: Release) -> dict[int, int]:
    """Join on the provenance line alone, ignoring every number. Cell 3."""
    by_prov: dict[str, int] = {}
    for row, record in enumerate(release.records):
        if record.provenance:
            by_prov.setdefault(record.provenance, row)
    return {i: by_prov[p.provenance] for i, p in enumerate(fleet) if p.provenance in by_prov}


def correct_links(links: dict[int, int], release: Release) -> int:
    return sum(1 for entity, row in links.items() if release.truth[entity] == row)


def trial_rows(trials: list[Trial]) -> list[dict]:
    return [asdict(t) for t in trials]
