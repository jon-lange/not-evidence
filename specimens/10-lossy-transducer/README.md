# Specimen 10 — generative transducers invent content from silence

Demonstrates [pattern 10 · Never Auto-Commit a Lossy Transducer](../../patterns/10-never-auto-commit-a-transducer.md).

Sends three synthetic inputs — digital silence, room tone, and a speech-level tone — to a
transcription model, each bare and each with a domain vocabulary hint. **None of them contains
speech. The correct output for every cell is empty.**

Measured output across three models: **[RESULTS.md](RESULTS.md)**.

## The finding

**Silence does not transcribe to nothing.** A generative recogniser is obliged to produce output and
will produce it from whatever is in its training distribution.

Bare, `whisper-1` returns `'you'` for digital silence and `"Merci d'avoir regardé!"` — *thanks for
watching* — for room tone. Those are subtitle-corpus artifacts: absurd in context, and therefore
catchable.

**Supply a domain hint and it stops being catchable.** Both `gpt-4o` transcription models return the
hint text itself as though it had been spoken. The worst cell in the matrix is
`gpt-4o-mini-transcribe` returning `'Mise en place.'` for a tone containing no speech — short,
fluent, grammatical, on-topic, and completely indistinguishable from a real transcription. A
verbatim echo of a ten-term vocabulary list is conspicuous. One plausible phrase from it is not.

**And the level gate is necessary but not sufficient.** The speech-level tone cleared the −40 dBFS
floor and still produced `'Foxglove'` and `'Mise en place.'`. Signal presence is not speech presence.

## Why the mitigation is on the input side

The gate refuses to send a clip whose peak never reaches speech level. It sits *before* the model,
and it has to, because by the time there is output there is nothing left to filter on — the text is
fine. What was lost is the knowledge that the input contained no speech.

This generalises past audio to any lossy or generative transducer whose failure mode is a
**plausible substitution** rather than visible garbling. A mis-read proper noun produces a
confident, well-formed answer about the wrong entity.

## Run it

```bash
python3 probe.py --offline                    # inputs + gate only; no key, no network
pip install -r requirements.txt
export OPENAI_API_KEY=...
python3 probe.py                              # live, whisper-1
STT_MODEL=gpt-4o-transcribe python3 probe.py  # any OpenAI-compatible endpoint via STT_BASE_URL
```

About 18 seconds of audio per run — a fraction of a cent.

Offline output:

```
digital silence (3s)        peak  -inf dBFS   REFUSED — no signal at all
room tone (3s, -60 dBFS)    peak -60.2 dBFS   REFUSED — never reached the -40 dBFS floor
speech-level signal (3s)    peak -15.0 dBFS   PASS — sent
```

## Tests

```bash
python3 test_gate.py          # or: python3 -m pytest test_gate.py -q
```

Seven tests, no network. The live path is exercised by hand rather than mocked — a mocked
transcriber only proves the mock returns what it was told to.

**Mutation-checked.** Two deliberate breakages, both caught:

| Mutation | Tests failed |
|---|---|
| Gate always allows | 4 |
| Peak measured as mean instead of maximum | 2 |

Averaging admits room tone, because a short utterance in a quiet room has a low mean and a high
peak — one defect that would present as two unrelated bugs.

## This specimen falsified its own pattern

The entry was written first, predicting that a domain hint would make hallucinations *fluent and
on-topic*. Across three models and nine cells, that reproduced in **one**. On `whisper-1` it was
flatly wrong: an English recipe hint produced French subtitle boilerplate, and on digital silence
the hint produced *empty* output — safer than the bare result.

The real mechanism is echo, not plausible invention. Pattern 10 was rewritten to the narrower claim
the evidence supports, and this paragraph stays as the record.

## What this specimen deliberately does not do

**The threshold is fixed, and fixed is wrong in the long run.** Noise floors vary by tens of dB
across environments; a value that works in an office is deaf in a car. The honest version is
adaptive with this as a degraded fallback.

**It does not generate real speech.** `spoken_tone` is a harmonic sum standing in for *something at
speaking volume is present* — the only property the gate is entitled to assert. Every input is
synthesised in-process, so nothing here is a recording whose provenance you must take on trust.

**Three models, one vendor, one hint, one day.** This establishes that the failure exists and that
it varies enormously by model. It does not establish bounds.

---

Reference implementation. Not maintained.
