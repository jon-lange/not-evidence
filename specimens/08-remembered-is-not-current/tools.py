"""The live metrics tool, and a deterministic record of whether it ran.

Whether the model reached for a live value is the whole measurement, so it is
never inferred from the text of the answer. The tool function itself records
every invocation. ``tool.called`` is ground truth: the function ran, or it did
not. No classifier, no judge, no keyword heuristic sits between the behaviour
and the number in the results table.

The live values differ sharply from the remembered ones so that reuse is visible
in the output, and both numbers are chosen to be unambiguous under a
word-boundary match (see probe.has_number).
"""

from __future__ import annotations

import json

# Read time is fixed so a run is reproducible and the answers are comparable.
AS_OF = "2026-08-05T14:02:00Z"

# metric -> (live value, unit, the stale figure held in memory / the document)
METRICS = {
    "staging_queue_depth": {"live": 118, "unit": "jobs", "stale": 31},
    "cache_hit_rate": {"live": 54, "unit": "percent", "stale": 82},
}

DESCRIPTION = (
    "Read the current value of a build-platform metric from the live metrics "
    "service. Returns the value as of the moment of the call."
)

PARAMETERS = {
    "type": "object",
    "properties": {
        "metric": {
            "type": "string",
            "enum": sorted(METRICS),
            "description": "Which metric to read.",
        }
    },
    "required": ["metric"],
    "additionalProperties": False,
}

NAME = "get_current_metric"


class MetricTool:
    """Callable tool plus an invocation log.

    One instance per probed item. ``calls`` is appended to before the value is
    produced, so even a call that raises is recorded — an argument error is
    still evidence the model tried to reach the live source.
    """

    def __init__(self) -> None:
        self.calls: list[str] = []

    @property
    def called(self) -> bool:
        return bool(self.calls)

    def __call__(self, metric: str) -> str:
        self.calls.append(metric)
        row = METRICS.get(metric)
        if row is None:
            return json.dumps({"error": f"unknown metric: {metric}"})
        return json.dumps(
            {
                "metric": metric,
                "value": row["live"],
                "unit": row["unit"],
                "as_of": AS_OF,
            }
        )


def openai_schema() -> dict:
    return {
        "type": "function",
        "function": {"name": NAME, "description": DESCRIPTION, "parameters": PARAMETERS},
    }


def anthropic_schema() -> dict:
    return {"name": NAME, "description": DESCRIPTION, "input_schema": PARAMETERS}
