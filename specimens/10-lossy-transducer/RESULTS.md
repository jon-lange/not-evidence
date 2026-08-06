# Observed results

**Adjudication: narrowed.** The central claim held emphatically — all three models invented content
from inputs containing no speech. The predicted *mechanism* did not: a domain hint was expected to
make hallucinations fluent and on-topic, and instead one model returned French subtitle boilerplate
and two echoed the prompt back as speech. The revised claim is narrower and better supported.

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

## What would falsify pattern 10

The entry's claim is that a lossy transducer's output must reach a review buffer rather than an
execution path, and the revised specimen claim is that a hint gives the transducer material to emit
when there is nothing to transcribe.

**Falsify the invention result:** a transcription model that returns empty for all three non-speech
inputs, bare *and* hinted, reproduced across runs. One such model does not overturn the pattern —
`gpt-4o-mini-transcribe` already returns empty when unprompted and stops the moment a hint arrives —
but a model that holds empty under a hint would show the failure is a vendor defect rather than a
property of generative transduction. If most current models did that, the pattern is arguing about a
fixed bug.

**Falsify the auto-commit refusal, which is the load-bearing claim:** a gate that reliably separates
invented output from real transcription without a human in the path. This run measured a level gate
as necessary and not sufficient — the speech-level tone cleared −40 dBFS and still produced
`'Mise en place.'`. A confidence score, a logprob threshold, or a second transducer used as a check,
shown to catch the invented cells while passing genuine speech, would make auto-commit defensible at
some risk tier and narrow the pattern to the tiers above it.

**What would not falsify it:** better average accuracy. The pattern is about the consequence of the
single wrong commit, not about the rate, and `'Mise en place.'` is the cell that matters precisely
because it is short, fluent, grammatical, on-topic, and indistinguishable from a real result.

**Not runnable from the recorded data.** Both conditions above need new calls — a different model set
for the first, and a scoring signal this harness does not currently capture for the second. Unlike
07's, this falsification cannot be re-derived from `results.jsonl` by re-classifying.
