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
| 01 | [Grounded or Refuse](patterns/01-grounded-or-refuse.md) | to answer without evidence | **field-tested** |
| 02 | [Refuse the Class, Not the Case](patterns/02-refuse-the-class.md) | a whole dangerous input class, with one identical error | **field-tested** |
| 03 | [Deterministic Over Prompted](patterns/03-deterministic-over-prompted.md) | to rely on instructing a model to disbelieve its source | **field-tested** |
| 04 | [Meta-Injection Is Not Content-Relay](patterns/04-meta-injection-is-not-relay.md) | to treat a refused meta-attack as a defended surface | **field-tested** |
| 05 | [The Judge Cannot Share a Family](patterns/05-judge-cannot-share-a-family.md) | to let a same-lineage judge gate a promotion | **field-tested** |
| 06 | [Refuse to Score Unratified Weights](patterns/06-refuse-unratified-weights.md) | to produce a number the domain owner never endorsed | **field-tested** |
| 07 | [Gate Over-Refusal Separately](patterns/07-gate-over-refusal-separately.md) | to quote quality without refusal beside it | draft |
| 08 | [A Remembered Figure Is Never a Current Figure](patterns/08-remembered-is-not-current.md) | to let a stored value stand in for a live one | draft |
| 09 | [Keep New Modalities Off the Reasoning Path](patterns/09-modalities-off-the-reasoning-path.md) | to widen the trusted surface for a new input type | **field-tested** |
| 10 | [Never Auto-Commit a Lossy Transducer](patterns/10-never-auto-commit-a-transducer.md) | to execute on a plausible substitution | **field-tested** |
| 11 | [Green Is Not Evidence](patterns/11-green-is-not-evidence.md) | to trust an absence-test that was never mutation-checked | **field-tested** |
| 12 | [Distrust the Sanitization Label](patterns/12-distrust-the-sanitization-label.md) | to publish on someone's assurance that it was scrubbed | **field-tested** |

**Every pattern carries a runnable specimen.** Not as illustration — as a test of whether the claim
survives contact with a model.

## Every claim here was measured before it was published

These are not assertions with citations attached. Each entry states a claim, and each claim was
tested against real models or a real adversary before it went in — then rewritten to whatever the
evidence actually supported.

The evidence is in the repository. Each specimen's `RESULTS.md` records what was run, what came back,
the scope of the run, and **what result would falsify the pattern**. Where a claim is narrower than
you would expect, that is usually because the wider version did not survive measurement.

Nine of the twelve entries were revised by their own specimens. Several are narrower than their first
draft; a few argue something different from what they set out to argue. That is what the specimens
are for.

## How to read an entry

Every pattern has the same shape: *Context · Forces · The Refusal · Consequences · The naive
approach it beats · Prior art · Specimen.*

**The Refusal** is the load-bearing paragraph — the rule stated so it can be violated.
**The naive approach it beats** is the honesty check: if there's no attractive wrong answer, it
isn't a pattern, it's a description.

**The entry states the current claim; the specimen records how it was reached.** A pattern is a
reference, not a lab notebook. A pattern that is retired rather than revised moves to `deprecated/`
with `superseded-by:` set, so inbound links keep resolving.

Status is one of `draft` · `field-tested` · `superseded-by: NN`.

## Specimens

Small, self-contained, and **explicitly unmaintained** — reference implementations, not software
you should depend on.

```bash
make test     # every suite, standard library only, no network, no keys
make demo     # every offline demonstration
make check    # scan + tests, what a commit runs
```

Four specimens need nothing at all — no venv, no dependencies. The rest have an offline mode that
runs the same way; only their live probes need credentials, and those are per-specimen and cost
money. `make help` shows how.

They use a generic domain on purpose. A specimen written against finance or healthcare would be
making a claim about a specific system rather than a general one.

## Skills

The applied layer, in [`skills/`](skills/). **A skill may only exist for a pattern that has a
specimen** — that gate keeps this repository finishable, and it means each one ships with measured
evidence rather than an assertion.

Spec-compliant (`skills/<name>/SKILL.md`), and each carries the `status` of the pattern it
operationalises. A skill cannot claim more than its pattern does.

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
