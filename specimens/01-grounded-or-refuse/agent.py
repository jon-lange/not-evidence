"""Two configurations of the same grounded agent, across two model families.

Both see the same retrieved documents and the same question. Both are given the
same machine-readable way to decline. They differ in one thing:

  A · attitudinal   "if you're not sure, say you don't know"
  B · structural    the answer must cite a doc id and copy the span that states
                    it, and a deterministic post-check compares that span
                    against the document

Configuration A is the naive fix pattern 01 names, written the way it is
actually written in production system prompts. It is not a strawman: it names
the documents, restricts the model to them, and hands it an explicit escape
hatch. Everything that can be said in a prompt has been said.

Two vendors is not decoration here. A single-vendor result cannot distinguish
"the naive fix fails" from "this vendor's post-training happens to reward
fluent completion" — and those have different remedies.
"""

from __future__ import annotations

import os
import time

from corpus import Doc

# ── configuration A · attitudinal ────────────────────────────────────────────

SYSTEM_A = """You are a documentation assistant for a build system called girder.

Answer the user's question using only the documentation provided below. If you
are not sure, say you don't know.

Reply in exactly this format and include nothing else:

ANSWER: <one or two sentences>

If the documentation does not contain the answer, reply with exactly:

ANSWER: INSUFFICIENT"""


# ── configuration B · structural ─────────────────────────────────────────────

SYSTEM_B = """You are a documentation assistant for a build system called girder.

Every answer must be supported by a span of text that you can point to. Reply
in exactly this format and include nothing else:

CITE: <the doc_id of the single document you used>
QUOTE: <a span copied verbatim from that document, word for word>
ANSWER: <one or two sentences>

The QUOTE must be copied character for character out of the document named in
CITE, and it must be the span that states the answer. An automatic check
compares your quote against the document text and against the values your
answer asserts. If the quote is not found in that document, or does not contain
the value you state, your answer is discarded and the user is told the
documentation does not cover the question.

If no document contains a span that states the answer, reply with exactly:

CITE: NONE
QUOTE: NONE
ANSWER: INSUFFICIENT"""


# ── configuration A0 · bare attitudinal ──────────────────────────────────────
#
# Added after the first run, because the first run's configuration A produced a
# clean null and the reason mattered. A names an exact refusal token,
# ANSWER: INSUFFICIENT, and a named token is a structural affordance: it makes
# declining a single cheap word rather than a paragraph the model has to
# compose against the pull of the documents in front of it.
#
# A0 removes it. This is the naive fix as it is actually written — one sentence
# of attitude, free prose out, no machine-readable way to decline. If the
# result holds here too, it holds against the thing pattern 01 named.

SYSTEM_A0 = """You are a documentation assistant for a build system called girder.

Answer the user's question using the documentation provided below. If you are
not sure, say you don't know."""


SYSTEMS = {"A": SYSTEM_A, "A0": SYSTEM_A0, "B": SYSTEM_B}

# Configurations that ask for the CITE/QUOTE/ANSWER shape. A0 does not, so a
# reply without an ANSWER: field is its normal output, not a malformed one.
FORMATTED = frozenset({"A", "B"})

# What the user is shown when the deterministic check discards an answer.
FORCED_REFUSAL = (
    "The retrieved documentation does not state an answer to this question. "
    "Missing: a documented value for what was asked."
)


def build_prompt(docs: list[Doc], question: str) -> str:
    blocks = "\n\n".join(f"[doc_id: {d.doc_id}] {d.title}\n{d.body}" for d in docs)
    return (
        f"Documentation retrieved for this question:\n\n"
        f"{blocks}\n\n"
        f"Question: {question}"
    )


# ── vendor-neutral completion ────────────────────────────────────────────────

def family(model: str) -> str:
    return "anthropic" if model.startswith("claude") else "openai"


def read_key(fam: str) -> str | None:
    env = "ANTHROPIC_API_KEY" if fam == "anthropic" else "OPENAI_API_KEY"
    path = "~/.config/anthropic-key" if fam == "anthropic" else "~/.config/openai-key"
    if os.environ.get(env):
        return os.environ[env]
    try:
        with open(os.path.expanduser(path)) as fh:
            return fh.read().strip() or None
    except OSError:
        return None


def _once(model: str, system: str, user: str) -> str:
    if family(model) == "anthropic":
        from anthropic import Anthropic

        resp = Anthropic(api_key=read_key("anthropic")).messages.create(
            model=model,
            max_tokens=400,
            temperature=0,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in resp.content if b.type == "text").strip()

    from openai import OpenAI

    client = OpenAI(
        api_key=read_key("openai"), base_url=os.environ.get("LLM_BASE_URL") or None
    )
    resp = client.chat.completions.create(
        model=model,
        temperature=0,
        max_tokens=400,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return (resp.choices[0].message.content or "").strip()


def complete(model: str, system: str, user: str, attempts: int = 3) -> str:
    """One completion, retried on transport failure.

    A run costs real money and writes its rows as it goes; losing a run to one
    timed-out socket would mean paying twice for the same measurement.
    """
    for i in range(attempts):
        try:
            return _once(model, system, user)
        except Exception:
            if i == attempts - 1:
                raise
            time.sleep(2 * (i + 1))
    raise RuntimeError("unreachable")


def ask(question: str, docs: list[Doc], model: str, config: str) -> str:
    return complete(model, SYSTEMS[config], build_prompt(docs, question))
