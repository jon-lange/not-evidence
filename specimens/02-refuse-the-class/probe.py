"""Specimen 02 — refuse the class, and say the same thing every time.

Pattern 02 has two halves. The first one everybody keeps; the second one is the
one that erodes. This measures both.

  HALF 1  Refusing the class is a smaller rule than the allowlist it replaces.
          Counted: predicates, table entries, and the references each boundary
          accepts that nobody meant to allow.

  HALF 2  One identical error for every rejection. An automated prober tries to
          discover the exact accepted set; the same prober runs against the
          same boundary twice, changing nothing but what a rejected caller is
          told. The probe counts are the headline.

  TIMING  If the helpful validator short-circuits, response latency draws the
          same map with the messages already identical. Shown, then mitigated.

No network, no API key, no dependencies. The claim here is about a validator's
own code rather than about a model, so everything is local and reproducible.

Usage:
    python3 probe.py
    python3 probe.py --quick     # fewer seeds, fewer timing repetitions

Reference implementation. Not maintained.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import prober
import validator as V

OUT = Path(__file__).parent / "_generated"
RUNS_JSONL = OUT / "runs.jsonl"

RULE = "=" * 92
SEEDS = 25
QUICK_SEEDS = 8
TIMING_REPS = 3
TIMING_BUDGET = 8_000
TIMING_SEEDS = 3
CAL_REFS = 12
TEST_REFS = 24


def pct(value: float) -> str:
    return f"{100 * value:5.1f}%"


class Sink:
    """One row per prober run and per latency measurement, written as produced.

    Before aggregation, deliberately. Every table below is a median over a
    distribution wide enough that the median is the least interesting thing
    about it, and a harness that persisted only the medians would have thrown
    away the spread along with every question its author did not think to ask.
    """

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = path.open("w", encoding="utf-8")
        self.count = 0

    def write(self, row: dict) -> None:
        self.handle.write(json.dumps(row, sort_keys=True) + "\n")
        self.count += 1

    def close(self) -> None:
        self.handle.close()


# ── half 1: the class refusal is a smaller rule ──────────────────────────────


def half_one() -> None:
    print("\nHALF 1 — refusing the class is a smaller rule than filtering the cases")
    print("-" * 92)
    print("   'entries' is table rows a reviewer has to read: an allowlisted scheme, a")
    print("   permitted host, a content type, a size cap. Each one is a value somebody")
    print("   had to think of in advance.\n")

    header = (f"   {'boundary':<22}{'predicates':>11}{'entries':>9}{'accepted':>10}"
              f"{'of 48,000':>11}{'unintended':>12}")
    print(header)
    print("   " + "-" * (len(header) - 3))
    for name in ("accreted", "carve-out", "class"):
        boundary = V.BOUNDARIES[name]
        accepted = V.accepted_set(boundary)
        bypass = V.bypass_refs(boundary)
        print(f"   {boundary.name:<22}{boundary.predicates:>11}{boundary.entries:>9}"
              f"{len(accepted):>10}{pct(len(accepted) / V.SPACE_SIZE):>11}{len(bypass):>12}")

    bypass = V.bypass_refs(V.ACCRETED)
    host = sorted({r.host for r in bypass})[0]
    print(f"\n   The 'unintended' column is one bug: the host check is a suffix match, so")
    print(f"   {host!r} satisfies an allowlist that names three hosts and")
    print(f"   not that one. It accepts {len(bypass)} of the accreted boundary's "
          f"{len(V.accepted_set(V.ACCRETED))} references —")
    print(f"   {pct(len(bypass) / len(V.accepted_set(V.ACCRETED))).strip()} of everything that gets"
          " through — and no additional allowlist entry fixes it,")
    print("   because the entries were never wrong. The matcher was.")
    print("\n   The class refusal has no host check to get past. Its two predicates read:")
    for rule in V.CLASS.rules:
        print(f"     - {rule.what}")
    print("\n   And note the error codes. The accreted boundary has "
          f"{len(set(V.ACCRETED.codes()))} of them because it has")
    print(f"   {V.ACCRETED.predicates} independent reasons to say no. The class refusal has "
          f"{len(set(V.CLASS.codes()))}, not out of discipline")
    print("   but because there is only one thing to say: this is not a reference we take.")


# ── half 2: what a distinct error message costs ──────────────────────────────


def dominance(worse: list[int], better: list[int]) -> float:
    """Share of all seed pairs in which the uniform run cost more.

    A ratio of medians hides how wide these distributions are. This is the
    question a defender actually has: given one run of each, how often is the
    silent boundary the more expensive one to map?
    """
    pairs = [(a, b) for a in worse for b in better]
    return sum(a > b for a, b in pairs) / len(pairs)


def probe_counts(seeds: int, sink: "Sink") -> dict:
    print("\nHALF 2 — what a distinct error message costs the prober")
    print("-" * 92)
    print("   One prober, two oracles. The accepted set is identical in both rows of each")
    print("   pair; the only difference is what a rejected probe is told. The prober treats")
    print("   codes as opaque labels — it compares them for equality and never reads them.\n")
    print("   'complete' is the probe count at which the prober's model first agreed with")
    print(f"   the boundary on all {V.SPACE_SIZE:,} references. {seeds} seeds; median, then range.")
    print("   'uniform costs more' is the share of all seed pairs in which it did.\n")

    header = (f"   {'boundary':<16}{'errors':<12}{'first accept':>13}{'complete':>10}"
              f"{'range':>16}{'ratio':>8}{'uniform costs more':>21}")
    print(header)
    print("   " + "-" * (len(header) - 3))

    results = {}
    for name in ("accreted", "carve-out", "class"):
        boundary = V.BOUNDARIES[name]
        truth = V.accepted_set(boundary)
        medians, samples = {}, {}
        for uniform, label in ((False, "distinct"), (True, "one code")):
            firsts, completes = [], []
            for seed in range(seeds):
                run = prober.characterise(
                    V.Validator(boundary, uniform=uniform), truth, seed=seed)
                firsts.append(run.probes_to_first_accept)
                completes.append(run.probes_to_complete)
                sink.write({"section": "probe_counts", "boundary": name,
                            "errors": label, "seed": seed, "probes": run.probes,
                            "first_accept": run.probes_to_first_accept,
                            "complete": run.probes_to_complete, "boxes": run.boxes,
                            "unsound_boxes": run.unsound_boxes})
            assert all(c is not None for c in completes), "a run never converged"
            samples[uniform] = completes
            medians[uniform] = (statistics.median(firsts), statistics.median(completes),
                                min(completes), max(completes))
            ratio = medians[uniform][1] / medians[False][1]
            share = ("-" if not uniform
                     else pct(dominance(samples[True], samples[False])).strip())
            span = f"{min(completes):,}-{max(completes):,}"
            print(f"   {name:<16}{label:<12}{statistics.median(firsts):>13,.0f}"
                  f"{statistics.median(completes):>10,.0f}{span:>16}"
                  f"{ratio:>7.1f}x{share:>21}")
        results[name] = medians
        if name == "class":
            print("   The class refusal has one error code either way, so those two rows are the")
            print("   same experiment run twice — which is the sanity check on the column: two")
            print("   identical distributions put 'uniform costs more' at a coin toss.")
        print()
    return results


# ── timing as the same side channel ──────────────────────────────────────────


def latency(validator, ref, reps: int) -> float:
    samples = []
    for _ in range(reps):
        start = time.perf_counter()
        validator(ref)
        samples.append(time.perf_counter() - start)
    return statistics.median(samples)


def refs_by_code(boundary) -> dict:
    grouped: dict[str, list] = {}
    for ref in V.SPACE:
        grouped.setdefault(V.rejection_code(boundary, ref), []).append(ref)
    grouped.pop(V.ACCEPT_CODE, None)
    return grouped


def calibrate(validator, grouped, reps: int, n: int) -> dict:
    return {
        code: statistics.median(latency(validator, ref, reps) for ref in refs[:n])
        for code, refs in grouped.items()
    }


def classify(centroids: dict, seconds: float) -> str:
    return min(centroids, key=lambda code: abs(seconds - centroids[code]))


def timing_section(quick: bool, sink: "Sink") -> dict:
    reps = 1 if quick else TIMING_REPS
    n_test = 8 if quick else TEST_REFS
    boundary = V.ACCRETED
    grouped = refs_by_code(boundary)
    codes = list(V.ACCRETED.codes())

    leaky = V.Validator(boundary, uniform=True, costly=True)
    constant = V.Validator(boundary, uniform=True, costly=True, constant_work=True)

    print("\nTIMING — the messages are already identical; the clock says it anyway")
    print("-" * 92)
    print("   Both validators below return exactly one string, 'E_REFUSED', for every")
    print("   rejection. The left column short-circuits on the first failing rule, which is")
    print("   what any validator does unless someone stopped it. The right column runs every")
    print("   rule regardless of the outcome.\n")

    cal_leaky = calibrate(leaky, grouped, reps, CAL_REFS)
    cal_constant = calibrate(constant, grouped, reps, CAL_REFS)

    print(f"   {'rule that fired':<20}{'short-circuit':>16}{'constant work':>16}")
    print("   " + "-" * 49)
    for code in codes:
        print(f"   {code:<20}{cal_leaky[code] * 1e6:>13.1f} us{cal_constant[code] * 1e6:>13.1f} us")

    accuracy = {}
    for name, validator, centroids in (("short-circuit", leaky, cal_leaky),
                                       ("constant work", constant, cal_constant)):
        hits = total = 0
        for code, refs in grouped.items():
            for ref in refs[CAL_REFS:CAL_REFS + n_test]:
                seconds = latency(validator, ref, reps)
                guess = classify(centroids, seconds)
                sink.write({"section": "timing", "mode": name, "true_code": code,
                            "guessed_code": guess, "seconds": seconds, "ref": str(ref)})
                hits += guess == code
                total += 1
        accuracy[name] = hits / total

    chance = 1 / len(grouped)
    spread = {"short-circuit": max(cal_leaky.values()) / min(cal_leaky.values()),
              "constant work": max(cal_constant.values()) / min(cal_constant.values())}
    print(f"\n   nearest-centroid recovery of the rule that fired, from latency alone,")
    print(f"   {n_test} held-out references per class, {len(grouped)} classes, chance "
          f"{pct(chance).strip()}:\n")
    print(f"     {'':16}{'accuracy':>10}{'slowest/fastest class':>24}")
    for name, value in accuracy.items():
        print(f"     {name:<16}{pct(value):>10}{spread[name]:>22.2f}x")
    print("\n   Accuracy is the attacker's number and the right-hand column is the robust")
    print("   one: a nearest-centroid classifier over centroids that are not separated is")
    print("   a coin toss whose accuracy wanders around chance from run to run, while the")
    print("   spread between the slowest and fastest class is a property of the validator.")

    print("\n   The same prober again, reading the clock instead of the message:\n")
    truth = V.accepted_set(boundary)
    timing_runs = {}
    for name, validator, centroids in (("short-circuit", leaky, cal_leaky),
                                       ("constant work", constant, cal_constant)):
        def label_of(ref, verdict, _v=validator, _c=centroids):
            return V.ACCEPT_CODE if verdict.ok else classify(_c, latency(_v, ref, reps))

        completes = []
        for seed in range(TIMING_SEEDS):
            run = prober.characterise(validator, truth, seed=seed,
                                      budget=TIMING_BUDGET, label_of=label_of)
            completes.append(run.probes_to_complete)
            sink.write({"section": "timing_prober", "mode": name, "seed": seed,
                        "probes": run.probes, "complete": run.probes_to_complete,
                        "budget": TIMING_BUDGET})
        timing_runs[name] = completes
        done = [c for c in completes if c is not None]
        summary = (f"{statistics.median(done):>7,.0f}" if len(done) == len(completes)
                   else f"{'>' + format(TIMING_BUDGET, ','):>7}")
        print(f"     {name:<16}{summary} probes to a complete map "
              f"({len(done)}/{len(completes)} runs finished within {TIMING_BUDGET:,})")

    message = [prober.characterise(V.Validator(boundary, uniform=False), truth,
                                   seed=seed).probes_to_complete
               for seed in range(TIMING_SEEDS)]
    identical = message == timing_runs["short-circuit"]
    print(f"\n     the message-guided prober, same seeds:  "
          f"{', '.join(f'{m:,}' for m in message)}")
    print(f"     the clock-guided prober, same seeds:    "
          f"{', '.join(f'{m:,}' if m else '>' + format(TIMING_BUDGET, ',') for m in timing_runs['short-circuit'])}")
    if identical:
        print("\n   Run for run, seed for seed, the same numbers. Recovery of the failing rule")
        print("   from latency is good enough that the clock-guided prober takes the same path")
        print("   the message-guided one takes. Making the strings identical changed nothing.")

    return {"accuracy": accuracy, "chance": chance, "runs": timing_runs, "message": message,
            "identical": identical, "spread": spread, "leaky": cal_leaky, "constant": cal_constant}


# ── entry point ──────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quick", action="store_true", help="fewer seeds, fewer timing repetitions")
    args = ap.parse_args()
    seeds = QUICK_SEEDS if args.quick else SEEDS

    print("Specimen 02 — refuse the class, not the case")
    print(RULE)
    print(f"space   {V.SPACE_SIZE:,} references = {len(V.SCHEMES)} schemes x {len(V.HOSTS)} hosts "
          f"x {len(V.KINDS)} types x {len(V.SIZES)} sizes x {len(V.FORMS)} forms")
    print("        a documentation build tool deciding what it will resolve")
    print(RULE)

    sink = Sink(RUNS_JSONL)
    try:
        half_one()
        counts = probe_counts(seeds, sink)
        timing = timing_section(args.quick, sink)
    finally:
        sink.close()

    accreted = counts["accreted"][True][1] / counts["accreted"][False][1]
    carve = counts["carve-out"][True][1] / counts["carve-out"][False][1]

    print("\n" + RULE)
    print(f"  Every run and every latency measurement above is on disk before it was\n"
          f"  averaged: {sink.count:,} rows in "
          f"{RUNS_JSONL.relative_to(Path(__file__).parent)}.\n")
    print(
        f"  One identical error is worth {accreted:.0f}x on the accreted boundary and "
        f"{carve:.0f}x on the\n"
        "  carve-out, measured as probes to a complete and correct map of the accepted\n"
        "  set. The pattern's second half is real and it is not free to skip.\n"
        "\n"
        "  But read the two rows together, because the gap between them is the finding.\n"
        "  Distinct errors do not hand over the boundary in six probes, one per error\n"
        f"  class — they hand it over in about {counts['accreted'][False][1]:,.0f}, and the "
        "uniform-error version costs\n"
        f"  about {counts['accreted'][True][1]:,.0f}. Both are within reach of an afternoon and a "
        "loop. Uniform errors\n"
        "  raise the price of mapping a filter; they do not close the oracle.\n"
        "\n"
        "  What decides the multiplier is geometry. When the accepted regions touch, a\n"
        "  prober with no signal at all walks from one to the next and the error channel\n"
        "  buys little. When the accepted region is a narrow carve-out that no single\n"
        "  edit reaches, the silent boundary has to be stumbled on, and the multiplier\n"
        "  is large. Pattern 02 states the refusal unconditionally; the size of the win\n"
        "  turns out to depend on something the entry does not mention.\n"
    )
    print(
        "  Timing says the rest. With every message identical, the slowest rejection\n"
        f"  class is {timing['spread']['short-circuit']:.0f}x slower than the fastest, "
        "nearest-centroid on latency alone recovers\n"
        f"  which rule fired "
        f"{pct(timing['accuracy']['short-circuit']).strip()} of the time against "
        f"{pct(timing['chance']).strip()} chance, and the prober reading\n"
        "  the clock reproduces the message-guided attack run for run and seed for seed.\n"
        f"  Running every rule regardless of outcome flattens the spread to "
        f"{timing['spread']['constant work']:.2f}x, and\n"
        f"  {sum(c is None for c in timing['runs']['constant work'])} of "
        f"{len(timing['runs']['constant work'])} clock-guided runs then fail to finish inside a "
        f"{TIMING_BUDGET:,}-probe budget the\n"
        "  leaky one clears three times out of three. 'One error, every time' is not a\n"
        "  claim about a string.\n"
        "\n"
        "  And half one is where the argument actually lands. The class refusal is two\n"
        f"  predicates and no tables against {V.ACCRETED.predicates} predicates over "
        f"{V.ACCRETED.entries} entries — and it has one\n"
        "  error code, not by discipline but because it only has one thing to say. The\n"
        "  accreted boundary needs six identical errors held identical by somebody\n"
        "  remembering to. Refusing the class is what makes the second half cheap.\n"
        "\n"
        "  Measured output, scope, and what would falsify this: RESULTS.md"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
