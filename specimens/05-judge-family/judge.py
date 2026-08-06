"""Generation and judging, across two model families.

Two families is the minimum for this specimen to mean anything. Within a single
vendor you can measure that judges disagree; you cannot separate self-preference
from ordinary disagreement, because there is no lineage boundary to compare
across.

The rubric is deliberately ordinary — this specimen is about *who* judges, not
about rubric design. Anchors are observable ("names a specific mechanism")
rather than evaluative ("is good"), so two judges have a chance of agreeing for
the same reason rather than by coincidence.
"""

from __future__ import annotations

import json
import os
import re

RUBRIC = """Score the answer from 1 to 5 on each dimension.

accuracy    1 = contains a clear error
            3 = broadly correct, imprecise in places
            5 = correct, with no misleading simplification

mechanism   1 = restates the question or gives only an analogy
            3 = names the mechanism but does not explain how it produces the effect
            5 = explains the causal chain from mechanism to observed behaviour

commitment  1 = hedges throughout, never states a conclusion
            3 = states a conclusion but buries it
            5 = states the conclusion plainly and qualifies it only where warranted

Reply with JSON only: {"accuracy": n, "mechanism": n, "commitment": n}
No prose, no code fence."""

DIMENSIONS = ("accuracy", "mechanism", "commitment")

SYSTEM_ANSWER = "Answer the engineering question in at most 120 words."


def family(model: str) -> str:
    """Which lineage a model belongs to. The whole specimen turns on this."""
    return "anthropic" if model.startswith("claude") else "openai"


def _read_key(path: str, env: str) -> str | None:
    if os.environ.get(env):
        return os.environ[env]
    try:
        with open(os.path.expanduser(path)) as fh:
            return fh.read().strip() or None
    except OSError:
        return None


def _complete(model: str, system: str, user: str) -> str:
    """One completion, normalised across both SDKs."""
    if family(model) == "anthropic":
        from anthropic import Anthropic

        key = _read_key("~/.config/anthropic-key", "ANTHROPIC_API_KEY")
        resp = Anthropic(api_key=key).messages.create(
            model=model,
            max_tokens=512,
            temperature=0,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in resp.content if b.type == "text").strip()

    from openai import OpenAI

    key = _read_key("~/.config/openai-key", "OPENAI_API_KEY")
    resp = OpenAI(api_key=key, base_url=os.environ.get("LLM_BASE_URL") or None).chat.completions.create(
        model=model,
        temperature=0,
        max_tokens=512,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return (resp.choices[0].message.content or "").strip()


def generate(question: str, model: str) -> str:
    return _complete(model, SYSTEM_ANSWER, question)


def parse_scores(raw: str) -> dict[str, int] | None:
    """Extract per-dimension scores, or None if nothing usable came back.

    A judge that returns unparseable output is recorded as a gap, never defaulted
    to a middle score. An imputed 3 is indistinguishable from a real 3 once it
    reaches an aggregate, and it silently drags every comparison toward a tie.
    """
    match = re.search(r"\{.*?\}", raw, re.S)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if not all(d in parsed for d in DIMENSIONS):
        return None
    try:
        scores = {d: int(parsed[d]) for d in DIMENSIONS}
    except (TypeError, ValueError):
        return None
    if any(not 1 <= s <= 5 for s in scores.values()):
        return None
    return scores


def score(question: str, answer: str, judge_model: str) -> dict[str, int] | None:
    raw = _complete(judge_model, RUBRIC, f"Question:\n{question}\n\nAnswer:\n{answer}")
    return parse_scores(raw)


PAIRWISE = """You are comparing two answers to the same question.

Reply with JSON only: {"winner": "A"} or {"winner": "B"} or {"winner": "tie"}
Choose "tie" only if the answers are genuinely indistinguishable in quality.
No prose, no code fence."""


def compare(question: str, answer_a: str, answer_b: str, judge_model: str) -> str | None:
    """Pairwise preference. Returns 'A', 'B', 'tie', or None if unparseable.

    Pairwise exists because absolute scoring saturates: on a competent task set
    every answer earns full marks and the judge stops carrying information.
    Forcing a choice cannot hit a ceiling.

    Position bias is real and large in LLM judges, so callers must run both
    orders and combine. This function deliberately does not hide that — it
    reports one order, and it is the caller's job to control for it.
    """
    raw = _complete(
        judge_model,
        PAIRWISE,
        f"Question:\n{question}\n\nAnswer A:\n{answer_a}\n\nAnswer B:\n{answer_b}",
    )
    match = re.search(r"\{.*?\}", raw, re.S)
    if not match:
        return None
    try:
        w = json.loads(match.group(0)).get("winner")
    except json.JSONDecodeError:
        return None
    return w if w in ("A", "B", "tie") else None
