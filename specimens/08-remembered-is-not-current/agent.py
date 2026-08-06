"""A minimal tool-using agent, normalised across both vendors.

Same shape as specimen 07's client.py — one ``run(model, ...)`` that dispatches
on model name — extended into a short tool loop, because this specimen has to
observe whether a tool was *invoked*, not merely whether one was offered.

Two vendor quirks carried over from specimen 07, both narrow and both recorded
in the returned ``meta`` so a degraded call can never pass as a clean one:

  * newer OpenAI models reject ``max_tokens`` and want ``max_completion_tokens``,
    which the older ones accept too, so we always send the latter;
  * some newer models reject ``temperature`` outright, so we send 0 and retry
    without it on that specific rejection.

The loop is capped at two rounds. One round is enough to see the tool call; the
second exists only to let the model turn the tool result into an answer. A model
that wanted a third round would be doing something this specimen does not test.

Errors are never swallowed. An empty answer from a crashed call would be scored
as "did not use the remembered figure", which is the wrong conclusion drawn from
the right-looking data.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

import tools

MAX_OUT = 1024
MAX_ROUNDS = 2


@dataclass
class Turn:
    text: str
    tool_calls: list[str] = field(default_factory=list)
    rounds: int = 0
    meta: dict = field(default_factory=dict)


def family(model: str) -> str:
    return "anthropic" if model.startswith("claude") else "openai"


def _read_key(path: str, env: str) -> str | None:
    if os.environ.get(env):
        return os.environ[env]
    try:
        with open(os.path.expanduser(path)) as fh:
            return fh.read().strip() or None
    except OSError:
        return None


def have_key(fam: str) -> bool:
    if fam == "anthropic":
        return bool(_read_key("~/.config/anthropic-key", "ANTHROPIC_API_KEY"))
    return bool(_read_key("~/.config/openai-key", "OPENAI_API_KEY"))


# ── OpenAI ───────────────────────────────────────────────────────────────────

def _run_openai(model: str, system: str, user: str, tool: tools.MetricTool) -> Turn:
    from openai import OpenAI

    client = OpenAI(
        api_key=_read_key("~/.config/openai-key", "OPENAI_API_KEY"),
        base_url=os.environ.get("LLM_BASE_URL") or None,
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    meta = {"temperature_dropped": False, "finish_reason": None}

    def create():
        kwargs = dict(
            model=model,
            max_completion_tokens=MAX_OUT,
            messages=messages,
            tools=[tools.openai_schema()],
        )
        try:
            return client.chat.completions.create(temperature=0, **kwargs)
        except Exception as exc:  # noqa: BLE001 — narrow re-raise
            if "temperature" in str(exc).lower():
                meta["temperature_dropped"] = True
                return client.chat.completions.create(**kwargs)
            raise

    for rounds in range(1, MAX_ROUNDS + 1):
        resp = create()
        msg = resp.choices[0].message
        meta["finish_reason"] = resp.choices[0].finish_reason
        if not msg.tool_calls:
            return Turn((msg.content or "").strip(), list(tool.calls), rounds, meta)

        messages.append(
            {
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ],
            }
        )
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": tool(args.get("metric", "")),
                }
            )

    meta["hit_round_cap"] = True
    return Turn("", list(tool.calls), MAX_ROUNDS, meta)


# ── Anthropic ────────────────────────────────────────────────────────────────

def _run_anthropic(model: str, system: str, user: str, tool: tools.MetricTool) -> Turn:
    from anthropic import Anthropic

    client = Anthropic(api_key=_read_key("~/.config/anthropic-key", "ANTHROPIC_API_KEY"))
    messages: list[dict] = [{"role": "user", "content": user}]
    meta = {"temperature_dropped": False, "stop_reason": None}

    def create():
        kwargs = dict(
            model=model,
            max_tokens=MAX_OUT,
            system=system,
            messages=messages,
            tools=[tools.anthropic_schema()],
        )
        try:
            return client.messages.create(temperature=0, **kwargs)
        except Exception as exc:  # noqa: BLE001 — narrow re-raise
            if "temperature" in str(exc).lower():
                meta["temperature_dropped"] = True
                return client.messages.create(**kwargs)
            raise

    for rounds in range(1, MAX_ROUNDS + 1):
        resp = create()
        meta["stop_reason"] = resp.stop_reason
        uses = [b for b in resp.content if b.type == "tool_use"]
        if not uses:
            text = "".join(b.text for b in resp.content if b.type == "text").strip()
            return Turn(text, list(tool.calls), rounds, meta)

        messages.append({"role": "assistant", "content": resp.content})
        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": u.id,
                        "content": tool(u.input.get("metric", "")),
                    }
                    for u in uses
                ],
            }
        )

    meta["hit_round_cap"] = True
    return Turn("", list(tool.calls), MAX_ROUNDS, meta)


def run(model: str, system: str, user: str, tool: tools.MetricTool) -> Turn:
    """One item against one model. The tool instance is the invocation record."""
    if family(model) == "anthropic":
        return _run_anthropic(model, system, user, tool)
    return _run_openai(model, system, user, tool)
