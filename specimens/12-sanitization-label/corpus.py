"""The fleet under study — synthetic build-duration series. Standard library only.

Everything the specimen measures is generated here, in process, from a fixed
seed. Nothing is loaded from a fixture and nothing was derived from a real
system, which is the only way a specimen about re-identification can be
published at all.

The domain is deliberately ordinary: a continuous-integration fleet, one
project per record, one build duration per day in whole seconds. Build times
are a good stand-in for the general case because they have the three properties
that make a series a fingerprint — a characteristic magnitude, a characteristic
spread, and occasional distinctive events.

The fleet is built in **tiers** on purpose. Twelve magnitude tiers, five
projects each, with per-project offsets small enough that projects sharing a
tier overlap. A fleet of sixty wildly different projects would make single-point
re-identification trivial and the measurement meaningless; the tiers are what
make the curve in RESULTS.md worth reading.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

N_PROJECTS = 60
SERIES_POINTS = 20
SEED = 20_260_805

# Twelve magnitude tiers, in seconds. Five projects land on each.
TIERS = (90, 120, 150, 185, 220, 260, 300, 350, 410, 480, 560, 650)

PROJECT_OFFSET = 0.06  # per-project deviation from its tier, +/-
DAILY_JITTER = 0.08  # day-to-day deviation from the project's own level, +/-
PEAK_MULTIPLIER = (1.9, 2.3)  # one slow day per project — a dependency refresh

_ADJECTIVES = (
    "amber", "basalt", "cobalt", "cedar", "dune", "ember",
    "flint", "garnet", "harbor", "indigo", "juniper", "kestrel",
)
_NOUNS = ("indexer", "packager", "linter", "scheduler", "compactor")

ENVIRONMENTS = ("staging", "canary", "preprod")


@dataclass(frozen=True)
class Project:
    """One record as it exists internally, before anyone sanitises anything."""

    name: str
    owner: str
    series: tuple[int, ...]
    run_id: str
    environment: str

    @property
    def provenance(self) -> str:
        """The line that makes the artefact auditable, and points back at us."""
        return f"derived from run {self.run_id} ({self.environment})"


def _approx_normal(rng: random.Random) -> float:
    """Standard-normal-ish, from three uniforms. sd is 0.5 by construction.

    Deliberately built from `random()` alone. That is the one method whose
    sequence CPython guarantees to be stable across releases, so the corpus is
    reproducible on a reader's machine rather than merely on mine.
    """
    return (rng.random() + rng.random() + rng.random()) - 1.5


def build_fleet(
    n: int = N_PROJECTS, points: int = SERIES_POINTS, seed: int = SEED
) -> list[Project]:
    """Generate the internal fleet. Deterministic for a given seed."""
    rng = random.Random(seed)
    fleet: list[Project] = []

    for i in range(n):
        tier = TIERS[i % len(TIERS)]
        level = tier * (1.0 + PROJECT_OFFSET * 2 * (rng.random() - 0.5))
        peak_day = int(rng.random() * points)

        series = []
        for day in range(points):
            value = level * (1.0 + DAILY_JITTER * 2 * (rng.random() - 0.5))
            if day == peak_day:
                lo, hi = PEAK_MULTIPLIER
                value *= lo + (hi - lo) * rng.random()
            series.append(int(round(value)))

        name = f"{_ADJECTIVES[i % len(_ADJECTIVES)]}-{_NOUNS[i // len(_ADJECTIVES)]}"
        run_id = f"{int(rng.random() * (1 << 24)):06x}"

        fleet.append(
            Project(
                name=name,
                owner=f"team-{chr(ord('a') + i % 6)}",
                series=tuple(series),
                run_id=run_id,
                environment=ENVIRONMENTS[i % len(ENVIRONMENTS)],
            )
        )

    return fleet


def pooled_values(fleet: list[Project]) -> list[int]:
    """Every measurement in the fleet, ignoring which project it came from."""
    return [v for p in fleet for v in p.series]


def median(values) -> float:
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def percentile(values, q: float) -> float:
    """Nearest-rank percentile. Exact, no interpolation, no dependency."""
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    rank = max(1, min(len(ordered), int(round(q / 100.0 * len(ordered)))))
    return float(ordered[rank - 1])


def relative_spread(values, centre: float) -> float:
    """Standard deviation of value/centre - 1. The shape parameter that a
    'synthetic' regeneration has to reproduce to be useful at all."""
    if centre == 0:
        return 0.0
    rel = [v / centre - 1.0 for v in values]
    mean = sum(rel) / len(rel)
    var = sum((r - mean) ** 2 for r in rel) / len(rel)
    return var**0.5
