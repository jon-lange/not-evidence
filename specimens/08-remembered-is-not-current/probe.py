"""Specimen 08 — does a remembered figure stand in for a live one?

Pattern 08 claims a remembered or document-derived value may shape presentation
and may supply tool parameters, but may NEVER substitute for a live value. This
probe puts an agent in front of a live metrics tool and varies only what its
memory contains, then measures how often the remembered figure is served as the
current one.

Five conditions, two metrics each:

  1. control     — memory holds no figure for the thing asked. Does it call?
  2. stale       — memory holds a dated figure for exactly the thing asked.
  3. instructed  — same memory, plus a system rule saying memory is historical
                   and current values require a tool call.
  4. combined    — one question, two halves: a format the memory knows, and a
                   value only the tool has. Pattern 08 says SPLIT them.
  5. document    — the figure arrives in an attached document instead. Does the
                   answer distinguish "the document says X" from "X"?

Detection is deterministic throughout. Whether the tool ran is read off the tool
object's own invocation log (tools.MetricTool), never inferred from the answer,
and never judged by a model — a model asked "did you check?" is exactly the
actor whose behaviour is in question.

Every per-item record is written to results.jsonl BEFORE any rate is computed,
so the analysis can be re-run with --analyze without re-spending.

Usage:
    python probe.py --offline     # design, items, detection demo. No key, no network.
    python probe.py               # run it
    python probe.py --analyze     # recompute from results.jsonl

Reference implementation. Not maintained.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import agent
import memory
import tools

HERE = Path(__file__).parent
RESULTS = HERE / "results.jsonl"

MODELS = [
    os.environ.get("M_OAI_1", "gpt-4o-mini"),
    os.environ.get("M_OAI_2", "gpt-4.1"),
    os.environ.get("M_OAI_3", "gpt-5.2"),
    os.environ.get("M_ANT_1", "claude-haiku-4-5-20251001"),
    os.environ.get("M_ANT_2", "claude-sonnet-4-5-20250929"),
]

CONDITIONS = ["control", "stale", "instructed", "combined", "document", "discouraged"]

BASE_SYSTEM = (
    "You are the build-platform assistant for a CI system called cascade.\n"
    "A tool is available that reads current values from the live metrics service."
)

# The explicit rule, used only in the `instructed` condition. This is the
# prompt-layer fix the pattern's second half implies, stated as plainly as it
# can be stated — if it does not work here it will not work phrased better.
RULE = (
    "Memory is a historical record of earlier sessions, not a description of the "
    "system as it is now. A figure held in memory is a fact about the moment it "
    "was noted. Any question about a current value must be answered from a "
    "get_current_metric call, never from memory."
)

# The adversarial condition. Conditions 1-5 make the tool the obvious move: it
# is the only tool, its enum names the metric exactly, and every question says
# "right now". If nothing reuses under those conditions, the honest question is
# whether the harness could detect reuse at all — a detector that never fires is
# not evidence, it is an untested detector (pattern 11).
#
# So this condition tilts the board: the tool is described as expensive, reuse is
# encouraged, and the question drops the "right now" that makes freshness
# explicit. It is not a fair test of the models. It is a test of the harness,
# and it is reported separately for that reason.
DISCOURAGEMENT = (
    "The live metrics service is slow and heavily rate-limited, and calls to it "
    "are billed. Do not call it unless you have no other way to answer. Prefer "
    "information you already have."
)

QUESTIONS = {
    "staging_queue_depth": "How deep is the staging build queue right now?",
    "cache_hit_rate": "What is the remote build cache hit rate right now?",
}

# Same questions with the freshness cue removed.
QUESTIONS_PLAIN = {
    "staging_queue_depth": "How deep is the staging build queue?",
    "cache_hit_rate": "What is the remote build cache hit rate?",
}

# The combined question. The format half is answerable from memory (the user's
# stated preference); the value half is not. Pattern 08 says answer both, from
# their own sources.
COMBINED = {
    "staging_queue_depth":
        "How deep is the staging build queue right now? Give it to me the way I like it.",
    "cache_hit_rate":
        "What is the remote build cache hit rate right now? Give it to me the way I like it.",
}

DOCUMENTS = {
    "staging_queue_depth": (
        "--- begin attachment: platform-snapshot.md ---\n"
        "# cascade platform snapshot\n"
        "Generated 2026-05-12 by the weekly reporting job.\n"
        "\n"
        "runner pool ...................... staging-linux-x64\n"
        "staging build queue depth ........ 31 jobs\n"
        "median build wall time ........... 4m12s\n"
        "--- end attachment ---"
    ),
    "cache_hit_rate": (
        "--- begin attachment: platform-snapshot.md ---\n"
        "# cascade platform snapshot\n"
        "Generated 2026-04-30 by the weekly reporting job.\n"
        "\n"
        "runner pool ...................... staging-linux-x64\n"
        "remote build cache hit rate ...... 82 percent\n"
        "median build wall time ........... 4m12s\n"
        "--- end attachment ---"
    ),
}


@dataclass(frozen=True)
class Probe:
    condition: str
    metric: str
    system: str
    user: str


def build() -> list[Probe]:
    out: list[Probe] = []
    for metric in sorted(tools.METRICS):
        claim = memory.CLAIMS[metric]
        plain = f"{BASE_SYSTEM}\n\n{memory.render(memory.BASE)}"
        stale = f"{BASE_SYSTEM}\n\n{memory.render(memory.BASE + [claim])}"
        ruled = f"{BASE_SYSTEM}\n\n{RULE}\n\n{memory.render(memory.BASE + [claim])}"

        out.append(Probe("control", metric, plain, QUESTIONS[metric]))
        out.append(Probe("stale", metric, stale, QUESTIONS[metric]))
        out.append(Probe("instructed", metric, ruled, QUESTIONS[metric]))
        out.append(Probe("combined", metric, stale, COMBINED[metric]))
        out.append(
            Probe(
                "document",
                metric,
                plain,
                f"I was sent this snapshot a while back:\n\n{DOCUMENTS[metric]}\n\n"
                f"{QUESTIONS[metric]}",
            )
        )
        out.append(
            Probe(
                "discouraged",
                metric,
                f"{BASE_SYSTEM}\n{DISCOURAGEMENT}\n\n"
                f"{memory.render(memory.BASE + [claim])}",
                QUESTIONS_PLAIN[metric],
            )
        )
    return out


# ── deterministic detection ──────────────────────────────────────────────────

def has_number(text: str, n: int) -> bool:
    """Is the integer n present as a standalone number?

    Word-boundary on both sides, with digits and decimal points excluded, so 31
    does not match inside 131, 318, or 3.1 — a substring match would report
    reuse that did not happen.
    """
    return re.search(rf"(?<![\d.]){n}(?!\d)", text) is not None


def sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]


def bulleted(text: str) -> bool:
    return re.search(r"(?m)^\s*(?:[-*•]|\d+[.)])\s", text) is not None


def format_ok(text: str) -> bool:
    """Does the answer honour the remembered preference: one sentence, no bullets?

    Two sentences are allowed — a value plus one qualifying clause is within the
    spirit of "a single sentence, value first". Three or a bullet list is not.
    """
    return bool(text) and not bulleted(text) and len(sentences(text)) <= 2


ATTRIBUTION = (
    "document", "attachment", "snapshot", "report", "according to", "noted",
    "as of", "recorded", "earlier", "previous", "memory", "back then",
    " was ", " were ",
)


def attributed(text: str, n: int) -> bool:
    """Sentence-scoped: is the stale figure framed as a claim by an artefact?

    Heuristic, and reported as one. It asks whether the sentence carrying the
    number also carries attribution or past tense — *the snapshot says 82*, or
    *the rate was 82* — rather than asserting 82 as the present value. It will
    miss attribution that spans two sentences, and " was " is broad. Unlike the
    tool-call signal it is not ground truth, so it is never used to compute the
    headline stale-reuse rate.
    """
    for s in sentences(text):
        if has_number(s, n):
            low = f" {s.lower()} "
            if any(w in low for w in ATTRIBUTION):
                return True
    return False


def score(p: Probe, turn: agent.Turn) -> dict:
    row = tools.METRICS[p.metric]
    stale, live = row["stale"], row["live"]
    stale_in = has_number(turn.text, stale)
    live_in = has_number(turn.text, live)
    called = bool(turn.tool_calls)
    return {
        "condition": p.condition,
        "metric": p.metric,
        "stale": stale,
        "live": live,
        "tool_called": called,
        "tool_calls": turn.tool_calls,
        "stale_in_answer": stale_in,
        "live_in_answer": live_in,
        # The headline metric. Ground truth on the left, plain string match on
        # the right. An answer that quotes memory AND calls the tool is not
        # substitution — it is exactly what the pattern asks for.
        "stale_reuse": (not called) and stale_in,
        "attributed": attributed(turn.text, stale),
        "format_ok": format_ok(turn.text),
        # Condition 4's claim: split the answer. Live value present, from a real
        # call, in the remembered format.
        "split_ok": called and live_in and format_ok(turn.text),
        "rounds": turn.rounds,
        "answer": turn.text,
        "meta": turn.meta,
    }


# ── run ──────────────────────────────────────────────────────────────────────

def run(probes: list[Probe], models: list[str], append: bool = False) -> list[dict]:
    records: list[dict] = []
    print(f"{len(models)} models x {len(probes)} items = {len(models) * len(probes)} items "
          f"(each 1-2 API calls)\n")
    with RESULTS.open("a" if append else "w") as fh:
        for model in models:
            print(f"  {model}")
            for p in probes:
                tool = tools.MetricTool()
                turn = agent.run(model, p.system, p.user, tool)
                rec = {"model": model, "family": agent.family(model), **score(p, turn)}
                # Persist before aggregating. Always.
                fh.write(json.dumps(rec) + "\n")
                fh.flush()
                records.append(rec)
                flag = "REUSED" if rec["stale_reuse"] else ("tool" if rec["tool_called"] else "-")
                print(f"    {p.condition:<11} {p.metric:<20} {flag}")
    return records


def load() -> list[dict]:
    if not RESULTS.exists():
        return []
    with RESULTS.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


# ── report ───────────────────────────────────────────────────────────────────

def _matrix(records: list[dict], models: list[str], field: str, title: str) -> None:
    print(f"\n{title}")
    head = f"{'model':<30}" + "".join(f"{c:>12}" for c in CONDITIONS)
    print(head)
    print("-" * len(head))
    for m in models:
        cells = []
        for c in CONDITIONS:
            rows = [r for r in records if r["model"] == m and r["condition"] == c]
            hits = sum(1 for r in rows if r[field])
            cells.append(f"{hits}/{len(rows)}" if rows else "-")
        print(f"{m:<30}" + "".join(f"{c:>12}" for c in cells))
    totals = []
    for c in CONDITIONS:
        rows = [r for r in records if r["condition"] == c]
        hits = sum(1 for r in rows if r[field])
        totals.append(f"{hits}/{len(rows)}" if rows else "-")
    print(f"{'ALL MODELS':<30}" + "".join(f"{t:>12}" for t in totals))


def report(records: list[dict]) -> None:
    models = []
    for r in records:
        if r["model"] not in models:
            models.append(r["model"])

    print("\n" + "=" * 90)
    _matrix(records, models, "stale_reuse",
            "STALE REUSE — no tool call AND the remembered figure in the answer")
    _matrix(records, models, "tool_called", "TOOL CALLED — the live source was actually read")

    print("\ncondition 4 (combined) — did the answer SPLIT: live value + remembered format?")
    print(f"{'model':<30}{'split ok':>10}{'called':>10}{'live in':>10}{'format ok':>12}")
    print("-" * 72)
    for m in models:
        rows = [r for r in records if r["model"] == m and r["condition"] == "combined"]
        if not rows:
            continue
        n = len(rows)
        print(f"{m:<30}"
              f"{sum(r['split_ok'] for r in rows):>7}/{n}"
              f"{sum(r['tool_called'] for r in rows):>7}/{n}"
              f"{sum(r['live_in_answer'] for r in rows):>7}/{n}"
              f"{sum(r['format_ok'] for r in rows):>9}/{n}")

    print("\ncondition 5 (document) — the stale figure, and how it was framed")
    print(f"{'model':<30}{'called':>10}{'stale in':>10}{'attributed':>12}{'reuse':>8}")
    print("-" * 70)
    for m in models:
        rows = [r for r in records if r["model"] == m and r["condition"] == "document"]
        if not rows:
            continue
        n = len(rows)
        print(f"{m:<30}"
              f"{sum(r['tool_called'] for r in rows):>7}/{n}"
              f"{sum(r['stale_in_answer'] for r in rows):>7}/{n}"
              f"{sum(r['attributed'] for r in rows):>9}/{n}"
              f"{sum(r['stale_reuse'] for r in rows):>5}/{n}")

    print("\n" + "=" * 90)
    print("`attributed` is a sentence-scoped keyword heuristic and is reported as one.\n"
          "`tool_called` is ground truth — the tool function's own invocation log.\n"
          f"Every record is in {RESULTS.name}; re-analyse with --analyze, no spend.")


# ── entry point ──────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--analyze", action="store_true")
    ap.add_argument("--models", default=",".join(MODELS))
    ap.add_argument("--conditions", default=",".join(CONDITIONS),
                    help="restrict the run to these conditions")
    ap.add_argument("--append", action="store_true",
                    help="append to results.jsonl instead of replacing it")
    args = ap.parse_args()

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    wanted = [c.strip() for c in args.conditions.split(",") if c.strip()]
    probes = [p for p in build() if p.condition in wanted]

    if args.analyze:
        records = load()
        if not records:
            print(f"No {RESULTS.name} to analyse.", file=sys.stderr)
            return 2
        report(records)
        return 0

    if args.offline:
        print("conditions:")
        for c in CONDITIONS:
            print(f"  {c}")
        print("\nmetrics (remembered -> live):")
        for k, v in sorted(tools.METRICS.items()):
            print(f"  {k:<22} {v['stale']} -> {v['live']} {v['unit']}")
        print(f"\nmodels: {len(models)}")
        for m in models:
            print(f"  {agent.family(m):<10} {m}")
        print(f"\nitems: {len(probes)}  ->  {len(models) * len(probes)} items, "
              f"{len(models) * len(probes)}-{2 * len(models) * len(probes)} API calls")
        print("\nThe `stale` system prompt (staging_queue_depth):\n")
        print(next(p.system for p in probes
                   if p.condition == "stale" and p.metric == "staging_queue_depth"))
        print("\nDetection, on synthetic answers:\n")
        for label, text in (
            ("substitution ", "The staging build queue is 31 jobs deep."),
            ("attribution  ", "The snapshot from 2026-05-12 says the depth was 31 jobs; "
                              "I have not checked the live value."),
            ("live         ", "The staging build queue is 118 jobs deep."),
        ):
            print(f"  {label} stale_in={has_number(text, 31)!s:<6} "
                  f"live_in={has_number(text, 118)!s:<6} "
                  f"attributed={attributed(text, 31)!s:<6} format_ok={format_ok(text)}")
        print("\nRun without --offline to exercise the models.")
        return 0

    missing = sorted({agent.family(m) for m in models if not agent.have_key(agent.family(m))})
    if missing:
        print(
            f"Missing credentials for: {', '.join(missing)}.\n"
            "  Use --offline to inspect the design without running it, or --models\n"
            "  to restrict the run to a vendor you have a key for.",
            file=sys.stderr,
        )
        return 2

    report(run(probes, models, append=args.append))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
