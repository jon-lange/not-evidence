# Refusal Engineering

> **Twelve patterns for AI systems that have to decline correctly.**

Most writing about AI systems is about getting them to answer. This is about the harder half —
knowing when not to, and building systems that can act on that knowledge.

The through-line across all twelve: **a system declining correctly when the reassuring signal is
the one that's lying.** The guardrail that refused the obvious attack. The green test that never
ran. The judge that shares the subject's lineage. The label that says "sanitized." Each of these
looks like evidence and isn't, and each one has a refusal that closes it.

This is a **bounded catalogue**. Twelve patterns, then it's finished. It is not a framework, not a
library, and not a blog.

---

## The catalogue

| # | Pattern | Refuses | Status |
|---|---|---|---|
| 01 | [Grounded or Refuse](patterns/01-grounded-or-refuse.md) | to answer without evidence | draft |
| 02 | [Refuse the Class, Not the Case](patterns/02-refuse-the-class.md) | a whole dangerous input class, with one identical error | draft |
| 03 | [Deterministic Over Prompted](patterns/03-deterministic-over-prompted.md) | to rely on instructing a model to disbelieve its source | draft |
| 04 | [Meta-Injection Is Not Content-Relay](patterns/04-meta-injection-is-not-relay.md) | to treat a refused meta-attack as a defended surface | **field-tested** |
| 05 | [The Judge Cannot Share a Family](patterns/05-judge-cannot-share-a-family.md) | to let a same-lineage judge gate a promotion | draft |
| 06 | [Refuse to Score Unratified Weights](patterns/06-refuse-unratified-weights.md) | to produce a number the domain owner never endorsed | draft |
| 07 | [Gate Over-Refusal Separately](patterns/07-gate-over-refusal-separately.md) | to quote quality without refusal beside it | draft |
| 08 | [A Remembered Figure Is Never a Current Figure](patterns/08-remembered-is-not-current.md) | to let a stored value stand in for a live one | draft |
| 09 | [Keep New Modalities Off the Reasoning Path](patterns/09-modalities-off-the-reasoning-path.md) | to widen the trusted surface for a new input type | **field-tested** |
| 10 | [Never Auto-Commit a Lossy Transducer](patterns/10-never-auto-commit-a-transducer.md) | to execute on a plausible substitution | **field-tested** |
| 11 | [Green Is Not Evidence](patterns/11-green-is-not-evidence.md) | to trust an absence-test that was never mutation-checked | draft |
| 12 | [Distrust the Sanitization Label](patterns/12-distrust-the-sanitization-label.md) | to publish on someone's assurance that it was scrubbed | draft |

Four patterns carry runnable specimens — **04, 05, 10, 11** — because those claims are more
convincing demonstrated than argued. The rest are prose, deliberately.

## How to read an entry

Every pattern has the same shape: *Context · Forces · The Refusal · Consequences · The naive
approach it beats · Prior art · Specimen.*

**The Refusal** is the load-bearing paragraph — the rule stated so it can be violated.
**The naive approach it beats** is the honesty check: if there's no attractive wrong answer, it
isn't a pattern, it's a description.

Entries are **append-only**. A pattern that turns out to be wrong is marked
`superseded-by:` and kept. Nothing is deleted, so inbound links keep resolving and the reasoning
survives its own revision.

Status is one of `draft` · `field-tested` · `superseded-by: NN`.

## Specimens

Small, self-contained, and **explicitly unmaintained** — reference implementations, not software
you should depend on. Each runs standalone, and `make dev` boots all of them together against a
mock inference path with no cloud account required.

They use a generic domain on purpose. A specimen written against finance or healthcare would be
making a claim about a specific system rather than a general one.

## Who wrote this

I lead AI platform engineering at an enterprise fintech. These are personal notes and patterns.

**The views expressed here are my own and do not represent those of my employer or any client.
Nothing in this repository is derived from, or discloses, confidential or proprietary information
of any employer. All material was developed on my own time, on my own equipment, from publicly
available sources.**

The method that keeps that true is written down in [METHOD.md](METHOD.md) — not as a disclaimer,
but as a working discipline that constrains what gets published and how.

## License

- **Code, specimens, and prompts** — Apache License 2.0, see [`LICENSE`](LICENSE)
- **Prose and pattern text** — CC BY 4.0, see [`LICENSE-CC-BY-4.0`](LICENSE-CC-BY-4.0)
