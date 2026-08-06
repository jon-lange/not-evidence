"""Specimen 05 — the ranking-flip test for judge independence.

Two candidate systems from different model families answer the same questions.
Every judge scores every answer. Then:

  * does each judge prefer its own family's output?
  * does the choice of judge change WHICH CANDIDATE WINS?

The second question is the useful one. It turns an abstract argument about
self-preference bias into a binary, cheap, decisive experiment on data you
already have: if the winner depends on who judged, no single-judge promotion
decision for that comparison can stand.

Every per-item, per-judge, per-dimension verdict is written to verdicts.jsonl
before any aggregation happens. A harness that persists only means has thrown
away what paired comparison and interval estimation need.

Usage:
    python probe.py --offline      # show the design; no keys, no network
    python probe.py                # run it

Reference implementation. Not maintained.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import analyze
import items
import judge

HERE = Path(__file__).parent
VERDICTS = HERE / "verdicts.jsonl"

# Two candidates, deliberately one per family.
CANDIDATES = {
    "openai": os.environ.get("CAND_OPENAI", "gpt-4o-mini"),
    "anthropic": os.environ.get("CAND_ANTHROPIC", "claude-sonnet-4-5"),
}

# Judges. Includes one from each family so that for every candidate there is
# both a same-family and a cross-family judge.
JUDGES = [
    os.environ.get("JUDGE_OPENAI", "gpt-4o-mini"),
    os.environ.get("JUDGE_ANTHROPIC", "claude-sonnet-4-5"),
    os.environ.get("JUDGE_OPENAI_2", "gpt-4o"),
]


def have_key(fam: str) -> bool:
    env = "ANTHROPIC_API_KEY" if fam == "anthropic" else "OPENAI_API_KEY"
    path = "~/.config/anthropic-key" if fam == "anthropic" else "~/.config/openai-key"
    return bool(os.environ.get(env)) or Path(os.path.expanduser(path)).exists()


def run() -> list[dict]:
    verdicts: list[dict] = []
    answers: dict[tuple[str, str], str] = {}

    print(f"generating {len(items.ITEMS)} × {len(CANDIDATES)} answers…")
    for name, model in CANDIDATES.items():
        for q in items.ITEMS:
            answers[(name, q)] = judge.generate(q, model)

    print(f"judging {len(items.ITEMS)} × {len(CANDIDATES)} × {len(JUDGES)} …")
    with VERDICTS.open("w") as fh:
        for j in JUDGES:
            for name in CANDIDATES:
                for q in items.ITEMS:
                    scores = judge.score(q, answers[(name, q)], j)
                    if scores is None:
                        # Recorded as a gap, never imputed. See judge.parse_scores.
                        print(f"  unparseable verdict: judge={j} candidate={name}")
                        continue
                    v = {"item": q, "candidate": name, "judge": j,
                         "judge_family": judge.family(j), **scores}
                    verdicts.append(v)
                    fh.write(json.dumps(v) + "\n")
    return verdicts


def report(verdicts: list[dict]) -> None:
    a, b = "openai", "anthropic"
    views = [analyze.judge_view(verdicts, j, a, b) for j in JUDGES]

    print("\n" + "=" * 78)
    print(f"{'judge':<26} {'family':<11} {'openai':>7} {'anthropic':>10} {'gap':>7} {'MDE':>6}  winner")
    print("-" * 78)
    for v in views:
        if not v.means:
            print(f"{v.judge:<26} {'—':<11} {'no verdicts':>36}")
            continue
        w = v.winner or "tie (below MDE)"
        print(f"{v.judge:<26} {judge.family(v.judge):<11} "
              f"{v.means[a]:>7.2f} {v.means[b]:>10.2f} {v.gap:>+7.2f} {v.mde:>6.2f}  {w}")

    print("\nitems paired / discordant per judge:")
    for v in views:
        print(f"  {v.judge:<26} n={v.n_paired:<3} discordant={v.n_discordant}")

    # Which judge generated which candidate — the self-preference mapping.
    generators = {m: fam for fam, m in CANDIDATES.items()}
    prefs = analyze.self_preference(views, generators)
    if prefs:
        print("\nself-preference — a judge's margin for its OWN family's output:")
        for j, margin in prefs:
            print(f"  {j:<26} {margin:+.2f}")

    flipped = analyze.ranking_flipped(views)
    print("\n" + "=" * 78)
    if flipped:
        print("RANKING FLIPPED. The winner depends on who judged.\n"
              "  Judge independence is not a methodological nicety for this comparison —\n"
              "  it is decision-critical, and no single-judge promotion decision here can\n"
              "  stand. Report the panel, or report nothing.")
    else:
        print("No flip observed. Every judge that resolved a winner agreed on it.\n"
              "  That is a real result and it is NOT proof of judge independence — it is\n"
              "  one comparison, on one task set, at one size. The flip test tells you when\n"
              "  you have a problem. Its absence does not tell you that you do not.")

    print("\nEvery verdict written to verdicts.jsonl before aggregation. Re-analyse\n"
          "without re-spending: python -c 'import analyze, json; ...'")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()

    if args.offline:
        print("candidates (one per family):")
        for fam, m in CANDIDATES.items():
            print(f"  {fam:<11} {m}")
        print("\njudges:")
        for j in JUDGES:
            print(f"  {judge.family(j):<11} {j}")
        print(f"\nitems: {len(items.ITEMS)}")
        print(f"calls: {len(items.ITEMS) * len(CANDIDATES)} generations "
              f"+ {len(items.ITEMS) * len(CANDIDATES) * len(JUDGES)} judgements")
        print("\nRun without --offline to execute.")
        return 0

    missing = [f for f in ("openai", "anthropic") if not have_key(f)]
    if missing:
        print(
            f"Missing credentials for: {', '.join(missing)}.\n"
            "  This specimen needs TWO model families. With one, you can measure that\n"
            "  judges disagree, but you cannot separate self-preference from ordinary\n"
            "  disagreement — there is no lineage boundary to compare across.\n"
            "  Use --offline to inspect the design without running it.",
            file=sys.stderr,
        )
        return 2

    report(run())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
