"""The gate. A weighted score is not produced without a ratification record.

`score()` is the only way to collapse a scorecard into one number, and it takes
a `Ratification` — not optionally, not with a fallback. Four things have to
hold, and each one fails with a different message naming a different person to
go and ask:

  1. a record exists at all
  2. it was issued against this scorecard and this dimension set
  3. the hash of the exact weights matches, so any edit invalidates it
  4. the person who ratified is not the person running the job

`score_with_warning()` is the same computation with the gate demoted to a line
of text. It exists for the comparison and should not be used for anything else.

No network, no dependencies. The control is organisational; the enforcement is
twenty lines of hashing.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from scorecard import Scorecard, weighted_total, winner

# Weights are rounded here before hashing. Two weightings that differ below this
# are the same weighting for ratification purposes; anything a person would type
# is far above it.
PRECISION = 6


class UnratifiedWeighting(Exception):
    """The scoring run failed because the weighting has no valid endorsement.

    Not a warning and not a subclass of anything a pipeline swallows by habit.
    It carries `escalate_to` because the audience is the point: a warning is
    addressed to the engineer reading the log, who already knows and cannot fix
    it, and a failure has to be addressed to whoever can.
    """

    def __init__(self, reason: str, escalate_to: str) -> None:
        super().__init__(f"{reason} — escalate to: {escalate_to}")
        self.reason = reason
        self.escalate_to = escalate_to


@dataclass(frozen=True)
class Ratification:
    """A claim about particular numbers, made by a particular person.

    `weights_hash` rather than the weights themselves, so the record is about
    one version and cannot be quietly widened to cover the next one.
    """

    scorecard: str
    dimensions: tuple[str, ...]
    weights_hash: str
    owner: str
    role: str
    ratified_at: str


def canonical(dimensions: tuple[str, ...], weights: dict[str, float]) -> str:
    """Stable text form of a weighting, for hashing.

    Sorted by dimension so the record does not depend on the order a dict
    happened to be built in, and required to sum to 1 so that {2, 2} and
    {0.5, 0.5} — the same weighting — cannot produce two different hashes.
    """
    if set(weights) != set(dimensions):
        raise ValueError("weighting does not cover exactly the scorecard's dimensions")
    total = sum(weights.values())
    if abs(total - 1.0) > 10 ** -PRECISION:
        raise ValueError(f"weights must be normalised; they sum to {total!r}")
    return ";".join(f"{d}={weights[d]:.{PRECISION}f}" for d in sorted(dimensions))


def weights_hash(dimensions: tuple[str, ...], weights: dict[str, float]) -> str:
    digest = hashlib.sha256(canonical(dimensions, weights).encode()).hexdigest()
    return f"sha256:{digest[:16]}"


def ratify(
    card: Scorecard,
    weights: dict[str, float],
    *,
    owner: str,
    role: str,
    at: str,
) -> Ratification:
    """Record that `owner` endorses exactly these weights for exactly this card."""
    if not owner.strip():
        raise ValueError("a ratification with no owner is not a ratification")
    return Ratification(
        scorecard=card.name,
        dimensions=tuple(sorted(card.dimensions)),
        weights_hash=weights_hash(card.dimensions, weights),
        owner=owner,
        role=role,
        ratified_at=at,
    )


def verify(
    card: Scorecard,
    weights: dict[str, float],
    record: Ratification | None,
    *,
    run_by: str,
) -> None:
    """Raise `UnratifiedWeighting` unless this exact weighting is endorsed."""
    if record is None:
        raise UnratifiedWeighting(
            f"no ratification record for {card.name!r}",
            "nobody — this weighting has never been shown to anyone",
        )
    if record.scorecard != card.name:
        raise UnratifiedWeighting(
            f"ratification is for {record.scorecard!r}, this run is {card.name!r}",
            record.owner,
        )
    if record.dimensions != tuple(sorted(card.dimensions)):
        added = sorted(set(card.dimensions) - set(record.dimensions))
        removed = sorted(set(record.dimensions) - set(card.dimensions))
        raise UnratifiedWeighting(
            f"dimension set changed since ratification (added {added}, removed {removed})",
            record.owner,
        )
    if weights_hash(card.dimensions, weights) != record.weights_hash:
        raise UnratifiedWeighting(
            f"weights edited since ratification ({record.weights_hash} was ratified, "
            f"{weights_hash(card.dimensions, weights)} was supplied)",
            record.owner,
        )
    if run_by == record.owner:
        raise UnratifiedWeighting(
            f"{run_by!r} ratified their own weighting",
            "somebody who owns the quality bar and is not running this job",
        )


@dataclass(frozen=True)
class ScoreResult:
    scorecard: str
    order: tuple[str, str]
    totals: dict[str, float]
    winner: str | None


def _compute(card: Scorecard, weights: dict[str, float]) -> ScoreResult:
    return ScoreResult(
        scorecard=card.name,
        order=card.candidates(),
        totals={c: weighted_total(card, c, weights) for c in card.candidates()},
        winner=winner(card, weights),
    )


def score(
    card: Scorecard,
    weights: dict[str, float],
    record: Ratification | None,
    *,
    run_by: str,
) -> ScoreResult:
    """The gated aggregate. There is no code path here that returns a number
    without a valid record, and no parameter that supplies a default weighting."""
    verify(card, weights, record, run_by=run_by)
    return _compute(card, weights)


def score_with_warning(
    card: Scorecard,
    weights: dict[str, float],
    record: Ratification | None,
    *,
    run_by: str,
) -> tuple[ScoreResult, str | None]:
    """The same number, with the gate demoted to a string the caller may ignore.

    Returns the warning alongside the result rather than printing it, which is
    already more careful than the version this is standing in for. It makes no
    difference: the result is the same object, and `decision_record` of it is
    the same bytes.
    """
    try:
        verify(card, weights, record, run_by=run_by)
    except UnratifiedWeighting as exc:
        return _compute(card, weights), f"WARNING: {exc}"
    return _compute(card, weights), None


def decision_record(result: ScoreResult) -> str:
    """The line that leaves the harness and gets quoted.

    It has no field for provenance, which is the ordinary case — and adding one
    would not help, because the warned path would have to write some value into
    it and the summary downstream would drop it either way. What travels is the
    winner.
    """
    left, right = result.order
    return (f"{result.scorecard}: {left} {result.totals[left]:.2f} | "
            f"{right} {result.totals[right]:.2f} -> {result.winner}")
