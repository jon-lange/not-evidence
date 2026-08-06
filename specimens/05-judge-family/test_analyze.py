"""Tests for the analysis layer and the verdict parser.

Run: python3 test_analyze.py   (or: python3 -m pytest test_analyze.py -q)

No network. The models' behaviour is measured live and recorded in RESULTS.md;
mocking a judge would only prove the mock returns what it was told to.

Two of these tests exist because the live run exposed defects in this file's
subject. Both are marked.
"""

from __future__ import annotations

import analyze
import judge


def verdict(item, candidate, j, a=5, m=5, c=5):
    return {"item": item, "candidate": candidate, "judge": j,
            "accuracy": a, "mechanism": m, "commitment": c}


def spread(judge_name, a_scores, b_scores):
    """Build verdicts for one judge from per-item totals (each 3..15)."""
    out = []
    for i, (x, y) in enumerate(zip(a_scores, b_scores)):
        out.append(verdict(f"q{i}", "openai", judge_name, x - 10, 5, 5))
        out.append(verdict(f"q{i}", "anthropic", judge_name, y - 10, 5, 5))
    return out


# ── pairing ──────────────────────────────────────────────────────────────────

def test_items_missing_one_candidate_are_dropped_not_imputed():
    """An imputed score is indistinguishable from a real one in the mean."""
    v = [verdict("q1", "openai", "j"), verdict("q1", "anthropic", "j"),
         verdict("q2", "openai", "j")]  # q2 has no anthropic verdict
    assert len(analyze.paired_scores(v, "j", "openai", "anthropic")) == 1


def test_verdicts_from_other_judges_are_excluded():
    v = [verdict("q1", "openai", "a"), verdict("q1", "anthropic", "a"),
         verdict("q1", "openai", "b"), verdict("q1", "anthropic", "b")]
    assert len(analyze.paired_scores(v, "a", "openai", "anthropic")) == 1


# ── the no-signal refusal (found by the live run) ────────────────────────────

def test_a_judge_that_never_discriminates_reports_no_signal():
    """REGRESSION. Two judges scored every answer identically; equal means read
    as a considered tie and the harness declared a winner from nothing."""
    v = spread("j", [15] * 8, [15] * 8)
    view = analyze.judge_view(v, "j", "openai", "anthropic")
    assert view.discriminating is False
    assert view.winner is None
    assert "no signal" in view.note


def test_zero_variance_and_zero_difference_is_infinite_mde():
    """REGRESSION. sd == 0 previously returned MDE 0.0, implying perfect
    precision from a run carrying no information at all."""
    assert analyze.minimum_detectable_effect([(15, 15)] * 8) == float("inf")


def test_an_exact_tie_is_not_a_win():
    """REGRESSION. gap == 0 fell through to `a if gap > 0 else b`."""
    v = spread("j", [14, 15, 13, 15], [15, 14, 15, 13])
    view = analyze.judge_view(v, "j", "openai", "anthropic")
    assert view.gap == 0
    assert view.winner is None
    # Assert the NOTE, not just the outcome. A zero gap is always below a
    # positive MDE, so removing this branch leaves behaviour unchanged and only
    # the explanation wrong — which a coarser assertion cannot see.
    assert view.note == "exact tie"


# ── resolution ───────────────────────────────────────────────────────────────

def test_a_gap_below_the_mde_is_a_tie():
    v = spread("j", [15, 14, 15, 14, 15, 14], [14, 15, 14, 15, 14, 13])
    view = analyze.judge_view(v, "j", "openai", "anthropic")
    if abs(view.gap) < view.mde:
        assert view.winner is None
        assert "detectable" in view.note


def test_a_consistent_large_gap_resolves_a_winner():
    v = spread("j", [15] * 8, [10] * 8)
    view = analyze.judge_view(v, "j", "openai", "anthropic")
    assert view.winner == "openai"
    assert view.discriminating


def test_discordant_counts_only_items_where_candidates_differ():
    v = spread("j", [15, 15, 14], [15, 13, 14])
    view = analyze.judge_view(v, "j", "openai", "anthropic")
    assert view.n_discordant == 1


# ── flip detection ───────────────────────────────────────────────────────────

def test_flip_requires_two_resolved_and_disagreeing_judges():
    a = analyze.judge_view(spread("a", [15] * 8, [10] * 8), "a", "openai", "anthropic")
    b = analyze.judge_view(spread("b", [10] * 8, [15] * 8), "b", "openai", "anthropic")
    assert analyze.ranking_flipped([a, b])


def test_a_no_signal_judge_cannot_create_a_flip():
    """The absence of a measurement must not count as disagreement."""
    a = analyze.judge_view(spread("a", [15] * 8, [10] * 8), "a", "openai", "anthropic")
    dead = analyze.judge_view(spread("d", [15] * 8, [15] * 8), "d", "openai", "anthropic")
    assert not analyze.ranking_flipped([a, dead])


def test_agreement_is_not_a_flip():
    a = analyze.judge_view(spread("a", [15] * 8, [10] * 8), "a", "openai", "anthropic")
    b = analyze.judge_view(spread("b", [14] * 8, [9] * 8), "b", "openai", "anthropic")
    assert not analyze.ranking_flipped([a, b])


# ── families and parsing ─────────────────────────────────────────────────────

def test_family_split_is_what_the_whole_specimen_turns_on():
    assert judge.family("claude-sonnet-4-5") == "anthropic"
    assert judge.family("gpt-4o-mini") == "openai"


def test_unparseable_verdicts_return_none_rather_than_a_default():
    for raw in ("no json here", "{}", '{"accuracy": 5}', '{"accuracy": "x", "mechanism": 5, "commitment": 5}'):
        assert judge.parse_scores(raw) is None


def test_out_of_range_scores_are_rejected():
    assert judge.parse_scores('{"accuracy": 9, "mechanism": 5, "commitment": 5}') is None
    assert judge.parse_scores('{"accuracy": 0, "mechanism": 5, "commitment": 5}') is None


def test_valid_json_survives_surrounding_prose():
    got = judge.parse_scores('Sure!\n{"accuracy": 4, "mechanism": 3, "commitment": 5}\nHope that helps')
    assert got == {"accuracy": 4, "mechanism": 3, "commitment": 5}


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS  {name}")
            except Exception as exc:          # noqa: BLE001
                # Not just AssertionError: a mutation that raises anything else
                # would otherwise crash the runner, print no FAIL line, and be
                # scored as survived. That is pattern 11 inside the harness.
                failures += 1
                print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
    print(f"\n{failures} failure(s)")
    raise SystemExit(1 if failures else 0)
