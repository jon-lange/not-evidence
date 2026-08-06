# Specimen 05 — judge independence and the ranking-flip test

Demonstrates [pattern 05 · The Judge Cannot Share a Family](../../patterns/05-judge-cannot-share-a-family.md).

Two candidates from different model families answer the same twelve questions. Three judges — two
from one family, one from the other — score every answer, first on an absolute rubric, then pairwise
in both orders.

Measured output: **[RESULTS.md](RESULTS.md)**.

## The question it answers

**Does the choice of judge change which candidate wins?**

That is the ranking-flip test, and it is the useful one because it is binary, cheap, and runs on data
you already have. If the winner depends on who judged, judge independence is decision-critical for
that comparison and no single-judge promotion can stand.

## What actually happened

**No flip.** Every judge that resolved a winner picked the same candidate. The pattern's central
claim — that a same-family judge favours its own lineage — **was not demonstrated here.**

Two things showed up first instead, neither of which was in the pattern's first draft:

**Two of three judges produced no signal at all.** Both OpenAI judges awarded a perfect 15/15 to all
24 answers. One distinct value across the entire run. They did not rate the candidates as equal —
they produced no measurement, and the harness initially reported a winner from them anyway.

**One judge flipped its verdict on half the items depending on answer order.** `gpt-4o` preferred
whichever answer came first on 6 of 12 items. A single-order pairwise evaluation using that judge
would have been measuring position as much as quality.

**And the apparent self-preference dissolved.** Absolute scoring showed the Anthropic judge rating
its own family +1.00 higher — textbook self-preference. Pairwise contradicted it: *both* cross-family
judges also preferred those answers, unanimously. The simplest explanation consistent with all six
measurements is that they were better and everyone noticed.

Had the run stopped after the first pass, the honest-looking conclusion would have been the wrong one.

## Two passes, because the first one saturates

**Absolute scoring** (1–5 on accuracy, mechanism, commitment) hits a ceiling on a competent task set.
Every answer earns full marks and the judge stops carrying information.

**Pairwise cannot saturate** — it forces a choice. But it introduces position bias, which is large and
judge-specific, so every comparison runs in **both orders** and the results are combined. A judge that
picks whichever came first has expressed a position preference, not a quality preference, and counting
those flips is a direct read on that judge's bias.

## Run it

```bash
python3 test_analyze.py                  # analysis + parser tests; stdlib only, no keys
./.venv/bin/python probe.py --offline    # show the design without spending
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./.venv/bin/python probe.py              # live — needs BOTH vendors
```

Two families is the minimum for this specimen to mean anything. Within one vendor you can measure
that judges disagree, but you cannot separate self-preference from ordinary disagreement — there is
no lineage boundary to compare across. Keys at `~/.config/openai-key` and `~/.config/anthropic-key`.

Roughly 24 generations, 72 absolute judgements, 72 pairwise comparisons.

## Per-item persistence is the point, not a nicety

Every verdict is written to `verdicts.jsonl` and `pairwise.jsonl` **before** any aggregation.

Both analysis defects found during this run were fixed and the results recomputed **from those files
without re-spending a cent.** A harness that stores only dimension means has permanently discarded
what paired comparison, discordance counting, and interval estimation need — and retrofitting it
means re-running everything.

## Tests

```bash
python3 test_analyze.py       # or: python3 -m pytest test_analyze.py -q
```

Fifteen tests, no network. The models' behaviour is measured live and recorded in RESULTS.md rather
than mocked — a mocked judge only proves the mock returns what it was told to.

**Mutation-checked**, six breakages, all caught:

| Mutation | Tests failed |
|---|---|
| No-signal guard removed | 1 |
| Zero-variance returns MDE 0 instead of ∞ | 1 |
| Exact-tie branch removed | 1 |
| MDE check ignored | 1 |
| Flip detection counts unresolved judges | 1 |
| Items missing a candidate get imputed | 1 |

**The mutation check found a false negative in its own harness.** The runner originally caught only
`AssertionError`, so a mutation raising `KeyError` crashed the script, printed no `FAIL` line, and
scored as *survived*. It now catches every exception. That is pattern 11 occurring inside the tooling
built to check for pattern 11.

It also found a **behaviourally dead branch**: a zero gap is always below any positive MDE, so
removing the exact-tie check changed no outcome — only the explanatory note. The test now asserts the
note, because a coarser assertion could not see the difference.

## What this specimen deliberately does not do

**No hand-labelled reference set.** Agreement between judges is *reliability*; agreement with ground
truth is *validity*. A panel can be reliably wrong, and nothing here can tell the difference.

**No adversarial task set.** Twelve general engineering explanation questions, a domain where both
candidates are strong — which is precisely why absolute scoring saturated. A harder set would likely
separate them and might well produce the flip this run did not.

**One rubric, one day, three judges, two vendors.** The flip test tells you when you have a problem.
Its absence does not tell you that you do not.

**The result that would confirm the pattern** is a comparison where a same-family judge picks one
winner and a cross-family judge picks the other. The harness is built to run it — swap the task set
and re-run.

---

Reference implementation. Not maintained.
