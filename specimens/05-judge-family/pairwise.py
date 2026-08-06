"""Pairwise pass — the measurement that cannot saturate.

Runs every (item, judge) in BOTH orders. Position bias in LLM judges is large
and well documented, so a single order measures preference confounded with
position. Combining the two orders separates them:

  consistent win   both orders agree on the same candidate  -> a real preference
  position flip    the judge picked whichever came first     -> no preference,
                   and a count of these is a direct read on that judge's bias
"""

from __future__ import annotations

import json
from pathlib import Path

import items
import judge

HERE = Path(__file__).parent


def run(answers: dict[tuple[str, str], str], judges: list[str],
        a: str = "openai", b: str = "anthropic") -> list[dict]:
    rows: list[dict] = []
    out = HERE / "pairwise.jsonl"
    with out.open("w") as fh:
        for j in judges:
            for q in items.ITEMS:
                fwd = judge.compare(q, answers[(a, q)], answers[(b, q)], j)
                rev = judge.compare(q, answers[(b, q)], answers[(a, q)], j)
                if fwd is None or rev is None:
                    continue
                # Normalise both orders onto candidate names.
                pick_fwd = {"A": a, "B": b, "tie": "tie"}[fwd]
                pick_rev = {"A": b, "B": a, "tie": "tie"}[rev]
                row = {"item": q, "judge": j, "judge_family": judge.family(j),
                       "forward": pick_fwd, "reverse": pick_rev,
                       "consistent": pick_fwd == pick_rev,
                       "winner": pick_fwd if pick_fwd == pick_rev else None}
                rows.append(row)
                fh.write(json.dumps(row) + "\n")
    return rows


def tally(rows: list[dict], j: str, a: str = "openai", b: str = "anthropic") -> dict:
    mine = [r for r in rows if r["judge"] == j]
    consistent = [r for r in mine if r["consistent"]]
    return {
        "n": len(mine),
        "consistent": len(consistent),
        "position_flips": len(mine) - len(consistent),
        a: sum(1 for r in consistent if r["winner"] == a),
        b: sum(1 for r in consistent if r["winner"] == b),
        "ties": sum(1 for r in consistent if r["winner"] == "tie"),
    }
