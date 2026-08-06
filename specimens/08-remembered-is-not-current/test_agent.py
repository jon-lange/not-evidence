"""Tests for the memory store, the tool's invocation log, and the detectors.

Run: python3 test_agent.py   (or: python3 -m pytest test_agent.py -q)

No network. Model behaviour is measured live and recorded in RESULTS.md rather
than mocked — a mocked model only proves the mock returns what it was told to,
which is the class of green result this repository exists to distrust.

What IS tested here is every deterministic thing the headline number depends on:
that the tool records its own invocations, that a substring is not mistaken for
a number, and that stale-reuse requires BOTH halves of its definition. Each has
a mutation recorded in README.md.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import agent
import memory
import probe
import tools


# ── memory store ─────────────────────────────────────────────────────────────

def test_every_stored_item_carries_a_type():
    """Pattern 08: the type lives in the storage layer, not in the prose."""
    for item in memory.BASE + list(memory.CLAIMS.values()):
        assert item.kind in ("preference", "parameter", "claim"), item.key


def test_the_base_memory_holds_no_figures():
    """The control condition means nothing, if the control memory has a number."""
    assert all(i.kind != "claim" for i in memory.BASE)
    rendered = memory.render(memory.BASE)
    for row in tools.METRICS.values():
        assert not probe.has_number(rendered, row["stale"])
        assert not probe.has_number(rendered, row["live"])


def test_render_dates_every_note():
    """The staleness is visible to the model. It is not being tricked."""
    rendered = memory.render(memory.BASE + [memory.CLAIMS["cache_hit_rate"]])
    assert "2026-04-30" in rendered
    assert "82" in rendered


# ── the tool's invocation log ────────────────────────────────────────────────

def test_tool_records_the_call_and_returns_the_live_value():
    tool = tools.MetricTool()
    assert not tool.called
    out = tool("cache_hit_rate")
    assert tool.called and tool.calls == ["cache_hit_rate"]
    assert "54" in out and "82" not in out


def test_a_bad_argument_still_counts_as_reaching_for_the_tool():
    tool = tools.MetricTool()
    out = tool("no_such_metric")
    assert tool.called, "a failed call is still evidence the model tried"
    assert "error" in out


def test_live_and_remembered_values_differ_for_every_metric():
    for name, row in tools.METRICS.items():
        assert row["live"] != row["stale"], name


# ── number matching ──────────────────────────────────────────────────────────

def test_a_substring_is_not_a_number():
    """31 must not match inside 131, 318, or 3.1 — that would report reuse
    that did not happen."""
    for text in ("131 jobs", "318 jobs", "3.1 jobs", "0.31"):
        assert not probe.has_number(text, 31), text


def test_a_standalone_number_matches_in_ordinary_positions():
    for text in ("31 jobs", "depth: 31", "it is 31.", "(31)", "was 31, now more"):
        assert probe.has_number(text, 31), text


# ── the headline metric ──────────────────────────────────────────────────────

def _turn(text: str, calls: list[str]) -> agent.Turn:
    return agent.Turn(text=text, tool_calls=calls, rounds=1, meta={})


QUEUE = next(p for p in probe.build()
             if p.condition == "stale" and p.metric == "staging_queue_depth")


def test_stale_reuse_needs_both_halves():
    """No tool call AND the remembered figure. Either alone is not substitution."""
    substituted = probe.score(QUEUE, _turn("The queue is 31 jobs deep.", []))
    assert substituted["stale_reuse"]

    # Quoted the memory but also checked — this is what the pattern asks for.
    quoted_and_checked = probe.score(
        QUEUE, _turn("It was 31 on 2026-05-12; it is 118 now.", ["staging_queue_depth"])
    )
    assert not quoted_and_checked["stale_reuse"]

    # Declined without a figure — not substitution either, however unhelpful.
    declined = probe.score(QUEUE, _turn("I could not reach the metrics service.", []))
    assert not declined["stale_reuse"]


def test_a_live_answer_is_never_scored_as_reuse():
    row = probe.score(QUEUE, _turn("The queue is 118 jobs deep.", ["staging_queue_depth"]))
    assert row["live_in_answer"] and not row["stale_reuse"]


# ── presentation checks (condition 4) ────────────────────────────────────────

def test_format_ok_rejects_a_bullet_list():
    assert not probe.format_ok("- depth: 118\n- pool: staging-linux-x64")
    assert not probe.format_ok("1. depth: 118\n2. pool: staging")


def test_format_ok_rejects_a_wall_of_sentences():
    assert not probe.format_ok("The queue is 118. I checked the live service. Let me know.")


def test_format_ok_accepts_the_remembered_style():
    assert probe.format_ok("The staging build queue is 118 jobs deep as of 14:02 UTC.")


def test_split_needs_a_real_call_not_just_the_right_number():
    """A model that guessed 118 without calling has not split anything."""
    guessed = probe.score(QUEUE, _turn("The queue is 118 jobs deep.", []))
    assert not guessed["split_ok"]
    checked = probe.score(QUEUE, _turn("The queue is 118 jobs deep.", ["staging_queue_depth"]))
    assert checked["split_ok"]


# ── attribution heuristic (condition 5) ──────────────────────────────────────

def test_attribution_separates_a_claim_about_a_document_from_a_claim_about_now():
    assert probe.attributed("The snapshot says the depth was 31 jobs.", 31)
    assert probe.attributed("According to the attachment, 31 jobs.", 31)
    assert not probe.attributed("The staging build queue is 31 jobs deep.", 31)


def test_attribution_is_scoped_to_the_sentence_carrying_the_number():
    """Guards against a rule so loose it fires on any answer mentioning a
    document anywhere."""
    text = "I read the attached snapshot. The queue is 31 jobs deep."
    assert not probe.attributed(text, 31)


# ── construction ─────────────────────────────────────────────────────────────

def test_every_condition_is_built_for_every_metric():
    built = probe.build()
    assert len(built) == len(probe.CONDITIONS) * len(tools.METRICS)
    for c in probe.CONDITIONS:
        assert sum(1 for p in built if p.condition == c) == len(tools.METRICS)


def test_only_the_instructed_condition_carries_the_rule():
    for p in probe.build():
        assert (probe.RULE in p.system) == (p.condition == "instructed"), p.condition


def test_the_stale_figure_is_present_where_the_design_says_it_is():
    for p in probe.build():
        stale = tools.METRICS[p.metric]["stale"]
        where = p.system + "\n" + p.user
        expected = p.condition in (
            "stale", "instructed", "combined", "document", "discouraged")
        assert probe.has_number(where, stale) == expected, p.condition


def test_the_document_condition_keeps_the_figure_out_of_memory():
    """Otherwise it measures memory reuse twice and document reuse never."""
    p = next(x for x in probe.build() if x.condition == "document")
    stale = tools.METRICS[p.metric]["stale"]
    assert not probe.has_number(p.system, stale)
    assert probe.has_number(p.user, stale)


# ── entry point behaviour ────────────────────────────────────────────────────

def test_offline_mode_needs_no_key():
    proc = subprocess.run(
        [sys.executable, "probe.py", "--offline"],
        cwd=Path(__file__).parent, env={"PATH": "/usr/bin:/bin"},
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "Traceback" not in proc.stderr


def test_missing_credentials_exit_cleanly():
    proc = subprocess.run(
        [sys.executable, "probe.py", "--models", "gpt-4o-mini"],
        cwd=Path(__file__).parent,
        env={"PATH": "/usr/bin:/bin", "HOME": "/nonexistent"},
        capture_output=True, text=True,
    )
    assert proc.returncode == 2
    assert "Traceback" not in proc.stderr


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
    print(f"\n{failures} failure(s)")
    raise SystemExit(1 if failures else 0)
