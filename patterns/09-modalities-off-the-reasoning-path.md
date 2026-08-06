---
pattern: 09
name: "Keep New Modalities Off the Reasoning Path"
status: field-tested   # draft | field-tested | superseded-by: NN
refuses: "to widen the trusted surface for a new input type"
specimen: 09-modality-surface
---

# 09 · Keep New Modalities Off the Reasoning Path

> **Refuses to widen the trusted surface for a new input type.**

## Context

A text pipeline has been hardened over years. Answers are grounded and cited. A dangerous input
class is refused at the boundary with one uniform error. The controls that must hold are transforms on
the data, not sentences in a prompt (pattern 03). The injection suite knows a meta-instruction from a
relayed claim (pattern 04). Output is scrubbed on the way out.

Then the roadmap says: add voice. Or images. Or let people upload their own documents.

## Forces

**Routing the new modality through the reasoning core is the intuitive design.** *The model should hear
the tone. It should see the layout. It should understand the document, not just its text.* Each is a
real capability, and each argues for putting the new input inside the loop.

**None of the text path's properties transfer automatically.** Grounding, citation discipline, injection
resistance, egress scrubbing — each was earned separately, against a specific medium, by a specific
mechanism. Not one is a property of "the system."

**Edge placement looks like under-building.** A component that only transcribes, or only speaks, reads
as a thin wrapper — and the modality is the demo, so the version that does more wins the design review.

## The Refusal

**Add a new modality at the edges of the verified pipeline, never inside it. It may change how input
arrives and how output is delivered. It may not change what the system decides or says.**

- **Speech-to-text deposits a transcript, and the transcript is the interface.** It enters the pipeline
  exactly as if typed; nothing downstream can tell it came from audio, or behaves differently because
  it did.
- **Text-to-speech reads output that has already cleared every gate** — grounding, citations, egress
  scrub. It renders an approved string. It never generates, summarises, or rephrases for fluency.
- **Neither component is in the decision loop.** Neither gets its own prompt, its own retrieval, or its
  own opinion about what the user meant.

The diagnostic: **if I deleted the new modality entirely, would every answer be identical?** If yes, it
is at the edge. If no, every property you proved for text is an open question again in a medium where
you have proved nothing — and where your existing tests cannot express the new cases.

Edge placement is not a compromise accepted to ship faster. It is the reason the modality was cheap to
add safely: the verified pipeline was not modified, so it did not need re-verifying.

## Consequences

**The modality costs a component, not a re-audit.** Grounding, citation, and injection posture are
unchanged because the reasoning path is unchanged. That is the entire return on the discipline.

**Each new input channel is a fresh indirect-injection surface,** from the first commit. Text that
reaches the model as pixels or as audio is still text that reaches the model, and pattern 04 applies in
full. The corollary: your injection fixtures must now exist *in that medium*. A suite made entirely of
text files says nothing about the image path, however green.

**Some channels have no allow-list available.** Source governance — controlling what may enter context
at all — is the strongest answer to indirect injection, and for user uploads it is unavailable by
construction: the whole point is that the user chose the file. What remains is the class refusal of
pattern 02 at the parse boundary, deterministic transforms on the extracted text, and attribution of
anything derived from that file to that file.

**You give up modality-specific intelligence** — tone of voice, the layout of a scanned page, whatever
an image shows beyond its extractable text. Some products need it; needing it means budgeting for a
second hardening effort in that medium, not skipping one.

**Transduction errors become content errors** — a misheard word is a wrong word in a real question, and
nothing downstream knows it was uncertain (pattern 10).

## The naive approach it beats

**Hand the multimodal model the raw input and let it reason over everything together.** Pass the audio,
the image, the document bytes. The model accepts them natively, so integration is nearly free — and it
is strictly more capable, since nothing was thrown away.

It fails for one mechanical reason: **your controls are text transforms, and there is no longer a text
field for them to operate on.** An instruction rendered as pixels in a screenshot, or spoken into an
uploaded recording, never becomes a string your scrubber inspects before it becomes tokens the model
attends to. The scrubber runs, finds an empty field, and passes. The class refusal of pattern 02 was
written against MIME types and URL schemes, and images are allowed because images are the feature. The
suite from pattern 04 stays green because every fixture in it is text — so the newest surface in the
system is the one it does not cover.

Two tells:

- **The green suite did not change when the modality shipped.** If a new input channel required no new
  fixtures, the channel is untested, not safe.
- **Someone says "the model is multimodal now, so it handles it."** Multimodal means the model accepts
  the input. It says nothing about whether anything you built around the model understands it.

## Prior art

- Bagdasaryan et al., *Abusing Images and Sounds for Indirect Instruction Injection in Multi-Modal LLMs*
  — [arXiv:2307.10490](https://arxiv.org/abs/2307.10490). Instructions delivered through non-text
  channels, arriving without passing anything that inspects text.
- Carlini et al., *Are aligned neural networks adversarially aligned?* —
  [arXiv:2306.15447](https://arxiv.org/abs/2306.15447). Attacks that fail against the text interface
  succeed through the image one: properties proved on the text path do not transfer.
- Bailey et al., *Image Hijacks: Adversarial Images can Control Generative Models at Runtime* —
  [arXiv:2309.00236](https://arxiv.org/abs/2309.00236). A modality inside the reasoning loop is a
  control channel, not merely an input.
- Carlini & Wagner, *Audio Adversarial Examples: Targeted Attacks on Speech-to-Text* —
  [arXiv:1801.01944](https://arxiv.org/abs/1801.01944). The edge transducer is itself attackable; edge
  placement bounds the damage to a wrong transcript rather than a compromised decision.

## Specimen

[`specimens/09-modality-surface/`](../specimens/09-modality-surface/) — **built.**
Measured output in [`RESULTS.md`](../specimens/09-modality-surface/RESULTS.md).

Specimen 04's corpus, guardrail wording and questions, byte-identical (asserted by test), with the
poison delivered as rendered images instead of text. Four models, two vendors, 103 completions.

**The section above was confirmed exactly, and one thing this entry implied was wrong.**

| | text | image |
|---|---|---|
| meta-injection | REFUSED | **REFUSED** |
| content-relay | RELAYED | RELAYED |
| ingress scanner fires | 100% | **0%** |
| specimen 04's suite covers it | yes | **no — 12 passed, 0 failed, 0 cells** |

**Model-layer posture transferred completely.** 24/24 meta-injection refusals through pixels, both
vendors, including text rendered as unreadable fine print. No model ever emitted the injected token.
This entry's rhetoric implies guardrails failing on the new channel; they did not, and that framing
should not be repeated. **The failure is in your code, not in the model.**

**Code-layer controls transferred not at all** — exactly as the naive-approach section predicts. The
scanner has no defect; a test feeds it the payload as characters and requires it to fire. There is
simply no longer a string to read. The bytes contain no matchable text and the PNG carries no `tEXt`
chunk.

**And one in-model control silently vanished.** One model spontaneously warned the reader that the
documented procedure looked like phishing — in 7 of 10 text trials and **0 of 20 image trials**
(Fisher exact, p ≈ 5.9 × 10⁻⁵). Both channels scored RELAYED; only one warned. The verdict matrix
could not see it. It was caught only because raw answers were persisted and re-scored later on a
dimension that did not exist when the calls were made — which is the argument for
[persisting per-item records](../CLAUDE.md) stated as a finding rather than a preference.
