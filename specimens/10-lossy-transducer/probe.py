"""Specimen 10 — a generative transducer invents content from silence.

Sends three inputs to a speech-to-text model, each twice: once bare, once with a
domain vocabulary hint. Prints what came back.

The finding is not that silence transcribes badly. It is that with a domain hint
configured, silence transcribes into fluent, on-topic, *plausible* text — output
that no downstream filter can distinguish from a real transcript, because there
is nothing wrong with it except that nobody said it.

Usage:
    export OPENAI_API_KEY=...
    python probe.py                 # send to the API
    python probe.py --offline       # generate inputs and run the gate only

Reference implementation. Not maintained.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import audio
from gate import GateResult, gate

OUT = Path(__file__).parent / "_generated"

# A generic domain, chosen deliberately. A hint drawn from a regulated vertical
# would make this specimen a claim about a particular system rather than a
# general property of generative transducers.
DOMAIN_HINT = (
    "Recipe terms: mise en place, deglaze, emulsify, blanch, chiffonade, "
    "roux, sous vide, proofing, tempering, reduction."
)

MODEL = os.environ.get("STT_MODEL", "whisper-1")


def transcribe(path: Path, hint: str | None) -> str:
    from openai import OpenAI

    client = OpenAI(base_url=os.environ.get("STT_BASE_URL") or None)
    kwargs = {"model": MODEL, "file": path.open("rb")}
    if hint:
        # The vendor calls this a prompt. It biases decoding toward the supplied
        # vocabulary — which is exactly what makes a hallucination plausible.
        kwargs["prompt"] = hint
    try:
        return client.audio.transcriptions.create(**kwargs).text.strip()
    except Exception as exc:  # noqa: BLE001 — surface provider errors verbatim
        return f"<error: {type(exc).__name__}: {exc}>"


def render(label: str, result: GateResult, bare: str | None, hinted: str | None) -> None:
    level = "-inf" if result.peak_dbfs == float("-inf") else f"{result.peak_dbfs:6.1f}"
    print(f"\n{label}")
    print(f"  peak            {level} dBFS")
    print(f"  gate            {'PASS — sent' if result.allowed else 'REFUSED — ' + result.reason}")
    if bare is not None:
        print(f"  bare            {bare!r}")
    if hinted is not None:
        print(f"  with hint       {hinted!r}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--offline", action="store_true", help="generate inputs and gate only")
    args = ap.parse_args()

    online = not args.offline
    if online and not os.environ.get("OPENAI_API_KEY"):
        print(
            "No OPENAI_API_KEY set.\n"
            "  Set one to run the transcription probe, or use --offline to\n"
            "  generate the inputs and exercise the gate without any API calls.",
            file=sys.stderr,
        )
        return 2

    cases = [
        ("digital silence (3s)", audio.digital_silence(OUT / "silence.wav")),
        ("room tone (3s, -60 dBFS)", audio.room_tone(OUT / "room.wav")),
        ("speech-level signal (3s)", audio.spoken_tone(OUT / "tone.wav")),
    ]

    print(f"model: {MODEL}   mode: {'live' if online else 'offline'}")
    print("=" * 68)

    for label, path in cases:
        result = gate(path)
        bare = hinted = None
        if online:
            # Deliberately transcribe even when the gate refused. The point of
            # the specimen is to show what the gate is protecting you from; a
            # real system would stop at the refusal.
            bare = transcribe(path, hint=None)
            hinted = transcribe(path, hint=DOMAIN_HINT)
        render(label, result, bare, hinted)

    print("\n" + "=" * 68)
    print(
        "None of these inputs contains speech. Every correct output is empty.\n"
        "\n"
        "  Bare, hallucinations tend to be training-data artifacts — subtitle\n"
        "  boilerplate, stray phrases in other languages. Absurd in context, and\n"
        "  therefore catchable.\n"
        "\n"
        "  With a hint, some models return the hint itself as though it had been\n"
        "  spoken. A verbatim echo of a vocabulary list is conspicuous; one\n"
        "  plausible phrase drawn from it is not, and that is the case that would\n"
        "  auto-send. Measure whether a hint helps on YOUR real input before\n"
        "  accepting it.\n"
        "\n"
        "  The gate refuses clips that never reach speech level. It sits before the\n"
        "  model because by the time there is output there is nothing left to filter\n"
        "  on — the text is fine. But note the third row: signal presence is not\n"
        "  speech presence, so the gate is necessary and not sufficient.\n"
        "\n"
        "  Measured results across three models: RESULTS.md"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
