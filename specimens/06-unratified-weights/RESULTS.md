# Observed results

**Run 2026-08-05.** Fully offline — standard library only, no key, no network, no model. The claim
under test is about scoring governance, so there is nothing here for a model to answer.

Three synthetic scorecards over six dimensions, two documentation generators each. Scores are 0–10,
higher better. `docgen-close` is the subject; the other two are boundary conditions, present so the
specimen reports the cases where pattern 06 has no bite.

## The measurements, verbatim

### Per-dimension results — never gated

```
 dimension                      alder   birch     delta
 api_coverage                     8.4     6.3     +2.10
 cross_reference_accuracy         9.1     7.7     +1.40
 output_accessibility             7.5     6.9     +0.60
 build_time                       5.2     8.0     -2.80
 incremental_rebuild              6.0     7.9     -1.90
 theme_customisation              7.0     7.5     -0.50
```

### 1–3 · Three weightings, all defensible, none ratified

```
 dimension                          equal weights   correctness-first     iteration-first
 api_coverage                               0.167               0.250               0.150
 cross_reference_accuracy                   0.167               0.250               0.150
 output_accessibility                       0.167               0.150               0.050
 build_time                                 0.167               0.150               0.300
 incremental_rebuild                        0.167               0.150               0.250
 theme_customisation                        0.167               0.050               0.100

 weighting                  alder     birch    margin   winner
 equal weights              7.200     7.383    -0.183   birch
 correctness-first          7.530     7.295    +0.235   alder
 iteration-first            6.760     7.570    -0.810   birch
```

Same measurements, same candidates, two winners. Nobody ratified any of the three.

### 4 · The weight simplex

```
 equal weights pick birch. Share of weightings that pick the other one:

 measure                               flip share   monte carlo
 uniform over every weighting              0.4055        0.4113
 every dimension at least 5%               0.3610        0.3654
 near equal weights, Dirichlet(8)          0.2334        0.2293

 Cheapest flip: move 3.7% of the total weight from build_time to api_coverage
 (equal weights give every dimension 16.7%, so the donor can afford it).
```

**40.6% of all weightings pick alder; equal weights pick birch.** The headline number.

The `flip share` column is exact, not estimated. The winner is decided by the sign of `delta . w`, so
the question is what share of the simplex lies on each side of a hyperplane through it, and that has
a closed form. `monte carlo` is the same quantity resampled by an estimator that shares none of that
reasoning — 20,000 draws per cell, and across the nine cells below the largest disagreement is 1.7
standard errors.

### The same search on two other shapes of scorecard

```
 docgen-lopsided — cedar vs dogwood, deltas [3.0, 2.5, 2.0, -4.0, 1.5, 1.0]
 measure                               flip share   monte carlo
 uniform over every weighting              0.1364        0.1383
 every dimension at least 5%               0.0774        0.0799
 near equal weights, Dirichlet(8)          0.0043        0.0043

 Cheapest flip: move 14.3% of the total weight from api_coverage to build_time

 docgen-dominant — elm vs fir, deltas [1.5, 0.7, 1.3, 0.3, 1.2, 0.5]
 measure                               flip share   monte carlo
 uniform over every weighting              0.0000        0.0000
 every dimension at least 5%               0.0000        0.0000
 near equal weights, Dirichlet(8)          0.0000        0.0000

 No move of weight away from equal weights changes the winner.
```

### The gate

```
 run                               refusing gate   reason / escalate to
 equal weights, no record          FAILED          no ratification record for 'docgen-close'
                                                   -> nobody — this weighting has never been shown to anyone
 ratified weighting                scored          docgen-close: alder 7.53 | birch 7.29 -> alder
 one weight nudged by 0.01         FAILED          weights edited since ratification (sha256:8ffacfc540c92668 was ratified, sha256:8dfc28de014a9182 was supplied)
                                                   -> r.okonkwo
 a seventh dimension added         FAILED          dimension set changed since ratification (added ['search_quality'], removed [])
                                                   -> r.okonkwo
 engineer ratified it themselves   FAILED          'j.mercer' ratified their own weighting
                                                   -> somebody who owns the quality bar and is not running this job

 run                               warning gate    what leaves the harness
 equal weights, no record          warned          docgen-close: alder 7.20 | birch 7.38 -> birch
 ratified weighting                clean           docgen-close: alder 7.53 | birch 7.29 -> alder
 one weight nudged by 0.01         warned          docgen-close: alder 7.51 | birch 7.30 -> alder
 a seventh dimension added         warned          docgen-close: alder 7.48 | birch 7.27 -> alder
 engineer ratified it themselves   warned          docgen-close: alder 7.53 | birch 7.29 -> alder
```

## What this shows

**1. Equal weights are not neutral, and the cost of that is 3.7 percentage points.** Move that much
of the total weight from `build_time` to `api_coverage` — 16.7% becomes 12.9% and 20.4% — and the
procurement decision reverses. Nobody reviewing a weights file would flag a difference that size, and
nobody reading the winner downstream can see it at all.

**2. The choice of weighting decides the winner over 40% of the time on this scorecard.** Not a
knife-edge case: two of the three weightings a real team would write disagree with the third, and the
region that disagrees with equal weights is a large fraction of the whole space.

**3. Closeness amplifies the effect but is not the mechanism.** `docgen-lopsided` has an equal-weight
margin of 1.00 — 5.5× the close card's 0.18 — and 13.6% of weightings still flip it. What produces a
flip region is mixed-sign deltas, and under the unfloored simplex *any* mixed-sign delta vector has
one, however large the margin: weight concentrated on a single dimension picks whoever won that
dimension.

**4. Where one candidate dominates, none of this applies.** `docgen-dominant` flips under no
weighting at all, and the cheapest-shift search returns nothing. This is the honest boundary: pattern
06's control buys exactly zero on a scorecard with no trade-off, and it cannot be known in advance
which kind you have — which is itself an argument for computing the flip share before arguing about
the weights.

**5. The warned number and the ratified number are byte-identical.** Both tables emit the same line
format at the same precision. `test_the_warned_number_is_byte_identical_to_the_ratified_one` asserts
it. Downstream of that string there is nothing left to inspect, and the two unratified runs in the
second table name *different winners* — the equal-weight run says birch, the nudged one says alder.

**6. The refusal's only real advantage is its audience.** Both paths carry the same information. The
warning path puts it in the log, which is read by the engineer, who already knew and cannot decide
what matters. The refusal path puts a name in the failure and stops.

## Where this is weaker than pattern 06 claims

**The flip share is not a property of the scorecard.** It is a property of the scorecard *and* a
measure over weightings, and choosing that measure is the same unargued act one level up. Declaring
"uniform over the simplex" is as much an unratified claim as declaring equal weights — it says a
weighting that puts 99% on theme customisation is as likely as any other. Concentrate the measure
toward equal weights and the number falls monotonically: 40.6% at Dirichlet(1), 30.5% at 4, 23.3% at
8, 15.1% at 16, 1.9% at 64. Raise the floor on `docgen-lopsided` from 5% to 14% and its flip region
vanishes entirely, from 7.7% to exactly 0. **There is no measure-free flip fraction, and this
specimen does not have a principled measure to recommend.** It reports three and shows the spread.

**The gate cannot tell a real owner from a plausible string.** `owner="TODO"` passes, and
`test_the_gate_cannot_tell_a_real_owner_from_a_plausible_string` pins that in place. A denylist of
placeholder-looking names would be worse than nothing — it would pass everything not on the list
while looking like it checked, which is pattern 02's failure. What the gate actually enforces is that
*some* name is attached, that the name travels with the version, and that any edit invalidates it.
Pattern 06's "the weighting acquires a named owner" is achieved. "The argument happens before the
number exists" is not enforced by anything here.

**The pattern's first clause is demonstrated structurally, not empirically.** That a failure reaches
a different audience than a warning is an organisational claim. What is measured is that the emitted
artefacts are identical and that the failure carries an escalation target. Whether a real team
escalates rather than deleting the gate is not something a specimen can establish, and the honest
version of clause 1 is *"a warning cannot reach the right audience"*, not *"a failure does"*.

**Re-ratification is cheap.** The hash makes an edit visible; it does not make it expensive. Somebody
who wants the other winner can nudge a weight and ask for a fresh signature, and the pattern's
sharpest observation — that showing an owner the scores first turns ratification into negotiation
with a result — is not defended against by anything in this specimen, and probably cannot be.

**The self-ratification check is an addition, not the pattern.** Refusing a record whose owner is the
person running the job is a separation-of-duties control that pattern 06 does not state. It is easy
to defeat (change the string) and is included because it is where the failure actually starts: the
engineer sitting in front of the field.

## Scope

Three constructed scorecards, six dimensions, two candidates each, one weighting hash, one day. The
scorecards are constructed and named as such — **40.6% is a measurement of `docgen-close`, not an
estimate of how often real evaluations flip.** No claim is made about the distribution of real
scorecards, and the only defensible general statement is the structural one: a mixed-sign delta
vector always has a flip region under the unfloored simplex.

Six dimensions, all commensurable on one 0–10 scale, all scored without uncertainty. Real scorecards
mix units, carry error bars, and contain dimensions that are gates rather than terms in a sum. Every
one of those makes the aggregate *more* sensitive to unstated choices, not less, so this is a lower
bound on the problem.

## What would falsify pattern 06

**A domain where winners are robustly weight-independent.** If real evaluation scorecards mostly look
like `docgen-dominant` — one candidate ahead on every dimension — then the weighting never decides
anything, and refusing to score without a ratification is ceremony with a real cost and no benefit.
The specimen supplies the shape of that counterexample and measures it at exactly zero. What it
cannot supply is how common that shape is.

**A demonstration that provenance survives the trip.** The pattern rests on emitted numbers arriving
stripped of their origin. If an evaluation artefact can be shown to carry its weighting, its owner,
and its ratification state all the way to the decision — and to be read there — then warn-and-proceed
is sufficient and the refusal is over-engineering.

**A ratification record that is routinely rubber-stamped.** The control produces a named owner. If
the name is reliably supplied by whoever is least inconvenienced, the pattern has bought a signature
rather than a decision, and the failure it prevents has moved rather than gone.

## Reproducing

```bash
python3 probe.py            # about half a second
python3 probe.py --quick    # skip the monte-carlo cross-check
python3 test_scorecard.py   # 30 tests
python3 test_ratify.py      # 26 tests
```

No key, no network, no dependencies, no configuration. Every number above is computed in process;
the exact shares are closed-form and the Monte Carlo column is reproducible from its seed using
`random.random()` only, so it does not depend on the interpreter's `gammavariate` implementation.
