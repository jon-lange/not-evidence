"""Tests for the reference space and the three boundaries.

Run: python3 test_validator.py   (or: python3 -m pytest test_validator.py -q)

No network, no dependencies. The claim is about a validator's own code, so
everything asserted here is local and reproducible.

Two groups of these test the *space* rather than the code, and they are the
load-bearing ones. The headline multiplier is a function of how far the
accepted regions sit from each other under single-field edits, and a change
that quietly moved them closer would shrink the result without breaking
anything that looks like a test.
"""

from __future__ import annotations

import validator as V
from validator import ACCRETED, CARVE_OUT, CLASS, Ref, Validator

CODES = set(ACCRETED.codes())


def distance(a: Ref, b: Ref) -> int:
    return sum(getattr(a, dim) != getattr(b, dim) for dim in V.DIMS)


def branches(boundary):
    """Accepted references split into the local branch and the remote branch."""
    accepted = V.accepted_set(boundary)
    local = {r for r in accepted if r.scheme == ""}
    return local, accepted - local


# ── the space ────────────────────────────────────────────────────────────────

def test_space_has_the_advertised_shape():
    assert V.SPACE_SIZE == 48_000
    assert V.SPACE_SIZE == len(V.SCHEMES) * len(V.HOSTS) * len(V.KINDS) * len(V.SIZES) * len(V.FORMS)
    assert len(set(V.SPACE)) == V.SPACE_SIZE


def test_every_reference_is_hashable_and_field_addressable():
    ref = V.SPACE[0]
    for dim in V.DIMS:
        assert getattr(ref, dim) in V.VALUES[dim]
    assert ref.with_("kind", "png").kind == "png"
    assert ref.with_("kind", "png").scheme == ref.scheme


# ── the two error channels describe one boundary ─────────────────────────────

def test_the_error_channel_does_not_move_the_boundary():
    """The load-bearing assertion of the whole specimen.

    If the helpful and uniform validators accepted different references, the
    probe-count comparison would be measuring two boundaries rather than two
    ways of describing one, and every number in RESULTS.md would be void.
    """
    for boundary in (ACCRETED, CARVE_OUT, CLASS):
        helpful = Validator(boundary, uniform=False)
        uniform = Validator(boundary, uniform=True)
        for ref in V.SPACE:
            assert helpful(ref).ok == uniform(ref).ok


def test_the_helpful_channel_has_one_code_per_rule():
    seen = {Validator(ACCRETED, uniform=False)(ref).code for ref in V.SPACE}
    assert seen == CODES | {V.ACCEPT_CODE}
    assert len(CODES) == ACCRETED.predicates == 6


def test_the_uniform_channel_has_exactly_one_rejection_code():
    seen = {Validator(ACCRETED, uniform=True)(ref).code for ref in V.SPACE}
    assert seen == {V.ACCEPT_CODE, V.UNIFORM_CODE}


def test_the_class_refusal_has_one_code_without_being_asked():
    """It is not disciplined about uniform errors. It only has one thing to say."""
    assert len(set(CLASS.codes())) == 1
    seen = {Validator(CLASS, uniform=False)(ref).code for ref in V.SPACE}
    assert seen == {V.ACCEPT_CODE, V.UNIFORM_CODE}


def test_the_code_names_the_first_failing_rule():
    validator = Validator(ACCRETED, uniform=False)
    for ref in V.SPACE:
        expected = next((r.code for r in ACCRETED.rules if not r.test(ref)), V.ACCEPT_CODE)
        assert validator(ref).code == expected


def test_constant_work_changes_neither_verdict_nor_code():
    """The timing mitigation must not be a behaviour change."""
    plain = Validator(ACCRETED, uniform=False)
    constant = Validator(ACCRETED, uniform=False, constant_work=True)
    costly = Validator(ACCRETED, uniform=False, costly=True)
    for ref in V.SPACE[::7]:
        assert plain(ref) == constant(ref) == costly(ref)


# ── what each boundary accepts ───────────────────────────────────────────────

def test_accepted_counts_are_the_published_ones():
    assert len(V.accepted_set(ACCRETED)) == 166
    assert len(V.accepted_set(CARVE_OUT)) == 9
    assert len(V.accepted_set(CLASS)) == 80


def test_rule_counts_are_the_published_ones():
    assert (ACCRETED.predicates, ACCRETED.entries) == (6, 18)
    assert (CLASS.predicates, CLASS.entries) == (2, 0)


def test_the_suffix_match_is_a_live_bypass():
    """Pins the fraud in place. A later 'fix' that closes it would quietly
    delete the half of this specimen about enumeration."""
    bypass = V.bypass_refs(ACCRETED)
    assert len(bypass) == 36
    assert all(r.host not in V.HOST_ALLOWLIST for r in bypass)
    assert V._host_allowed("evil-docs.example.com")


def test_the_class_refusal_has_no_bypass_to_have():
    assert V.bypass_refs(CLASS) == frozenset()
    assert all(r.host == "" and r.scheme == "" for r in V.accepted_set(CLASS))


def test_the_class_refusal_takes_local_references_of_any_type():
    """It loses remote images, which is a real cost and is named in the README.
    What it does not do is care what a local file is, which is why it needs no
    content-type table."""
    accepted = V.accepted_set(CLASS)
    assert {r.kind for r in accepted} == set(V.KINDS)
    assert {r.size_kb for r in accepted} == set(V.SIZES)


def test_the_class_refusal_is_not_a_superset_of_the_allowlist():
    """Both directions matter: it refuses things the allowlist took, and takes
    things the allowlist refused. Neither boundary dominates the other."""
    strict, loose = V.accepted_set(CLASS), V.accepted_set(ACCRETED)
    assert strict - loose
    assert loose - strict


# ── the geometry the headline depends on ─────────────────────────────────────

def test_the_accreted_regions_are_adjacent():
    """Two single-field edits reach the remote branch from the local one.

    This is why the accreted multiplier is the small one: a prober with no
    signal walks there. If this ever became 3, the published ratio would rise
    for a reason that has nothing to do with error messages.
    """
    local, remote = branches(ACCRETED)
    assert min(distance(a, b) for a in local for b in remote) == 2


def test_the_carve_out_regions_are_isolated():
    """Four edits, and no single-field walk from the local branch reaches it."""
    local, remote = branches(CARVE_OUT)
    assert len(remote) == 1
    assert min(distance(a, b) for a in local for b in remote) == 4


def test_the_accepted_regions_are_a_small_share_of_the_space():
    """Blind search has to be expensive or the uniform row means nothing."""
    for boundary in (ACCRETED, CARVE_OUT, CLASS):
        share = len(V.accepted_set(boundary)) / V.SPACE_SIZE
        assert 0 < share < 0.01, f"{boundary.name} accepts {share:.1%} of the space"


def test_most_of_the_space_is_rejected_by_the_cheapest_rule():
    """Which is why short-circuit timing is so loud: the modal rejection is the
    one that costs almost nothing."""
    codes = [V.rejection_code(ACCRETED, ref) for ref in V.SPACE]
    assert codes.count("E_MALFORMED") / len(codes) > 0.5


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS  {name}")
            except AssertionError as exc:
                failures += 1
                print(f"  FAIL  {name}: {exc}")
            except Exception as exc:  # noqa: BLE001 — a crash is a failure, not a stop
                failures += 1
                print(f"  ERROR {name}: {type(exc).__name__}: {exc}")
    print(f"\n{failures} failure(s)")
    raise SystemExit(1 if failures else 0)
