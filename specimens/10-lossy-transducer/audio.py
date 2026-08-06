"""Audio synthesis and level measurement. Standard library only.

Everything here exists so the specimen can generate its own inputs. Nothing is
loaded from a fixture, which keeps the demonstration reproducible and keeps this
directory free of recordings whose provenance a reader would have to trust.
"""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 16_000
SAMPLE_WIDTH = 2  # 16-bit PCM
FULL_SCALE = 32_767


def _write_wav(path: Path, samples: list[int]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(SAMPLE_WIDTH)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(b"".join(struct.pack("<h", s) for s in samples))
    return path


def digital_silence(path: Path, seconds: float = 3.0) -> Path:
    """Exactly zero. Not 'quiet' — no signal at all."""
    return _write_wav(path, [0] * int(SAMPLE_RATE * seconds))


def room_tone(path: Path, seconds: float = 3.0, peak_dbfs: float = -60.0) -> Path:
    """Near-silence: a low-level deterministic hiss.

    This is what a real microphone in a quiet room produces. It is the input a
    naive 'is the buffer empty?' check passes straight through, which is why the
    gate in this specimen measures level rather than emptiness.

    Deterministic by construction — a linear congruential generator rather than
    `random`, so two runs on two machines produce identical bytes.
    """
    amplitude = FULL_SCALE * (10 ** (peak_dbfs / 20.0))
    n = int(SAMPLE_RATE * seconds)
    state = 12345
    samples = []
    for _ in range(n):
        state = (1103515245 * state + 12345) % (1 << 31)
        samples.append(int(((state / (1 << 31)) * 2.0 - 1.0) * amplitude))
    return _write_wav(path, samples)


def spoken_tone(path: Path, seconds: float = 3.0, nominal_dbfs: float = -12.0) -> Path:
    """A speech-level signal.

    A sum of harmonics under an envelope. It is not speech and will not
    transcribe to words — it stands in for 'something at speaking volume is
    present', which is the only property the gate is entitled to assert.

    `nominal_dbfs` scales the harmonic sum; the achieved peak lands a few dB
    below it, because the harmonics do not align in phase. Measure with
    `peak_dbfs()` rather than assuming this value — that is the whole habit
    this repository is about.
    """
    amplitude = FULL_SCALE * (10 ** (nominal_dbfs / 20.0))
    n = int(SAMPLE_RATE * seconds)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        envelope = 0.5 * (1 - math.cos(2 * math.pi * min(t / 0.05, 1.0)))
        value = (
            math.sin(2 * math.pi * 140 * t) * 0.6
            + math.sin(2 * math.pi * 280 * t) * 0.3
            + math.sin(2 * math.pi * 560 * t) * 0.1
        )
        samples.append(int(value * envelope * amplitude))
    return _write_wav(path, samples)


def peak_dbfs(path: Path) -> float:
    """Peak level in dBFS. Returns -inf for digital silence."""
    with wave.open(str(path), "rb") as w:
        frames = w.readframes(w.getnframes())
    if not frames:
        return float("-inf")
    peak = max(abs(s) for (s,) in struct.iter_unpack("<h", frames))
    if peak == 0:
        return float("-inf")
    return 20.0 * math.log10(peak / FULL_SCALE)
