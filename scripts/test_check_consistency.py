"""Mutation harness for the consistency checker. Standard library only.

Run: python3 test_check_consistency.py   (or: python3 -m pytest -q)

The checker asserts that this repository's metadata agrees with itself. A
checker that passes because it looked at nothing produces the same output as
one that passed because everything was fine — which is pattern 11, aimed at a
tool this repository now depends on. So every rule is proven by breaking it.

Two kinds of test live here:

  * The synthetic tree. A minimal fixture repository is built in a temp dir,
    one mutation is applied, and the checker must fail *and say which rule*.
    Synthetic rather than a copy of the real tree so the mutations stay exact
    and the suite does not depend on the real tree being clean.

  * The real tree. One test runs the checker against this repository. It is
    expected to fail until the drift it finds is fixed, and that is the point:
    the failing test is the work order.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CHECKER = Path(__file__).resolve().parent / "check-consistency.py"
REPO = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------- the fixture

PATTERN = """\
---
pattern: {num}
name: "{name}"
status: {status}
refuses: "to do the thing"
specimen: {specimen}
---

# {num} · {name}

> **Refuses to do the thing.**

See [the other one](../patterns/{other}.md) and its [specimen](../specimens/{body}/README.md).
"""

SKILL = """\
---
name: {name}
description: Does a thing. Use when a thing needs doing.
pattern: {pattern}
status: {status}
---

# {title}
"""

SKILLS_README = """\
# Skills

| skill | pattern | status | what it is for |
|---|---|---|---|
| [alpha-check](alpha-check/) | [01 · Alpha](../patterns/01-alpha.md) | {status} | Does a thing |
"""

README = """\
# Fixture

## Start here

| If this sounds familiar | Start with |
|---|---|
| something broke | [01](patterns/01-alpha.md){triage2} |

## The catalogue

| # | Pattern | Refuses | Status |
|---|---|---|---|
| 01 | [Alpha](patterns/01-alpha.md) | to do the thing | **{s1}** |
| 02 | [Beta](patterns/02-beta.md) | to do the thing | {s2} |

Run `make test` to see it.

## {c_revised} of the twelve entries were revised by their own specimens

{c_revised} came back changed. {c_failed} were contradicted
outright and now argue something different.

{c_revised} entries were revised by measurement; the {c_failed} marked `revised-by-specimen` are
the ones whose central claim failed. The other {c_narrowed} were narrowed rather than overturned.

**The views expressed here are my own and do not represent those of my employer
or any client.**
"""

MAKEFILE = "test:\n\t@echo ok\n"

SPECIMENS_README = """\
# Specimens

| # | Specimen | Pattern |
|---|---|---|
| 01 | [alpha](01-alpha/) | Alpha{extra1} |
| 02 | [beta](02-beta/) | Beta |
"""

EVIDENCE = """\
# Evidence

| # | Pattern | Result | Working |
|---|---|---|---|
| 01 | Alpha | `{fig1}` | [RESULTS](specimens/01-alpha/RESULTS.md) |
| 02 | Beta | `0 of 9` | [RESULTS](specimens/02-beta/RESULTS.md) |

## The {c_failed} that contradicted their own pattern
"""

RESULTS = """\
# results

**Adjudication: {verdict}.** Because of what the run showed.

Measured 0 out of 36, and 0 of 9 elsewhere.
"""


def build_fixture(root: Path, **over: str) -> None:
    """Write a minimal, internally consistent repository."""
    opt = {
        "p1_status": "field-tested",
        "p2_status": "draft",
        "p1_specimen": "01-alpha",
        # The body link is separable from the frontmatter key on purpose. If
        # they moved together, a bad `specimen:` value would also break a link,
        # and the specimen rule could be deleted without any test noticing —
        # the link rule would be catching it. It survived exactly that mutation
        # before this was split out.
        "p1_body_specimen": None,
        "extra_specimen_dir": None,
        "drop_readme_row": False,
        "evidence": True,
        "evidence_figure": "0 out of 36",
        "drop_evidence_row": False,
        "orphan_in_triage": False,
        "skill_pattern": "01",
        "skill_status": "field-tested",
        "readme_s1": "field-tested",
        "readme_s2": "draft",
        "skills_readme_status": "field-tested",
        "disclaimer": True,
        "link_target": "02-beta",
        "make_target": "test",
        # 02 is `draft` by default, so it is unmeasured and exempt from
        # adjudication. Its verdict only matters in tests that measure it.
        "adj1": "narrowed",
        "adj2": "central-claim-failed",
        "drop_adjudication": False,
        "p1_no_specimen_key": False,
        # Consistent with the defaults above: one measured pattern, narrowed.
        "c_revised": "One",
        "c_failed": "Zero",
        "c_narrowed": "One",
        "rephrase_readme_claim": False,
        "specimens_index": True,
        "specimens_index_extra": "",
        "drop_specimens_index_row": False,
    }
    opt.update(over)

    (root / "patterns").mkdir(parents=True)
    (root / "skills" / "alpha-check").mkdir(parents=True)
    dirs = ["01-alpha", "02-beta"]
    if opt["extra_specimen_dir"]:
        dirs.append(opt["extra_specimen_dir"])
    for slug in dirs:
        (root / "specimens" / slug).mkdir(parents=True)
        (root / "specimens" / slug / "README.md").write_text("# specimen\n")
        verdict = opt["adj2"] if slug == "02-beta" else opt["adj1"]
        results = RESULTS.format(verdict=verdict)
        if opt["drop_adjudication"] and slug != "02-beta":
            results = "\n".join(
                l for l in results.splitlines() if "Adjudication" not in l
            )
        (root / "specimens" / slug / "RESULTS.md").write_text(results)

    p1 = PATTERN.format(
        num="01", name="Alpha", status=opt["p1_status"],
        specimen=opt["p1_specimen"], other=opt["link_target"],
        body=opt["p1_body_specimen"] or opt["p1_specimen"],
    )
    if opt["p1_no_specimen_key"]:
        p1 = "\n".join(l for l in p1.splitlines() if not l.startswith("specimen:"))
    (root / "patterns" / "01-alpha.md").write_text(p1)
    (root / "patterns" / "02-beta.md").write_text(
        PATTERN.format(
            num="02", name="Beta", status=opt["p2_status"],
            specimen="02-beta", other="01-alpha", body="02-beta",
        )
    )
    (root / "skills" / "alpha-check" / "SKILL.md").write_text(
        SKILL.format(
            name="alpha-check", pattern=opt["skill_pattern"],
            status=opt["skill_status"], title="Alpha check",
        )
    )
    (root / "skills" / "README.md").write_text(
        SKILLS_README.format(status=opt["skills_readme_status"])
    )

    body = README.format(
        s1=opt["readme_s1"], s2=opt["readme_s2"],
        triage2="" if opt["orphan_in_triage"] else ", [02](patterns/02-beta.md)",
        c_revised=opt["c_revised"], c_failed=opt["c_failed"],
        c_narrowed=opt["c_narrowed"],
    )
    body = body.replace("make test", f"make {opt['make_target']}")
    if opt["rephrase_readme_claim"]:
        body = body.replace("came back changed", "turned out differently")
    if opt["drop_readme_row"]:
        body = "\n".join(l for l in body.splitlines() if not l.startswith("| 02 "))
    if not opt["disclaimer"]:
        body = body.split("**The views")[0]
    (root / "README.md").write_text(body)
    (root / "Makefile").write_text(MAKEFILE)

    if opt["specimens_index"]:
        idx = SPECIMENS_README.format(extra1=opt["specimens_index_extra"])
        if opt["drop_specimens_index_row"]:
            idx = "\n".join(l for l in idx.splitlines() if not l.startswith("| 02 "))
        (root / "specimens" / "README.md").write_text(idx)

    if opt["evidence"]:
        ev = EVIDENCE.format(fig1=opt["evidence_figure"], c_failed=opt["c_failed"])
        if opt["drop_evidence_row"]:
            ev = "\n".join(l for l in ev.splitlines() if not l.startswith("| 02 "))
        (root / "EVIDENCE.md").write_text(ev)


def check(root: Path) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(CHECKER), "--root", str(root)],
        capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


class fixture:
    """Context manager yielding a fixture tree built with the given overrides."""

    def __init__(self, **over: str) -> None:
        self.over = over

    def __enter__(self) -> Path:
        self.dir = Path(tempfile.mkdtemp(prefix="consistency-"))
        build_fixture(self.dir, **self.over)
        return self.dir

    def __exit__(self, *exc: object) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)


# ------------------------------------------------------------- the happy path


def test_a_consistent_fixture_passes():
    with fixture() as root:
        code, out = check(root)
    assert code == 0, out


def test_a_clean_run_says_what_it_checked():
    """A checker that passes silently is indistinguishable from one that
    checked nothing. It has to report its own coverage."""
    with fixture() as root:
        _, out = check(root)
    assert "patterns" in out.lower()
    assert any(ch.isdigit() for ch in out), "no counts in a clean report"


# ----------------------------------------------------------------- mutations
# Each breaks exactly one rule. The checker must fail AND name the rule.


def test_readme_status_disagreeing_with_frontmatter_is_caught():
    with fixture(readme_s1="draft") as root:
        code, out = check(root)
    assert code != 0
    assert "01" in out and "draft" in out and "field-tested" in out


def test_a_skill_claiming_more_than_its_pattern_is_caught():
    with fixture(skill_pattern="02", skills_readme_status="field-tested") as root:
        code, out = check(root)
    assert code != 0
    assert "alpha-check" in out


def test_skills_readme_disagreeing_with_the_skill_is_caught():
    with fixture(skills_readme_status="draft") as root:
        code, out = check(root)
    assert code != 0
    assert "alpha-check" in out


def test_a_specimen_key_pointing_nowhere_is_caught():
    """The body link is held valid so only the specimen rule can fire. Without
    that isolation the link rule catches this, and the specimen rule could be
    deleted with every test still green."""
    with fixture(p1_specimen="99-does-not-exist", p1_body_specimen="01-alpha") as root:
        code, out = check(root)
    assert code != 0
    assert "[specimen-key]" in out and "99-does-not-exist" in out


def test_a_bare_numeric_specimen_key_is_caught():
    """`specimen: 01` resolves to nothing and renders wrong on the site. The
    convention is the directory slug."""
    with fixture(p1_specimen="01", p1_body_specimen="01-alpha") as root:
        code, out = check(root)
    assert code != 0
    assert "[specimen-key]" in out


def test_a_specimen_directory_off_the_slug_convention_is_caught():
    """Isolates the convention rule from the existence rule: the directory is
    real, so only the slug check can fail."""
    with fixture(
        p1_specimen="Alpha_One",
        p1_body_specimen="Alpha_One",
        extra_specimen_dir="Alpha_One",
    ) as root:
        code, out = check(root)
    assert code != 0
    assert "[specimen-key]" in out and "slug" in out


def test_a_readme_missing_a_pattern_row_is_caught():
    """A table with a row silently dropped reports nothing under a
    row-by-row comparison — the count is the only thing that sees it."""
    with fixture(drop_readme_row=True) as root:
        code, out = check(root)
    assert code != 0
    assert "[readme-status]" in out and "rows" in out


def test_a_broken_relative_link_is_caught():
    with fixture(link_target="03-nonexistent") as root:
        code, out = check(root)
    assert code != 0
    assert "03-nonexistent" in out


def test_a_make_target_that_does_not_exist_is_caught():
    with fixture(make_target="dev") as root:
        code, out = check(root)
    assert code != 0
    assert "dev" in out


def test_docs_may_discuss_targets_that_do_not_exist():
    """Both directions of the exclusion are asserted: a planning document
    quoting a removed target must pass (this test), and the same reference in
    a live document must still fail (the test above). A rule verified in only
    one direction is how scanners end up firing on prose."""
    with fixture() as root:
        (root / "docs").mkdir()
        (root / "docs" / "plan.md").write_text(
            "The audit found `make dev`, which no longer exists.\n"
        )
        code, out = check(root)
    assert code == 0, out


def test_a_missing_employer_disclaimer_is_caught():
    with fixture(disclaimer=False) as root:
        code, out = check(root)
    assert code != 0
    assert "disclaimer" in out.lower()


def test_a_status_outside_the_vocabulary_is_caught():
    with fixture(p2_status="probably-fine", readme_s2="probably-fine") as root:
        code, out = check(root)
    assert code != 0
    assert "probably-fine" in out


def test_the_new_status_term_is_in_the_vocabulary():
    """Measuring 02 makes it adjudicable, so the derived counts move with it —
    which is the rule working, not interference."""
    with fixture(
        p2_status="revised-by-specimen", readme_s2="revised-by-specimen",
        c_revised="Two", c_failed="One", c_narrowed="One",
    ) as root:
        code, out = check(root)
    assert code == 0, out


# -------------------------------------------------------- the specimens index


def test_a_specimens_index_missing_a_pattern_is_caught():
    with fixture(drop_specimens_index_row=True) as root:
        code, out = check(root)
    assert code != 0
    assert "[specimens-index]" in out and "02" in out


def test_a_status_term_reappearing_in_the_specimens_index_is_caught():
    """The drift that shipped. This table carried hand-written outcome notes
    that were correct when written and stale by the time anyone read them. The
    rule asserts the vocabulary's *absence*, because the failure mode is the
    column growing back, not the column disagreeing once."""
    with fixture(specimens_index_extra=" | **field-tested**") as root:
        code, out = check(root)
    assert code != 0
    assert "[specimens-index]" in out and "field-tested" in out


def test_an_adjudication_term_reappearing_in_the_specimens_index_is_caught():
    """Both vocabularies are forbidden there, not just the status one."""
    with fixture(specimens_index_extra=" | central-claim-failed") as root:
        code, out = check(root)
    assert code != 0
    assert "[specimens-index]" in out and "central-claim-failed" in out


def test_a_duplicated_row_in_the_specimens_index_is_caught():
    """Found by mutation: the duplicate guard broke no test. A pattern listed
    twice satisfies the every-pattern-has-a-row check completely, so only the
    row count sees it — and two rows for one specimen is the index disagreeing
    with itself, which is what this file is now here to not do."""
    with fixture() as root:
        idx = root / "specimens" / "README.md"
        text = idx.read_text()
        row = next(l for l in text.splitlines() if l.startswith("| 01 "))
        idx.write_text(text + row + "\n")
        code, out = check(root)
    assert code != 0
    assert "[specimens-index]" in out and "distinct" in out


def test_a_repository_without_a_specimens_index_still_checks_everything_else():
    with fixture(specimens_index=False) as root:
        code, out = check(root)
    assert code == 0, out


# ------------------------------------------------- the derived revision count
# The headline claim used to be asserted in five places and derived from
# nothing. These break every part of the derivation.


def test_a_specimen_with_no_adjudication_line_is_caught():
    """Without a verdict the count cannot be derived, and a count derived from
    eleven of twelve specimens is not the count the README states."""
    with fixture(drop_adjudication=True) as root:
        code, out = check(root)
    assert code != 0
    assert "[adjudication]" in out and "carries no" in out


def test_an_adjudication_outside_the_vocabulary_is_caught():
    with fixture(adj1="mostly-fine") as root:
        code, out = check(root)
    assert code != 0
    assert "[adjudication]" in out and "mostly-fine" in out


def test_a_central_claim_failure_not_marked_revised_by_specimen_is_caught():
    """This is the drift that shipped: specimen 03 recorded 'falsified as
    written' while its pattern carried `field-tested`. The status vocabulary and
    the adjudication vocabulary describe the same outcome, so they must agree."""
    with fixture(adj1="central-claim-failed") as root:
        code, out = check(root)
    assert code != 0
    assert "[adjudication]" in out and "revised-by-specimen" in out


def test_revised_by_specimen_without_a_central_claim_failure_is_caught():
    """The other direction. An entry cannot claim its specimen overturned it
    when the specimen says the claim merely narrowed."""
    with fixture(
        p2_status="revised-by-specimen", readme_s2="revised-by-specimen",
        adj2="narrowed", c_revised="Two", c_failed="Zero", c_narrowed="Two",
    ) as root:
        code, out = check(root)
    assert code != 0
    assert "[adjudication]" in out and "narrowed" in out


def test_a_published_count_disagreeing_with_the_derivation_is_caught():
    with fixture(c_revised="Nine") as root:
        code, out = check(root)
    assert code != 0
    assert "[adjudication]" in out and "Nine" in out


def test_each_copy_of_the_count_is_checked_independently():
    """EVIDENCE.md states the failure count separately from README.md. Changing
    only one must fail, or the copies are not really being compared."""
    with fixture() as root:
        ev = (root / "EVIDENCE.md").read_text().replace(
            "## The Zero that", "## The Four that"
        )
        (root / "EVIDENCE.md").write_text(ev)
        code, out = check(root)
    assert code != 0
    assert "[adjudication]" in out and "EVIDENCE.md" in out


def test_a_rephrased_claim_fails_rather_than_silently_unchecking_itself():
    """The rule reads English sentences. If one is reworded, the regex stops
    matching — and a rule that quietly checks nothing prints exactly what a
    correct run prints. That is the failure this repository is named for, so
    an unmatched claim is a failure, not a skip."""
    with fixture(rephrase_readme_claim=True) as root:
        code, out = check(root)
    assert code != 0
    assert "[adjudication]" in out and "rephrased" in out


def test_a_measured_pattern_with_no_specimen_key_is_caught():
    """Found by mutation: deleting the completeness check broke no test. A
    measured pattern with no `specimen:` key contributes no verdict and fires
    none of the per-specimen rules, so the totals quietly derive from a smaller
    set than the catalogue. Only the count sees it — the same reason the README
    row-count rule exists."""
    with fixture(p1_no_specimen_key=True) as root:
        code, out = check(root)
    assert code != 0
    assert "[adjudication]" in out and "incomplete count" in out


def test_a_draft_pattern_needs_no_adjudication():
    """`draft` means written and not yet measured. Demanding a verdict there
    would force one to be invented, which is the opposite of the point."""
    with fixture() as root:
        results = root / "specimens" / "02-beta" / "RESULTS.md"
        # The figure stays: this test isolates the adjudication rule, and
        # dropping it would fire the evidence rule instead.
        results.write_text("# results\n\nNot measured yet. 0 of 9 elsewhere.\n")
        code, out = check(root)
    assert code == 0, out


def test_malformed_frontmatter_fails_rather_than_passing_silently():
    """Asserts the specific branch. `frontmatter` alone is satisfied by the
    missing-`pattern:`-key message too, which let the no-frontmatter guard be
    deleted with this test still passing."""
    with fixture() as root:
        (root / "patterns" / "01-alpha.md").write_text("no frontmatter here\n")
        code, out = check(root)
    assert code != 0
    assert "no frontmatter block" in out


def test_running_against_a_directory_that_is_not_the_repo_fails_loudly():
    """A checker that reports a clean tree because it found no patterns is the
    vacuous-pass failure this repository is about."""
    with tempfile.TemporaryDirectory() as empty:
        code, out = check(Path(empty))
    assert code != 0
    assert "no patterns" in out.lower()


def test_a_pattern_reachable_from_no_symptom_is_caught():
    """A catalogue entry nobody can arrive at is unreachable in practice, and
    the failure is silent — the catalogue table still lists it."""
    with fixture(orphan_in_triage=True) as root:
        code, out = check(root)
    assert code != 0
    assert "[triage]" in out and "02" in out


def test_an_evidence_figure_absent_from_its_source_is_caught():
    """The whole value of EVIDENCE.md is that it restates the specimens rather
    than authoring numbers of its own. A figure that has drifted from the
    working is the failure this file could otherwise introduce."""
    with fixture(evidence_figure="0 out of 35") as root:
        code, out = check(root)
    assert code != 0
    assert "[evidence]" in out and "drifted" in out


def test_an_evidence_row_citing_no_source_is_caught():
    """A row with a figure and no working is an assertion, which is the one
    thing this file exists not to be."""
    with fixture() as root:
        ev = (root / "EVIDENCE.md").read_text()
        ev = ev.replace("[RESULTS](specimens/01-alpha/RESULTS.md)", "trust me")
        (root / "EVIDENCE.md").write_text(ev)
        code, out = check(root)
    assert code != 0
    assert "[evidence]" in out and "cites no RESULTS.md" in out


def test_an_evidence_table_missing_a_pattern_is_caught():
    with fixture(drop_evidence_row=True) as root:
        code, out = check(root)
    assert code != 0
    assert "[evidence]" in out and "rows" in out


def test_a_repository_without_an_evidence_file_still_checks_everything_else():
    with fixture(evidence=False) as root:
        code, out = check(root)
    assert code == 0, out


# ------------------------------------------------------------- the real tree


def test_the_repository_is_consistent():
    """Runs against this repository. Expected to fail until the drift it
    reports is fixed."""
    code, out = check(REPO)
    assert code == 0, "\n" + out


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
            except Exception as exc:  # noqa: BLE001
                # A crash is a failure. A runner that only counts
                # AssertionError scores a mutation that raises as a pass —
                # the exact defect the mutation run found in specimen 03.
                failures += 1
                print(f"  ERROR {name}: {type(exc).__name__}: {exc}")
    print(f"\n{failures} failure(s)")
    raise SystemExit(1 if failures else 0)
