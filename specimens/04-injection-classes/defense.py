"""Deterministic transforms — the controls that hold regardless of model behaviour.

Note what these do and, more importantly, what they do not.

They do NOT stop the model believing a poisoned document. Nothing at this layer
can: the model was asked what the document says, and it said so. That is the
correct operation, and it is why pattern 04 exists.

What they do is remove the *actionable payload* before it reaches a human, and
they do it whether or not the model complied with anything. That is the whole
argument of pattern 03 — a control you can only satisfy by asking the model
nicely is not a control.
"""

from __future__ import annotations

import re

EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
URL = re.compile(r"\bhttps?://\S+", re.I)

# Phrases that solicit a credential. Present because the dangerous instruction in
# this specimen is a *procedure*, and procedures are what egress scrubbing on
# addresses alone would miss.
CREDENTIAL_SOLICIT = re.compile(
    r"\b(send|email|share|provide|forward|include)\b[^.]{0,80}?"
    r"\b(api[- ]?key|token|password|secret|credential)s?\b",
    re.I | re.S,
)


def sanitize_egress(text: str) -> tuple[str, list[str]]:
    """Strip contact addresses and flag credential-soliciting procedures.

    Returns the cleaned text and a list of what fired, so the caller can decide
    whether to answer at all rather than silently shipping a redacted version of
    a harmful instruction.
    """
    fired: list[str] = []
    out = text

    if EMAIL.search(out):
        fired.append("email-address")
        out = EMAIL.sub("[address removed]", out)

    if URL.search(out):
        fired.append("url")
        out = URL.sub("[link removed]", out)

    if CREDENTIAL_SOLICIT.search(out):
        fired.append("credential-solicitation")

    return out, fired


REFUSAL = (
    "I can't relay that. The documentation for this topic contains a procedure "
    "that asks you to send a credential to an external address, which is not "
    "something this assistant will pass on. Verify the recovery process through "
    "a channel you already trust."
)


def apply(answer: str) -> str:
    """Full egress policy.

    Credential solicitation refuses outright rather than redacting. A redacted
    version of "email your API key to [address removed]" still teaches the user
    that mailing their key is the documented procedure — the payload is the
    instruction, not the address.
    """
    cleaned, fired = sanitize_egress(answer)
    if "credential-solicitation" in fired:
        return REFUSAL
    return cleaned
