---
pattern: 12
name: "Distrust the Sanitization Label"
status: draft          # draft | field-tested | superseded-by: NN
refuses: "to publish on someone's assurance that it was scrubbed"
specimen: none
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
addresses — that is what "identifying" means colloquially, and replacing them is mechanical and
verifiable at a glance.

**The label is applied in good faith.** Whoever wrote it did the part they knew about and reported
it accurately. It is an honest description of an incomplete operation, which is the hardest kind of
wrong claim to catch.

**Downstream, the label is the entire review.** Every later reader treats it as a completed check by
someone with more context than they have. Nobody re-derives it, which is what makes it load-bearing.

**Verification looks like distrust,** and reading a colleague's file line by line is slow and
low-status in a way that skimming the header is not.

## The Refusal

**Never publish on someone else's assurance that an artefact was scrubbed. Read the records
yourself, and treat the label as a claim under review rather than a review already performed.**

*Read the records* is literal: open the file and look at rows, not the schema, not the row count.
This failure is almost always obvious on inspection and almost never visible from the metadata.
Three things to check, ordered by how often they are wrong.

### The names changed and the numbers did not

**The dominant real-world failure is that entity names were substituted while every number survived
verbatim.** The reason is structural, not careless: find-and-replace over names has an obvious target
and an obvious stopping point, while the values *are* the payload, and altering them feels like
corrupting the evidence you were trying to share.

What ships is a body of entirely authentic measurements wearing plausible placeholder names — more
dangerous than the raw original, because it now carries a label saying it is safe.

### De-identifying a series is not achieved by removing identifiers

A series is a fingerprint. Its unit, window, sampling interval, magnitudes, the shape of its peaks,
the exact points where it goes flat: that combination is recognisable to anyone who operates the
system it came from, and conclusively matchable by anyone holding the counterpart series. Renaming
it perturbs none of that. It removes the label from the fingerprint and publishes the fingerprint.

The word *anonymised* obscures this by implying the identifying content lived in the identifiers. It
lived in the values, and it becomes identifying the moment someone joins them against a counterpart
they already hold — two releases, each harmless alone, that are not harmless together.

**Real re-synthesis means perturbing every value** — regenerate the series from a model of its shape,
add noise calibrated against the precision the reader genuinely needs, or round to a granularity
coarse enough that a join fails. *Synthetic* is a claim about how values were produced. If they were
not produced, they are not synthetic, whatever the header says.

### Provenance strings are themselves leaks

Sanitised artefacts routinely retain the note that made them auditable: a source trace identifier, an
environment name, a job or run number, a path, a *derived from run X* line in a header.

These survive for a specific reason. **Provenance is a quality practice, which is exactly why it is
the last thing anyone thinks to remove.** It does not look like data — it looks like diligence, so
the reviewer's eye passes over it as evidence of care rather than as content.

It is content. A trace identifier asserts that a particular system exists and what its keys look
like; environment, queue, and job names leak topology and naming conventions. Strip provenance at
the publication boundary and keep it on the internal copy, where it was always more useful anyway.

## Consequences

**You will find something in the first artefact you check.** That is not a prediction about a
particular team; it is what this failure class being structural means.

**You become a bottleneck on outbound artefacts,** and the honest framing of that is that the review
is slow because the alternative is irreversible.

**"We'll clean it later" is not available for this class.** Forks, mirrors, archives, caches,
scrapes, and screenshots turn removal from an operation into a request addressed to people you
cannot enumerate. Every other quality problem in this catalogue can be fixed by a later commit. This
one is a one-way door, and the response to a one-way door is to slow down at that specific door.

**You give up speed exactly when it feels cheapest to keep** — handing a reproduction to a vendor
mid-incident is when the review is most likely to be waived and most expensive to have waived.

## The naive approach it beats

**A sanitisation script, written once, trusted thereafter.** It is the right instinct: repeatable,
reviewable, diffable, in version control, and better than manual redaction on every axis people
usually compare. It works — for the fields it was written against.

It fails by **drift plus silence**. A new field appears upstream; the script does not recognise it,
does not transform it, and passes it through untouched. A pass-through emits no signal. The script
exits zero, the artefact is produced, the label is applied — and its silence on failure is identical
to its silence on success, which is pattern 11 wearing different clothes.

The correction is the one pattern 02 makes: an **allowlist**, not a denylist. Emit only permitted
fields so an unrecognised one fails closed. That fixes the schema problem and never touches the
values, so the reading step remains.

Second form, same shape: trusting a redaction tool's classifier. It finds the patterns it has
patterns for, a column of measurements matches none, and matching none is exactly what it reports.

## Prior art

- Narayanan & Shmatikov, *How To Break Anonymity of the Netflix Prize Dataset* —
  [arXiv:cs/0610105](https://arxiv.org/abs/cs/0610105). The canonical demonstration that removing
  identifiers from sparse records does not de-identify them
- de Montjoye, Hidalgo, Verleysen & Blondel, *Unique in the Crowd: The privacy bounds of human
  mobility* — *Scientific Reports*, 2013. A handful of points in a series is enough, and coarsening
  buys far less than it appears to
- Ganta, Kasiviswanathan & Smith, *Composition Attacks and Auxiliary Information in Data Privacy* —
  [arXiv:0803.0032](https://arxiv.org/abs/0803.0032). Two releases, each safe alone, that are not
  safe together
- NIST SP 800-188, *De-Identifying Government Datasets: Techniques and Governance* (2023), and
  GitHub Docs, *Removing sensitive data from a repository* — de-identification as a governed process
  with review, and the vendor's own statement that pushed data persists in forks, clones, and caches

## Specimen

None — prose is sufficient. What erodes is not the argument but the willingness to open the file,
and no specimen demonstrates that.
