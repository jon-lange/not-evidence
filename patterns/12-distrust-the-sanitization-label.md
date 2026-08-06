---
pattern: 12
name: "Distrust the Sanitization Label"
status: field-tested   # draft | field-tested | superseded-by: NN
refuses: "to publish on someone's assurance that it was scrubbed"
specimen: 12-sanitization-label
---

# 12 · Distrust the Sanitization Label

> **Refuses to publish on someone's assurance that it was scrubbed.**

## Context

Something is about to cross a boundary it was not produced inside: a reproduction attached to a
vendor ticket, a dataset released with a paper, a fixture in an open repository.

It did not start life public. Somebody derived it from something real and marked the result
*sanitised*, *anonymised*, or *synthetic*. That word is now the only thing between the original and
everyone — a word, not a check.

## Forces

**Substitution is the obvious operation and most of the visible work.** Names, hostnames, email
addresses — what "identifying" means colloquially, verifiable at a glance.

**The label is applied in good faith** — an honest description of an incomplete operation, the
hardest kind of wrong claim to catch.

**Downstream, the label is the entire review.** Every later reader treats it as a completed check by
someone with more context; nobody re-derives it.

**Verification looks like distrust,** and reading a colleague's file line by line is slow and
low-status in a way skimming the header is not.

## The Refusal

**Never publish on someone else's assurance that an artefact was scrubbed. Read the records yourself,
and treat the label as a claim under review, not a review already performed.**

*Read the records* is literal: look at rows, not the schema. The failure is obvious on inspection and
invisible from metadata. Three things to check:

### The names changed and the numbers did not

**The dominant real-world failure is that entity names were substituted while every number survived
verbatim.** Find-and-replace over names has an obvious stopping point; the values *are* the payload,
and altering them feels like corrupting the evidence. What ships is authentic measurements in
placeholder names, now labelled safe.

### De-identifying a series is not achieved by removing identifiers

A series is a fingerprint: its unit, window, magnitudes and peak shape are matchable by anyone holding
the counterpart. Renaming removes the label from the fingerprint and publishes it.

Sixty projects, twenty daily build durations each, names substituted and rows shuffled: **four
consecutive values identify one project in sixty on every trial, and two do it 96% of the time.** An
adversary holding no value from the release, who measured the same builds to within a few percent, is
right 82% of the time from four points against a 1.7% baseline. The power is in the **magnitudes**,
not the silhouette.

**Real re-synthesis means perturbing every value.** A model fitted to *each entity* reproduces the
magnitude faithfully and leaves re-identification at 4.5× chance; only a **pooled** model reached the
baseline, destroying 87% of the per-entity signal. Coarsening must go as far — rounding to the nearest
minute still re-identifies 70% of ten-point fragments. *Synthetic* is a claim about how values were
produced.

### Provenance strings are themselves leaks

Sanitised artefacts retain the note that made them auditable: a trace identifier, an environment name,
a *derived from run X* header. **Provenance is a quality practice, which is exactly why it is the last
thing anyone thinks to remove:** it looks like diligence, not data.

It is content — in the specimen, the *only* leak that survives regenerating every value. A trace
identifier asserts that a system exists and what its keys look like; environment and job names leak
topology. Strip it at the boundary.

## Consequences

**You will find something in the first artefact you check,** and you become a bottleneck — slow,
because the alternative is irreversible.

**"We'll clean it later" is not available for this class.** Forks, mirrors, archives and caches turn
removal into a request to people you cannot enumerate. Every other problem in this catalogue
can be fixed by a later commit; this one is a one-way door, and the cost lands exactly when it feels
cheapest to skip, mid-incident.

## The naive approach it beats

**A sanitisation script, written once, trusted thereafter.** Repeatable, diffable, in version control,
better than manual redaction — and it works for the fields it was written against.

It fails by **drift plus silence**. A new field appears upstream; the script does not recognise it and
passes it through untouched; a pass-through emits no signal. The artefact is produced and the
label applied; its silence on failure is identical to its silence on success — pattern 11 in other
clothes.

The correction is pattern 02's: an **allowlist**, so an unrecognised field fails closed. That fixes
the schema but never touches the values, so the reading step remains — as it does for a redaction
classifier, which finds only the patterns it has. A column of measurements matches none.

## Prior art

- Narayanan & Shmatikov, *How To Break Anonymity of the Netflix Prize Dataset* —
  [arXiv:cs/0610105](https://arxiv.org/abs/cs/0610105). Removing identifiers from sparse records does
  not de-identify them
- de Montjoye, Hidalgo, Verleysen & Blondel, *Unique in the Crowd: The privacy bounds of human
  mobility* — *Scientific Reports*, 2013. A handful of points in a series is enough
- Ganta, Kasiviswanathan & Smith, *Composition Attacks and Auxiliary Information in Data Privacy* —
  [arXiv:0803.0032](https://arxiv.org/abs/0803.0032)
- NIST SP 800-188, *De-Identifying Government Datasets: Techniques and Governance* (2023), and
  GitHub Docs, *Removing sensitive data from a repository* — de-identification as a governed process;
  pushed data persists in forks and caches

## Specimen

[`specimens/12-sanitization-label/`](../specimens/12-sanitization-label/) — **built.** Runs offline on
the standard library, in about six seconds.

Sixty synthetic projects, twenty daily build durations each, sanitised eight ways and attacked by
three adversaries. Names substituted and rows shuffled re-links 60/60 on an exact numeric join. A
release whose values were regenerated from scratch — not one real measurement left in the file — is
still 100% re-identifiable through a retained `derived from run cf694e (staging)` line.

What no specimen demonstrates is the part that actually erodes: the willingness to open the file.
