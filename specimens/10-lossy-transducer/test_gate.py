"""Tests for the gate and the synthesis it depends on.

Run: python3 -m pytest test_gate.py -q   (or: python3 test_gate.py)

No network. The live probe is exercised by hand — mocking a transcription API
would only prove that the mock returns what it was told to, which is the class
of green result this repository exists to distrust.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import audio
from gate import SPEECH_PEAK_FLOOR_DBFS, gate

TMP = Path(__file__).parent / "_generated" / "test"


def test_digital_silence_is_refused():
    r = gate(audio.digital_silence(TMP / "s.wav", seconds=0.5))
    assert not r.allowed
    assert r.peak_dbfs == float("-inf")
    assert "no signal" in r.reason


def test_room_tone_is_refused():
    """Near-silence is the case an is-the-buffer-empty check waves through."""
    r = gate(audio.room_tone(TMP / "r.wav", seconds=0.5, peak_dbfs=-60.0))
    assert not r.allowed
    assert r.peak_dbfs < SPEECH_PEAK_FLOOR_DBFS


def test_speech_level_passes():
    r = gate(audio.spoken_tone(TMP / "t.wav", seconds=0.5))
    assert r.allowed
    assert r.peak_dbfs > SPEECH_PEAK_FLOOR_DBFS


def test_boundary_just_below_floor_is_refused():
    r = gate(audio.room_tone(TMP / "b.wav", seconds=0.5, peak_dbfs=SPEECH_PEAK_FLOOR_DBFS - 2))
    assert not r.allowed


def test_synthesis_is_deterministic():
    """Two runs must produce identical bytes, or the specimen is not reproducible."""
    a = audio.room_tone(TMP / "d1.wav", seconds=0.25).read_bytes()
    b = audio.room_tone(TMP / "d2.wav", seconds=0.25).read_bytes()
    assert a == b


def test_missing_api_key_exits_cleanly():
    """No key must produce guidance and exit 2 — never a traceback."""
    proc = subprocess.run(
        [sys.executable, "probe.py"],
        cwd=Path(__file__).parent,
        env={"PATH": "/usr/bin:/bin"},  # deliberately no OPENAI_API_KEY
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert "Traceback" not in proc.stderr
    assert "--offline" in proc.stderr


def test_offline_mode_needs_no_key_and_no_network():
    proc = subprocess.run(
        [sys.executable, "probe.py", "--offline"],
        cwd=Path(__file__).parent,
        env={"PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "REFUSED" in proc.stdout
    assert "PASS" in proc.stdout


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS  {name}")
            except AssertionError as exc:
                failures += 1
                print(f"  FAIL  {name}: {exc}")
    print(f"\n{failures} failure(s)")
    raise SystemExit(1 if failures else 0)
