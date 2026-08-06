# Specimen 08 — a remembered figure, in front of a live tool

Demonstrates [pattern 08 · A Remembered Figure Is Never a Current Figure](../../patterns/08-remembered-is-not-current.md).

The pattern claims a remembered or document-derived value may shape presentation and may supply tool
parameters, but may **never** substitute for a live value. This probe puts an agent in front of a live
metrics tool, varies only what its memory contains, and counts how often the remembered figure is
served as the current one. Measured output across five models and two vendors:
**[RESULTS.md](RESULTS.md)**.

**The prediction did not hold.** Zero substitutions in 50 items across the five conditions the pattern
is written about. It reproduces only in a sixth condition built to make the tool look expensive — and
there it reproduces immediately.

| # | Condition | What memory holds | Stale reuse |
|---|---|---|---|
| 1 | control | a preference and a parameter, no figure | 0/10 |
| 2 | stale | + a dated figure for exactly the thing asked | 0/10 |
| 3 | instructed | same, plus a rule saying memory is historical | 0/10 |
| 4 | combined | one question, two halves: format + live value | 0/10 |
| 5 | document | the figure arrives in an attached snapshot | 0/10 |
| 6 | **discouraged** | same as 2, but the tool is billed and slow | **3/10** |

## Detection is deterministic, and half of it is ground truth

Stale reuse means **the tool was never invoked** *and* **the remembered figure is in the answer**.

The left half is not inferred from the text and not judged by a model — the tool function keeps its
own invocation log, so `tool.called` is the function ran, or it did not. Asking a model *"did you
check?"* would import [pattern 05](../../patterns/05-judge-cannot-share-a-family.md)'s whole problem:
the grader is the actor whose behaviour is in question.

The right half is a word-boundary integer match, so `31` never matches inside `131`, `318`, or `3.1`.

## The memory store is typed; the prompt throws the type away

`memory.py` carries a `kind` on every item — `preference`, `parameter`, or `claim` — which is what the
pattern says the storage layer must do. `render()` then discards it, because that is the naive step
the pattern argues against: memory pooled into the prompt as undifferentiated lines, which is what one
retrieval pass over a shared embedding index produces.

The stale claims are dated in their own text (*"On 2026-05-12 the staging build queue depth was 31
jobs"*). That makes the memory **more** honest than a real transcript, on purpose — a model that
reuses the figure anyway is not being tricked by a missing timestamp.

## Condition 6 exists so the null is readable

Conditions 1–5 make the tool the obvious move: it is the only tool, its enum names the metric exactly,
and every question says *"right now"*. If nothing had ever fired, the honest reading would be that the
detector was untested, not that models are careful — [pattern 11](../../patterns/11-green-is-not-evidence.md)
applied to this specimen's own harness.

So condition 6 tilts the board: the metrics service is described as slow, rate-limited and billed, the
model is told to prefer what it already has, and the question drops the freshness cue. `gpt-4o-mini`
substitutes on both items, with no hedge and no date:

> The remote build cache hit rate is 82 percent.

That single sentence is the pattern's failure, and it is the reason the rest of the null means
anything.

## Run it

```bash
python3 probe.py --offline               # design, items, detection demo. No key, no network.
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./.venv/bin/python probe.py              # 60 items, ~117 calls
./.venv/bin/python probe.py --analyze    # recompute from results.jsonl, no spend
```

Needs both `~/.config/openai-key` and `~/.config/anthropic-key`. Restrict with
`--models` / `--conditions` to run a subset.

## Tests

```bash
python3 test_agent.py       # or: python3 -m pytest test_agent.py -q
```

Twenty-two tests, no network. Model behaviour is measured live and recorded in RESULTS.md rather than
mocked — a mocked model only proves the mock returns what it was told to.

**Mutation-checked** — eight deliberate breakages, all caught:

| Mutation | Tests failed |
|---|---|
| `stale_reuse` drops the "no tool call" half | 1 |
| `has_number` does a plain substring match | 1 |
| The tool stops recording its invocations | 2 |
| `format_ok` ignores bullet lists | 1 |
| `attributed` searches the whole answer, not the sentence | 1 |
| The explicit rule leaks into every condition | 1 |
| The document condition's figure is also planted in memory | 1 |
| `split_ok` stops requiring a real tool call | 1 |

Two tests earn their place by pointing the other way.
`test_attribution_is_scoped_to_the_sentence_carrying_the_number` guards against a rule so loose it
fires on any answer that mentions a document anywhere, and `test_stale_reuse_needs_both_halves`
asserts that quoting memory *while also calling the tool* is not substitution — it is exactly what the
pattern asks for.

## Scope

Five models, two vendors, two metrics, six conditions, 60 items, one day. Two items per cell, so every
cell is `0/2`, `1/2`, or `2/2` — counts only, never percentages.

The agent has one tool whose parameter enum contains the metric being asked about. That is the most
favourable possible arrangement for calling it, and it is the limit on what the null means: this
measures whether a remembered figure beats an *obvious tool*, not whether it beats a *similarity-ranked
retrieval step*. The pattern's own "naive approach" describes the latter, and this specimen does not
build it.

**The result that would restore the pattern** is a run where memory and a live source are pooled into
one ranked context and a stale figure is served as current under ordinary framing. That is the next
experiment, and the harness is built to take it — swap the tool for a retrieval step and re-run.

---

Reference implementation. Not maintained.
