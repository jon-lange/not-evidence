"""Specimen 06 — an un-ratified weighting is a failure, not a warning.

Four analyses of one scorecard, then the gate.

  1  equal weights, the weighting that gets used when nobody has been asked
  2  a plausible weighting from the person who cares about correctness
  3  an equally plausible weighting from the person who cares about iteration
  4  the whole weight simplex: what share of weightings flips the winner

Then five scoring runs against the ratification gate, and the same five through
a version that warns instead — including the line each one emits downstream,
which is the point.

No network, no API key, no dependencies. The claim is about scoring governance,
so everything it needs is arithmetic.

Usage:
    python3 probe.py
    python3 probe.py --quick     # skip the monte-carlo cross-check

Reference implementation. Not maintained.
"""

from __future__ import annotations

import argparse

import scorecard as sc
from ratify import (
    Ratification,
    UnratifiedWeighting,
    decision_record,
    ratify,
    score,
    score_with_warning,
    weights_hash,
)

RULE = "=" * 88
DASH = "-" * 88

MEASURES = (
    ("uniform over every weighting", {}),
    ("every dimension at least 5%", {"floor": 0.05}),
    ("near equal weights, Dirichlet(8)", {"concentration": 8}),
)

WEIGHTINGS = (
    ("equal weights", sc.equal()),
    ("correctness-first", sc.CORRECTNESS_FIRST),
    ("iteration-first", sc.ITERATION_FIRST),
)


def per_dimension(card: sc.Scorecard) -> None:
    print(f"Per-dimension results for {card.name} — no weighting, no gate, always available.\n")
    print(f" {'dimension':<28}{card.left:>8}{card.right:>8}{'delta':>10}")
    for dim, left, right, delta in sc.per_dimension_rows(card):
        print(f" {dim:<28}{left:>8.1f}{right:>8.1f}{delta:>+10.2f}")


def weighting_block(card: sc.Scorecard) -> None:
    print(f" {'dimension':<28}" + "".join(f"{label:>20}" for label, _ in WEIGHTINGS))
    for dim in card.dimensions:
        cells = "".join(f"{weights[dim]:>20.3f}" for _, weights in WEIGHTINGS)
        print(f" {dim:<28}{cells}")
    print()
    print(f" {'weighting':<22}{card.left:>10}{card.right:>10}{'margin':>10}   winner")
    for label, weights in WEIGHTINGS:
        left = sc.weighted_total(card, card.left, weights)
        right = sc.weighted_total(card, card.right, weights)
        won = sc.winner(card, weights)
        print(f" {label:<22}{left:>10.3f}{right:>10.3f}{left - right:>+10.3f}   {won}")


def simplex_block(card: sc.Scorecard, trials: int) -> None:
    reference = sc.equal()
    decided = sc.winner(card, reference)
    deltas = card.deltas()
    print(f" equal weights pick {decided}. Share of weightings that pick the other one:\n")
    header = f" {'measure':<36}{'flip share':>12}"
    if trials:
        header += f"{'monte carlo':>14}"
    print(header)
    for label, measure in MEASURES:
        exact = sc.flip_share(card, reference, **measure)
        row = f" {label:<36}{exact:>12.4f}"
        if trials:
            below = sc.monte_carlo_share(deltas, trials=trials, **measure)
            mc = below if decided == card.left else 1.0 - below
            row += f"{mc:>14.4f}"
        print(row)
    shift = sc.minimum_flip_shift(card)
    print()
    if shift is None:
        print(" No move of weight away from equal weights changes the winner.")
    else:
        size, donor, receiver = shift
        print(f" Cheapest flip: move {size:.1%} of the total weight from {donor}"
              f" to {receiver}\n (equal weights give every dimension"
              f" {1 / len(card.dimensions):.1%}, so the donor can afford it).")


# ── the gate ─────────────────────────────────────────────────────────────────

OWNER = "r.okonkwo"
ROLE = "owns the documentation quality bar"
ENGINEER = "j.mercer"
TODAY = "2026-08-05"


def gate_cases() -> list[tuple[str, sc.Scorecard, dict[str, float], Ratification | None, str]]:
    card = sc.CLOSE
    good = ratify(card, sc.CORRECTNESS_FIRST, owner=OWNER, role=ROLE, at=TODAY)

    edited = dict(sc.CORRECTNESS_FIRST)
    edited["build_time"] = round(edited["build_time"] + 0.01, 6)
    edited["theme_customisation"] = round(edited["theme_customisation"] - 0.01, 6)

    widened = sc.Scorecard(
        name=card.name,
        left=card.left,
        right=card.right,
        scores={c: dict(card.scores[c], search_quality=7.0) for c in card.candidates()},
        dimensions=card.dimensions + ("search_quality",),
    )
    widened_weights = sc.normalised(dict(sc.CORRECTNESS_FIRST, search_quality=0.10))

    self_ratified = ratify(card, sc.CORRECTNESS_FIRST, owner=ENGINEER, role=ROLE, at=TODAY)

    return [
        ("equal weights, no record", card, sc.equal(), None, ENGINEER),
        ("ratified weighting", card, sc.CORRECTNESS_FIRST, good, ENGINEER),
        ("one weight nudged by 0.01", card, edited, good, ENGINEER),
        ("a seventh dimension added", widened, widened_weights, good, ENGINEER),
        ("engineer ratified it themselves", card, sc.CORRECTNESS_FIRST, self_ratified, ENGINEER),
    ]


def gate_block() -> None:
    print(f" {'run':<34}{'refusing gate':<16}reason / escalate to")
    for label, card, weights, record, run_by in gate_cases():
        try:
            result = score(card, weights, record, run_by=run_by)
        except UnratifiedWeighting as exc:
            print(f" {label:<34}{'FAILED':<16}{exc.reason}")
            print(f" {'':<34}{'':<16}-> {exc.escalate_to}")
        else:
            print(f" {label:<34}{'scored':<16}{decision_record(result)}")


def warning_block() -> None:
    print(f" {'run':<34}{'warning gate':<16}what leaves the harness")
    for label, card, weights, record, run_by in gate_cases():
        result, warning = score_with_warning(card, weights, record, run_by=run_by)
        state = "warned" if warning else "clean"
        print(f" {label:<34}{state:<16}{decision_record(result)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true",
                        help="skip the monte-carlo cross-check of the exact shares")
    args = parser.parse_args()
    trials = 0 if args.quick else 20_000

    card = sc.CLOSE
    print("Specimen 06 — the weighting is the verdict")
    print(RULE)
    per_dimension(card)
    print()
    print(RULE)
    print("1-3 · Three weightings, all defensible, none ratified\n")
    weighting_block(card)
    print()
    print(RULE)
    print("4 · The weight simplex\n")
    simplex_block(card, trials)

    print()
    print(RULE)
    print("The same search on two other shapes of scorecard\n")
    for other in (sc.LOPSIDED, sc.DOMINANT):
        print(f" {other.name} — {other.left} vs {other.right}, deltas "
              f"{[round(d, 1) for d in other.deltas()]}")
        simplex_block(other, trials)
        print()

    print(RULE)
    print("The gate — five scoring runs\n")
    gate_block()
    print()
    print("The same five, with the gate demoted to a warning\n")
    warning_block()

    print()
    print(RULE)
    print(
        "Every run in the second table produced a number, and every number is the\n"
        "same shape as the one ratified run's. Nothing downstream of that line can\n"
        "tell which of the five it came from — the warning went to the log, and the\n"
        "log is read by the engineer, who already knew.\n"
        "\n"
        "In the first table the run that could not be justified did not produce a\n"
        "number at all, and the failure names somebody who can fix it. That is the\n"
        "whole mechanism: same information, different audience.\n"
        "\n"
        "The per-dimension table at the top was never gated. The exploratory run is\n"
        "not what needs an owner; the collapse into one number is."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
