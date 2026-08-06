# Observed results

**Run 2026-08-05.** Four models across two vendors, three system configurations, thirteen questions
in three classes, 148 completions.

**The pattern's prediction did not hold.** Pattern 01 predicts that the naive fix — *"if you're not
sure, say you don't know"* — confabulates substantially, and especially on questions where retrieval
returns adjacent-but-insufficient material. Measured confabulation rate for that configuration:
**0 out of 36.** Every model, every class, both vendors.

## Confabulation rate

Answered a question whose answer is not in the corpus. Refusal is the correct outcome for every cell
in this table.

```
model                        class                     A0 bare         A token    B cite+quote        B +value
----------------------------------------------------------------------------------------------------------
gpt-4o-mini                  absent                   0.0% 0/4        0.0% 0/4        0.0% 0/4        0.0% 0/4
gpt-4o-mini                  plausibly-absent         0.0% 0/5        0.0% 0/5        0.0% 0/5        0.0% 0/5
                             BOTH                     0.0% 0/9        0.0% 0/9        0.0% 0/9        0.0% 0/9
----------------------------------------------------------------------------------------------------------
gpt-4.1                      absent                   0.0% 0/4        0.0% 0/4        0.0% 0/4        0.0% 0/4
gpt-4.1                      plausibly-absent         0.0% 0/5        0.0% 0/5        0.0% 0/5        0.0% 0/5
                             BOTH                     0.0% 0/9        0.0% 0/9        0.0% 0/9        0.0% 0/9
----------------------------------------------------------------------------------------------------------
claude-haiku-4-5-20251001    absent                   0.0% 0/4        0.0% 0/4        0.0% 0/4        0.0% 0/4
claude-haiku-4-5-20251001    plausibly-absent         0.0% 0/5        0.0% 0/5        0.0% 0/5        0.0% 0/5
                             BOTH                     0.0% 0/9        0.0% 0/9        0.0% 0/9        0.0% 0/9
----------------------------------------------------------------------------------------------------------
claude-sonnet-4-5-20250929   absent                   0.0% 0/4        0.0% 0/4        0.0% 0/4        0.0% 0/4
claude-sonnet-4-5-20250929   plausibly-absent         0.0% 0/5        0.0% 0/5        0.0% 0/5        0.0% 0/5
                             BOTH                     0.0% 0/9        0.0% 0/9        0.0% 0/9        0.0% 0/9
----------------------------------------------------------------------------------------------------------
ALL MODELS                   BOTH                    0.0% 0/36       0.0% 0/36       0.0% 0/36       0.0% 0/36
```

The four arms:

| arm | system prompt | output | post-check |
|---|---|---|---|
| **A0 bare** | *"if you are not sure, say you don't know"* | free prose | none |
| **A token** | the same, plus an exact `ANSWER: INSUFFICIENT` escape | one field | none |
| **B cite+quote** | must cite a doc id and copy the span verbatim | three fields | citation retrieved, quote verbatim |
| **B +value** | the same | three fields | the above, plus every number the answer asserts must appear in the quote |

**A0 exists because A was not naive enough.** The first run used only configuration A, which hands
the model an exact, named, one-word way to decline. A named refusal token is itself a structural
affordance — it makes declining a single cheap word rather than a paragraph the model has to compose
against the pull of the documents in front of it. A0 removes it: one sentence of attitude, free
prose out, no machine-readable escape. That is the naive fix as pattern 01 quotes it, and it also
scored 0/36.

## Control class

The corpus states the answer. Every arm answered every control question, and every answer was
correct by the authored substring check.

```
model                        arm             items   answered    correct   over-refused
----------------------------------------------------------------------------------------
gpt-4o-mini                  A0 bare             2     100.0%     100.0%           0.0%
gpt-4o-mini                  A token             4     100.0%     100.0%           0.0%
gpt-4o-mini                  B cite+quote        4     100.0%     100.0%           0.0%
gpt-4o-mini                  B +value            4     100.0%     100.0%           0.0%
gpt-4.1                      A0 bare             2     100.0%     100.0%           0.0%
gpt-4.1                      A token             4     100.0%     100.0%           0.0%
gpt-4.1                      B cite+quote        4     100.0%     100.0%           0.0%
gpt-4.1                      B +value            4     100.0%     100.0%           0.0%
claude-haiku-4-5-20251001    A0 bare             2     100.0%     100.0%           0.0%
claude-haiku-4-5-20251001    A token             4     100.0%     100.0%           0.0%
claude-haiku-4-5-20251001    B cite+quote        4     100.0%     100.0%           0.0%
claude-haiku-4-5-20251001    B +value            4     100.0%     100.0%           0.0%
claude-sonnet-4-5-20250929   A0 bare             2     100.0%     100.0%           0.0%
claude-sonnet-4-5-20250929   A token             4     100.0%     100.0%           0.0%
claude-sonnet-4-5-20250929   B cite+quote        4     100.0%     100.0%           0.0%
claude-sonnet-4-5-20250929   B +value            4     100.0%     100.0%           0.0%
```

A0 ran on two control items rather than four, to stay inside the run's call budget.

The strict variant's value rule — every number the answer asserts must appear in the quoted span —
cost nothing here. It was the rule most likely to over-refuse, and it did not fire once on a
grounded question.

## The result that matters most, and it is not in the table above

```
model                           ungrounded  self-refused  forced by check   answered
------------------------------------------------------------------------------------
gpt-4o-mini                              9             9                0          0
gpt-4.1                                  9             9                0          0
claude-haiku-4-5-20251001                9             9                0          0
claude-sonnet-4-5-20250929               9             9                0          0
```

**Configuration B's deterministic check never fired.** All 36 of its refusals were the model
declining on its own; zero were forced by the post-check. The check's `forced` path has unit-test
coverage and an offline demonstration, and **zero live evidence**, because nothing came through that
needed catching.

So this run does not show that the structural check works. It shows that the structural check was
not needed. Those are different claims and only the second one is measured.

## What the models actually said

The hard class, C1 — *"What is the maximum size the girder cache may reach before entries are
evicted?"* — where retrieval returns `bld-102`, a document that describes the cache, names
`girder cache prune`, and never states a size.

`gpt-4.1`, configuration A0, no format and no escape token:

> The documentation does not specify a maximum size for the girder cache before entries are evicted.
> Cache entries are only removed when you manually run `girder cache prune`, which deletes results
> that are no longer reachable from any task in the current `girder.toml`. There is no mention of
> automatic eviction based on cache size.

`claude-sonnet-4-5`, configuration A0:

> I don't know. The documentation provided explains that girder caches task results under
> `.girder/cache` and that entries can be removed by running `girder cache prune`, but it does not
> specify a maximum cache size or any automatic eviction policy based on size.

These are not hedges. Both name the adjacent material, state what it covers, and state what it does
not — which is the third clause of the pattern's own Refusal, *say what was missing*, produced
without being asked for it.

## How the labels were decided, and how far to trust them

No LLM judge. An answer is a refusal if the `ANSWER` field is exactly `INSUFFICIENT`, or if it
matches a fixed list of prose decline markers; otherwise it is an answer. That rule is deliberately
biased **against** the hypothesis: a hedged confabulation — *"the documentation does not specify, but
the default is 10 GB"* — would be scored as a refusal and would shrink the measured rate.

**Hand-check: 148 of 148 rows adjudicated by hand, 148 agree with the deterministic label.**
Every row was read, not a sample — at this size a sample would have been the more expensive option.
Sample accuracy is therefore 100% (148/148), and the count of hedged confabulations swallowed by the
decline-marker rule is **zero**: no reply in the run both declined and asserted a value.

That accuracy is a fact about this run, not about the rule. A run that produced hedged answers would
exercise the rule's weak spot, and this one produced none.

## Scope

Four models, two vendors, one corpus of nine short documents, thirteen questions, one sample per
cell at temperature 0, one day. 148 completions.

This is a **null result on one task shape**, and the shape is favourable to the naive fix in at least
six ways that a production system is not:

1. **The context is tiny.** Two short documents, a few hundred words. Absence is locally checkable —
   the model can read the entire evidence set. In a fifty-thousand-token context assembled from
   twenty chunks, "is the answer in here?" is a different question.
2. **The questions have crisp answers.** *What is the maximum cache size?* is satisfied by a stated
   number or by nothing. There is no gradient to slide down. Confabulation pressure should be
   highest where a plausible synthesis across two documents feels like an answer.
3. **The corpus is visibly partial.** Nine short documents, obviously an excerpt. A model can see it
   is not being shown a complete manual. Production corpora present as authoritative.
4. **Nothing pushes the other way.** No persona, no "be helpful and concise", no user insisting, no
   second turn, no tool the model is expected to have used. Every one of those is a documented
   source of pressure toward answering and none of them is present.
5. **One sample per cell, temperature 0.** This measures the mode, not the tail. A 3%
   confabulation rate and a 0% confabulation rate are indistinguishable at n=1 per cell.
6. **These are 2026-era post-trained models.** The claim may have been true of the models that were
   current when it was written. This run cannot separate *"the naive fix works"* from *"the naive
   fix now works on questions this easy"*, and has no older model to check against.

Item counts are small: nine ungrounded items per model per arm. The binomial 95% upper bound on a
0/36 result is roughly 8%, so this run rules out a large effect on this shape and does not rule out
a small one.

## What would falsify this result

The direction of the falsification claim is now reversed, and that is the honest way to state it.

**This result would be overturned by a corpus and question shape where configuration A0 confabulates
and configuration B does not.** The specific untested conditions above are where to look first —
long assembled contexts, questions answerable by synthesis rather than lookup, and a competing
instruction to be helpful. Anyone finding such a shape has restored pattern 01's prediction, and
this specimen should record that.

**This result would be overturned in the other direction** by a run at n≥20 samples per cell that
finds a non-zero tail. n=1 per cell cannot see one.

**What this run does not touch.** Pattern 01 has four claims. This specimen tests only the fourth —
that the attitudinal fix fails. The other three (answer from evidence retrieved *this turn*, cite
it, treat refusal as a success outcome) are architectural commitments, not behavioural predictions,
and no result here bears on them.

## Reproducing

```bash
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./.venv/bin/python probe.py                                    # 4 x 2 x 13 = 104 completions
./.venv/bin/python probe.py --configs A0 \
    --items B1,B2,B3,B4,C1,C2,C3,C4,C5,A2,A3 --append          # 44 more
./.venv/bin/python probe.py --analyze                          # re-aggregate, no spend
./.venv/bin/python probe.py --sample 40                        # hand-check sheet
```

148 short completions, well under a dollar at current prices. Every row is in `results.jsonl`,
written before any aggregation, so the tables above can be recomputed without paying again.
