"""Specimen 12 — the label says sanitised; the payload is intact.

Three cells and a curve.

  1  Names substituted, numbers verbatim. The released rows are shuffled and
     renamed, and every one of them joins straight back to its original on an
     exact numeric match.

  2  The series is the fingerprint. An adversary holding a few points of one
     project's series picks it out of sixty — verbatim, independently measured
     to within a few percent, or with every published value multiplied by an
     undisclosed constant. The curve reports how few points that takes.

  3  Provenance strings. 'derived from run 7f3a2c (staging)' is a join key. It
     survives every value-level defence in this file, because it is not a value.

Then: what actual re-synthesis requires, and the configuration under which the
attack finally fails.

No network, no API key, no dependencies. The claim here is about data, and the
data is generated in process, so everything is local and reproducible.

Usage:
    python3 probe.py
    python3 probe.py --quick     # smaller grid; same shape, coarser curve

Reference implementation. Not maintained.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import corpus
import reidentify as attack
import sanitize
from sanitize import Release

OUT = Path(__file__).parent / "_generated"
TRIALS_JSONL = OUT / "trials.jsonl"

K_VALUES = (1, 2, 3, 4, 5, 6, 8, 10)
MAX_OFFSETS_NN = 10  # nearest-window modes are O(fleet x windows); the exact mode is indexed
FIXED_K = 4  # fragment length used for the re-synthesis matrix
RULE = "=" * 92


@dataclass(frozen=True)
class Config:
    label: str
    kwargs: dict


# Ordered by how much work each one looks like, which is almost exactly the
# reverse of how much re-identification it prevents.
CONFIGS = (
    Config("names substituted only", {}),
    Config("+ values rescaled x1.37", {"scale": attack.UNIT_SCALE}),
    Config("+ 3% jitter on every value", {"jitter": 0.03}),
    Config("+ 25% jitter on every value", {"jitter": 0.25}),
    Config("+ rounded to 60 s", {"quantum": 60}),
    Config("regenerated per project", {"regenerate": "entity"}),
    Config("regenerated from fleet model", {"regenerate": "fleet"}),
    Config("regenerated + provenance stripped", {"regenerate": "fleet", "strip_provenance": True}),
)


def build_releases(fleet) -> list[Release]:
    releases = [sanitize.naive_sanitize(fleet)]
    for config in CONFIGS[1:]:
        releases.append(sanitize.resynthesize(fleet, label=config.label, **config.kwargs))
    return releases


class Sink:
    """Per-trial rows to JSONL, written as they are produced.

    Before aggregation, deliberately. A harness that persists only the rates in
    the tables below has discarded the entity and offset columns, and with them
    every question a reader might ask that the author did not think of.
    """

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = path.open("w", encoding="utf-8")
        self.count = 0

    def write(self, trials):
        for row in attack.trial_rows(trials):
            self.handle.write(json.dumps(row, sort_keys=True) + "\n")
            self.count += 1
        return trials

    def close(self):
        self.handle.close()


def pct(value: float) -> str:
    return f"{100 * value:5.1f}%"


# ── cell 1 ───────────────────────────────────────────────────────────────────


def cell_one(fleet, naive: Release) -> None:
    print("\nCELL 1 — the names changed and the numbers did not")
    print("-" * 92)

    links = attack.link_by_values(fleet, naive)
    correct = attack.correct_links(links, naive)

    example = 0
    published = naive.truth[example]
    head = ", ".join(str(v) for v in fleet[example].series[:6])
    print(f"  internal   {fleet[example].name:<20} owner={fleet[example].owner}")
    print(f"             series  [{head}, ...]")
    print(f"             {fleet[example].provenance}")
    print(f"  published  {naive.records[published].label:<20} (row {published} of "
          f"{len(naive.records)}, order shuffled)")
    print(f"             series  [{head}, ...]")
    print(f"             {naive.records[published].provenance}")
    print()
    print(f"  exact full-series join      {correct}/{len(fleet)} rows re-linked, "
          f"{len(links) - correct} wrong")
    print("  the substitution is real — the names are gone, the row order is gone, and the")
    print("  join is a dictionary lookup on numbers nobody thought of as identifying")


# ── cell 2 ───────────────────────────────────────────────────────────────────


def cell_two(fleet, releases: list[Release], sink: Sink, k_values) -> dict:
    naive = releases[0]
    rescaled = releases[1]

    print("\nCELL 2 — the series is the fingerprint")
    print("-" * 92)
    print(f"  Each adversary holds k consecutive points of ONE project and must pick that project")
    print(f"  out of {len(fleet)}. Chance is{pct(1 / len(fleet))}. Fragments always come from the internal")
    print("  fleet, never from the release — so a sanitiser that moves the values is entitled")
    print("  to defeat them.\n")
    print("    exact   verbatim counterpart values, matched by exact subsequence")
    print(f"    noisy   independently measured, every point off by up to "
          f"{attack.NOISE_FRACTION:.0%}, nearest window")
    print(f"    shape   published values secretly multiplied by {attack.UNIT_SCALE}; matched on")
    print("            mean-normalised windows, so magnitude is discarded entirely\n")

    header = f"   {'k':>3}  {'exact':>8} {'candidates':>11}   {'noisy':>8}   {'shape':>8}"
    print(header)
    print("   " + "-" * (len(header) - 3))

    curve = {}
    for k in k_values:
        exact = sink.write(attack.run_trials(fleet, naive, "exact", k))
        noisy = sink.write(
            attack.run_trials(fleet, naive, "noisy", k, max_offsets=MAX_OFFSETS_NN)
        )
        shape = sink.write(
            attack.run_trials(fleet, rescaled, "shape", k, max_offsets=MAX_OFFSETS_NN)
        )
        curve[k] = (attack.rate(exact), attack.mean_candidates(exact),
                    attack.rate(noisy), attack.rate(shape))
        e, c, n, s = curve[k]
        print(f"   {k:>3}  {pct(e):>8} {c:>11.2f}   {pct(n):>8}   {pct(s):>8}")

    return curve


def coarsening(fleet, releases: list[Release], sink: Sink, k_values) -> dict:
    """Exact-match re-identification against releases rounded ever more coarsely.

    'Round until a join fails' is the pattern's own mitigation. This is the
    measurement of how coarse that has to be, against an adversary who rounds
    their own fragment to the published resolution.
    """
    print("\n  Coarsening — the same exact-match adversary against rounded releases")
    print("  (the adversary rounds their own fragment to the published resolution)\n")

    quanta = (1, 10, 60, 300)
    rounded = {
        q: sanitize.resynthesize(fleet, label=f"rounded to {q} s", quantum=q) for q in quanta
    }

    print(f"   {'k':>3}  " + "  ".join(f"{str(q) + ' s':>8}" for q in quanta))
    print("   " + "-" * (5 + 10 * len(quanta)))
    table = {}
    for k in k_values:
        row = []
        for q in quanta:
            trials = sink.write(
                attack.run_trials(fleet, rounded[q], "exact", k, adversary_quantum=q)
            )
            row.append(attack.rate(trials))
        table[k] = row
        print(f"   {k:>3}  " + "  ".join(f"{pct(v):>8}" for v in row))
    return table


# ── cell 3 ───────────────────────────────────────────────────────────────────


def cell_three(fleet, releases: list[Release]) -> None:
    print("\nCELL 3 — provenance strings are themselves the join key")
    print("-" * 92)

    run_ids = {p.run_id for p in fleet}
    environments = sorted({p.environment for p in fleet})
    shape = "all six lowercase hex" if all(
        len(r) == 6 and all(c in "0123456789abcdef" for c in r) for r in run_ids
    ) else "mixed"

    print(f"  the retained line     {fleet[0].provenance!r}")
    print(f"  distinct run ids      {len(run_ids)} in {len(fleet)} rows — a 1:1 key, {shape}")
    print(f"  environments named    {', '.join(environments)}")
    print("  what it asserts       that a run registry exists, what its keys look like, and")
    print("                        which deployment tiers the fleet has\n")

    print(f"   {'release':<38}{'values re-link':>16}{'provenance re-link':>21}")
    print("   " + "-" * 73)
    for release in releases:
        by_values = attack.correct_links(attack.link_by_values(fleet, release), release)
        by_prov = attack.correct_links(attack.link_by_provenance(fleet, release), release)
        print(f"   {release.label:<38}{f'{by_values}/{len(fleet)}':>16}"
              f"{f'{by_prov}/{len(fleet)}':>21}")

    print("\n  Read the last three rows. Values fully regenerated, nothing in the file is a real")
    print("  measurement any more — and the release is still 100% re-identifiable, by a string")
    print("  that was left in because it looked like diligence rather than like data.")


# ── what re-synthesis actually requires ──────────────────────────────────────


MEDIAN_TOLERANCE = 0.10


def median_retention(fleet, release: Release, tol: float = MEDIAN_TOLERANCE) -> float:
    """Share of projects whose published median is within `tol` of the internal one.

    The utility column. Without it this table reads as a list of defences
    ordered by strength, which is the wrong reading: the two configurations
    that defeat the attack are the two that destroy the per-project signal the
    release existed to carry.
    """
    kept = 0
    for entity, project in enumerate(fleet):
        internal = corpus.median(project.series)
        published = corpus.median(release.series_of(release.truth[entity]))
        if internal and abs(published / internal - 1.0) <= tol:
            kept += 1
    return kept / len(fleet)


def resynthesis_matrix(fleet, releases: list[Release], sink: Sink) -> None:
    print(f"\nWHAT RE-SYNTHESIS ACTUALLY REQUIRES  (k={FIXED_K} points, chance "
          f"{pct(1 / len(fleet))})")
    print("-" * 92)
    print("   the last column is the utility being paid: share of projects whose published")
    print(f"   median is still within {MEDIAN_TOLERANCE:.0%} of the internal one\n")
    print(f"   {'release':<38}{'exact':>8}{'noisy':>8}{'shape':>8}{'prov':>7}"
          f"  {'p50':>5}{'p95':>6}{'median kept':>13}")
    print("   " + "-" * 87)

    for config, release in zip(CONFIGS, releases):
        q = config.kwargs.get("quantum", 1)
        rates = []
        for mode in attack.MATCH_MODES:
            trials = sink.write(
                attack.run_trials(
                    fleet, release, mode, FIXED_K,
                    max_offsets=MAX_OFFSETS_NN, adversary_quantum=q,
                )
            )
            rates.append(attack.rate(trials))
        prov = attack.correct_links(attack.link_by_provenance(fleet, release), release)
        values = [v for r in release.records for v in r.series]
        print(f"   {release.label:<38}{pct(rates[0]):>8}{pct(rates[1]):>8}{pct(rates[2]):>8}"
              f"{f'{prov}/{len(fleet)}':>7}  {corpus.percentile(values, 50):>5.0f}"
              f"{corpus.percentile(values, 95):>6.0f}{pct(median_retention(fleet, release)):>13}")

    original = corpus.pooled_values(fleet)
    print(f"   {'(internal original)':<38}{'':>8}{'':>8}{'':>8}{'':>7}  "
          f"{corpus.percentile(original, 50):>5.0f}{corpus.percentile(original, 95):>6.0f}"
          f"{pct(1.0):>13}")


# ── entry point ──────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quick", action="store_true", help="smaller k grid; coarser curve")
    args = ap.parse_args()

    k_values = (1, 2, 4, 8) if args.quick else K_VALUES

    fleet = corpus.build_fleet()
    releases = build_releases(fleet)
    sink = Sink(TRIALS_JSONL)

    print("Specimen 12 — the label says sanitised")
    print(RULE)
    print(f"fleet   {len(fleet)} projects x {len(fleet[0].series)} daily build durations in whole "
          f"seconds,")
    print(f"        {corpus.percentile(corpus.pooled_values(fleet), 50):.0f} s median, "
          f"twelve magnitude tiers, five projects per tier,")
    print("        generated in process from a fixed seed — nothing here came from a real system")
    print(RULE)

    try:
        cell_one(fleet, releases[0])
        curve = cell_two(fleet, releases, sink, k_values)
        coarsening(fleet, releases, sink, k_values)
        cell_three(fleet, releases)
        resynthesis_matrix(fleet, releases, sink)
    finally:
        sink.close()

    unique_at = next((k for k in sorted(curve) if curve[k][0] >= 1.0), None)
    print("\n" + RULE)
    print(
        f"  Every trial above is on disk before it was averaged: {sink.count} rows in\n"
        f"  {TRIALS_JSONL.relative_to(Path(__file__).parent)}.\n"
        "\n"
        "  The substitution in cell 1 is real work, honestly reported. It removes the\n"
        "  names, and it removes nothing else. What ships is a body of entirely\n"
        "  authentic measurements wearing placeholder labels — more dangerous than the\n"
        "  original, because it now carries a word saying it is safe.\n"
    )
    if unique_at:
        print(
            f"  Cell 2 is the one to argue with. {unique_at} consecutive points pin one project\n"
            f"  in {len(fleet)} every time for an adversary holding the counterpart values, and the\n"
            "  shape column says that survives multiplying every published number by a\n"
            "  constant the adversary does not know. De-identifying a series is not\n"
            "  achieved by removing identifiers, because the identifier is the series.\n"
            "\n"
            "  Two honest qualifications, both visible above. Those counts are a property\n"
            "  of THIS fleet's entropy, which was chosen; a fleet of sixty identical\n"
            "  projects would not behave like this. And shape-only matching is the\n"
            "  brittle attack, not the strong one — it beats a pure rescale and then\n"
            "  falls apart under 3% jitter, where the adversary who kept magnitude is\n"
            "  still at 68%. The identifying power is mostly in the magnitudes.\n"
        )
    print(
        "  Cell 3 is the one that will actually get you. Provenance is a quality\n"
        "  practice, which is exactly why it is the last thing anyone removes — and\n"
        "  why it survives, intact, on a release whose values were regenerated from\n"
        "  scratch. It is one boolean, and it is free, and it is missing.\n"
        "\n"
        "  And read the last table as a price list rather than a ranking. Nothing here\n"
        "  both defeated the attack and kept the per-project signal. Regenerating from\n"
        "  a per-project model — which is what 'synthetic' usually means — leaves\n"
        "  re-identification several times above chance. Only pooling to a fleet-level\n"
        "  model reached chance, and it took most of the utility with it.\n"
        "\n"
        "  Measured output and scope: RESULTS.md"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
