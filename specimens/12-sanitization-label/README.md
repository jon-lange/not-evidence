# Specimen 12 — four numbers are enough

Demonstrates [pattern 12 · Distrust the Sanitization Label](../../patterns/12-distrust-the-sanitization-label.md).

Sixty synthetic projects, twenty daily build durations each. A sanitiser substitutes every name and
shuffles every row — the operation the word *sanitised* denotes in practice. Then an adversary
holding a fragment of one project's series tries to find it again.

```
 k     exact  candidates      noisy      shape
 1     21.9%        2.48      20.8%       1.7%
 2     96.1%        1.04      36.3%      19.8%
 3     99.8%        1.00      58.8%      82.7%
 4    100.0%        1.00      82.0%      99.2%
 6    100.0%        1.00      99.0%     100.0%
```

**Four consecutive build durations pin one project in sixty, on every one of 1,020 trials.** Two
points do it 96% of the time. Chance is 1.7%.

Measured output across three adversaries and eight sanitiser configurations:
**[RESULTS.md](RESULTS.md)**.

## The finding

**The label is applied to the operation that was performed, and the operation removes the names.**
Cell 1 is the whole failure in one line: substitute every name, drop the owner, shuffle the rows, and
an exact join on the numbers recovers 60/60 of the pseudonym map. That is arithmetic rather than a
finding, and it is included because it is what actually ships.

The finding is **how little of the record is enough**. The `noisy` adversary above holds *no value
that appears anywhere in the release* — they measured the same builds themselves, a few percent off —
and still identifies the right project 82% of the time from four points. De-identifying a series is
not achieved by removing identifiers, because the identifier is the series.

**And the last thing anyone removes is the thing that works on its own.** A release whose values were
regenerated from scratch — not one real measurement left in the file — is still 100% re-identifiable
through a retained `derived from run cf694e (staging)` line. Sixty run ids, sixty rows, a 1:1 key,
orthogonal to every value-level defence in the specimen. It survives because it does not look like
data. It looks like diligence.

## What re-synthesis costs

The last table in `probe.py` is a price list, not a ranking of defences.

| Release | best attack | median kept |
|---|---|---|
| names substituted only | 100.0% | 100.0% |
| values rescaled ×1.37 | 99.2% | 0.0% |
| 25% jitter on every value | 12.8% | 91.7% |
| regenerated per project | 7.5% | 76.7% |
| regenerated from fleet model | 2.3% | 13.3% |

**Rescaling is the worst trade available.** It changes every number in the file, which is why it
feels like the strongest operation, and it costs all of the absolute utility while a shape-matching
adversary re-identifies 99.2% of fragments.

**Per-project regeneration is not de-identification.** Drawing fresh values from a model fitted to
each project — what *synthetic* usually means, and what pattern 12 itself recommends — leaves the
attack at 4.5× chance, because the model faithfully reproduces the magnitude and the magnitude is
most of the fingerprint.

**Nothing here both defeated the attack and kept the per-project signal.** Only pooling to a
fleet-level model reached chance, and it took 87% of the per-project medians with it.

## Run it

```bash
python3 probe.py            # about six seconds
python3 probe.py --quick    # coarser k grid
```

No network, no API key, no dependencies, no configuration. The corpus is generated in process from a
fixed seed, which is the only honest way to publish a re-identification result. Per-trial rows —
62,700 of them, carrying release, mode, k, entity, offset and outcome — are written to
`_generated/trials.jsonl` before any of the tables are computed.

## Tests

```bash
python3 test_sanitize.py      # 21 tests
python3 test_reidentify.py    # 29 tests
# or: python3 -m pytest -q
```

**Mutation-checked.** Twenty-seven deliberate breakages, all caught:

| Mutation | Tests failed |
|---|---|
| The answer key is the identity mapping | 14 |
| `naive_sanitize` perturbs the values | 8 |
| No row is ever a candidate | 5 |
| `nearest_row` always answers row 0 | 5 |
| Jitter is ignored | 4 |
| Every row is a candidate | 4 |
| The fragment is taken from the release, not the fleet | 4 |
| The index only holds the first window of each row | 3 |
| The fleet seed is ignored | 2 |
| `strip_provenance` is ignored | 2 |
| `quantum` is ignored | 2 |
| `scale` is ignored | 2 |
| The fleet model uses per-project parameters | 2 |
| Normalisation is a no-op | 2 |
| The noisy adversary's fragment is not perturbed | 2 |
| The last window of every series is dropped | 2 |
| No project has a slow day | 1 |
| `percentile` always returns the minimum | 1 |
| `relative_spread` reports zero | 1 |
| The release is not shuffled | 1 |
| `naive_sanitize` drops provenance | 1 |
| The config seed uses the salted builtin `hash()` | 1 |
| Any candidate at all counts as unique | 1 |
| The provenance join returns nothing | 1 |
| The adversary never matches the published resolution | 1 |
| Per-trial rows are never written | 1 |
| Projects no longer share magnitude tiers | 1 |

**The mutation check found a hole, and the hole was in the guard on the published numbers.** The last
row survived the first pass. `test_one_point_is_usually_not_enough` asserted `0 < rate < 0.5`, and a
tenfold increase in per-project spread moved the k=1 rate only from 21.9% to 34.7% — through the
assertion, while RESULTS.md went on quoting 21.9%. The test now pins a band.

That surfaced something worth keeping. **The headline is far less sensitive to the fleet's spread
than expected**: at ten times the per-project offset, k=2 does not move at all (96.1% → 96.7%). The
result is not balanced on the corpus tuning, which is the objection it most deserved.

## Where this is weaker than pattern 12 claims

The entry says a series is recognisable **"by shape"**. Separating shape from magnitude says
something the entry does not.

**Magnitude does nearly all the work.** The shape adversary — magnitude discarded by construction —
defeats an exact rescale completely (99.2%) and then collapses to 15.5% under 3% jitter, where the
adversary who kept magnitude is still at 68.3%. Pure shape matching is defeated by a perturbation an
order of magnitude smaller than what it takes to defeat magnitude matching.

That sharpens the pattern rather than overturning it: the reason a "sanitised" series is dangerous is
not mainly that its silhouette is recognisable to an operator, it is that the numbers are the right
size. But the phrasing invites a reader to picture curve-matching, and the leak is coarser and more
robust than that.

**And the entry's prescription is measurably insufficient.** *"Regenerate from a model of the shape"*
is the `regenerated per project` row, and it leaves the release at 4.5× chance.

## Scope

**One corpus, one domain, one adversary model, one day.** Sixty entities, twenty points, whole
seconds, twelve magnitude tiers. The tiers exist specifically so a single point is *not* uniquely
identifying — sixty obviously different projects would report 100% at k=1 and mean nothing.
**"Four points" is a measurement of this fleet, not a constant.**

**The result that would falsify the pattern** is a partial series that stays ambiguous: a fragment
worth a fifth of a record matching many entities rather than one, or a noisy adversary at chance. The
full list, with the observed value beside each, is in [RESULTS.md](RESULTS.md).

## What this specimen deliberately does not do

**The attack is nearest-neighbour over contiguous windows.** No alignment search, no time warping, no
use of the peak day as a landmark, no composition across two releases. A better attack exists and
would move every number the same direction, so these are lower bounds on what is recoverable.

**It cannot demonstrate cell 3's most important claim.** That provenance is *the last thing anyone
removes* is an assertion about people. What is measured is only that it is a live 1:1 join key when
retained, and that it is orthogonal to everything done to the values. How often real releases retain
it is not something a specimen can establish.

**It does not test the drift-plus-silence failure.** Pattern 12's naive approach — a sanitisation
script that passes an unrecognised field straight through — is a denylist problem, answered by
pattern 02, and it is not exercised here. Every sanitiser in this specimen knows every field.

**One sanitiser author, eight configurations.** The claim that nothing both defeats the attack and
preserves per-project utility is a statement about the four operations tried, not a search over
mechanisms. Someone will find a better point on that curve, and the trade-off table is where they
should aim.

---

Reference implementation. Not maintained.
