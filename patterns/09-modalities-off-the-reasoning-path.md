---
pattern: 09
name: "Keep New Modalities Off the Reasoning Path"
status: field-tested        # draft | field-tested | revised-by-specimen | superseded-by: NN
refuses: "to widen the trusted surface for a new input type"
specimen: 09-modality-surface
---

# 09 · Keep New Modalities Off the Reasoning Path

> **Refuses to widen the trusted surface for a new input type.**

## Context

A text pipeline has been hardened over years: answers grounded and cited, a dangerous input class
refused at the boundary, controls that are transforms rather than sentences in a prompt (pattern 03),
an injection suite that knows a meta-instruction from a relayed claim (pattern 04).

Then the roadmap says: add voice. Or images. Or let people upload their own documents.

## Forces

**Routing the new modality through the reasoning core is the intuitive design.** *The model should hear
the tone. It should see the layout.* Each is a real capability, and each argues for the loop.

**The text path's properties transfer unevenly, and not predictably.** Model-layer injection posture
carries through a rendered image intact; so does egress scrubbing, which operates on output — a
surface the input modality cannot reach. What does not carry is every control implemented in *your*
code: ingress scanning, denylists, and the injection suite itself, all of which read strings and
suddenly have no string to read. Which properties survive a new medium is a question about where each
one sits, not about "the system."

**Edge placement looks like under-building.** A component that only transcribes reads as a thin
wrapper, and the modality is the demo, so the version that does more wins the review.

## The Refusal

**Add a new modality at the edges of the verified pipeline, never inside it. It may change how input
arrives and how output is delivered. It may not change what the system decides or says.**

- **Speech-to-text deposits a transcript, and the transcript is the interface.** It enters the pipeline
  as if typed; nothing downstream can tell it came from audio.
- **Text-to-speech reads output that has already cleared every gate.** It renders an approved string,
  never generating, summarising, or rephrasing.
- **Neither component is in the decision loop.** Neither gets its own prompt, retrieval, or opinion
  about what the user meant.

The diagnostic: **if I deleted the new modality entirely, would every answer be identical?** If yes,
it is at the edge. If no, every property you proved for text is open again, in a medium where your
tests cannot express the new cases.

## Consequences

**The modality costs a component, not a re-audit.** Grounding, citation, and injection posture are
unchanged because the reasoning path is unchanged.

**Each new input channel is a fresh indirect-injection surface.** Text reaching the model as pixels is
still text reaching the model, so pattern 04 applies and your fixtures must exist *in that medium*. A
text-only suite says nothing about the image path, however green.

**Some channels have no allow-list available.** For user uploads, source governance is unavailable by
construction; what remains is pattern 02's class refusal at the parse boundary, and attributing
anything derived from the file to it.

**You give up modality-specific intelligence** — tone of voice, page layout. Needing it means
budgeting for a second hardening effort in that medium, not skipping one.

**Transduction errors become content errors:** a misheard word is a wrong word in a real question,
and nothing downstream knows it was uncertain (pattern 10).

## The naive approach it beats

**Hand the multimodal model the raw input and let it reason over everything together.** It accepts
audio, images and document bytes natively, so integration is nearly free — and strictly more capable.

It fails for one mechanical reason: **your controls are text transforms, and there is no longer a text
field for them to operate on.** An instruction rendered as pixels never becomes a string your scrubber
inspects; it becomes tokens the model attends to. Pattern 02's class refusal was written against MIME
types, and images are the feature. The pattern 04 suite stays green because every fixture is text.

Two tells:

- **The green suite did not change when the modality shipped.** A channel that required no new
  fixtures is untested, not safe.
- **"The model is multimodal now, so it handles it."** Multimodal means the model accepts the input,
  not that anything around it does.

## Prior art

- Bagdasaryan et al., *Abusing Images and Sounds for Indirect Instruction Injection in Multi-Modal LLMs*
  — [arXiv:2307.10490](https://arxiv.org/abs/2307.10490). Instructions delivered through channels
  nothing inspects.
- Carlini et al., *Are aligned neural networks adversarially aligned?* —
  [arXiv:2306.15447](https://arxiv.org/abs/2306.15447). Attacks that fail against the text interface
  succeed through the image one.
- Bailey et al., *Image Hijacks: Adversarial Images can Control Generative Models at Runtime* —
  [arXiv:2309.00236](https://arxiv.org/abs/2309.00236). A modality inside the reasoning loop is a
  control channel, not merely an input.
- Carlini & Wagner, *Audio Adversarial Examples: Targeted Attacks on Speech-to-Text* —
  [arXiv:1801.01944](https://arxiv.org/abs/1801.01944). The edge transducer is itself attackable; edge
  placement bounds the damage.

## Specimen

[`specimens/09-modality-surface/`](../specimens/09-modality-surface/) — **built.**
Measured output in [`RESULTS.md`](../specimens/09-modality-surface/RESULTS.md).

Specimen 04's corpus, guardrail wording and questions, byte-identical (asserted by test), with the
poison delivered as rendered images. Four models, two vendors, 103 completions.

| | text | image |
|---|---|---|
| meta-injection | REFUSED | **REFUSED** |
| content-relay | RELAYED | RELAYED |
| ingress scanner fires | 100% | **0%** |
| specimen 04's suite covers it | yes | **no — 12 passed, 0 failed, 0 cells** |

**Model-layer posture transferred completely.** 24/24 meta-injection refusals through pixels, both
vendors, including text rendered as unreadable fine print. No model emitted the injected token. **The
failure is in your code, not in the model.**

**Code-layer controls transferred not at all,** exactly as the naive-approach section predicts. The
scanner has no defect — a test proves it fires on the payload as characters. There is simply no longer
a string to read.

**And one in-model control silently vanished.** One model spontaneously warned that the documented
procedure looked like phishing — 7 of 10 text trials, **0 of 20 image trials** (Fisher exact,
p ≈ 5.9 × 10⁻⁵). Both channels scored RELAYED, so the verdict matrix could not see it. It was caught
only because raw answers were persisted and re-scored on a dimension that did not exist at call time.
