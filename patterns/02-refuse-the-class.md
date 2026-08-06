---
pattern: 02
name: "Refuse the Class, Not the Case"
status: draft          # draft | field-tested | superseded-by: NN
refuses: "a whole dangerous input class, with one identical error"
specimen: none
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
- **One error, every time.** Same string, same code, same latency envelope, whatever was wrong. A
  prober who gets different responses for *unsupported scheme*, *host not permitted*, and *content
  type rejected* has been handed a map of your filter, drawn by you, for free.

Then **say what you removed.** A capability quietly missing is a bug report; a capability documented
as refused is a design decision.

## Consequences

**The filter can't be mapped,** and there is no enumeration race to lose.

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
that *someone else* performs the fetch. And the error messages fail because they turn every
rejection into a free oracle query. This is the same reason a login form says *invalid credentials*
rather than *no such user*: the specific failure is the leak.

The tell that you're in this anti-pattern: your validation code keeps growing, and each new entry
was added after someone found a way around the last one.

## Prior art

- Saltzer & Schroeder, *The Protection of Information in Computer Systems* (1975) — fail-safe
  defaults and economy of mechanism, still the clearest statement of why the default must be denial
- OWASP — Server-Side Request Forgery prevention, and the long-standing guidance on uniform
  authentication errors to prevent account enumeration
- OWASP Top 10 for LLM Applications — on untrusted input reaching model-adjacent fetchers

## Specimen

None — prose is sufficient. The mechanism is simple; the discipline of returning one error is what
erodes under pressure to be helpful.
