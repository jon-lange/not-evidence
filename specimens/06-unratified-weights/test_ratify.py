"""Tests for the ratification gate.

Run: python3 test_ratify.py   (or: python3 -m pytest test_ratify.py -q)

Three of these assert something the gate is *unable* to do —
test_the_warned_number_is_byte_identical_to_the_ratified_one,
test_the_warning_path_scores_every_run_the_gate_refused, and
test_the_gate_cannot_tell_a_real_owner_from_a_plausible_string. They pin the
limits in place so a later change that quietly widens the claim is caught.

No network, no dependencies.
"""

from __future__ import annotations

import inspect
import subprocess
import sys
from pathlib import Path

import scorecard as sc
from ratify import (
    Ratification,
    UnratifiedWeighting,
    canonical,
    decision_record,
    ratify,
    score,
    score_with_warning,
    verify,
    weights_hash,
)

OWNER = "r.okonkwo"
ENGINEER = "j.mercer"
CARD = sc.CLOSE
WEIGHTS = sc.CORRECTNESS_FIRST


def record() -> Ratification:
    return ratify(CARD, WEIGHTS, owner=OWNER, role="owns the quality bar", at="2026-08-05")


def edited(delta: float = 0.01) -> dict[str, float]:
    """A weighting one nudge away from the ratified one, still summing to 1."""
    out = dict(WEIGHTS)
    out["build_time"] = round(out["build_time"] + delta, 6)
    out["theme_customisation"] = round(out["theme_customisation"] - delta, 6)
    return out


def refusal(fn, *args, **kwargs) -> UnratifiedWeighting:
    try:
        fn(*args, **kwargs)
    except UnratifiedWeighting as exc:
        return exc
    raise AssertionError("the run was not refused")


# ── the canonical form ───────────────────────────────────────────────────────

def test_canonical_form_ignores_declaration_order():
    """The order the dimensions were declared in is not part of the weighting.

    The first assertion below was the whole test until the mutation check showed
    it could not fail: `canonical` iterates the dimension tuple and looks the
    weights up by name, so the dict's own order was never reachable. The second
    assertion is the one that tests something."""
    shuffled = {d: WEIGHTS[d] for d in reversed(sc.DIMENSIONS)}
    assert canonical(sc.DIMENSIONS, shuffled) == canonical(sc.DIMENSIONS, WEIGHTS)
    assert canonical(tuple(reversed(sc.DIMENSIONS)), WEIGHTS) == canonical(sc.DIMENSIONS, WEIGHTS)


def test_canonical_form_requires_normalised_weights():
    """{2, 2} and {0.5, 0.5} are the same weighting. Two hashes for one
    weighting would let an edit hide as a rescale."""
    doubled = {d: w * 2 for d, w in WEIGHTS.items()}
    try:
        canonical(sc.DIMENSIONS, doubled)
    except ValueError:
        return
    raise AssertionError("hashed an unnormalised weighting")


def test_canonical_form_requires_exactly_the_scorecard_dimensions():
    for weights in ({d: 1.0 / 5 for d in sc.DIMENSIONS[:5]},
                    dict(WEIGHTS, search_quality=0.0)):
        try:
            canonical(sc.DIMENSIONS, weights)
        except ValueError:
            continue
        raise AssertionError(f"hashed the wrong dimension set: {sorted(weights)}")


def test_the_hash_moves_when_a_weight_moves():
    assert weights_hash(sc.DIMENSIONS, WEIGHTS) != weights_hash(sc.DIMENSIONS, edited())
    assert weights_hash(sc.DIMENSIONS, WEIGHTS) == weights_hash(sc.DIMENSIONS, dict(WEIGHTS))


def test_the_hash_is_stable_across_runs():
    """Recorded so a change to the canonical form shows up as a test failure
    rather than as every historical ratification silently expiring."""
    assert weights_hash(sc.DIMENSIONS, sc.equal()) == "sha256:4be7febb1fbe9646"


# ── issuing a ratification ───────────────────────────────────────────────────

def test_a_ratification_names_a_person_a_version_and_a_dimension_set():
    rec = record()
    assert rec.owner == OWNER
    assert rec.scorecard == CARD.name
    assert rec.weights_hash == weights_hash(sc.DIMENSIONS, WEIGHTS)
    assert rec.dimensions == tuple(sorted(sc.DIMENSIONS))


def test_a_ratification_with_no_owner_is_refused_at_issue_time():
    for owner in ("", "   "):
        try:
            ratify(CARD, WEIGHTS, owner=owner, role="r", at="2026-08-05")
        except ValueError:
            continue
        raise AssertionError(f"issued a record owned by {owner!r}")


def test_the_gate_cannot_tell_a_real_owner_from_a_plausible_string():
    """The honest limit, asserted. Any non-empty name is accepted, because a
    denylist of plausible-looking placeholders is a worse control than none —
    it would pass anything not on the list while looking like it checked."""
    rec = ratify(CARD, WEIGHTS, owner="TODO", role="?", at="2026-08-05")
    score(CARD, WEIGHTS, rec, run_by=ENGINEER)


# ── the four refusals ────────────────────────────────────────────────────────

def test_a_ratified_weighting_scores():
    result = score(CARD, WEIGHTS, record(), run_by=ENGINEER)
    assert result.winner == "alder"
    assert set(result.totals) == {"alder", "birch"}


def test_no_record_at_all_fails_and_names_nobody():
    exc = refusal(score, CARD, sc.equal(), None, run_by=ENGINEER)
    assert "no ratification record" in exc.reason
    assert "nobody" in exc.escalate_to


def test_editing_a_weight_invalidates_the_record():
    """The pattern's third clause. Sign-off was about particular numbers."""
    exc = refusal(score, CARD, edited(), record(), run_by=ENGINEER)
    assert "weights edited" in exc.reason
    assert exc.escalate_to == OWNER


def test_a_change_far_below_a_percent_still_invalidates_the_record():
    exc = refusal(score, CARD, edited(1e-4), record(), run_by=ENGINEER)
    assert "weights edited" in exc.reason


def test_adding_a_dimension_invalidates_the_record():
    """The edit that does not look like an edit: the weights that were ratified
    are all still there, and the weighting means something else."""
    widened = sc.Scorecard(
        name=CARD.name, left=CARD.left, right=CARD.right,
        dimensions=sc.DIMENSIONS + ("search_quality",),
        scores={c: dict(CARD.scores[c], search_quality=7.0) for c in CARD.candidates()},
    )
    weights = sc.normalised(dict(WEIGHTS, search_quality=0.10))
    exc = refusal(score, widened, weights, record(), run_by=ENGINEER)
    assert "dimension set changed" in exc.reason
    assert "search_quality" in exc.reason
    assert exc.escalate_to == OWNER


def test_a_record_for_another_scorecard_does_not_transfer():
    exc = refusal(score, sc.LOPSIDED, WEIGHTS, record(), run_by=ENGINEER)
    assert "docgen-lopsided" in exc.reason


def test_ratifying_your_own_weighting_fails():
    own = ratify(CARD, WEIGHTS, owner=ENGINEER, role="built the harness", at="2026-08-05")
    exc = refusal(score, CARD, WEIGHTS, own, run_by=ENGINEER)
    assert "own weighting" in exc.reason
    assert ENGINEER not in exc.escalate_to


def test_verify_returns_nothing_and_raises_everything():
    assert verify(CARD, WEIGHTS, record(), run_by=ENGINEER) is None


def test_the_refusal_carries_an_audience():
    """A warning is addressed to whoever reads the log. A refusal has to be
    addressed to whoever can clear it, which means carrying a name."""
    exc = refusal(score, CARD, edited(), record(), run_by=ENGINEER)
    assert "escalate to" in str(exc)
    assert exc.escalate_to in str(exc)


def test_the_refusal_is_a_hard_failure_not_a_warning():
    assert issubclass(UnratifiedWeighting, Exception)
    assert not issubclass(UnratifiedWeighting, Warning)


def test_there_is_no_way_to_score_without_a_record_argument():
    """No default for `record`, so the ungated call is not expressible. If this
    ever grows one, every caller silently acquires an unratified score."""
    for fn in (score, score_with_warning, verify):
        assert inspect.signature(fn).parameters["record"].default is inspect.Parameter.empty


# ── the warning version, which is the comparison ─────────────────────────────

def test_the_warning_path_scores_every_run_the_gate_refused():
    cases = [
        (CARD, sc.equal(), None),
        (CARD, edited(), record()),
        (CARD, WEIGHTS, ratify(CARD, WEIGHTS, owner=ENGINEER, role="r", at="2026-08-05")),
    ]
    for card, weights, rec in cases:
        refusal(score, card, weights, rec, run_by=ENGINEER)
        result, warning = score_with_warning(card, weights, rec, run_by=ENGINEER)
        assert warning is not None and warning.startswith("WARNING")
        assert result.winner in card.candidates()


def test_the_warned_number_is_byte_identical_to_the_ratified_one():
    """The mechanism the pattern turns on. Downstream of this string there is
    nothing left to inspect: same format, same precision, same authority."""
    ratified, warning = score_with_warning(CARD, WEIGHTS, record(), run_by=ENGINEER)
    unratified, unratified_warning = score_with_warning(CARD, WEIGHTS, None, run_by=ENGINEER)
    assert warning is None and unratified_warning is not None
    assert decision_record(ratified) == decision_record(unratified)


def test_the_warning_path_and_the_gate_agree_on_the_number_when_it_is_earned():
    gated = score(CARD, WEIGHTS, record(), run_by=ENGINEER)
    warned, warning = score_with_warning(CARD, WEIGHTS, record(), run_by=ENGINEER)
    assert warning is None
    assert decision_record(gated) == decision_record(warned)


def test_the_decision_record_carries_no_provenance():
    """Not an oversight — it is what the artefact looks like. The winner is the
    part that travels; the weighting that produced it does not."""
    line = decision_record(score(CARD, WEIGHTS, record(), run_by=ENGINEER))
    assert OWNER not in line
    assert "sha256" not in line
    assert line.endswith("-> alder")


def test_the_two_unratified_defaults_disagree_about_the_winner():
    """Why the identical shape matters. Equal weights and the ratified
    weighting emit the same kind of line and name different winners."""
    equal_line = decision_record(score_with_warning(CARD, sc.equal(), None,
                                                   run_by=ENGINEER)[0])
    ratified_line = decision_record(score(CARD, WEIGHTS, record(), run_by=ENGINEER))
    assert equal_line.endswith("-> birch")
    assert ratified_line.endswith("-> alder")


# ── the un-collapsed results are not gated ───────────────────────────────────

def test_the_per_dimension_table_is_available_with_no_record():
    rows = sc.per_dimension_rows(CARD)
    assert len(rows) == len(sc.DIMENSIONS)


# ── entry point ──────────────────────────────────────────────────────────────

def test_probe_runs_and_prints_both_tables():
    proc = subprocess.run(
        [sys.executable, "probe.py"],
        cwd=Path(__file__).parent,
        env={"PATH": "/usr/bin:/bin"},  # no key, no network, nothing to configure
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "Traceback" not in proc.stderr
    assert "FAILED" in proc.stdout
    assert "flip share" in proc.stdout
    assert "escalate" not in proc.stdout.lower() or "-> r.okonkwo" in proc.stdout


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
            except Exception as exc:  # noqa: BLE001 — a crash is a failure, keep counting
                failures += 1
                print(f"  ERROR {name}: {type(exc).__name__}: {exc}")
    print(f"\n{failures} failure(s)")
    raise SystemExit(1 if failures else 0)
