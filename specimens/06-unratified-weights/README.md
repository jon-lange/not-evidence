# Specimen 06 — equal weights pick the loser 40% of the time

Demonstrates [pattern 06 · Refuse to Score Unratified Weights](../../patterns/06-refuse-unratified-weights.md).

Two documentation generators, six dimensions, scores measured. Then somebody has to collapse six
numbers into one, and the only thing standing between the measurements and the verdict is a weighting
nobody has ratified.

```
 weighting                  alder     birch    margin   winner
 equal weights              7.200     7.383    -0.183   birch
 correctness-first          7.530     7.295    +0.235   alder
 iteration-first            6.760     7.570    -0.810   birch

 measure                               flip share
 uniform over every weighting              0.4055
 every dimension at least 5%               0.3610
 near equal weights, Dirichlet(8)          0.2334
```

**40.6% of all weightings pick the candidate equal weights reject.** Measured output, including the
gate and the boundary conditions: **[RESULTS.md](RESULTS.md)**.

## The finding

**Equal weights are a strong claim wearing the costume of no claim, and the claim is worth 3.7
percentage points of weight.** Take that much of the total off `build_time` and put it on
`api_coverage` — 16.7% becomes 12.9% and 20.4% — and the winner reverses. No reviewer flags a
difference that size in a config file. Nobody downstream of the winner can see it at all.

The flip share is exact rather than estimated. A weighting picks the left candidate exactly when
`delta . w > 0`, so the question is what share of the simplex lies on one side of a hyperplane
through it, and that has a closed form: with `w` uniform on the simplex, `sign(delta . w)` matches
`sign(sum delta_i E_i)` for `E_i` iid exponential, which turns a volume into a probability with a
short recursion over the positive and negative deltas. `monte_carlo_share` re-derives the same number
by sampling and agrees to within 1.7 standard errors across nine cells.

**What makes a flip region is mixed-sign deltas, not a close result.** The lopsided scorecard wins by
1.00 under equal weights — 5.5× the close card's margin — and 13.6% of weightings still reverse it.
Under the unfloored simplex any mixed-sign delta vector has a flip region, because weight
concentrated on one dimension elects whoever won that dimension.

**And where one candidate dominates, none of it applies.** The third scorecard flips under no
weighting at all: 0.0000 in every measure, and the cheapest-shift search returns nothing. That is
pattern 06's boundary, and it is reported here rather than left out.

## The gate

`score()` takes a `Ratification` and has no parameter that could supply a default weighting. Four
checks, each failing with a different message naming a different person:

```
 run                               refusing gate   reason / escalate to
 equal weights, no record          FAILED          no ratification record for 'docgen-close'
                                                   -> nobody — this weighting has never been shown to anyone
 ratified weighting                scored          docgen-close: alder 7.53 | birch 7.29 -> alder
 one weight nudged by 0.01         FAILED          weights edited since ratification
                                                   -> r.okonkwo
 a seventh dimension added         FAILED          dimension set changed since ratification
                                                   -> r.okonkwo
 engineer ratified it themselves   FAILED          'j.mercer' ratified their own weighting
                                                   -> somebody who owns the quality bar and is not running this job
```

The third row is the one that matters most in practice. Sign-off is a claim about particular numbers,
so the record stores a hash of the canonical weighting and any edit — down to `1e-4` — invalidates
it. The fourth row is the same idea applied to the dimension *set*: every weight that was ratified is
still present and unchanged, a seventh dimension has appeared beside them, and the weighting now
means something the owner never saw.

**Run the same five through a version that warns, and all five produce a number:**

```
 equal weights, no record          warned          docgen-close: alder 7.20 | birch 7.38 -> birch
 ratified weighting                clean           docgen-close: alder 7.53 | birch 7.29 -> alder
 one weight nudged by 0.01         warned          docgen-close: alder 7.51 | birch 7.30 -> alder
```

Same format, same precision, same authority — and the first two name different winners. The line the
warned run emits is byte-identical in shape to the ratified one, which is asserted rather than
described (`test_the_warned_number_is_byte_identical_to_the_ratified_one`). Adding a provenance field
does not fix this: the warned path would have to write some value into it, and the summary
downstream drops it either way.

**The difference is not severity, it is audience.** Both paths carry the same information. The
warning goes to the log, read by the engineer, who already knew and does not own the quality bar. The
refusal carries `escalate_to` and stops.

**The un-collapsed table is never gated.** `per_dimension_rows` needs no record and always runs. Six
numbers side by side carry no endorsement, because nobody mistakes a table of dimensions for a
verdict — so the exploratory run survives, and only the collapse needs an owner.

## Run it

```bash
python3 probe.py            # about half a second
python3 probe.py --quick    # skip the monte-carlo cross-check
```

No network, no API key, no dependencies, no configuration. This specimen makes a claim about scoring
governance rather than about a model, so everything it asserts is arithmetic and reproducible.

## Tests

```bash
python3 test_scorecard.py   # 30 tests
python3 test_ratify.py      # 26 tests
# or: python3 -m pytest -q
```

Three tests assert something the gate *cannot* do rather than something it guarantees —
`test_the_gate_cannot_tell_a_real_owner_from_a_plausible_string`,
`test_the_warning_path_scores_every_run_the_gate_refused`, and
`test_the_warned_number_is_byte_identical_to_the_ratified_one`. They pin the limits so a later change
that quietly widens the claim is caught.

**Mutation-checked.** Forty-eight deliberate breakages; forty-seven caught, and 55 of the 56 tests
are killed by at least one.

| Mutation | Tests failed |
|---|---|
| The correctness-first weighting drops a dimension | 20 |
| `share_below_zero` always reports no flip region | 13 |
| The no-negatives base case is never reset | 11 |
| `ratify` records the dimensions in scorecard order | 11 |
| `verify` accepts everything | 10 |
| The recursion drops the sign on the negative term | 9 |
| `score` falls back to a number when the gate fails | 9 |
| `margin` is computed the other way round | 8 |
| The close scorecard is not actually a trade-off | 7 |
| The hash covers the dimensions but not the weights | 6 |
| The recursion swaps its two previous states | 5 |
| A one-sided scorecard reports a full flip region | 4 |
| `equal` hands every dimension a weight of 1 | 4 |
| The weights hash is never compared | 4 |
| The warning path raises instead of warning | 4 |
| The concentration is ignored | 3 |
| A missing record is not a refusal | 3 |
| The floor is ignored | 2 |
| `flip_share` ignores which candidate the reference picked | 2 |
| The dominant scorecard has a weakness after all | 2 |
| The un-collapsed table is gated too, and returns nothing | 2 |
| Self-ratification is allowed | 2 |
| `canonical` keeps the caller's dimension order | 2 |
| The decision record carries the owner after all | 2 |
| The warning path warns even when the weighting was ratified | 2 |
| Tied dimensions count as favouring the right-hand candidate | 1 |
| `flip_share` invents a winner for a tied scorecard | 1 |
| `minimum_flip_shift` skips the feasibility check | 1 |
| `minimum_flip_shift` moves the weight the wrong way | 1 |
| The monte-carlo check ignores the floor | 1 |
| The monte-carlo check ignores its seed | 1 |
| A tie under a weighting is reported as a win for the left | 1 |
| `weighted_total` accepts a weighting that omits a dimension | 1 |
| `per_dimension_rows` reports the sum instead of the difference | 1 |
| `normalised` does not normalise | 1 |
| A default weighting appears on `weighted_total` | 1 |
| The dimension set is never compared | 1 |
| A record transfers between scorecards | 1 |
| `canonical` does not require normalised weights | 1 |
| `canonical` does not check the dimension set | 1 |
| The hash rounds weights to one decimal place | 1 |
| `ratify` issues records with no owner | 1 |
| The refusal does not name anyone to escalate to | 1 |
| `UnratifiedWeighting` is a warning | 1 |
| The gate screens owners against a placeholder denylist | 1 |
| `record` acquires a default of `None` | 1 |
| `verify` reports success instead of returning nothing | 1 |
| The positives keep their zeros while the negatives drop theirs | **0** |

**The mutation check found two vacuous tests in this specimen's own suite, and deleted a third.**

`test_normalised_rescales_a_weighting_that_does_not_sum_to_one` did not exist. Both authored
weightings were written already summing to 1, so a `normalised()` that returned its input unchanged
passed every test in the file — the test that "checked" normalisation was checking the literals.

`test_canonical_form_ignores_dict_order` could not fail. `canonical` iterates the dimension tuple and
looks weights up by name, so the dict's own ordering was never reachable; the assertion held for
reasons unrelated to what it claimed to test. It now also asserts against a reordered *dimension
tuple*, which is the order that can actually vary.

`test_a_zero_floor_is_the_unfloored_simplex` was deleted. No mutation could break it, because the
identity it asserted was true by construction — and the guard it was defending (`0.0 if floor == 0`)
turned out to be dead code, since the general expression already yields zero at `floor=0`. Both are
gone.

**One mutation survived, and it is the same fact as the one test nothing kills.** Filing zero deltas
with the positives instead of leaving them out changes no result, because a zero is an absorbing
no-op on either side of the recursion — which is precisely what `test_zero_deltas_are_inert` asserts.
A surviving mutation normally means one of two things is wrong; here it means the code is insensitive
to that change by construction, and the test and the mutation are two views of one property.

## Where this is weaker than pattern 06 claims

**The flip share is not a property of the scorecard.** It is a property of the scorecard *and* a
measure over weightings, and picking that measure is the same unargued act one level up. "Uniform
over the simplex" says a weighting that puts 99% on theme customisation is as likely as any other.
Concentrate toward equal weights and the headline falls monotonically — 40.6%, 30.5%, 23.3%, 15.1%,
1.9% at Dirichlet 1, 4, 8, 16, 64 — and raising the floor on the lopsided card from 5% to 14% takes
its flip region to exactly zero. There is no measure-free flip fraction, and this specimen does not
have a principled measure to recommend. It declares three and shows the spread.

**The gate cannot tell a real owner from a plausible string.** `owner="TODO"` passes. A denylist of
placeholder-looking names would be worse than none — it would pass everything not on the list while
looking like it checked, which is [pattern 02](../../patterns/02-refuse-the-class.md)'s failure. What
is enforced is that a name is attached, that it is bound to one version, and that editing the version
invalidates it.

**Clause 1 is demonstrated structurally, not empirically.** That a failure reaches a different
audience than a warning is a claim about people. What is measured is that the two artefacts are
identical and that the failure carries an escalation target. The defensible half is *a warning cannot
reach the right audience*; that a failure does is not established here.

**Re-ratification is cheap.** The hash makes an edit visible, not expensive. The pattern's sharpest
observation — that showing an owner the scores first turns ratification into negotiation with a
result — is not defended against by anything in this specimen.

## Scope

Three constructed scorecards, six commensurable dimensions, two candidates, one day. **40.6% is a
measurement of `docgen-close`, not an estimate of how often real evaluations flip**, and no number
here would be honest about that. The general statement the specimen does support is structural: a
mixed-sign delta vector always has a flip region under the unfloored simplex.

**The result that would falsify the pattern** is a domain where winners are robustly
weight-independent — where real scorecards mostly look like `docgen-dominant`, which flips under
nothing. Then the gate is ceremony with a real cost. The full list, with what was observed against
each, is in [RESULTS.md](RESULTS.md).

## What this specimen deliberately does not do

**It does not model uncertainty in the scores.** Every dimension is a point estimate on one 0–10
scale. Real scorecards mix units and carry error bars, and both make the aggregate *more* sensitive
to unstated choices — so this is a lower bound on the problem, not a characterisation of it.

**It does not handle dimensions that are gates rather than terms.** "Fails accessibility audit" is
not a score to be weighed against build time; it is a veto. A weighted sum cannot express that, and
the failure mode where a hard requirement gets traded away by a large weight elsewhere is real,
common, and not exercised here.

**It does not persist ratifications anywhere.** Records are constructed in process. A real
implementation needs them checked in, reviewed, and signed by something stronger than a string field
— and the moment they live in the repository, the question of who can edit that file becomes the
whole control.

**The self-ratification check is an addition, not the pattern.** Refusing a record whose owner is the
person running the job is separation of duties, which pattern 06 does not state and which is trivial
to defeat by changing a string. It is here because that is where the failure starts: the engineer
sitting in front of the field labelled `weights`.

---

Reference implementation. Not maintained.
