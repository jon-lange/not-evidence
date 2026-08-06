# Observed results

**Run 2026-08-05.** Three hosted transcription models, three synthetic inputs, each sent bare and
with a recipe-vocabulary hint. Every cell reproduced identically across three consecutive runs —
these models are effectively deterministic at default settings.

None of the three inputs contains speech. The correct output for every cell is empty.

## Bare — no hint

| Input | `whisper-1` | `gpt-4o-transcribe` | `gpt-4o-mini-transcribe` |
|---|---|---|---|
| digital silence | `'you'` | `'きっとそうね。'` | `''` |
| room tone (−60 dBFS) | `'.'` | `'こんにちは'` | `''` |
| speech-level tone | `'you'` | `'Foxglove'` | `''` |

## With a recipe-vocabulary hint

| Input | `whisper-1` | `gpt-4o-transcribe` | `gpt-4o-mini-transcribe` |
|---|---|---|---|
| digital silence | `''` | *hint echoed verbatim* | *hint echoed verbatim* |
| room tone (−60 dBFS) | `"Merci d'avoir regardé!"` | `'context:'` | *hint echoed verbatim* |
| speech-level tone | `'❤️ par SousTitreur.com'` | *hint echoed, prefix dropped* | `'Mise en place.'` |

## What this shows

**1. All three models invent content from non-speech.** Only `gpt-4o-mini-transcribe` returns empty
when unprompted, and it stops doing so the moment a hint is supplied.

**2. `whisper-1` hallucinates training-data artifacts.** *"Merci d'avoir regardé!"* — "thanks for
watching" — and a French subtitling service credit are boilerplate from subtitle corpora. Visibly
wrong, and filterable precisely because they are absurd in context.

**3. The `gpt-4o` models echo the hint back as transcript.** Given silence and a vocabulary hint,
both return the hint text as though someone had spoken it. The prompt becomes the output.

**4. The most dangerous single cell is `'Mise en place.'`** A verbatim echo of a ten-term vocabulary
list is conspicuous — no one says that aloud. A short, fluent, grammatical, on-topic phrase drawn
from that list is indistinguishable from a real transcription. It is the same failure wearing a
disguise, and it is the one that would auto-send.

**5. The level gate is necessary but not sufficient.** The speech-level tone cleared the −40 dBFS
floor and still produced `'Foxglove'`, `'❤️ par SousTitreur.com'`, and `'Mise en place.'`. Signal
presence is not speech presence. The gate removes the empty-input case; it does not make the
transducer trustworthy.

**6. Behaviour varies enormously across models from one vendor.** Japanese, French, English,
silence, and echo — same inputs, same day. Any claim of the form *"transcription models do X"*
that rests on one model is unsupported. Including the claim this specimen originally made.

## What was tested and did not reproduce

The original write-up of this specimen predicted that **a domain hint would make hallucinations
fluent and on-topic**, and that this was the hint's real cost.

On `whisper-1` that is **false**. The English recipe hint produced *French subtitle boilerplate* —
less on-topic than the bare output — and on digital silence it produced empty output, which is
strictly safer than the bare `'you'`.

On the `gpt-4o` models the prediction was **directionally right but mechanically wrong**. Hints do
corrupt the output, but by being *echoed*, not by shaping a plausible invention. Only one cell of
nine — `'Mise en place.'` — matches what was predicted.

The revised claim is narrower and better supported: **supplying a hint to a generative transducer
gives it material to emit when there is nothing to transcribe, and at least one model will emit
your own prompt back at you as speech.**

## Reproducing

```bash
export OPENAI_API_KEY=...
./.venv/bin/python probe.py                              # whisper-1
STT_MODEL=gpt-4o-transcribe ./.venv/bin/python probe.py
STT_MODEL=gpt-4o-mini-transcribe ./.venv/bin/python probe.py
```

Roughly 18 seconds of audio per model — a fraction of a cent per run.

## Scope

Three models, one vendor, one hint, three synthetic inputs, one day. This establishes that the
failure exists and that it varies by model. It does not establish bounds, and it says nothing about
other vendors or about real speech in noisy conditions.
