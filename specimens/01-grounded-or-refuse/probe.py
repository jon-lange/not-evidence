"""Specimen 01 — does "if you're not sure, say you don't know" actually work?

Pattern 01 claims a system must answer only from evidence retrieved this turn,
cite it, and otherwise decline — and that the attractive shortcut, an
instruction in the system prompt telling the model to admit uncertainty, fails
because it asks the model to report a state it does not have.

This probe tests that shortcut head-on. One authored corpus, thirteen
questions in three classes, two configurations, four models across two vendors:

  answerable         the corpus states the answer          (control)
  absent             the corpus does not touch it          (refusal is correct)
  plausibly-absent   the corpus names the concept and       (refusal is correct,
                     never states the value                  and it is hard)

  A · attitudinal    "if you are not sure, say you don't know"
  B · structural     cite a doc id, copy the span that states the answer, and
                     a deterministic post-check compares that span against the
                     document. Failing the check forces a refusal.

The measured quantity is the CONFABULATION RATE: the fraction of questions
whose answer is not in the corpus that the system answered anyway.

No LLM judge decides whether an answer was a confabulation. That would import
pattern 05's problem into pattern 01's specimen. The decision is deterministic
(check.py) and its error is measured by hand on a sample.

Usage:
    python probe.py --offline           # corpus, items, and the check; no key
    python probe.py                     # run it
    python probe.py --analyze           # re-aggregate results.jsonl, no spend
    python probe.py --sample 32         # print a hand-check sheet from results

Reference implementation. Not maintained.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import agent
import check
import corpus

HERE = Path(__file__).parent
RESULTS = HERE / "results.jsonl"

MODELS = [
    os.environ.get("M_OPENAI_1", "gpt-4o-mini"),
    os.environ.get("M_OPENAI_2", "gpt-4.1"),
    os.environ.get("M_ANTHROPIC_1", "claude-haiku-4-5-20251001"),
    os.environ.get("M_ANTHROPIC_2", "claude-sonnet-4-5-20250929"),
]
CONFIGS = ("A", "B")


# ── running ──────────────────────────────────────────────────────────────────

def run_one(model: str, config: str, item: corpus.Item) -> dict:
    docs = corpus.retrieve(item.question)
    raw = agent.ask(item.question, docs, model, config)
    reply = check.parse(raw)
    texts = {d.doc_id: d.text for d in docs}

    if config not in agent.FORMATTED:
        # A0 was never asked for a format, so a missing ANSWER: field is not a
        # defect. parse() already falls back to the whole reply.
        reply = check.Reply(reply.raw, None, None, reply.raw.strip(), False)

    if config.startswith("A"):
        lax = strict = check.decide_attitudinal(reply)
    else:
        lax = check.decide_structural(reply, texts, strict=False)
        strict = check.decide_structural(reply, texts, strict=True)

    return {
        "model": model,
        "family": agent.family(model),
        "config": config,
        "item_id": item.item_id,
        "cls": item.cls,
        "question": item.question,
        "grounded": item.grounded,
        "retrieved": [d.doc_id for d in docs],
        "raw": raw,
        "cite": reply.cite,
        "quote": reply.quote,
        "answer": reply.answer,
        "malformed": reply.malformed,
        "lax": asdict(lax),
        "strict": asdict(strict),
        "correct": check.is_correct(reply.answer, item.expect) if item.grounded else None,
    }


def run(models: list[str], configs: tuple[str, ...], items: list[corpus.Item],
        append: bool = False) -> list[dict]:
    """Write every row as it is produced, before any aggregation happens.

    A harness that stores only means has discarded what paired comparison
    needs, and a harness that buffers has discarded everything the moment the
    network blinks.
    """
    rows: list[dict] = []
    total = len(models) * len(configs) * len(items)
    n = 0
    with RESULTS.open("a" if append else "w") as fh:
        for model in models:
            for config in configs:
                for item in items:
                    n += 1
                    row = run_one(model, config, item)
                    fh.write(json.dumps(row) + "\n")
                    fh.flush()
                    mark = "!" if row["strict"]["final"] == "answered" and not row["grounded"] else " "
                    print(f"  [{n:>3}/{total}] {model:<28} {config} {item.item_id:<3} "
                          f"{row['strict']['final']:<8}{mark}")
                    rows.append(row)
    return rows


def load() -> list[dict]:
    if not RESULTS.exists():
        return []
    with RESULTS.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


# ── aggregation ──────────────────────────────────────────────────────────────

def rate(rows: list[dict], variant: str) -> tuple[int, int]:
    """(confabulations, opportunities) — answered when it should have refused."""
    ungrounded = [r for r in rows if not r["grounded"]]
    bad = [r for r in ungrounded if r[variant]["final"] == "answered"]
    return len(bad), len(ungrounded)


def pct(num: int, den: int) -> str:
    return "   —  " if den == 0 else f"{100 * num / den:5.1f}%"


def cell(rows: list[dict], variant: str) -> str:
    n, d = rate(rows, variant)
    return f"{pct(n, d)} {n}/{d}"


def report(rows: list[dict], models: list[str]) -> None:
    def sub(**kw) -> list[dict]:
        return [r for r in rows if all(r[k] == v for k, v in kw.items())]

    # (label, config, variant) — the four systems the run can produce.
    ARMS = (
        ("A0 bare", "A0", "strict"),
        ("A token", "A", "strict"),
        ("B cite+quote", "B", "lax"),
        ("B +value", "B", "strict"),
    )
    present = [a for a in ARMS if sub(config=a[1])]
    width = 100

    def line(label: str, cls_label: str, pick) -> None:
        cells = "".join(f"{cell(pick(cfg), var):>16}" for _, cfg, var in present)
        print(f"{label:<28} {cls_label:<17}{cells}")

    print("\n" + "=" * width)
    print("CONFABULATION RATE — answered a question whose answer is not in the corpus")
    print("=" * width)
    print(f"{'model':<28} {'class':<17}" + "".join(f"{n:>16}" for n, _, _ in present))
    print("-" * width)
    for model in models:
        for cls in ("absent", "plausibly-absent"):
            line(model, cls, lambda cfg, m=model, c=cls: sub(model=m, config=cfg, cls=c))
        line("", "BOTH",
             lambda cfg, m=model: [r for r in sub(model=m, config=cfg) if not r["grounded"]])
        print("-" * width)
    line("ALL MODELS", "BOTH",
         lambda cfg: [r for r in sub(config=cfg) if not r["grounded"]])

    # ── the control class ────────────────────────────────────────────────────
    print("\n" + "=" * width)
    print("CONTROL — the corpus states the answer. Refusing here is the cost of the check.")
    print("=" * width)
    print(f"{'model':<28} {'arm':<14} {'items':>6} {'answered':>10} {'correct':>10} "
          f"{'over-refused':>14}")
    print("-" * width)
    for model in models:
        for label, config, variant in present:
            g = [r for r in sub(model=model, config=config) if r["grounded"]]
            if not g:
                continue
            ans = [r for r in g if r[variant]["final"] == "answered"]
            cor = [r for r in ans if r["correct"]]
            print(f"{model:<28} {label:<14} {len(g):>6} {pct(len(ans), len(g)):>10} "
                  f"{pct(len(cor), len(g)):>10} {pct(len(g) - len(ans), len(g)):>14}")

    # ── where configuration B's refusals come from ───────────────────────────
    print("\n" + "=" * 92)
    print("WHERE B's REFUSALS COME FROM — prompt or check?")
    print("=" * 92)
    print(f"{'model':<30} {'ungrounded':>11} {'self-refused':>13} "
          f"{'forced by check':>16} {'answered':>10}")
    print("-" * 92)
    for model in models:
        b = [r for r in sub(model=model, config="B") if not r["grounded"]]
        if not b:
            continue
        self_ref = [r for r in b if r["strict"]["stated"] == "refused"]
        forced = [r for r in b if r["strict"]["forced"]]
        answered = [r for r in b if r["strict"]["final"] == "answered"]
        print(f"{model:<30} {len(b):>11} {len(self_ref):>13} "
              f"{len(forced):>16} {len(answered):>10}")

    reasons = Counter(
        r["strict"]["check"] for r in sub(config="B") if r["strict"]["check"].startswith("fail")
    )
    if reasons:
        print("\ncheck failures by reason:")
        for reason, n in reasons.most_common():
            print(f"  {n:>3}  {reason}")

    malformed = [r for r in rows if r["malformed"]]
    if malformed:
        print(f"\nreplies missing the ANSWER: field: {len(malformed)}")
        for r in malformed:
            print(f"  {r['model']} {r['config']} {r['item_id']}")

    print("\n" + "=" * 92)
    print(f"{len(rows)} rows in results.jsonl, written before any of the above was computed.")
    print("Re-aggregate without re-spending: python probe.py --analyze")


# ── hand-check sheet ─────────────────────────────────────────────────────────

def sample(rows: list[dict], n: int, seed: int) -> None:
    """Print raw replies next to the deterministic label, for human adjudication.

    The deterministic label is what the numbers above are made of. Its error
    rate is not assumed to be zero; it is read off this sheet by hand and
    reported in RESULTS.md as a measured quantity.
    """
    rng = random.Random(seed)
    picked = rng.sample(rows, min(n, len(rows)))
    picked.sort(key=lambda r: (r["config"], r["model"], r["item_id"]))
    for i, r in enumerate(picked, 1):
        print("=" * 92)
        print(f"[{i}] {r['model']}  cfg={r['config']}  {r['item_id']} ({r['cls']})  "
              f"grounded={r['grounded']}")
        print(f"    Q: {r['question']}")
        print(f"    retrieved: {r['retrieved']}")
        print(f"    RAW:\n{r['raw']}")
        print(f"    deterministic: stated={r['strict']['stated']} "
              f"check={r['strict']['check']} final={r['strict']['final']}")
    print("=" * 92)
    print(f"{len(picked)} rows, seed={seed}")


# ── offline ──────────────────────────────────────────────────────────────────

def offline() -> None:
    print("Corpus — every document authored for this specimen:\n")
    for d in corpus.DOCS:
        print(f"  [{d.doc_id}] {d.title}")

    print("\nQuestions, and what retrieval returns for each:\n")
    print(f"  {'id':<4} {'class':<17} {'in corpus':<10} retrieved")
    for it in corpus.ITEMS:
        ids = [d.doc_id for d in corpus.retrieve(it.question)]
        print(f"  {it.item_id:<4} {it.cls:<17} {str(it.grounded):<10} {ids}")

    print("\nThe hard class, C1, in full:\n")
    it = next(i for i in corpus.ITEMS if i.item_id == "C1")
    doc = corpus.CORPUS[it.adjacent]
    print(f"  question   {it.question}")
    print(f"  retrieved  [{doc.doc_id}] {doc.title}")
    print(f"  the document says entries can be pruned. It never says how large the")
    print(f"  cache may grow. A fluent completion of that document is a number.")

    print("\nThe deterministic check, on two synthetic replies:\n")
    texts = {doc.doc_id: doc.text}
    confab = check.parse(
        "CITE: bld-102\n"
        "QUOTE: Entries are removed by running girder cache prune\n"
        "ANSWER: The cache is capped at 10 GB, after which entries are evicted."
    )
    honest = check.parse("CITE: NONE\nQUOTE: NONE\nANSWER: INSUFFICIENT")
    for label, reply in (("confabulated", confab), ("declined", honest)):
        out = check.decide_structural(reply, texts, strict=True)
        print(f"  {label:<13} A: {out.stated:<9} check: {out.check:<34} -> {out.final}")

    print("\n  The quote is real. The citation is real. The number is not in the")
    print("  quote, so the answer is discarded and the user is told the")
    print("  documentation does not cover it. No model was asked its opinion.")
    print("\nRun without --offline to exercise the models.")


# ── entry point ──────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--offline", action="store_true", help="no key, no network")
    ap.add_argument("--analyze", action="store_true", help="re-aggregate results.jsonl")
    ap.add_argument("--sample", type=int, metavar="N", help="print a hand-check sheet")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--configs", default=",".join(CONFIGS),
                    help=f"comma-separated, from {sorted(agent.SYSTEMS)}")
    ap.add_argument("--items", default="", help="comma-separated item ids; default all")
    ap.add_argument("--append", action="store_true",
                    help="append to results.jsonl instead of replacing it")
    args = ap.parse_args()

    if args.offline:
        offline()
        return 0

    if args.analyze or args.sample:
        rows = load()
        if not rows:
            print("No results.jsonl. Run the probe first.", file=sys.stderr)
            return 2
        if args.sample:
            sample(rows, args.sample, args.seed)
        else:
            report(rows, list(dict.fromkeys(r["model"] for r in rows)))
        return 0

    missing = [f for f in ("openai", "anthropic") if not agent.read_key(f)]
    if missing:
        print(
            f"Missing credentials for: {', '.join(missing)}.\n"
            "  This specimen needs both vendors. A single-vendor result cannot\n"
            "  separate 'the naive fix fails' from 'this vendor's post-training\n"
            "  happens to reward fluent completion', and those have different\n"
            "  remedies.\n"
            "  Keys are read from ~/.config/openai-key and ~/.config/anthropic-key,\n"
            "  or from OPENAI_API_KEY and ANTHROPIC_API_KEY.\n"
            "  Use --offline to inspect the corpus and the check without any calls.",
            file=sys.stderr,
        )
        return 2

    configs = tuple(c.strip() for c in args.configs.split(",") if c.strip())
    wanted = {i.strip() for i in args.items.split(",") if i.strip()}
    items = [i for i in corpus.ITEMS if not wanted or i.item_id in wanted]
    calls = len(MODELS) * len(configs) * len(items)
    print(f"{len(MODELS)} models x {len(configs)} configs x {len(items)} items "
          f"= {calls} completions\n")
    run(MODELS, configs, items, append=args.append)
    report(load(), MODELS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
