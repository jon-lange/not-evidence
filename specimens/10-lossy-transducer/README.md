# Specimen 10 — a generative transducer invents content from silence

Demonstrates [pattern 10 · Never Auto-Commit a Lossy Transducer](../../patterns/10-never-auto-commit-a-transducer.md).

Sends three inputs to a speech-to-text model, each twice — once bare, once with a domain vocabulary
hint — and prints what comes back.

## The finding

Silence does not transcribe to nothing. It transcribes to *something*, because a generative
recogniser is obliged to produce output and will produce it from whatever is there.

Bare, that output is usually incoherent — visibly wrong, and therefore filterable.

**With a domain hint configured, it becomes fluent, on-topic, and plausible.** At that point no
transcript-side check can distinguish it from something a person actually said. There is nothing
wrong with the text except that nobody uttered it.

That is the trade the hint really makes. It is sold as an accuracy feature, and its cost is that it
converts a detectable failure into an undetectable one. **Measure whether it improves accuracy on
your own real input before accepting it** — if it doesn't, it is pure liability.

## Why the mitigation is on the input side

The gate refuses to send a clip whose peak never reaches speech level. It sits *before* the model,
and it has to, because by the time there is output there is nothing left to filter on.

This generalises past audio: it applies to any lossy or generative transducer whose failure mode is
a **plausible substitution** rather than visible garbling. A mis-heard proper noun produces a
confident, well-formed answer about the wrong entity — indistinguishable from a correct one.

## Run it

```bash
python3 probe.py --offline        # generates inputs, exercises the gate, no network, no key
pip install -r requirements.txt
export OPENAI_API_KEY=...
python3 probe.py                  # live probe
```

Offline output:

```
digital silence (3s)
  peak            -inf dBFS
  gate            REFUSED — no signal at all

room tone (3s, -60 dBFS)
  peak             -60.2 dBFS
  gate            REFUSED — peak -60.2 dBFS never reached the -40 dBFS floor

speech-level signal (3s)
  peak             -15.0 dBFS
  gate            PASS — sent
```

Swap providers with `STT_MODEL` and `STT_BASE_URL`; any OpenAI-compatible transcription endpoint
works.

## Tests

```bash
python3 test_gate.py              # or: python3 -m pytest test_gate.py -q
```

Seven tests, no network. The live transcription path is exercised by hand rather than mocked — a
mocked transcriber only proves the mock returns what it was told to, which is the class of green
result this repository exists to distrust.

**These tests are mutation-checked.** Two deliberate breakages were introduced and confirmed to fail
them:

| Mutation | Tests failed |
|---|---|
| Gate always allows | 4 |
| Peak measured as mean instead of maximum | 2 |

The second matters more than it looks: averaging passes room tone, because a short utterance in a
quiet room has a low mean and a high peak. A gate built on the mean would be both too permissive
here and too strict on real speech.

## What this specimen deliberately does not do

**It uses a fixed threshold, and a fixed threshold is the wrong long-term answer.** Noise floors
vary by tens of dB across environments; a value that works in an office is deaf in a car and
permissive in a studio. The honest version is an adaptive detector with the fixed one as a degraded
fallback. That is a different pattern, and pretending this gate is finished would be the same
over-claiming the catalogue argues against.

**It does not generate real speech.** `spoken_tone` is a harmonic sum, not language — it stands in
for *something at speaking volume is present*, which is the only property the gate is entitled to
assert. Every input is synthesised in-process, so nothing here is a recording whose provenance you
would have to take on trust.

**One probe is not a battery.** This exercises one provider, one hint, three inputs. It establishes
that the failure exists, not its bounds.

---

Reference implementation. Not maintained.
