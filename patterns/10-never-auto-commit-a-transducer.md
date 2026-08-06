---
pattern: 10
name: "Never Auto-Commit a Lossy Transducer"
status: field-tested        # draft | field-tested | revised-by-specimen | superseded-by: NN
refuses: "to execute on a plausible substitution"
specimen: 10-lossy-transducer
---

# 10 · Never Auto-Commit a Lossy Transducer

> **Refuses to execute on a plausible substitution.**

## Context

A step in your pipeline converts one representation into another and loses information doing it:
speech to text, image to text, PDF to structured fields, audio to intent. Its output then feeds
something that acts — a query, a tool call, a message, a form submission.

The failure people design for is *garbling*: the transducer produces obvious nonsense and something
downstream notices. That failure is real, visible, and largely harmless.

The failure that matters is **plausible substitution**: the transducer produces something clean,
grammatical, and wrong. A different name. A different number. A different entity. Nothing about the
output announces it, because there is nothing wrong with it except that it is not what was there.

## Forces

**Auto-commit is the entire value proposition.** A hands-free flow that stops for confirmation is
a flow with a step in it, and the step is what you were removing.

**Accuracy metrics measure the wrong thing.** Word error rate averages over a transcript. The
substitution of one proper noun barely moves it, and that one token is the entire semantic payload.

**These models are obliged to produce output.** A generative recogniser given no signal does not
return empty — it returns its best guess at what such input would contain, which is drawn from its
training distribution rather than from your microphone.

**Supplying domain context feels like a pure win.** Vendors offer a prompt or vocabulary hint to
improve recognition of in-domain terms, and it is documented as an accuracy feature.

## The Refusal

**Output from a lossy transducer enters a review buffer, never an execution path.**

The user sees it before it acts. The transcript lands in the composer for editing rather than being
sent. The extracted fields are shown before the form submits. The recognised intent is confirmed
before the tool runs.

Where auto-commit is genuinely required, it is justified **per risk tier, explicitly** — and the
justification has to be about consequence, not confidence. A read-only lookup that mis-hears yields
a wrong answer you can re-ask. A transfer that mis-hears yields a wrong transfer. Those are not the
same decision and they must not share a default.

Two corollaries the specimen measured directly:

- **Gate on signal before calling.** Do not send a clip that never reached speech level. This is
  cheap and it removes the worst input class.
- **Do not add a domain hint without measuring it on your real input.** It gives the model material
  to emit when there is nothing to transcribe. Two of three models tested returned the hint itself
  as though it had been spoken.

## Consequences

**You keep the step you were trying to remove.** Say so honestly rather than describing a review
buffer as a feature. The trade is real: you are buying the ability to catch a silent substitution.

**You need somewhere for the review to live.** A composer, a confirmation, a diff. This is design
work, not just a flag.

**Level gating is necessary and not sufficient.** In the specimen, a signal that cleared the
loudness floor and contained no speech still produced confident output. Gating removes empty input;
it does not make the transducer trustworthy.

**You cannot generalise across models.** Same vendor, same day, same inputs produced Japanese from
one model, French subtitle boilerplate from another, and silence from a third. Whatever you measure,
you measured one model.

## The naive approach it beats

**Filtering the output.** Confidence thresholds, profanity screens, length checks, "does this look
like a sentence."

It fails because **the output is fine.** It is fluent, grammatical, correctly punctuated, and
frequently on-topic. There is no property to filter on. By the time text exists, the information
that would have revealed the substitution — that the input contained no speech — has been discarded.

The mitigation has to sit on the **input** side, or on the **human** side. There is no third place.

A second naive approach, and the one the specimen was built to test: **adding a domain hint to
improve accuracy.** On the models tested this did not make output safer, and on two of three it
made things actively worse by handing the model a script to recite.

## Prior art

- Koenecke, Choi, Mei, Schellmann & Sloane, *Careless Whisper: Speech-to-Text Hallucination Harms* —
  ACM FAccT 2024, [doi:10.1145/3630106.3658996](https://doi.org/10.1145/3630106.3658996).
  Hallucinated content in clinical and accessibility contexts.

## Specimen

[`specimens/10-lossy-transducer/`](../specimens/10-lossy-transducer/) — **built.**
Measured output in [`RESULTS.md`](../specimens/10-lossy-transducer/RESULTS.md).

Three models, three synthetic inputs, each sent bare and with a recipe-vocabulary hint. None of the
inputs contains speech; the correct output for every cell is empty. Every cell reproduced identically
across three consecutive runs.

**Bare, the models emit training-data artefacts** — subtitle boilerplate, stray phrases in other
languages. Absurd in context, and catchable. **Hinted, two of three return the hint text itself as
though it had been spoken.** The dangerous cell is a single short phrase drawn from that vocabulary:
fluent, grammatical, on-topic, indistinguishable from a real transcription.
