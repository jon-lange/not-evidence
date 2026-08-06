"""The deterministic layer: parse a reply, and decide whether it is an answer.

Nothing here calls a model. That is the point. Deciding "was this a
confabulation?" with an LLM judge would import pattern 05's problem into
pattern 01's specimen — the measurement would inherit the same failure it is
supposed to detect.

Three separable jobs:

  classify()   did the system assert an answer, or decline?
  verify()     does the cited document exist in what was retrieved, and does
               the quoted span actually appear in it?
  supported()  does every number the answer asserts appear in the quoted span?

`classify` is used for BOTH configurations, so the two are read the same way.
`verify` and `supported` are configuration B's post-check and are what the
pattern calls structural.

A note on the bias in `classify`. The decline-marker list below will read a
hedged confabulation — "the documentation does not specify, but the default is
10 GB" — as a refusal. That undercounts configuration A's confabulations. The
error is deliberately pointed AGAINST the hypothesis this specimen is testing,
and its size is measured by hand-checking a sample rather than assumed to be
zero.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

MIN_QUOTE_CHARS = 24
MIN_FRAGMENT_CHARS = 12

# An explicit, machine-readable decline. Both configurations are told to use it.
INSUFFICIENT = "INSUFFICIENT"

# Prose declines, for models that ignore the token and write a sentence instead.
# Counting these as refusals is the conservative direction: it can only shrink
# the measured confabulation rate.
_DECLINE_VERBS = (
    "specify|state|mention|say|indicate|define|contain|document|list|provide|"
    "cover|include|give|describe|address"
)
DECLINE_PATTERNS = (
    r"\binsufficient\b",
    rf"\b(does not|doesn't|do not|don't|did not|didn't) ({_DECLINE_VERBS})\b",
    r"\b(i|we) (do not|don't) know\b",
    r"\bnot (specified|stated|mentioned|documented|provided|listed|covered|"
    r"defined|available|given|described|addressed)\b",
    r"\bno (information|mention|documentation|details?) (about|on|regarding|for)\b",
    r"\b(cannot|can't|unable to) (be )?(determine|determined|tell|answer)\b",
    r"\bnot (in|found in) the (provided )?documentation\b",
    r"\bsilent (on|about)\b",
    r"\bnothing (in|about) the (provided )?(documentation|docs)\b",
)
_DECLINE_RE = re.compile("|".join(DECLINE_PATTERNS), re.I)

_DOC_ID_RE = re.compile(r"\bbld-\d+\b", re.I)
_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")
_FIELD_RE = r"^\s*{}\s*:\s*(.*)$"


# ── normalisation ────────────────────────────────────────────────────────────

def normalize(text: str) -> str:
    """Fold the differences that are not about content.

    Smart quotes, dashes and whitespace vary between a document and a model's
    reproduction of it for reasons that have nothing to do with whether the
    span is really there.
    """
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("—", "-").replace("–", "-").replace("−", "-")
    text = text.replace("…", "...")
    return re.sub(r"\s+", " ", text).strip().lower()


def _strip_wrapping(text: str) -> str:
    text = text.strip().strip("`")
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        text = text[1:-1]
    return text.strip().rstrip(".").strip()


# ── parsing ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Reply:
    raw: str
    cite: str | None
    quote: str | None
    answer: str
    malformed: bool


def _field(raw: str, name: str) -> str | None:
    m = re.search(_FIELD_RE.format(name), raw, re.I | re.M)
    if not m:
        return None
    value = m.group(1).strip()
    return value or None


def parse(raw: str) -> Reply:
    """Pull the three fields out of a reply.

    A reply that omits ANSWER: is recorded as malformed AND read whole — a
    model that ignored the format but asserted something has still asserted it,
    and dropping those items would quietly delete the worst cases.
    """
    answer = _field(raw, "ANSWER")
    malformed = answer is None
    return Reply(
        raw=raw,
        cite=(_field(raw, "CITE") or "").strip() or None,
        quote=_field(raw, "QUOTE"),
        answer=answer if answer is not None else raw.strip(),
        malformed=malformed,
    )


# ── did the system assert an answer? ─────────────────────────────────────────

def classify(answer: str) -> str:
    """"answered" or "refused". Used identically for both configurations."""
    n = normalize(answer)
    if not n:
        return "refused"
    if n.strip(".!\"' ") == INSUFFICIENT.lower():
        return "refused"
    if _DECLINE_RE.search(n):
        return "refused"
    return "answered"


# ── configuration B's post-check ─────────────────────────────────────────────

def verify(cite: str | None, quote: str | None, doc_ids_to_text: dict[str, str]) -> str:
    """Is the citation real and does the quoted span actually appear in it?

    Returns "pass" or "fail:<reason>". Substring containment after
    normalisation — no model, no embedding, no similarity threshold. A
    threshold would be a knob, and a knob is somewhere for the result to hide.
    """
    if not cite:
        return "fail:no-citation"
    ids = _DOC_ID_RE.findall(cite)
    if not ids:
        return "fail:no-citation"
    if len(ids) > 1:
        return "fail:ambiguous-citation"
    doc_id = ids[0].lower()
    if doc_id not in doc_ids_to_text:
        return "fail:citation-not-retrieved"

    if not quote:
        return "fail:no-quote"
    q = normalize(_strip_wrapping(quote))
    if len(q) < MIN_QUOTE_CHARS:
        return "fail:quote-too-short"

    haystack = normalize(doc_ids_to_text[doc_id])
    # Models elide with "...". Require every fragment, not the literal string.
    fragments = [f.strip() for f in q.split("...") if len(f.strip()) >= MIN_FRAGMENT_CHARS]
    if not fragments:
        return "fail:quote-too-short"
    if any(f not in haystack for f in fragments):
        return "fail:quote-not-in-document"
    return "pass"


def supported(answer: str, quote: str | None) -> str:
    """Does every number the answer asserts appear in the quoted span?

    The pattern's third clause is that the cited span must actually contain the
    claim, not merely exist. Full entailment is not decidable here, but the
    lexical shadow of it is: an answer that states "10 GB" against a span
    containing no 10 has been assembled, not read.

    Numbers only. It is a proxy, it is incomplete, and it is honest about being
    a proxy — an answer whose claim carries no number passes trivially.
    """
    stripped = _DOC_ID_RE.sub(" ", answer)
    claimed = set(_NUMBER_RE.findall(stripped))
    if not claimed:
        return "pass"
    in_quote = set(_NUMBER_RE.findall(quote or ""))
    missing = sorted(claimed - in_quote)
    return "pass" if not missing else f"fail:number-not-in-quote:{','.join(missing)}"


# ── the two configurations' final outcomes ───────────────────────────────────

@dataclass(frozen=True)
class Outcome:
    final: str          # "answered" | "refused"
    stated: str         # what the model itself produced
    check: str          # "n/a" | "pass" | "fail:<reason>"
    forced: bool        # did the deterministic check turn an answer into a refusal?


def decide_attitudinal(reply: Reply) -> Outcome:
    """Configuration A. Whatever the model said is what the system says."""
    stated = classify(reply.answer)
    return Outcome(final=stated, stated=stated, check="n/a", forced=False)


def decide_structural(
    reply: Reply, doc_ids_to_text: dict[str, str], strict: bool = True
) -> Outcome:
    """Configuration B. An answer survives only if the check passes.

    strict=False checks only that the citation is real and the quote verbatim.
    strict=True additionally requires the answer's numbers to appear in the
    quote. Both are computed from the same reply, so the split between them
    costs nothing and shows which half of the check does the work.
    """
    stated = classify(reply.answer)
    if stated == "refused":
        return Outcome(final="refused", stated=stated, check="n/a", forced=False)

    result = verify(reply.cite, reply.quote, doc_ids_to_text)
    if result == "pass" and strict:
        result = supported(reply.answer, reply.quote)

    if result == "pass":
        return Outcome(final="answered", stated=stated, check="pass", forced=False)
    return Outcome(final="refused", stated=stated, check=result, forced=True)


# ── correctness on the control class ─────────────────────────────────────────

def is_correct(answer: str, expect: tuple[str, ...]) -> bool:
    """A grounded item's answer must contain one of the authored substrings.

    Only meaningful for the answerable class. A refusal is not correct here —
    the corpus states the answer, so declining is an over-refusal.
    """
    n = normalize(answer)
    return any(normalize(e) in n for e in expect)
