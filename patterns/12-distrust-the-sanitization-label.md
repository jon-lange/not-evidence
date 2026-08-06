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
vendor ticket, a dataset released with a paper, a fixture committed to an open repository.

The artefact did not start life public. Somebody derived it from something real, ran a pass over it,
and marked the result *sanitised*, *anonymised*, or *synthetic*. That word is now the only thing
between the original and everyone. It is a word, not a check.

## Forces

**Substitution is the obvious operation and most of the visible work.** Names, hostnames, email
addresses — that is what "identifying" means colloquially, and replacing them is verifiable at a
glance.

**The label is applied in good faith** — an honest description of an incomplete operation, which is
the hardest kind of wrong claim to catch.

**Downstream, the label is the entire review.** Every later reader treats it as a completed check by
someone with more context than they have. Nobody re-derives it, which is what makes it load-bearing.

**Verification looks like distrust,** and reading a colleague's file line by line is slow and
low-status in a way that skimming the header is not.

## The Refusal

**Never publish on someone else's assurance that an artefact was scrubbed. Read the records
yourself, and treat the label as a claim under review rather than a review already performed.**

*Read the records* is literal: open the file and look at rows, not the schema, not the row count.
This failure is almost always obvious on inspection and almost never visible from metadata. Three
things to check, in order of how often they are wrong.

### The names changed and the numbers did not

**The dominant real-world failure is that entity names were substituted while every number survived
verbatim.** The reason is structural, not careless: find-and-replace over names has an obvious target
and an obvious stopping point, while the values *are* the payload, and altering them feels like
corrupting the evidence you were trying to share. What ships is a body of entirely authentic
measurements wearing placeholder names — more dangerous than the raw original, because it now carries
a label saying it is safe.

### De-identifying a series is not achieved by removing identifiers

A series is a fingerprint. Its unit, window, sampling interval, magnitudes and the shape of its peaks
are conclusively matchable by anyone holding the counterpart. Renaming the series perturbs none of
it. It removes the label from the fingerprint and publishes the fingerprint.

The specimen measures how little is enough. Sixty projects, twenty daily build durations each, names
substituted and rows shuffled: **four consecutive values identify one project in sixty on every
trial, and two do it 96% of the time.** An adversary holding no value present in the release at all,
having measured the same builds themselves to within a few percent, is right 82% of the time from
four points against a 1.7% baseline. The power is mostly in the **magnitudes**, not the silhouette.

*Anonymised* obscures this by implying the identifying content lived in the identifiers. It lived in
the values — two releases, each harmless alone, that are not harmless together.

**Real re-synthesis means perturbing every value,** further than feels necessary. A model fitted to
*each entity* is not enough: it reproduces the magnitude faithfully and left re-identification at
4.5× chance. Only a **pooled** model reached the baseline, and it destroyed 87% of the per-entity
signal doing it. Coarsening has to go equally far — rounding to the nearest minute still re-identifies
70% of ten-point fragments. *Synthetic* is a claim about how values were produced. If they were not
produced, they are not synthetic, whatever the header says.

### Provenance strings are themselves leaks

Sanitised artefacts routinely retain the note that made them auditable: a source trace identifier, an
environment name, a run number, a *derived from run X* line in a header.

These survive for a reason. **Provenance is a quality practice, which is exactly why it is the last
thing anyone thinks to remove.** It does not look like data. It looks like diligence, so the
reviewer's eye passes over it as evidence of care rather than as content.

It is content, and in the specimen it is the *only* leak that survives regenerating every value.
A trace identifier asserts that a system exists and what its keys look like; environment and job
names leak topology and naming conventions. Strip provenance at the publication boundary and keep it
on the internal copy, where it was always more useful anyway.

## Consequences

**You will find something in the first artefact you check,** and you become a bottleneck on outbound
artefacts. The review is slow because the alternative is irreversible.

**"We'll clean it later" is not available for this class.** Forks, mirrors, archives and caches turn
removal from an operation into a request addressed to people you cannot enumerate. Every other
problem in this catalogue can be fixed by a later commit. This one is a one-way door, and the
response to a one-way door is to slow down at that door specifically — which costs you speed exactly
when it feels cheapest to keep, because handing a reproduction to a vendor mid-incident is when the
review is most likely to be waived.

## The naive approach it beats

**A sanitisation script, written once, trusted thereafter.** The right instinct: repeatable,
diffable, in version control, better than manual redaction on every axis people usually compare. It
works — for the fields it was written against.

It fails by **drift plus silence**. A new field appears upstream; the script does not recognise it,
does not transform it, passes it through untouched — and a pass-through emits no signal. The script
exits zero, the artefact is produced, the label is applied. Its silence on failure is identical to
its silence on success, which is pattern 11 wearing different clothes.

The correction is pattern 02's: an **allowlist**, so an unrecognised field fails closed. That fixes
the schema problem and never touches the values, so the reading step remains — as it does for a
redaction classifier, which finds the patterns it has patterns for. A column of measurements matches
none, and matching none is exactly what it reports.

## Prior art

- Narayanan & Shmatikov, *How To Break Anonymity of the Netflix Prize Dataset* —
  [arXiv:cs/0610105](https://arxiv.org/abs/cs/0610105). Removing identifiers from sparse records does
  not de-identify them
- de Montjoye, Hidalgo, Verleysen & Blondel, *Unique in the Crowd: The privacy bounds of human
  mobility* — *Scientific Reports*, 2013. A handful of points in a series is enough
- Ganta, Kasiviswanathan & Smith, *Composition Attacks and Auxiliary Information in Data Privacy* —
  [arXiv:0803.0032](https://arxiv.org/abs/0803.0032)
- NIST SP 800-188, *De-Identifying Government Datasets: Techniques and Governance* (2023), and
  GitHub Docs, *Removing sensitive data from a repository* — de-identification as a governed process,
  and the vendor's own statement that pushed data persists in forks and caches

## Specimen

[`specimens/12-sanitization-label/`](../specimens/12-sanitization-label/) — **built.** Runs offline on
the standard library alone, in about six seconds.

Sixty synthetic projects, twenty daily build durations each, sanitised eight ways and attacked by
three adversaries. Names substituted and rows shuffled re-links 60/60 on an exact numeric join. A
release whose values were regenerated from scratch — not one real measurement left in the file — is
still 100% re-identifiable through a retained `derived from run cf694e (staging)` line.

**It corrected this entry twice.** *"Regenerate from a model of the shape"* stood unqualified; a
per-entity model measures at 4.5× chance, so the section above now says *pooled* and names the cost.
And *"recognisable by shape"* overstated the silhouette — separating shape from magnitude showed
magnitude doing nearly all the work.

What no specimen demonstrates is the part that actually erodes: the willingness to open the file.
