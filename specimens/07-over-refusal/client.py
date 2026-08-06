"""One completion, normalised across both vendors.

Same shape as specimen 05's judge.py — a single ``complete(model, ...)`` that
dispatches on model name — but hardened for the model quirks this specimen ran
into on 2026-08-05, because the whole point here is to run *old and new* models
from each family side by side and the newest ones have moved the API surface:

  * Newer OpenAI models reject ``max_tokens`` and require
    ``max_completion_tokens``. The latter is accepted by the older models too,
    so we always send it.
  * ``claude-sonnet-5`` (and its generation) reject ``temperature`` outright:
    "temperature is deprecated for this model". Older Claude models still take
    it. We send ``temperature=0`` and, on that specific rejection, retry
    without it.

Both fallbacks are narrow and logged via the returned ``meta`` so a silently
degraded call can never be mistaken for a clean one. A call that fails for any
other reason raises — a refusal must never be confused with an API error, so we
do not swallow errors and return empty strings.
"""

from __future__ import annotations

import os

# Generous output budget. Newer OpenAI models are reasoning models that spend
# completion tokens on hidden reasoning before emitting any text; too small a
# budget yields an empty string that would misclassify as a refusal.
MAX_OUT = 1024


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


def _complete_anthropic(model: str, system: str, user: str) -> tuple[str, dict]:
    from anthropic import Anthropic

    key = _read_key("~/.config/anthropic-key", "ANTHROPIC_API_KEY")
    client = Anthropic(api_key=key)
    kwargs = dict(model=model, max_tokens=MAX_OUT, system=system,
                  messages=[{"role": "user", "content": user}])
    meta = {"temperature_dropped": False}
    try:
        resp = client.messages.create(temperature=0, **kwargs)
    except Exception as exc:  # noqa: BLE001 — narrow re-raise below
        if "temperature" in str(exc).lower() and "deprecated" in str(exc).lower():
            meta["temperature_dropped"] = True
            resp = client.messages.create(**kwargs)
        else:
            raise
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    meta["stop_reason"] = resp.stop_reason
    return text, meta


def _complete_openai(model: str, system: str, user: str) -> tuple[str, dict]:
    from openai import OpenAI

    key = _read_key("~/.config/openai-key", "OPENAI_API_KEY")
    client = OpenAI(api_key=key, base_url=os.environ.get("LLM_BASE_URL") or None)
    kwargs = dict(
        model=model,
        max_completion_tokens=MAX_OUT,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    meta = {"temperature_dropped": False}
    try:
        resp = client.chat.completions.create(temperature=0, **kwargs)
    except Exception as exc:  # noqa: BLE001 — narrow re-raise below
        if "temperature" in str(exc).lower():
            meta["temperature_dropped"] = True
            resp = client.chat.completions.create(**kwargs)
        else:
            raise
    text = (resp.choices[0].message.content or "").strip()
    meta["finish_reason"] = resp.choices[0].finish_reason
    return text, meta


def complete(model: str, system: str, user: str) -> tuple[str, dict]:
    """Return (text, meta). Raises on any API error other than the two known
    parameter incompatibilities, which are handled and recorded in meta."""
    if family(model) == "anthropic":
        return _complete_anthropic(model, system, user)
    return _complete_openai(model, system, user)
