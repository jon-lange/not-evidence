"""Two sanitisers: the one people write, and the one the job actually needs.

`naive_sanitize` is not a straw man. It is the operation the word *sanitised*
denotes in practice — substitute the names, shuffle the rows, ship it. It has an
obvious target, an obvious stopping point, and it is verifiable at a glance,
which is exactly why it is what gets written.

`resynthesize` is the same function with the knobs the naive one does not have:
perturb the values, coarsen them, regenerate them from a model, and drop the
provenance. Each knob is separate because the specimen's finding is that they do
not substitute for one another — and in particular that the last one, the
cheapest and most obviously correct, is the one that gets left off.

The row order is shuffled by every sanitiser here. That matters: without it,
position alone re-links the release to the original and the demonstration would
be about record ordering rather than about values. The attack in `reidentify.py`
has to go through the numbers.
"""

from __future__ import annotations

import random
import zlib
from dataclasses import dataclass, replace

import corpus
from corpus import Project

RESYNTH_SEED = 771_003


@dataclass(frozen=True)
class Record:
    """One published row. Note what is *not* here: the original name.

    Note also what is: the whole series, and — unless someone remembers — the
    provenance line. A reader of this dataclass sees a de-identified record.
    """

    label: str
    series: tuple[int, ...]
    provenance: str | None


@dataclass(frozen=True)
class Release:
    """A published artefact plus the mapping that was never published.

    `truth[i]` is the index in `records` of the row derived from `fleet[i]`. It
    exists so the harness can score the attack. It is deliberately *not* a field
    on `Record`: a re-identification measurement whose answer key travels inside
    the artefact is measuring nothing.
    """

    label: str
    records: tuple[Record, ...]
    truth: tuple[int, ...]

    def series_of(self, published_index: int) -> tuple[int, ...]:
        return self.records[published_index].series


def _shuffled_order(n: int, seed: int) -> list[int]:
    """Fisher-Yates on `random()` alone, so the order is stable across CPython
    releases. `random.shuffle` is not guaranteed to be."""
    rng = random.Random(seed)
    order = list(range(n))
    for i in range(n - 1, 0, -1):
        j = int(rng.random() * (i + 1))
        order[i], order[j] = order[j], order[i]
    return order


def _assemble(label: str, rows: list[Record], seed: int) -> Release:
    order = _shuffled_order(len(rows), seed)
    records = [rows[src] for src in order]
    truth = [0] * len(rows)
    for published_index, source_index in enumerate(order):
        truth[source_index] = published_index
    return Release(label, tuple(records), tuple(truth))


def naive_sanitize(fleet: list[Project], seed: int = RESYNTH_SEED) -> Release:
    """Substitute the names. Shuffle the rows. Change nothing else.

    This is the dominant real-world operation, and the label it earns is
    'sanitised'. Every measurement survives verbatim and so does the provenance
    line, because neither of those looks like an identifier.
    """
    rows = [
        Record(label=f"project-{i:02d}", series=p.series, provenance=p.provenance)
        for i, p in enumerate(fleet)
    ]
    return _assemble("names substituted only", rows, seed)


def resynthesize(
    fleet: list[Project],
    *,
    label: str,
    scale: float = 1.0,
    jitter: float = 0.0,
    quantum: int = 1,
    regenerate: str | None = None,
    strip_provenance: bool = False,
    seed: int = RESYNTH_SEED,
) -> Release:
    """The sanitiser with the knobs that actually move re-identification.

    scale
        Multiply every value by one constant — 'we normalised the units'. This
        is included because it is a real thing people do and because it changes
        every number in the file, which makes it feel like the strongest
        operation here. It preserves shape exactly.
    jitter
        Independent relative perturbation of every value, +/- this fraction.
    quantum
        Round to this many seconds. Coarsening, the mitigation the pattern
        names: round until a join fails.
    regenerate
        None      values are perturbed originals
        'entity'  values are drawn fresh from a model fitted to *that project* —
                  its own median and its own relative spread. Nothing is a real
                  measurement any more, and the magnitude survives.
        'fleet'   values are drawn fresh from a model fitted to the whole fleet.
                  Per-project magnitude is gone, and so is most of the utility.
    strip_provenance
        Drop the provenance line. One boolean, no cost, routinely forgotten.
    """
    # `hash()` on a str is salted per process, so it cannot appear in a seed.
    # This is a small thing that would have silently destroyed reproducibility.
    rng = random.Random(seed ^ zlib.crc32(label.encode()))

    pool = corpus.pooled_values(fleet)
    fleet_centre = corpus.median(pool)
    fleet_spread = corpus.relative_spread(pool, fleet_centre)

    rows: list[Record] = []
    for i, project in enumerate(fleet):
        if regenerate == "entity":
            centre = corpus.median(project.series)
            spread = corpus.relative_spread(project.series, centre)
        elif regenerate == "fleet":
            centre, spread = fleet_centre, fleet_spread
        else:
            centre = spread = None

        values = []
        for original in project.series:
            if centre is None:
                value = original * scale
            else:
                # sd of _approx_normal is 0.5, so double it to hit `spread`.
                value = centre * (1.0 + 2.0 * spread * corpus._approx_normal(rng)) * scale
            if jitter:
                value *= 1.0 + jitter * 2 * (rng.random() - 0.5)
            value = max(1.0, value)
            values.append(int(round(value / quantum)) * quantum)

        rows.append(
            Record(
                label=f"project-{i:02d}",
                series=tuple(values),
                provenance=None if strip_provenance else project.provenance,
            )
        )

    return _assemble(label, rows, seed)


def strip_provenance(release: Release) -> Release:
    """The one-line fix, applied after the fact — for showing what it is worth."""
    return replace(
        release,
        records=tuple(replace(r, provenance=None) for r in release.records),
    )
