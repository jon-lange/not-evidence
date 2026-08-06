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

A remote URL handed to a model provider is dereferenced by the provider, from the provider's
network — which is a server-side request you did not make and cannot see, and simultaneously an
exfiltration channel out of your context. A rich document format arrives with a parser that is
native code, historically the most reliable source of memory-safety bugs in any stack. Neither
danger lives in a particular value. It lives in the category.

## Forces

**Case-by-case filtering feels precise.** You keep the capability and block only the bad instances.
It reads as engineering rather than capitulation.

**Enumeration is unwinnable.** Any list of bad schemes, hosts, encodings, or magic bytes is a list of
the ones you thought of. The attacker only needs the one you didn't.

**Helpful errors are a design instinct.** Telling a caller *why* their input failed is normally the
right thing, and every distinct message is a bit of information about where the boundary sits.

**Refusing a whole class removes real functionality** for real users who had legitimate uses.

## The Refusal

**When the danger is a property of the class, refuse the class — and return one identical error for
every rejected variant.**

Two halves, and the second is the one that gets dropped:

- **Refuse the class.** Not "URLs from untrusted hosts" but *remote URLs*. Not "malformed documents"
  but *that format, at this boundary* — move the parser somewhere it can't hurt you and accept a
  single normalised input type behind the trust boundary instead.
- **One error, every time.** Same string, same code, whatever was wrong. A prober who gets different
  responses for *unsupported scheme*, *host not permitted*, and *content type rejected* is being
  handed a gradient to climb.
- **And the same latency — which is not a footnote.** Measured, this is the half that carries the
  result. Collapsing six distinct error strings to one identical code changed the prober's cost *not
  at all* — same counts, same seeds, run for run — because evaluation still short-circuited and the
  clock carried the whole signal. A check that returns in microseconds and one that returns in
  hundreds of microseconds are two different error messages written in time. Do the constant work, or
  the identical string buys you nothing.

Then **say what you removed.** A capability quietly missing is a bug report; a capability documented
as refused is a design decision.

## Consequences

**The filter gets an order of magnitude more expensive to map.** Not impossible — this entry used to
say "can't be mapped" and that is wrong. Every uniform-error run in the specimen still produced a
complete, correct map of the boundary. It cost about 10× more probes to get there.

**And the size of that win is geometry, not principle.** It depends on how far apart the accepted
regions sit: ~10× when they are two single-field edits apart, ~55× when an exception is isolated four
edits away, and **1.0× — nothing at all — when the boundary already has only one thing to say.** A
class refusal has one error code by construction, which is why the two halves of this pattern
reinforce each other: refuse the class and the uniform error becomes free to maintain.

**The blast radius shrinks to something describable.** "This boundary accepts exactly one input
type" is a sentence you can hand to a reviewer, which is not true of any allowlist that grew by
accretion.

**You lose legitimate uses,** and you should name them rather than pretend the gap isn't there.

**Uniform errors make support harder.** Someone with a genuinely malformed input now gets a generic
refusal. Compensate with server-side logging that records the real reason where the caller can't
see it — the information should exist, just not on that side of the boundary.

## The naive approach it beats

**Allow-with-validation, plus helpfully specific errors.** A blocklist of dangerous URL schemes,
a size cap, a MIME sniff, and a distinct message for each check.

It fails twice. The blocklist fails because the dangerous property was never the scheme — it was
that *someone else* performs the fetch. And the error messages fail because they turn every rejection
into a cheap oracle query — *cheap*, not free: measured, a full map cost ~2,300 probes with distinct
messages against ~24,600 without. Six error classes buy a hill to climb, not six probes.

This is the same reason a login form says *invalid credentials* rather than *no such user*: the
specific failure is the leak.

The tell that you're in this anti-pattern: your validation code keeps growing, and each new entry
was added after someone found a way around the last one.

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

**Three corrections to this entry, all folded in above.** The map is not prevented, only made ~10×
dearer. "Free" was wrong by roughly 400×. And the multiplier is a property of the boundary's
geometry, which the entry never mentioned.

**The finding that reordered the entry:** collapsing six error strings to one identical code changed
the prober's cost *by nothing* — same counts, same seeds, run for run — because evaluation still
short-circuited. A nearest-centroid classifier recovered which rule fired **100% of the time** from
timing alone (chance 16.7%). Forcing constant work dropped that to 18.8% and pushed the prober past
8,000 probes without completing. The latency clause was third in a sub-list; it is the half that
carries the result.
