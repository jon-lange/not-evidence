# Specimen 04 — the two injection classes

**Status: planned.** Not yet built.

Demonstrates [pattern 04](../../patterns/04-meta-injection-is-not-relay.md) by running two poison
classes against the same guardrailed agent over a public documentation corpus.

## What it will show

| Input | Expected |
|---|---|
| Clean document | Grounded answer, no relay |
| Meta-instruction poison (*"ignore your rules…"*) | **Refused** |
| Content-framed poison (a calm, false assertion) | **Relayed** — this is the demonstration |
| Content-framed poison, deterministic transform enabled | **Closed**, with the prompt unchanged |

The point of the third row is that nothing appears to go wrong. No guardrail fires, no error is
raised, and the model behaves correctly throughout — it was asked what the document says, and it
said so.

## Constraints

- Every fixture authored from scratch. No corpus is reused from anywhere.
- Generic domain. A specimen written against a regulated vertical would be making a claim about a
  particular system rather than a general one.
- Reference implementation, explicitly unmaintained.
