---
pattern: 02
name: "Refuse the Class, Not the Case"
status: field-tested   # draft | field-tested | superseded-by: NN
refuses: "a whole dangerous input class, with one identical error"
specimen: 02-refuse-the-class
---

# 02 · Refuse the Class, Not the Case

> **Refuses a whole dangerous input class, with one identical error.**

## Context

Some inputs are dangerous not because of what they contain but because of what *processing them*
entails.

A remote URL handed to a model provider is dereferenced from the provider's network — a server-side
request you did not make and cannot see, and an exfiltration channel out of your context. A rich
document format arrives with a native-code parser, historically the most reliable source of
memory-safety bugs. Neither danger lives in a particular value; it lives in the category.

## Forces

**Case-by-case filtering feels precise.** You keep the capability and block only the bad instances —
engineering rather than capitulation.

**Enumeration is unwinnable.** Any list of bad schemes, hosts, encodings, or magic bytes is a list of
the ones you thought of. The attacker only needs the one you didn't.

**Helpful errors are a design instinct.** Telling a caller *why* their input failed is normally
right, and every distinct message is a bit of information about where the boundary sits.

**Refusing a whole class removes real functionality** for users who had legitimate uses.

## The Refusal

**When the danger is a property of the class, refuse the class — and return one identical error for
every rejected variant.**

Two halves, and the second is the one that gets dropped:

- **Refuse the class.** Not "URLs from untrusted hosts" but *remote URLs*. Not "malformed documents"
  but *that format, at this boundary* — move the parser outside the trust boundary and accept a
  single normalised input type instead.
- **One error, every time.** Same string, same code, whatever was wrong. A prober who gets different
  responses for *unsupported scheme* and *host not permitted* is being handed a gradient to climb.
- **And the same latency.** A check that returns in microseconds and one that returns in hundreds of
  microseconds are two different error messages written in time. Do the constant work, or the
  identical string buys you nothing.

Then **say what you removed.** A capability quietly missing is a bug report; a capability documented
as refused is a design decision.

## Consequences

**The filter gets an order of magnitude more expensive to map — not impossible.** A determined
prober still recovers the boundary from uniform errors; it costs roughly 10× the queries. Budget for
an attacker who is willing to spend that, and treat the multiplier as the win rather than the wall.

**And the size of that win is geometry, not principle.** It depends on how far apart the accepted
regions sit: ~10× when they are two single-field edits apart, ~55× when an exception is isolated four
edits away, and **1.0× — nothing at all — when the boundary already has only one thing to say.** A
class refusal has one error code by construction: refuse the class and the uniform error is free to
maintain.

**The blast radius shrinks to something describable.** "This boundary accepts exactly one input
type" is a sentence you can hand to a reviewer; no allowlist that grew by accretion has one.

**You lose legitimate uses,** and should name them rather than pretend otherwise.

**Uniform errors make support harder.** Someone with a genuinely malformed input now gets a generic
refusal. Compensate with server-side logging that records the real reason where the caller can't
see it.

## The naive approach it beats

**Allow-with-validation, plus helpfully specific errors.** A blocklist of dangerous URL schemes,
a size cap, a MIME sniff, and a distinct message for each check.

It fails twice. The blocklist fails because the dangerous property was never the scheme — it was
that *someone else* performs the fetch. And the error messages fail because they turn every rejection
into a cheap oracle query — *cheap*, not free: measured, a full map cost ~2,300 probes with distinct
messages against ~24,600 without. Six error classes buy a hill to climb, not six probes.

The tell: your validation code keeps growing, and each entry was added after someone found a way
around the last one.

## Prior art

- Saltzer & Schroeder, *The Protection of Information in Computer Systems* (1975) — fail-safe
  defaults and economy of mechanism, still the clearest statement of why the default must be denial
- OWASP — Server-Side Request Forgery prevention, and the long-standing guidance on uniform
  authentication errors to prevent account enumeration
- OWASP Top 10 for LLM Applications — on untrusted input reaching model-adjacent fetchers

## Specimen

[`specimens/02-refuse-the-class/`](../specimens/02-refuse-the-class/) — **built.**
Measured output in [`RESULTS.md`](../specimens/02-refuse-the-class/RESULTS.md).

Offline. One automated prober against two validators that accept an identical set over all 48,000
references — only the error channel differs. Codes are treated as opaque labels, pinned by a test
that renames every one and requires an identical run. 25 seeds.

| boundary shape | probes to a complete map, distinct errors | one code | ratio |
|---|---|---|---|
| accreted allowlist | 2,298 | 24,592 | **10.7×** |
| carve-out | 488 | 26,885 | **55.1×** |
| class refusal | 1,114 | 1,114 | **1.0×** |

**Timing is not a weaker channel than the message — it is an exact substitute.** Collapsing six
error strings to one identical code changed the prober's cost *by nothing*: same counts, same seeds,
run for run, because evaluation still short-circuited. A nearest-centroid classifier recovered which
rule fired **100% of the time** from timing alone, against 16.7% chance. Forcing constant work
dropped that to 18.8% and pushed the prober past 8,000 probes without completing.

Uniform strings without uniform latency are not uniform errors.
