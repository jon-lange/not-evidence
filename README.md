# Not Evidence

> **Twelve signals that look like evidence and aren't — and the refusal that closes each one.**

The guardrail that refused the obvious attack. The green test that never ran. The judge that shares
the subject's lineage. The label that says "sanitized." Every one of them is reassuring, every one
is routinely accepted as proof, and none of them is evidence of the thing it is taken to prove.

Most writing about AI systems is about getting them to answer. This is about the harder half —
knowing when not to, and building systems that can act on that knowledge. Each entry names a signal
you are probably already trusting, and states the refusal that stops it being trusted.

**The failure they share is aggregation.** A comfortable summary — a pass rate, a green suite, a
verdict, a label — is where the dangerous case hides, because averaging is how a failure stops
looking like one. Every refusal here is, underneath, a refusal to let one reassuring number stand
in for the thing it summarises.

This is a **bounded catalogue**. Twelve entries, then it's finished. It is not a framework, not a
library, and not a blog.

---

## All twelve claims were measured. Seven survived.

Each pattern was written as a claim, then put in front of real models or a real adversary, then
rewritten to whatever the evidence supported. Seven survived that. Five did not, and now argue
something different from what they set out to argue — **and the five are why the seven are worth
anything.**

The comparison worth making is not against a catalogue whose claims all held. It is against the
usual case, where nobody ran them.

- **01** predicted that *"if you're not sure, say you don't know"* confabulates. It did not — not
  once in 36 opportunities, across four models and both vendors.
- **03** predicted that a prompt defence reworded three times is no defence. The third rewording is
  exactly where it started working — 80% relay to 0%, on every model. The entry now argues from
  verifiability rather than generality.
- **05** predicted a same-family judge would favour its own lineage. No flip occurred. What actually
  disqualified two of three judges was saturation and position instability, neither about lineage.
- **07** predicted that newer models refuse more. Flat across both vendors, every vintage.
- **08** predicted that agents reuse remembered figures instead of fetching live ones. They called
  the tool in 57 of 60 items.

Every one of the twelve carries an **Adjudication** line at the top of its `RESULTS.md` — `confirmed`,
`narrowed`, or `central-claim-failed`. The counts above are derived from those twelve lines and
checked against them, so this heading cannot drift from the evidence under it.

**[EVIDENCE.md](EVIDENCE.md) is the whole record on one page** — what was measured, the figure that
came back, and a link to the working for every entry.

A catalogue that only reports its confirmations is telling you about its author's confidence, not
about the world.

## Start here

You probably arrived with one of these.

| If this sounds familiar | Start with |
|---|---|
| "The suite is green and I can't say what that proves" | [11](patterns/11-green-is-not-evidence.md), [01](patterns/01-grounded-or-refuse.md) |
| "A model grades another model, and the score gates a release" | [05](patterns/05-judge-cannot-share-a-family.md), [06](patterns/06-refuse-unratified-weights.md) |
| "We shipped image or document upload and the injection suite didn't change" | [09](patterns/09-modalities-off-the-reasoning-path.md), [04](patterns/04-meta-injection-is-not-relay.md) |
| "Our defence is a prompt telling the model to ignore instructions it finds" | [03](patterns/03-deterministic-over-prompted.md), [04](patterns/04-meta-injection-is-not-relay.md) |
| "Someone handed me a file marked *sanitised* and asked me to publish it" | [12](patterns/12-distrust-the-sanitization-label.md) |
| "The agent quoted a figure it had seen earlier instead of fetching it" | [08](patterns/08-remembered-is-not-current.md) |
| "The allowlist has grown to eighteen entries and nobody can review it" | [02](patterns/02-refuse-the-class.md) |
| "A transcript, parse, or extraction gets acted on automatically" | [10](patterns/10-never-auto-commit-a-transducer.md) |
| "Quality went up and nobody measured what we started refusing" | [07](patterns/07-gate-over-refusal-separately.md) |

## The catalogue

| # | Pattern | Refuses | Status |
|---|---|---|---|
| 01 | [Grounded or Refuse](patterns/01-grounded-or-refuse.md) | to answer without evidence | **revised-by-specimen** |
| 02 | [Refuse the Class, Not the Case](patterns/02-refuse-the-class.md) | a whole dangerous input class, with one identical error | **field-tested** |
| 03 | [Deterministic Over Prompted](patterns/03-deterministic-over-prompted.md) | to rely on instructing a model to disbelieve its source | **revised-by-specimen** |
| 04 | [Meta-Injection Is Not Content-Relay](patterns/04-meta-injection-is-not-relay.md) | to treat a refused meta-attack as a defended surface | **field-tested** |
| 05 | [The Judge Cannot Share a Family](patterns/05-judge-cannot-share-a-family.md) | to let a same-lineage judge gate a promotion | **revised-by-specimen** |
| 06 | [Refuse to Score Unratified Weights](patterns/06-refuse-unratified-weights.md) | to produce a number the domain owner never endorsed | **field-tested** |
| 07 | [Gate Over-Refusal Separately](patterns/07-gate-over-refusal-separately.md) | to quote quality without refusal beside it | **revised-by-specimen** |
| 08 | [A Remembered Figure Is Never a Current Figure](patterns/08-remembered-is-not-current.md) | to let a stored value stand in for a live one | **revised-by-specimen** |
| 09 | [Keep New Modalities Off the Reasoning Path](patterns/09-modalities-off-the-reasoning-path.md) | to widen the trusted surface for a new input type | **field-tested** |
| 10 | [Never Auto-Commit a Lossy Transducer](patterns/10-never-auto-commit-a-transducer.md) | to execute on a plausible substitution | **field-tested** |
| 11 | [Green Is Not Evidence](patterns/11-green-is-not-evidence.md) | to trust an absence-test that was never mutation-checked | **field-tested** |
| 12 | [Distrust the Sanitization Label](patterns/12-distrust-the-sanitization-label.md) | to publish on someone's assurance that it was scrubbed | **field-tested** |

**Every pattern carries a runnable specimen.** Not as illustration — as a test of whether the claim
survives contact with something that can contradict it. For eight of them that is a real model; for
02, 06, 11 and 12 it is an adversary or an exhaustive search, and those four run offline for real.

## How to read an entry

Every pattern has the same shape: *Context · Forces · The Refusal · Consequences · The naive
approach it beats · Prior art · Specimen.*

**The Refusal** is the load-bearing paragraph — the rule stated so it can be violated.
**The naive approach it beats** is the honesty check: if there's no attractive wrong answer, it
isn't a pattern, it's a description.

**The entry states the current claim; the specimen records how it was reached.** A pattern is a
reference, not a lab notebook. A pattern that is retired rather than revised moves to `deprecated/`
with `superseded-by:` set, so inbound links keep resolving.

Status is one of:

- **`draft`** — written, not yet measured
- **`field-tested`** — a specimen ran and the claim held
- **`revised-by-specimen`** — a specimen ran and the claim *did not* hold; the entry states what the
  evidence supports instead, and the specimen's `RESULTS.md` says what was predicted and what happened
- **`superseded-by: NN`** — retired in favour of another entry

Five entries had their central claim fail and carry `revised-by-specimen`. Five more held and were
narrowed by what came back — the claim survived, and its `RESULTS.md` says where it tightened. Two,
04 and 11, came through confirmed. So a central claim survived in seven of twelve.

*Revised* and *wrong* are not the same thing, and this repository is careful about the difference:
ten entries changed in response to evidence, but only five changed because they were wrong. Each
specimen's `RESULTS.md` opens with the **Adjudication** line these counts are derived from.

**Several patterns also contain architectural commitments a specimen cannot test** — a claim about
how a system should be *structured* is not a behavioural prediction. Each `RESULTS.md` states which
of its pattern's claims it exercised and which it did not.

## Specimens

Reference implementations, **not maintained software**. Don't depend on them; read them, run them,
and take the idea.

```bash
make test     # every suite — no network, no keys
make demo     # every offline demonstration
make offline  # the four that need nothing at all, run for real
```

Eleven of twelve need nothing but Python; specimen 09 needs Pillow to rasterise its fixtures and
says so rather than skipping quietly. Four of them — 02, 06, 11 and 12 — have no live component at
all, so `make offline` runs the real thing rather than a demonstration of it. The rest reach a model
only through their `probe.py`, which needs credentials and costs money.

`make check` additionally runs a private forbidden-token scan and **will refuse without its config**
— that refusal is intended, and [CONTRIBUTING.md](CONTRIBUTING.md) explains why.

They use a generic domain on purpose. A specimen written against a regulated vertical would be
making a claim about a specific system rather than a general one.

## One file here is meant to be taken

[`tools/mutcheck.py`](tools/mutcheck.py) — standard library only, importing nothing from this
repository. See it fail before you read anything:

```bash
python3 tools/mutcheck.py --demo
```

That reproduces specimen 11's result: one live assertion, two that pass while the property they
guard is broken. Then drop the file beside your tests and wrap one absence assertion:

```python
require_live(subject, "redact", redact_nothing, lambda: subject.absence_check(SECRET))
```

*With redaction reduced to a no-op, this test must fail.* If it passes, the assertion was never
watching the thing it names. It is not a mutation-testing framework and does not want to be —
[mutmut](https://github.com/boxed/mutmut) and [cosmic-ray](https://github.com/sixty-north/cosmic-ray)
answer *which of my assertions are weak?* over a whole suite, offline. This answers *is this
assertion, guarding this property, live?* — which belongs in the suite, on the line below the
assertion it is about.

It ships its own mutation record — seven breakages, no survivors — in
[`tools/README.md`](tools/README.md), along with what it is bad at. A mutation checker that is not
mutation-checked is the joke this repository exists to prevent.

## Also published as an OKF bundle

[`okf/`](okf/) is this catalogue in the
[Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog) —
a directory of markdown concepts with YAML frontmatter, meant to be read by agents
without a bespoke SDK. Twenty-seven concepts: twelve patterns, twelve specimens,
three indexes.

The repository turned out to already be one, structurally. What the producer adds
is the vocabulary, and one mapping is worth stating: **a specimen becomes an
`Attested Computation`** — the spec's term for a concept carrying *"a sanctioned
way to compute a value, so a consumer can confirm the value was produced by
running it."* That is what every specimen here is, which is why each ships the
harness that produced its figures rather than only the figures.

`scripts/check-consistency.py` becomes the bundle's `attester` — the spec asks for
deterministic, LLM-free code that inspects and returns a verdict, and that is what
it already was.

```bash
make okf          # regenerate
make okf-check    # conformant, and current — runs in CI and in `make check`
```

The bundle is committed rather than built on demand, because OKF's argument is
that a bundle should be clonable and browsable. Committed generated output
drifts, so `make okf-check` fails when it has — and checks conformance first,
since a bundle byte-identical to its producer's output proves nothing if the
producer emits something the spec rejects.

## Skills

The applied layer, in [`skills/`](skills/). **A skill may only exist for a pattern that has a
specimen** — that gate keeps this repository finishable, and it means each one ships with measured
evidence rather than an assertion.

Spec-compliant (`skills/<name>/SKILL.md`), and each carries the `status` of the pattern it
operationalises. A skill cannot claim more than its pattern does.

## Who wrote this

I work on AI platforms for a living. These are personal notes and patterns.

**How this was written.** The entries were drafted and revised with a coding agent, under the
constraints in [CLAUDE.md](CLAUDE.md). Every measurement was actually run, every result checked by
hand, and every citation fetched and verified rather than recalled. Where a specimen contradicted the
pattern it was built for, the pattern was rewritten — which happened more often than not.

**The views expressed here are my own and do not represent those of my employer or any client.
Nothing in this repository is derived from, or discloses, confidential or proprietary information
of any employer. All material was developed on my own time, on my own equipment, from publicly
available sources.**

Working in a regulated industry usually means publishing nothing. [METHOD.md](METHOD.md) is the
discipline that makes this publishable instead — six rules, enforced by hooks and CI rather than by
remembering, including the one that matters most: **no number appears here that was not generated
here.** It is written down because a method you can inspect is worth more than an assurance you have
to take on faith.

## License

- **Code, specimens, and prompts** — Apache License 2.0, see [`LICENSE`](LICENSE)
- **Prose and pattern text** — CC BY 4.0, see [`LICENSE-CC-BY-4.0`](LICENSE-CC-BY-4.0)
