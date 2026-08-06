"""The controls, and the exact point at which they stop being controls.

Two layers, both deterministic, both taken from specimen 04:

  scan_ingress   inspects the prompt before it is sent. This stands in for
                 every text-based control a team actually ships — a denylist,
                 a regex gate, an injection classifier, or the injection test
                 suite itself. All of them take a string.

  sanitize_egress / apply
                 inspects the answer after generation. Unchanged from
                 specimen 04, where it closed the content-relay cell without
                 touching the prompt.

The ingress layer is the one this specimen is about. It does not have a bug.
It is not badly written. It is handed the prompt, and under image delivery the
document body is not in the prompt — it is in a deflate stream of pixel rows.
The scanner runs, finds nothing, and passes. That is not a false negative in
any useful sense: there was no text to negate.
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

# The meta-injection signature — what an ingress denylist is built to catch.
META_MARKER = re.compile(
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions"
    r"|disregard\s+your\s+system\s+prompt"
    r"|you\s+are\s+no\s+longer\s+a",
    re.I,
)


def scan_ingress(prompt_text: str) -> list[str]:
    """What a text-based control sees in an outgoing prompt.

    Returns the names of the rules that fired. An empty list means the prompt
    is clean *as text* — which is a different statement from the prompt being
    clean, and the distance between those two statements is this specimen.
    """
    fired = []
    if META_MARKER.search(prompt_text):
        fired.append("meta-instruction")
    if CREDENTIAL_SOLICIT.search(prompt_text):
        fired.append("credential-solicitation")
    if EMAIL.search(prompt_text):
        fired.append("email-address")
    return fired


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

    Note what survives the modality change and what does not. Egress works on
    both channels, because the model's ANSWER is text no matter what the input
    was. Ingress does not. That asymmetry is the practical takeaway.
    """
    cleaned, fired = sanitize_egress(answer)
    if "credential-solicitation" in fired:
        return REFUSAL
    return cleaned
