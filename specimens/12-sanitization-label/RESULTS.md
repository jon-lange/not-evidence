# Observed results

**Adjudication: narrowed.** The conclusion was not overturned and in one respect was sharpened — 60
of 60 rows re-linked from the numbers alone. Two things in the entry required correction: the *"by
shape"* phrasing, since magnitude does nearly all the work and pure shape matching is the brittle
attack; and the prescription to regenerate from a model of the shape, which measurably leaves the
release re-identifiable.

**Run 2026-08-05, one machine, no network.** Sixty synthetic projects, twenty daily build durations
each, in whole seconds, generated in process from a fixed seed. Median build 285 s across the fleet,
twelve magnitude tiers, five projects per tier. Nothing here was derived from a real system, and the
whole run takes about six seconds.

Every trial is written to `_generated/trials.jsonl` **before** any of these tables are computed —
62,700 rows carrying release, mode, fragment length, entity, offset, candidate count and outcome.
The tables are aggregates of that file, not the record of the experiment.

## Cell 1 — the names changed and the numbers did not

The sanitiser substitutes every project name, drops the owner field, and shuffles the row order. It
is real work and it is honestly described.

| Join | Result |
|---|---|
| exact full-series match, original → published | **60 / 60 rows re-linked, 0 wrong** |

The row order is shuffled, so this is not a positional join. It is a dictionary lookup on numbers
that nobody classified as identifying, and it recovers the entire pseudonym map.

## Cell 2 — the series is the fingerprint

Each adversary holds *k* consecutive points of one project and must pick that project out of sixty.
Chance is 1.7%. Fragments always come from the internal fleet, never from the release, so a sanitiser
that moves the values is entitled to defeat them.

- **exact** — holds the counterpart values verbatim; matches by exact contiguous subsequence
- **noisy** — measured the same builds independently, every point off by up to 3%; nearest window by
  mean absolute difference
- **shape** — holds original-unit values while every published value was secretly multiplied by 1.37;
  matches on mean-normalised windows, so magnitude is discarded entirely

| k | exact | mean candidates | noisy | shape (vs ×1.37 release) |
|---|---|---|---|---|
| 1 | 21.9% | 2.48 | 20.8% | 1.7% |
| 2 | 96.1% | 1.04 | 36.3% | 19.8% |
| 3 | 99.8% | 1.00 | 58.8% | 82.7% |
| 4 | **100.0%** | 1.00 | 82.0% | 99.2% |
| 5 | 100.0% | 1.00 | 93.2% | 100.0% |
| 6 | 100.0% | 1.00 | 99.0% | 100.0% |
| 8 | 100.0% | 1.00 | 99.8% | 100.0% |
| 10 | 100.0% | 1.00 | 100.0% | 100.0% |

**Four consecutive build durations out of a twenty-point series pin one project in sixty, on every
one of 1,020 trials.** Two points already do it 96% of the time. One point — a single build
duration, the smallest unit of this dataset there is — is uniquely identifying 22% of the time, and
narrows sixty projects to an average of 2.5.

The noisy row is the one that generalises. That adversary holds **no value that appears anywhere in
the release** and still reaches 82% at four points and 99% at six.

### Coarsening

The pattern's own mitigation is *round coarsely enough that a join fails*. Measured against an
adversary who rounds their own fragment to the published resolution, because the resolution is
visible in the file:

| k | 1 s | 10 s | 60 s | 300 s |
|---|---|---|---|---|
| 1 | 21.9% | 1.4% | 0.2% | 0.0% |
| 2 | 96.1% | 31.1% | 2.7% | 0.0% |
| 3 | 99.8% | 67.1% | 7.6% | 0.0% |
| 4 | 100.0% | 86.1% | 16.9% | 0.4% |
| 5 | 100.0% | 93.4% | 30.7% | 2.0% |
| 6 | 100.0% | 96.4% | 46.6% | 4.4% |
| 8 | 100.0% | 99.5% | 62.1% | 7.3% |
| 10 | 100.0% | 100.0% | 69.7% | 10.2% |

Coarsening works, and it has to go much further than it feels like it should. Rounding build times
**to the nearest minute** — which reads as a drastic loss of resolution — still re-identifies 70% of
ten-point fragments. Five-minute buckets are the first column that looks like a defence, and by then
the dataset can no longer distinguish a 90-second build from a 300-second one.

## Cell 3 — provenance strings are the join key

Retained line: `derived from run cf694e (staging)`.

| Property | Value |
|---|---|
| distinct run ids | 60 in 60 rows — a 1:1 key |
| key shape | six lowercase hex characters, inferable from the release alone |
| environments named | canary, preprod, staging |

| Release | values re-link | provenance re-link |
|---|---|---|
| names substituted only | 60/60 | 60/60 |
| + values rescaled ×1.37 | 0/60 | 60/60 |
| + 3% jitter on every value | 0/60 | 60/60 |
| + 25% jitter on every value | 0/60 | 60/60 |
| + rounded to 60 s | 0/60 | 60/60 |
| regenerated per project | 0/60 | 60/60 |
| regenerated from fleet model | 0/60 | 60/60 |
| regenerated + provenance stripped | 0/60 | **0/60** |

**Row seven is the result.** Every value in that release was drawn fresh from a pooled statistical
model. Not one number in the file is a measurement of anything. The release is still 100%
re-identifiable, by a string that survived because it looked like diligence rather than like data.

## What re-synthesis actually requires

k = 4 points, chance 1.7%. The last column is the price: share of projects whose published median is
still within 10% of the internal one.

| Release | exact | noisy | shape | prov | p50 | p95 | median kept |
|---|---|---|---|---|---|---|---|
| names substituted only | 100.0% | 82.0% | 100.0% | 60/60 | 285 | 662 | 100.0% |
| + values rescaled ×1.37 | 0.0% | 1.7% | **99.2%** | 60/60 | 390 | 907 | **0.0%** |
| + 3% jitter on every value | 0.0% | 68.3% | 15.5% | 60/60 | 286 | 666 | 100.0% |
| + 25% jitter on every value | 0.0% | 12.8% | 2.2% | 60/60 | 289 | 703 | 91.7% |
| + rounded to 60 s | 18.3% | 35.2% | 31.7% | 60/60 | 300 | 660 | 81.7% |
| regenerated per project | 0.0% | **7.5%** | 1.8% | 60/60 | 275 | 714 | 76.7% |
| regenerated from fleet model | 0.0% | 0.5% | 2.3% | 60/60 | 278 | 622 | 13.3% |
| regenerated + provenance stripped | 0.0% | 2.0% | 1.3% | **0/60** | 292 | 612 | 13.3% |
| *(internal original)* | | | | | 285 | 662 | 100.0% |

Three things in that table are worth more than the headline.

**1. Rescaling is the worst trade in the file.** Multiplying every value by an undisclosed constant
changes every number in the artefact, which is why it feels like the strongest operation available.
It costs 100% of the absolute utility — no published median is within 10% of the truth any more —
and buys nothing: the shape adversary re-identifies 99.2% of fragments.

**2. Per-project regeneration is not de-identification.** Drawing fresh values from a model fitted to
each project — which is what *synthetic* usually means in practice, and what pattern 12 itself
recommends — leaves re-identification at 7.5%, **four and a half times chance**, because the model
faithfully reproduces the magnitude, and the magnitude is most of the fingerprint.

**3. Only pooling reached chance, and it took the dataset with it.** The fleet-level model is the one
row where the attack fails outright (0.5%, below the 1.7% baseline), and it is also the row where
only 13% of per-project medians survive. Nothing in this experiment both defeated the attack and
preserved the per-project signal the release existed to carry.

*(The exact column for the 60 s release reads 18.3% here and 16.9% in the coarsening table. The
coarsening table uses every window offset; this table samples ten per project so the three modes in
each row are scored on identical trials.)*

## What this measured that the pattern got wrong

Pattern 12 says a series is recognisable **"by shape"** and lists unit, interval, magnitudes and the
shape of its peaks together. Separating them says something the entry does not.

**Magnitude does nearly all the work, and shape alone is the brittle attack.** The shape adversary —
magnitude discarded by construction — defeats an exact rescale completely (99.2%) and then collapses
to 15.5% under 3% jitter, where the adversary who kept magnitude is still at 68.3%. Pure shape
matching is defeated by perturbation an order of magnitude smaller than what it takes to defeat
magnitude matching.

That does not overturn the pattern's conclusion, and in one respect it sharpens it: the reason a
"sanitised" series is dangerous is *not* mainly that its silhouette is recognisable to someone who
operates the system. It is that the numbers are the right size. But the entry's phrasing invites a
reader to picture pattern-matching on a curve, and the measurement says the leak is coarser and more
robust than that.

**And the pattern's prescription is measurably insufficient.** *"Regenerate from a model of the
shape"* is exactly the operation in the `regenerated per project` row, and it leaves the release at
4.5× chance. The entry should say *pooled* model, and should say what pooling costs.

## What would falsify pattern 12

Any of the following, measured on a corpus generated the way this one was:

1. **A naive release that does not re-link.** If substituting names and shuffling rows left the
   published records un-joinable to their originals by exact numeric match, cell 1 is wrong. Observed:
   60/60.
2. **A partial series that stays ambiguous.** If a fragment amounting to a fifth of a series matched
   many entities rather than one — say, uniqueness below 50% at k = 4 in a fleet of sixty — the claim
   that a series is a fingerprint is unsupported. Observed: 100% at k = 4, 96% at k = 2.
3. **A noisy adversary at chance.** If holding an *independently measured* fragment gave no advantage
   — that is, if only verbatim values re-linked — then cell 2 would be a statement about exact
   duplicates rather than about series, and the pattern's second section would be a tautology dressed
   as a finding. Observed: 82% at k = 4, holding no value present in the release.
4. **Provenance that is not a key.** If retained provenance strings were categorical rather than
   1:1 — an environment name shared by hundreds of rows — cell 3 is a much weaker claim. Observed:
   60 distinct run ids in 60 rows, re-linking a fully regenerated release at 100%.
5. **A configuration that defeated the attack while preserving per-project utility.** This is the one
   that would most change the advice, because it would mean the trade-off in the last table is an
   artefact of the four sanitisers tried rather than a real cost. Not observed here — but four
   sanitisers is not a search, and this is the falsification I would most expect someone to deliver.

## What the mutation check found

Twenty-seven deliberate breakages across all four modules; the table is in
[README.md](README.md). Twenty-six were caught on the first pass. The survivor was
`PROJECT_OFFSET = 0.06 → 0.60` — a tenfold increase in how far projects sit from their magnitude
tier, which is the single parameter every number on this page depends on.

`test_one_point_is_usually_not_enough` asserted `0 < rate < 0.5` and let it through. The suite would
have accepted a materially different fleet while this file went on quoting 21.9%. The test now pins a
band, and the mutation is caught.

The sensitivity table in **Scope** below exists because of that survivor. It is the more useful
outcome: the reason the mutation survived is that the result genuinely is robust to fleet spread at
k ≥ 2, which is a stronger claim than the one the test was written to defend.

## Reproducing

```bash
python3 probe.py             # about six seconds; writes _generated/trials.jsonl
python3 probe.py --quick     # coarser k grid
python3 test_sanitize.py
python3 test_reidentify.py   # or: python3 -m pytest -q
```

No network, no key, no dependencies, no configuration.

## Scope

**One corpus, one domain, one adversary model, one day.** Sixty entities, twenty points each, whole
seconds, twelve magnitude tiers. Every number above is a function of how much entropy that fleet has,
and the fleet was designed by hand — the tiers exist specifically so that a single point is *not*
uniquely identifying, because a fleet of sixty obviously different projects would report 100% at
k = 1 and mean nothing. **"Four points" is a measurement of this fleet, not a constant.** A denser
fleet needs more; a sparser one needs fewer.

That said, the sensitivity was measured rather than assumed, because the mutation check forced the
question. Varying the per-project spread over a thirtyfold range:

| per-project spread | shared values | k = 1 | mean candidates at k = 1 | k = 2 |
|---|---|---|---|---|
| ±6% *(as published)* | 278 | 21.9% | 2.48 | 96.1% |
| ±20% | 266 | 26.6% | 2.36 | 96.8% |
| ±60% | 255 | 34.7% | 2.00 | 96.7% |
| ±200% | 172 | 53.7% | 1.68 | 96.5% |

**k = 2 does not move.** Spreading the fleet out by a factor of thirty changes single-point
uniqueness a great deal and two-point uniqueness not at all. The headline is not balanced on the
corpus tuning, which is the objection it most deserved.

**The attack is nearest-neighbour matching over contiguous windows.** No alignment search, no
dynamic time warping, no exploitation of the peak day as a landmark, no cross-artefact composition.
A better attack exists and would move every number in the same direction, so these are lower bounds
on what is recoverable, not estimates of it.

**Cell 3 cannot demonstrate its own most important claim.** That provenance is *the last thing anyone
removes* is an assertion about human behaviour. What is measured here is only that provenance is a
live 1:1 join key if it is retained, and that it is orthogonal to every value-level defence. The
frequency with which real releases retain it is not something this specimen can establish, and no
number here should be read as if it were.

**Cell 1 is close to a tautology and is included anyway.** Identical numbers match identical numbers;
that is arithmetic, not a finding. It earns its place because it is the operation that actually
happens, and because the interesting question it raises — *how little of the record is enough* — is
what cell 2 answers.
