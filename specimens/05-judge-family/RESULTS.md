# Observed results

**Adjudication: central-claim-failed.** No same-family ranking flip occurred, and the one signal
that looked like self-preference dissolved when cross-family judges agreed with it. What disqualified
two of three judges was saturation and position instability — neither about lineage. The Refusal was
rewritten around those.

**Run 2026-08-05.** Two candidates from different model families, twelve items, three judges — two
from one family, one from the other. Absolute scoring first, then pairwise in both orders.

Candidates: `gpt-4o-mini` (openai) · `claude-sonnet-4-5` (anthropic).
Judges: `gpt-4o-mini`, `gpt-4o` (openai) · `claude-sonnet-4-5` (anthropic).

## Pass 1 — absolute scoring, 1–5 on three dimensions

| Judge | Family | openai | anthropic | gap | MDE | discordant | verdict |
|---|---|---|---|---|---|---|---|
| `gpt-4o-mini` | openai | 15.00 | 15.00 | +0.00 | ∞ | **0** | **NO SIGNAL** |
| `claude-sonnet-4-5` | anthropic | 13.58 | 14.58 | −1.00 | 0.77 | 8 | anthropic |
| `gpt-4o` | openai | 15.00 | 15.00 | +0.00 | ∞ | **0** | **NO SIGNAL** |

**Both OpenAI judges awarded a perfect 15/15 to all 24 answers.** One distinct score across the
entire run. They did not rate the candidates as equal — they produced no measurement at all.

This is a ceiling effect, and it is the first thing that goes wrong in practice. Judge independence
is moot when two of your three judges carry no information.

## Pass 2 — pairwise, both orders

Every (item, judge) pair was run twice with the answers swapped. A judge that picks whichever answer
came first has expressed a position preference, not a quality preference.

| Judge | Family | n | consistent | **position flips** | openai wins | anthropic wins |
|---|---|---|---|---|---|---|
| `gpt-4o-mini` | openai | 12 | 9 | 3 | 0 | 9 |
| `claude-sonnet-4-5` | anthropic | 12 | 12 | **0** | 0 | 12 |
| `gpt-4o` | openai | 12 | 6 | **6** | 0 | 6 |

## What this shows

**1. No ranking flip. The decisive test did not fire.** Every judge that resolved a winner picked the
same candidate. On this comparison, the choice of judge did not change the outcome.

**2. The apparent self-preference was not self-preference.** Pass 1 showed the Anthropic judge
scoring its own family +1.00 higher, which reads as textbook self-preference. Pass 2 contradicts
that: **both cross-family judges also preferred the Anthropic answers, unanimously.** The simplest
explanation consistent with all six measurements is that those answers were better on this task set,
and every judge noticed.

Had the run stopped after pass 1, the honest-looking conclusion would have been the wrong one.

**3. Position bias is large, judge-specific, and separable only by running both orders.** `gpt-4o`
flipped its answer on **half** the items — on six of twelve it simply preferred whichever came
first. A single-order pairwise evaluation using that judge would have been measuring position as
much as quality. `claude-sonnet-4-5` flipped on none.

**4. Judge quality varies more than judge bias did, here.** Across three judges the differences that
mattered were *saturation* (two produced nothing) and *position sensitivity* (0 to 50%). Neither is
about lineage. Both would invalidate a promotion decision.

## What was tested and did not reproduce

The pattern's central claim is the **cross-family judge rule**: that a judge sharing a model family
with the subject will favour it, and that excluding the subject's lineage is the mitigation.

**This run does not demonstrate that.** It could not: with the cross-family judges saturated in pass 1
and unanimous in pass 2, there was no disagreement for lineage to explain. The one signal that looked
like self-preference dissolved when cross-family judges agreed with it.

**Absence of a flip is not evidence of judge independence.** The flip test tells you when you have a
problem. It cannot tell you that you do not — a unanimous panel can be unanimously wrong, and
agreement between two judges is reliability, not validity. Establishing validity needs a
hand-labelled reference set, which this specimen does not have.

## Scope

Twelve items, two vendors, three judges, one rubric, one day. The task set is general engineering
explanation — a domain where both candidates are strong, which is precisely why absolute scoring
saturated. A harder or more adversarial task set would likely separate them, and might well produce
the flip this run did not.

**The result that would confirm the pattern** is a comparison where a same-family judge picks one
winner and a cross-family judge picks the other. Finding one is future work, and the harness is built
to run it — swap the task set and re-run.

## Reproducing

```bash
printf '%s' 'sk-...'      > ~/.config/openai-key    && chmod 600 ~/.config/openai-key
printf '%s' 'sk-ant-...'  > ~/.config/anthropic-key && chmod 600 ~/.config/anthropic-key
./.venv/bin/python probe.py
```

Roughly 24 generations plus 72 absolute judgements plus 72 pairwise comparisons.

Every verdict is written to `verdicts.jsonl` and `pairwise.jsonl` **before** aggregation. Both
analysis defects found during this run were fixed and the results recomputed from those files
without re-spending a cent — which is the entire argument for persisting per-item records.
