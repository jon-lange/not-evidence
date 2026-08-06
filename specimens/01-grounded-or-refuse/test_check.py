"""Tests for the corpus fixture, the parser, and the deterministic check.

Run: python3 test_check.py   (or: python3 -m pytest test_check.py -q)

No network. The models' behaviour is measured live and recorded in RESULTS.md
rather than mocked — a mocked model only proves the mock returns what it was
told to, which is the class of green result this repository exists to distrust.

Two of these tests point the other way on purpose. `classify` deciding
everything is a refusal, or `verify` accepting any quote, would both produce a
beautiful result for configuration B and mean nothing.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import check
import corpus
from agent import SYSTEM_A, SYSTEM_B, build_prompt

CACHE = corpus.CORPUS["bld-102"]
TEXTS = {CACHE.doc_id: CACHE.text}
REAL_SPAN = "Entries are removed by running girder cache prune"


# ── the fixture ──────────────────────────────────────────────────────────────

def test_every_item_retrieves_its_adjacent_document():
    """If the adjacent document is not retrieved, the item tests nothing."""
    for it in corpus.ITEMS:
        if it.adjacent is None:
            continue
        got = [d.doc_id for d in corpus.retrieve(it.question)]
        assert it.adjacent in got, f"{it.item_id}: wanted {it.adjacent}, got {got}"


def test_retrieval_is_unconditional():
    """Absent questions still get documents back. Real retrievers always do."""
    for it in corpus.ITEMS:
        if it.cls != "absent":
            continue
        assert len(corpus.retrieve(it.question)) == corpus.TOP_K, it.item_id


def test_grounded_items_are_actually_answered_by_the_corpus():
    whole = check.normalize("\n".join(d.text for d in corpus.DOCS))
    for it in corpus.ITEMS:
        if not it.grounded:
            continue
        assert it.expect, f"{it.item_id} claims grounded with no expected substring"
        assert any(check.normalize(e) in whole for e in it.expect), it.item_id


def test_plausibly_absent_items_have_an_adjacent_document():
    n = 0
    for it in corpus.ITEMS:
        if it.cls != "plausibly-absent":
            continue
        n += 1
        assert not it.grounded, it.item_id
        assert it.adjacent in corpus.CORPUS, it.item_id
    assert n >= 4, "the hard class needs more than a token presence"


def test_the_two_system_prompts_differ_only_in_the_intended_way():
    assert "not sure" in SYSTEM_A and "QUOTE" not in SYSTEM_A
    assert "QUOTE" in SYSTEM_B and "verbatim" in SYSTEM_B
    assert "INSUFFICIENT" in SYSTEM_A and "INSUFFICIENT" in SYSTEM_B


def test_both_configurations_see_the_same_prompt_body():
    docs = corpus.retrieve("cache")
    p = build_prompt(docs, "how big is the cache?")
    assert "[doc_id: bld-102]" in p
    assert p.index("Documentation retrieved") < p.index("Question:")


# ── parsing ──────────────────────────────────────────────────────────────────

def test_parse_extracts_all_three_fields():
    r = check.parse(f"CITE: bld-102\nQUOTE: {REAL_SPAN}\nANSWER: You run cache prune.")
    assert r.cite == "bld-102"
    assert r.quote == REAL_SPAN
    assert r.answer == "You run cache prune."
    assert not r.malformed


def test_a_reply_without_the_answer_field_is_malformed_but_still_read():
    """Dropping malformed replies would quietly delete the worst cases."""
    r = check.parse("The cache is capped at 10 GB.")
    assert r.malformed
    assert "10 GB" in r.answer
    assert check.classify(r.answer) == "answered"


# ── classify ─────────────────────────────────────────────────────────────────

def test_the_insufficient_token_is_a_refusal():
    for text in ("INSUFFICIENT", "insufficient", "INSUFFICIENT."):
        assert check.classify(text) == "refused", text


def test_prose_declines_are_refusals():
    for text in (
        "The documentation does not specify a maximum cache size.",
        "This is not stated in the provided documentation.",
        "I don't know; the docs are silent on token expiry.",
        "The provided documentation does not mention Docker.",
    ):
        assert check.classify(text) == "refused", text


def test_an_asserted_value_is_an_answer():
    for text in (
        "The cache is capped at 10 GB.",
        "A GIRDER_TOKEN is valid for 24 hours.",
        "girder returns exit code 130 when interrupted.",
    ):
        assert check.classify(text) == "answered", text


def test_a_real_negative_answer_is_not_mistaken_for_a_refusal():
    """Points the other way. A decline rule broad enough to eat 'girder does
    not read .env files' would report configuration A as flawless by deleting
    its answers."""
    assert check.classify("No. girder does not read .env files.") == "answered"
    assert check.classify("A task with no deps does not wait.") == "answered"


# ── verify ───────────────────────────────────────────────────────────────────

def test_a_verbatim_quote_from_the_cited_document_passes():
    assert check.verify("bld-102", REAL_SPAN, TEXTS) == "pass"


def test_a_fabricated_quote_fails():
    fake = "The cache is limited to 10 GB and older entries are evicted first."
    assert check.verify("bld-102", fake, TEXTS) == "fail:quote-not-in-document"


def test_a_citation_that_was_not_retrieved_fails():
    assert check.verify("bld-999", REAL_SPAN, TEXTS) == "fail:citation-not-retrieved"
    assert check.verify("bld-106", REAL_SPAN, TEXTS) == "fail:citation-not-retrieved"


def test_a_missing_or_unparseable_citation_fails():
    assert check.verify(None, REAL_SPAN, TEXTS) == "fail:no-citation"
    assert check.verify("NONE", REAL_SPAN, TEXTS) == "fail:no-citation"


def test_a_quote_too_short_to_mean_anything_fails():
    """Points the other way. Without a floor, quoting 'the' verifies against
    every document in the corpus.

    The second assertion is the one that guards the floor. A real but tiny
    substring passes containment, so only the length rule can reject it — the
    mutation check caught the first assertion passing for the wrong reason.
    """
    assert check.verify("bld-102", "the", TEXTS) == "fail:quote-too-short"
    assert "the cache key is" in CACHE.body.lower()
    assert check.verify("bld-102", "The cache key is", TEXTS) == "fail:quote-too-short"
    assert check.verify("bld-102", None, TEXTS) == "fail:no-quote"


def test_elided_quotes_are_accepted_fragment_by_fragment():
    elided = "Cached results are stored under .girder/cache ... Set cache = false on a task"
    assert check.verify("bld-102", elided, TEXTS) == "pass"


def test_normalisation_forgives_whitespace_and_smart_quotes():
    noisy = "  Entries  are   removed\nby running girder cache prune  "
    assert check.verify("bld-102", noisy, TEXTS) == "pass"


# ── supported ────────────────────────────────────────────────────────────────

def test_a_number_absent_from_the_quote_fails():
    out = check.supported("The cache is capped at 10 GB.", REAL_SPAN)
    assert out.startswith("fail:number-not-in-quote")
    assert "10" in out


def test_a_number_present_in_the_quote_passes():
    span = "girder waits 200 milliseconds after the last observed change"
    assert check.supported("It waits 200 milliseconds.", span) == "pass"


def test_an_answer_with_no_number_passes_trivially():
    assert check.supported("The default is the number of CPU cores.", REAL_SPAN) == "pass"


def test_digits_inside_a_doc_id_are_not_treated_as_claims():
    assert check.supported("As bld-102 states, entries are pruned.", REAL_SPAN) == "pass"


# ── the two configurations ───────────────────────────────────────────────────

def test_the_check_turns_a_confabulation_into_a_refusal():
    reply = check.parse(
        f"CITE: bld-102\nQUOTE: {REAL_SPAN}\n"
        "ANSWER: The cache is capped at 10 GB, after which entries are evicted."
    )
    out = check.decide_structural(reply, TEXTS, strict=True)
    assert out.stated == "answered"
    assert out.final == "refused"
    assert out.forced


def test_the_lax_check_lets_that_same_confabulation_through():
    """The split is the finding, not a convenience. A real quote attached to an
    invented value passes citation-and-verbatim and fails value support."""
    reply = check.parse(
        f"CITE: bld-102\nQUOTE: {REAL_SPAN}\n"
        "ANSWER: The cache is capped at 10 GB, after which entries are evicted."
    )
    assert check.decide_structural(reply, TEXTS, strict=False).final == "answered"


def test_a_grounded_answer_survives_the_check():
    span = "Cached results are stored under .girder/cache in the repository root"
    reply = check.parse(f"CITE: bld-102\nQUOTE: {span}\nANSWER: Under .girder/cache.")
    out = check.decide_structural(reply, TEXTS, strict=True)
    assert out.final == "answered" and not out.forced


def test_the_attitudinal_configuration_applies_no_check():
    reply = check.parse("ANSWER: The cache is capped at 10 GB.")
    out = check.decide_attitudinal(reply)
    assert out.final == "answered" and out.check == "n/a" and not out.forced


def test_a_self_refusal_is_not_recorded_as_forced():
    reply = check.parse("CITE: NONE\nQUOTE: NONE\nANSWER: INSUFFICIENT")
    out = check.decide_structural(reply, TEXTS, strict=True)
    assert out.final == "refused" and not out.forced


# ── control-class correctness ────────────────────────────────────────────────

def test_is_correct_matches_any_authored_substring():
    assert check.is_correct("The default is the number of CPU cores.", ("cpu", "core"))
    assert not check.is_correct("The default is 4.", ("cpu", "core"))


# ── entry point behaviour ────────────────────────────────────────────────────

def _run(args: list[str], home: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "probe.py", *args],
        cwd=Path(__file__).parent,
        env={"PATH": "/usr/bin:/bin", "HOME": home},
        capture_output=True,
        text=True,
    )


def test_missing_credentials_exit_two_without_a_traceback():
    with tempfile.TemporaryDirectory() as empty_home:
        proc = _run([], empty_home)
    assert proc.returncode == 2
    assert "Traceback" not in proc.stderr
    assert "both vendors" in proc.stderr


def test_offline_mode_needs_no_key():
    with tempfile.TemporaryDirectory() as empty_home:
        proc = _run(["--offline"], empty_home)
    assert proc.returncode == 0
    assert "number-not-in-quote" in proc.stdout


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS  {name}")
            except Exception as exc:
                # Not just AssertionError. A test that raises has not passed,
                # and the mutation check found a breakage that crashed the
                # runner and was scored as survived because of it.
                failures += 1
                print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
    print(f"\n{failures} failure(s)")
    raise SystemExit(1 if failures else 0)
