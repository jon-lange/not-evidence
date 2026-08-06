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

| # | Pattern | Refuses | Status |
|---|---|---|---|
| 01 | [Alpha](patterns/01-alpha.md) | to do the thing | **{s1}** |
| 02 | [Beta](patterns/02-beta.md) | to do the thing | {s2} |

Run `make test` to see it.

**The views expressed here are my own and do not represent those of my employer
or any client.**
"""

MAKEFILE = "test:\n\t@echo ok\n"


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
        "skill_pattern": "01",
        "skill_status": "field-tested",
        "readme_s1": "field-tested",
        "readme_s2": "draft",
        "skills_readme_status": "field-tested",
        "disclaimer": True,
        "link_target": "02-beta",
        "make_target": "test",
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
        (root / "specimens" / slug / "RESULTS.md").write_text("# results\n")

    (root / "patterns" / "01-alpha.md").write_text(
        PATTERN.format(
            num="01", name="Alpha", status=opt["p1_status"],
            specimen=opt["p1_specimen"], other=opt["link_target"],
            body=opt["p1_body_specimen"] or opt["p1_specimen"],
        )
    )
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

    body = README.format(s1=opt["readme_s1"], s2=opt["readme_s2"])
    body = body.replace("make test", f"make {opt['make_target']}")
    if opt["drop_readme_row"]:
        body = "\n".join(l for l in body.splitlines() if not l.startswith("| 02 "))
    if not opt["disclaimer"]:
        body = body.split("**The views")[0]
    (root / "README.md").write_text(body)
    (root / "Makefile").write_text(MAKEFILE)


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
    with fixture(p2_status="revised-by-specimen", readme_s2="revised-by-specimen") as root:
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
