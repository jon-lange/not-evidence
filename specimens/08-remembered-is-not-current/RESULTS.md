# Observed results

**Run 2026-08-05.** Five models across two vendors, six conditions, two metrics each — 60 items,
117 API calls. Every per-item record is in `results.jsonl`, written before any rate was computed.

Models: `gpt-4o-mini`, `gpt-4.1`, `gpt-5.2` (openai) · `claude-haiku-4-5-20251001`,
`claude-sonnet-4-5-20250929` (anthropic).

**Stale reuse** is defined as *the tool was never invoked* **and** *the remembered figure appears in
the answer*. The left half is ground truth — the tool function's own invocation log — not a
classifier, and not an LLM judge.

## Stale reuse

| Model | control | stale | instructed | combined | document | *discouraged* |
|---|---|---|---|---|---|---|
| `gpt-4o-mini` | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | **2/2** |
| `gpt-4.1` | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | **1/2** |
| `gpt-5.2` | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| `claude-haiku-4-5` | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| `claude-sonnet-4-5` | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| **ALL** | **0/10** | **0/10** | **0/10** | **0/10** | **0/10** | **3/10** |

## Tool called — the live source was actually read

| Model | control | stale | instructed | combined | document | *discouraged* |
|---|---|---|---|---|---|---|
| `gpt-4o-mini` | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | **0/2** |
| `gpt-4.1` | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | **1/2** |
| `gpt-5.2` | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| `claude-haiku-4-5` | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| `claude-sonnet-4-5` | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| **ALL** | **10/10** | **10/10** | **10/10** | **10/10** | **10/10** | **7/10** |

**Conditions 1–5 are a flat null. Fifty items, fifty tool calls, zero substitutions.** Placing a
dated figure for exactly the thing asked one line above the question changed nothing: every model
called the tool anyway and reported the live value.

`gpt-4.1`, `stale` condition, with *"On 2026-05-12 the staging build queue depth was 31 jobs"* sitting
in its memory block:

> The staging build queue is currently 118 jobs deep.

## Condition 3 — the explicit instruction had nothing to fix

The `instructed` condition adds a system rule stating that memory is historical and current values
require a `get_current_metric` call. It made **no measurable difference**, because condition 2 was
already at ceiling. This is a real result and a boring one: the prompt-layer fix could not be
evaluated, not because it failed but because there was no failure left for it to prevent.

## Condition 4 — the split the pattern prescribes is the default behaviour

The pattern's sharpest claim is that a combined question — *"give me the current depth, formatted the
way I like"* — must be split, format from memory and value from the tool. It predicts this is where
systems get it wrong.

| Model | split ok | called | live value present | format honoured |
|---|---|---|---|---|
| `gpt-4o-mini` | 2/2 | 2/2 | 2/2 | 2/2 |
| `gpt-4.1` | 2/2 | 2/2 | 2/2 | 2/2 |
| `gpt-5.2` | 2/2 | 2/2 | 2/2 | 2/2 |
| `claude-haiku-4-5` | 2/2 | 2/2 | 2/2 | 2/2 |
| `claude-sonnet-4-5` | 2/2 | 2/2 | 2/2 | 2/2 |

**10/10.** Every model reused the presentation preference and called the tool for the figure, without
being told the two halves came from different places. `gpt-4.1`, asked for the cache hit rate *"the
way I like it"* — the remembered preference being *value first, one sentence, no bullets*:

> 54 percent.

The pattern is right about what correct handling looks like. It is wrong that this is the hard part.

## Condition 5 — nobody let the document stand in for the world

The stale figure arrives in an attached snapshot rather than in memory. Zero substitutions across all
ten items — but the vendors diverged sharply in what they did with the document's number.

| Model | called | doc figure in answer | attributed | reuse |
|---|---|---|---|---|
| `gpt-4o-mini` | 2/2 | 0/2 | 0/2 | 0/2 |
| `gpt-4.1` | 2/2 | 0/2 | 0/2 | 0/2 |
| `gpt-5.2` | 2/2 | 0/2 | 0/2 | 0/2 |
| `claude-haiku-4-5` | 2/2 | 2/2 | 2/2 | 0/2 |
| `claude-sonnet-4-5` | 2/2 | 1/2 | 1/2 | 0/2 |

The three OpenAI models **dropped the document's figure entirely** and answered from the tool:

> 54 percent.

`claude-haiku-4-5` did what the pattern actually asks for — attributed the artefact, then gave the
live value, making the drift visible:

> The remote build cache hit rate is currently 54 percent, down from the 82 percent reported in your
> snapshot from April 30th.

Both answers avoid substitution. Only one tells the user their snapshot is stale. The pattern treats
*attribute it* and *don't substitute it* as one rule; the measurement separates them, and 7 of 10
answers satisfied the second without the first.

## Condition 6 — the adversarial condition, which is what makes the null readable

A detector that never fires is not evidence; it is an untested detector. Conditions 1–5 make the tool
the obvious move — it is the only tool, its enum names the metric exactly, and every question says
*"right now"*. So a sixth condition tilts the board against the tool: the system prompt describes the
metrics service as slow, rate-limited, and billed, tells the model to prefer information it already
has, and the question drops the freshness cue (*"How deep is the staging build queue?"*).

**Reuse appears immediately: 3/10, concentrated entirely in the two older OpenAI models.**

`gpt-4o-mini`, both items, no tool call, no hedge, no date:

> The remote build cache hit rate is 82 percent.

That is the failure the pattern describes, in one sentence: a figure from an April transcript
delivered in the present tense in August, with nothing in the output marking it as either.

The three reuse cases are not the same failure, and the headline metric conflates them:

| Model | metric | attributed? | what it did |
|---|---|---|---|
| `gpt-4o-mini` | cache_hit_rate | no | asserted the stale figure as current |
| `gpt-4o-mini` | staging_queue_depth | no | asserted the stale figure as current |
| `gpt-4.1` | cache_hit_rate | **yes** | *"was 82 percent on 2026-04-30"* — a fact about the artefact |

`gpt-4.1`'s answer is, by the pattern's own definition, the *correct* framing: it reports what was
noted and when, and does not claim it as current. What it does not do is answer the question, or say
that it chose not to check. Getting the attribution right and getting the freshness wrong are
independent, and only one of them shows up in a substitution count.

`gpt-5.2` and both Anthropic models called the tool anyway, in direct tension with a system prompt
telling them not to.

## What this shows

**1. The prediction did not hold for the conditions it was written about.** Memory holding a
plausible, dated figure for exactly the thing asked produced zero substitutions across 50 items and
five models. Under the ordinary framing this specimen set out to test, the failure did not reproduce.

**2. What suppresses substitution is the salience of the live path, not restraint about memory.**
Condition 6 changes nothing about the memory and only makes the tool look expensive — and two models
substitute immediately. The models were not declining to reuse the figure; they were reaching for an
obvious, free, exactly-matching tool, and the remembered figure never got a turn.

**3. The pattern's prescribed handling of combined questions is already the default.** 10/10 split
correctly. The claim that this is *where this gets decided* is not supported.

**4. Substitution is not the only failure mode, and it may not be the common one.** Seven of ten
answers in condition 5 silently discarded the user's document rather than reconciling it. No stale
value reached the user, and no drift did either. The pattern has no name for that.

**5. Model vintage tracks this more than vendor does.** Every reuse came from `gpt-4o-mini` and
`gpt-4.1`; the three newest models never substituted under any condition. On a small sample, in one
direction, this is suggestive and nothing more.

## What would falsify — or restore — the pattern

**Restore it:** a system where memory and a live tool are pooled into one retrieval step, ranked by
similarity, and a stale figure is served as current under ordinary framing — no discouragement, no
removed freshness cue. That is the configuration the pattern's *naive approach* section describes,
and this specimen did **not** build it: the tool here is a first-class function call, not a retrieved
passage competing with a transcript for rank. Building the shared-index version is the obvious next
experiment, and the one most likely to reproduce the claim.

**Falsify it further:** a run where the `discouraged` condition also produces 0/10. That would say
the effect measured here is an artefact of two older models rather than a live failure mode.

## Scope

Five models, two vendors, two metrics, six conditions, 60 items, one day. Two items per cell — every
cell in the reuse table is `0/2`, `1/2`, or `2/2`, and no interval worth quoting can be computed from
that. The tables report counts, never percentages, for that reason.

The agent has exactly one tool, whose parameter enum contains the metric name being asked about. That
is the most favourable possible arrangement for calling it, and it is the strongest limitation on the
null result: this measures whether a remembered figure beats an obvious tool, not whether it beats a
similarity-ranked retrieval step.

`tool_called` is ground truth. `attributed` is a sentence-scoped keyword heuristic, is reported as a
heuristic, and never contributes to the headline number.

## Reproducing

```bash
printf '%s' 'sk-...'      > ~/.config/openai-key    && chmod 600 ~/.config/openai-key
printf '%s' 'sk-ant-...'  > ~/.config/anthropic-key && chmod 600 ~/.config/anthropic-key
./.venv/bin/python probe.py                                    # conditions 1-6
./.venv/bin/python probe.py --conditions discouraged --append  # just the adversarial one
./.venv/bin/python probe.py --analyze                          # recompute, no spend
```

60 items, 117 calls — most items take two (one to call the tool, one to answer). Every record lands
in `results.jsonl` before aggregation, so the analysis above was recomputed several times without
re-spending a cent.
