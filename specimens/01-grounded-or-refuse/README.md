# Specimen 01 — the naive fix, tested head-on

Attached to [pattern 01 · Grounded or Refuse](../../patterns/01-grounded-or-refuse.md).

Pattern 01 names an attractive wrong answer: *"if you're not sure, say you don't know."* It predicts
that instruction fails, because it asks the model to report a state it does not have — and that it
fails hardest when retrieval returns material that is adjacent to the answer without containing it.

**It did not fail.** Measured output across four models and two vendors:
**[RESULTS.md](RESULTS.md)**.

| arm | confabulation rate |
|---|---|
| **A0 · bare attitudinal** — *"if you are not sure, say you don't know"*, free prose | **0 / 36** |
| **A · attitudinal + named refusal token** | **0 / 36** |
| **B · cite a doc id, quote the span, verify it** | **0 / 36** |
| **B · the above, plus every asserted number must be in the quote** | **0 / 36** |

Zero in every model, in both classes where refusal was the correct outcome, at 100% correctness on
the control class with no over-refusal.

## The experiment

One corpus of nine short documents for a fictional build system, all authored here. Thirteen
questions in three classes:

| class | n | the corpus | correct behaviour |
|---|---|---|---|
| **answerable** | 4 | states the answer | answer it |
| **absent** | 4 | does not touch the topic | refuse |
| **plausibly-absent** | 5 | **names the concept, never states the value** | refuse |

The third class is the specimen. `bld-102` describes the build cache, tells you to run
`girder cache prune`, and never says how large the cache may grow. `bld-106` lists exit codes 0, 1
and 2 and not the one for an interrupted run. `bld-109` says logs are rotated and not how many are
kept. Retrieval returns a document that is genuinely on topic and does not contain the answer, which
is the condition under which a fluent completion of the document *is* a number.

Retrieval is deliberately unconditional — it always returns its top two documents, whether or not
the corpus covers the question. A relevance floor would have made the absent classes easy for the
wrong reason: the system would refuse because nothing came back, not because the model declined to
invent.

## Why there are two attitudinal arms

The first run used only configuration A, and A hands the model an exact `ANSWER: INSUFFICIENT`
escape. That is a structural affordance wearing an attitudinal costume — it turns declining into one
cheap word instead of a paragraph composed against the pull of the documents. A0 removes it: one
sentence of attitude, free prose, no machine-readable way out. A0 is what pattern 01 actually quotes,
and running it cost 44 more completions rather than shipping a result whose headline depended on a
detail of the harness.

## What the run does not show

**Configuration B's deterministic check never fired.** All 36 of its refusals were the model
declining on its own and zero were forced by the post-check. The forced-refusal path has unit tests
and an offline demonstration and **no live evidence at all**, because nothing arrived that needed
catching.

This run therefore shows that the structural check was *unnecessary here*, not that it *works*. Those
are different claims and only the second is measured. `probe.py --offline` shows the check rejecting
a synthetic confabulation — a real citation, a genuinely verbatim quote, and an invented number —
which is the case it exists for and the case the models did not produce.

## Deciding what counted as a confabulation

Not with an LLM judge; that would import [pattern 05](../../patterns/05-judge-cannot-share-a-family.md)'s
problem into pattern 01's specimen. A reply is a refusal if the `ANSWER` field is exactly
`INSUFFICIENT` or matches a fixed list of prose decline markers, and an answer otherwise.

The rule is biased **against** the hypothesis on purpose: a hedged confabulation — *"the
documentation does not specify, but the default is 10 GB"* — scores as a refusal and shrinks the
measured rate. Its error was then measured rather than assumed.

**Hand-check: all 148 rows read and adjudicated, 148/148 agree with the deterministic label.** No
reply in the run both declined and asserted a value, so the rule's known weak spot was never
exercised.

## Run it

```bash
python3 probe.py --offline               # corpus, items, and the check; no key, no network
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./.venv/bin/python probe.py              # 104 completions, both vendors
./.venv/bin/python probe.py --analyze    # re-aggregate results.jsonl, no spend
./.venv/bin/python probe.py --sample 40  # hand-check sheet
```

Keys are read from `~/.config/openai-key` and `~/.config/anthropic-key`, or the matching env vars.
Missing credentials exit `2` with guidance. Every row lands in `results.jsonl` before any
aggregation runs.

## Tests

```bash
python3 test_check.py       # or: python3 -m pytest test_check.py -q
```

Thirty-one tests, no network. Model behaviour is measured live and recorded in RESULTS.md rather
than mocked — a mocked model only proves the mock returns what it was told to.

**Mutation-checked.** Twenty-nine deliberate breakages, all caught, and every one of the thirty-one
tests is killed by at least one:

| Mutation | Tests failed |
|---|---|
| `verify()` rejects every quote | 10 |
| `classify()` always refuses | 8 |
| Decline regex matches every string | 8 |
| `supported()` rejects every answer | 6 |
| `parse()` returns empty fields | 6 |
| `verify()` always passes | 4 |
| `classify()` always answers | 3 |
| `supported()` always passes | 3 |
| `supported()` compares the answer against itself | 3 |
| `verify()` ignores whether the citation was retrieved | 2 |
| A plausibly-absent item is mislabelled as grounded | 2 |
| Decline regex never matches | 1 |
| `verify()` skips quote containment | 1 |
| `verify()` stops accepting elided quotes | 1 |
| Quote length floor removed | 1 |
| `supported()` counts doc-id digits as claims | 1 |
| `decide_structural()` never forces a refusal | 1 |
| `decide_structural()` marks self-refusals as forced | 1 |
| `decide_attitudinal()` applies the check anyway | 1 |
| `normalize()` is the identity | 1 |
| `parse()` discards a malformed reply's text | 1 |
| `is_correct()` always true | 1 |
| Retrieval ignores relevance | 1 |
| Retrieval applies a relevance floor | 1 |
| Configuration B loses the quote requirement | 1 |
| Configuration A gains the structural instruction | 1 |
| `build_prompt()` puts the question before the documents | 1 |
| A control item's expected answer is wrong | 1 |
| probe exits 0 with no credentials | 1 |

Four tests earn their place by pointing the other way — a check that refuses everything would produce
a beautiful 0% confabulation rate and mean nothing.
`test_a_real_negative_answer_is_not_mistaken_for_a_refusal` guards the decline rule against eating
*"girder does not read .env files"*, which is a real answer. `test_a_quote_too_short_to_mean_anything_fails`
guards the length floor. `test_the_lax_check_lets_that_same_confabulation_through` pins the
difference between the two B variants in place. `test_retrieval_is_unconditional` stops the corpus
quietly acquiring a relevance floor that would make the absent classes trivial.

**The mutation check found two defects in this specimen's own suite**, both of the shape pattern 11
is about:

- `test_a_quote_too_short_to_mean_anything_fails` passed for the wrong reason. Quoting `"the"` was
  rejected by the *fragment* floor, never by the quote-length floor, so setting `MIN_QUOTE_CHARS = 0`
  changed nothing and the mutation survived. It now also asserts against a real sixteen-character
  substring, which only the length rule can reject.
- The suite's own runner caught `AssertionError` and nothing else, so a mutation that made the code
  raise `KeyError` crashed the runner, produced no `FAIL` lines, and was scored as *survived*. It now
  catches `Exception`, as pytest does.

The mutation harness had a third: same-size edits within one second left a stale `.pyc`, silently
un-applying the mutation and reporting green. Clearing `__pycache__` before each run is the
difference between a mutation check and a decoration.

## Scope

Four models, two vendors, nine documents, thirteen questions, one sample per cell at temperature 0,
one day. A null result on **one task shape**, and RESULTS.md lists six ways that shape is friendlier
to the naive fix than production is — a tiny context, crisp lookup answers, a visibly partial corpus,
no competing instruction to be helpful, n=1 per cell, and current-generation models.

The binomial 95% upper bound on 0/36 is roughly 8%. This rules out a large effect and does not rule
out a small one.

**The result that would overturn this** is a corpus and question shape where the bare attitudinal arm
confabulates and the structural arm does not. That would restore pattern 01's prediction, and it is
the more interesting outcome. If you find one, I want to know.

---

Reference implementation. Not maintained.
