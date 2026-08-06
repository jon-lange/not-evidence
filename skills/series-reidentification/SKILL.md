---
name: series-reidentification
description: Test whether a "sanitised" dataset re-identifies before it is published. Use when an artefact marked sanitised, anonymised, or synthetic is about to cross a boundary it was not produced inside — a reproduction attached to a vendor ticket, a dataset released with a paper, a fixture committed to a public repo — or when reviewing a release whose de-identification someone else performed. Also use when the only evidence a file is safe is the word in its header.
pattern: 12
status: field-tested
---

# Series re-identification

The label is a description of the operation that was performed. **It is not a measurement of what
survived it.** Somebody substituted the names, saw the names change, and wrote *sanitised* — an
honest account of an incomplete job, which is the hardest kind of wrong claim to catch.

Downstream, that word is the entire review. Nobody re-derives it. So derive it yourself: run the
attack against the file you are about to publish, and report a number instead of a word.

## When to run this

Any artefact leaving the boundary it was produced inside, where the values are measurements of
something real. Also:

- Anything described as *synthetic* that you did not watch being generated
- Any release you are told is safe because the identifying columns were dropped
- A second release from the same source — two artefacts each harmless alone are not harmless together
- Any reproduction handed to a vendor mid-incident, which is when the review is most likely waived

**This class has no later commit.** Forks, mirrors, archives and caches turn removal from an
operation into a request addressed to people you cannot enumerate.

## The procedure

**1. Read the rows, not the schema.** The dominant failure is that entity *names* were substituted
while every *number* survived verbatim — find-and-replace over names has an obvious target and an
obvious stopping point, and the values *are* the payload, so altering them feels like corrupting the
evidence you meant to share. Row count and column list will not show you this. The rows will.

**2. Run the matching attack yourself.** Hold out a short fragment of one entity's series from your
internal copy, and try to find it in the release. Report **the smallest k at which one fragment pins
one row, and the right one.** That number is the finding. A word is not.

**3. Grep for provenance.** Source run ids, trace identifiers, environment names, job numbers,
`derived from X` header lines. These are live pointers into internal systems, and they survive
because they do not look like data — they look like diligence, so the reviewing eye reads them as
evidence of care rather than as content.

**4. Only then decide whether re-synthesis is sufficient.** Use the price list below. Decide against
measured re-identification and measured utility loss, not against how thorough an operation felt.

```python
# The whole attack. Not a framework.
def reidentify(fragment, release, k):
    """Hold k points of one entity. Find its row in the 'sanitised' release."""
    windows = [(row, rec[o : o + k])                     # every contiguous k-window
               for row, rec in enumerate(release)
               for o in range(len(rec) - k + 1)]

    hits = {row for row, w in windows if w == tuple(fragment)}
    if hits:                                             # values survived verbatim
        return hits                                      # len(hits) == 1 is the failure

    l1 = lambda a, b: sum(abs(x - y) for x, y in zip(a, b))
    return {min(windows, key=lambda rw: l1(fragment, rw[1]))[0]}   # nearest window
```

**The fragment must come from your internal copy, never from the release.** Drawing it from the
published file measures a self-join, and a sanitiser that moved the values would score as broken when
it worked. Sweep k upward until the answer is one right row; compare against chance, which is 1/rows.

Runnable reference implementation:
[`../../specimens/12-sanitization-label/`](../../specimens/12-sanitization-label/).

## What the measurement says

Specimen 12: sixty synthetic projects, twenty daily build durations each, 62,700 trials, offline in
six seconds. Chance is 1.7%. Three adversaries — **exact** holds the values verbatim; **noisy**
measured the same builds independently, off by up to 3% on every point; **shape** discards magnitude
and matches mean-normalised windows.

| k | exact | mean candidates | noisy | shape |
|---|---|---|---|---|
| 1 | 21.9% | 2.48 | 20.8% | 1.7% |
| 2 | **96.1%** | 1.04 | 36.3% | 19.8% |
| 4 | **100.0%** | 1.00 | **82.0%** | 99.2% |
| 6 | 100.0% | 1.00 | 99.0% | 100.0% |

**Four consecutive values pin one project in sixty on every one of 1,020 trials.** Two do it 96% of
the time. The row that generalises is `noisy`: that adversary holds **no value present anywhere in
the release** and is still right 82% of the time from four points.

Names-substituted-only re-links **60/60 rows, zero wrong**, on an exact join over the full series —
after every name was replaced and every row shuffled.

Coarsening has to go much further than it feels like it should. Against an adversary who rounds their
own fragment to the published resolution — visible in the file — ten-point fragments still
re-identify **69.7% at 60-second buckets**. 300-second buckets are the first real defence at 10.2%,
and by then the data cannot distinguish a 90-second build from a 300-second one.

## What each defence costs

k = 4, chance 1.7%. *median kept* is the share of entities whose published median is still within 10%
of the internal one — the utility the release existed to carry.

| Release | exact | noisy | shape | provenance | median kept |
|---|---|---|---|---|---|
| names substituted only | 100.0% | 82.0% | 100.0% | 60/60 | 100.0% |
| + rescaled ×1.37 | 0.0% | 1.7% | **99.2%** | 60/60 | **0.0%** |
| + 3% jitter | 0.0% | 68.3% | 15.5% | 60/60 | 100.0% |
| + 25% jitter | 0.0% | 12.8% | 2.2% | 60/60 | 91.7% |
| + rounded to 60 s | 18.3% | 35.2% | 31.7% | 60/60 | 81.7% |
| regenerated per project | 0.0% | **7.5%** | 1.8% | 60/60 | 76.7% |
| regenerated from pooled model | 0.0% | 0.5% | 2.3% | 60/60 | **13.3%** |
| pooled + provenance stripped | 0.0% | 2.0% | 1.3% | **0/60** | 13.3% |

**Rescaling by an undisclosed constant is the worst trade in the table.** It changes every number in
the file, which is why it feels strongest, and it buys nothing: shape matching recovers 99.2% while
no published median survives.

**Provenance re-links 60/60 on seven of the eight releases — including the one where every value was
regenerated and not a single number is a measurement of anything.** It is orthogonal to every
value-level defence, and dropping it is one boolean at no cost.

## Honest limits

**"Recognisable by shape" overstates it.** Separating shape from magnitude shows **magnitude doing
nearly all the work**. Shape-only matching collapses to 15.5% under 3% jitter, where the adversary
who kept magnitude is still at 68.3% — pure shape is defeated by a perturbation an order of magnitude
smaller. The leak is coarser and more robust than curve-matching: the numbers are the right size.

**Pattern 12's own prescription is insufficient.** *"Regenerate from a model of the shape"* is the
`regenerated per project` row, and it lands at **4.5× chance**, because a per-entity model faithfully
reproduces that entity's magnitude. Only a **pooled** model reached baseline.

**Nothing tested both defeated the attack and kept utility.** The pooled-model release is the one row
where the attack fails outright, and it is the row where only 13.3% of per-entity medians survive.
The trade-off is real in this experiment; four sanitisers is not a search, and a better point on that
curve is the result that would most change this advice.

**"The last thing anyone removes" is a claim about people, and this evidence cannot establish it.**
What is measured is only that retained provenance is a live 1:1 join key, orthogonal to every defence
applied to the values. How often real releases retain it is not something a specimen can show.

**The sanitisers were constructed, not found.** They are written to be the operation the word
*sanitised* denotes, but no release in the wild was sampled, so retention frequency is unmeasured.

**"Four points" is a measurement of that fleet, not a constant.** Sixty entities, twenty points,
twelve magnitude tiers. A denser fleet needs more; a sparser one needs fewer. Run it on yours.

**The attack is nearest-neighbour over contiguous windows** — no alignment search, no time warping,
no landmark exploitation, no composition across releases. Every number above is a lower bound.

## Prior art

- Narayanan & Shmatikov, *How To Break Anonymity of the Netflix Prize Dataset* —
  [arXiv:cs/0610105](https://arxiv.org/abs/cs/0610105)
- de Montjoye, Hidalgo, Verleysen & Blondel, *Unique in the Crowd: The privacy bounds of human
  mobility* — *Scientific Reports*, 2013, [doi:10.1038/srep01376](https://doi.org/10.1038/srep01376)
- Ganta, Kasiviswanathan & Smith, *Composition Attacks and Auxiliary Information in Data Privacy* —
  [arXiv:0803.0032](https://arxiv.org/abs/0803.0032)
- Garfinkel et al., NIST SP 800-188, *De-Identifying Government Datasets: Techniques and Governance*
  — September 2023
