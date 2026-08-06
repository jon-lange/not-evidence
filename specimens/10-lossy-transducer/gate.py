"""The signal gate — refuse to send a clip that never reached speech level.

This is the mitigation, and it sits *before* the model rather than after it.
That placement is the whole point: a hallucinated transcript is fluent,
well-formed and on-topic, so there is no property of the output to filter on.
The only place the failure is still detectable is the input.

Deliberately absolute rather than adaptive. A fixed threshold is the wrong
long-term answer — noise floors vary by tens of dB across environments, and a
fixed value will be deaf in one room and permissive in another. That is a
separate pattern. Here the fixed gate is the honest starting point, and naming
its limitation is part of the specimen.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import audio

# Peak, not average. A short utterance in a quiet room has a low average level
# and a high peak; averaging would reject real speech.
SPEECH_PEAK_FLOOR_DBFS = -40.0


@dataclass(frozen=True)
class GateResult:
    allowed: bool
    peak_dbfs: float
    reason: str


def gate(path: Path, floor_dbfs: float = SPEECH_PEAK_FLOOR_DBFS) -> GateResult:
    """Decide whether a clip is worth sending to a transcriber."""
    peak = audio.peak_dbfs(path)

    if peak == float("-inf"):
        return GateResult(False, peak, "no signal at all")
    if peak < floor_dbfs:
        return GateResult(
            False, peak, f"peak {peak:.1f} dBFS never reached the {floor_dbfs:.0f} dBFS floor"
        )
    return GateResult(True, peak, "reached speech level")
