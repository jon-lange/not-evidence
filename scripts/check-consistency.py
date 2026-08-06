#!/usr/bin/env python3
"""Assert that this repository's metadata agrees with itself.

Pattern frontmatter is the single source of truth. Every other surface — the
README table, the skills table, the generated site — is derived from it or
checked against it. Before this existed there were four hand-maintained copies
and they had drifted: two patterns were published as `field-tested` while the
README called them `draft`, and the skills README asserted a status for pattern
05 that pattern 05 did not have.

That drift is the repository's own subject matter. A catalogue arguing that the
reassuring signal is the one that is lying cannot ship a status table that
lies, and a discipline that depends on remembering is not enforcement.

Failures are reported as a diff — what the source says, what the copy says —
because a checker that reports "FAILED" without saying what teaches people to
bypass it. Same reasoning as scripts/review.sh being advisory rather than a
gate.

Run:  python3 scripts/check-consistency.py [--root DIR]
Exit: 0 consistent, 1 drift found.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

VOCABULARY = {"draft", "field-tested", "revised-by-specimen"}
SUPERSEDED = "superseded-by"

# Each RESULTS.md opens with one of these. `revised` — the number the README
# leads with — is narrowed plus central-claim-failed.
ADJUDICATIONS = {"confirmed", "narrowed", "central-claim-failed"}

# A falsification heading with nothing under it reads, from the index, exactly
# like one that states a condition. Low enough to admit a genuinely terse
# condition; high enough that a bare heading cannot pass.
FALSIFICATION_MIN_WORDS = 25

NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
}

# Every published statement of a derived count, and which count it states. The
# repository spells these as words, so they are checked as words. A claim that
# stops matching is a failure — see check_adjudication for why that matters more
# than it looks.
COUNT_CLAIMS = [
    ("README.md", r"##\s+(\w+) of the twelve entries were revised", "revised"),
    ("README.md", r"(\w+) came back changed", "revised"),
    ("README.md", r"(\w+) were contradicted\s+outright", "failed"),
    ("README.md", r"(\w+) entries were revised by measurement", "revised"),
    ("README.md", r"the (\w+) marked `revised-by-specimen`", "failed"),
    ("README.md", r"The other (\w+) were narrowed rather than overturned", "narrowed"),
    ("METHOD.md", r"(\w+)\s+of twelve entries were revised by measurement", "revised"),
    ("METHOD.md", r"and (\w+) had their central claim fail", "failed"),
    ("CLAUDE.md", r"(\w+) entries were\s+revised by their specimens", "revised"),
    ("CLAUDE.md", r"(\w+) had their central claim fail", "failed"),
    ("EVIDENCE.md", r"## The (\w+) that contradicted their own pattern", "failed"),
]

# Asserted, not trusted to survive editing. Losing this sentence is the one
# documentation regression with consequences outside the repository.
DISCLAIMER = "do not represent those of my employer"

SKIP_DIRS = {".git", ".venv", "_build", "__pycache__", "node_modules", "_generated"}


def frontmatter(text: str) -> tuple[dict, str]:
    """Same naive parser as site/build.py, deliberately. If the two disagreed
    about what a file says, the checker would be validating a different
    document from the one that gets published."""
    if not text.startswith("---"):
        return {}, text
    _, block, body = text.split("---", 2)
    meta = {}
    for line in block.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.split("#")[0].strip().strip('"')
    return meta, body.lstrip()


def valid_status(status: str) -> bool:
    return status in VOCABULARY or status.startswith(SUPERSEDED)


def markdown_files(root: Path) -> list[Path]:
    return sorted(
        p for p in root.rglob("*.md")
        if not any(part in SKIP_DIRS for part in p.parts)
    )


def table_rows(text: str) -> list[list[str]]:
    """Cells of every pipe-table row, header and separator rows dropped."""
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|") or set(line) <= set("|-: "):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows.append(cells)
    return rows


def plain(cell: str) -> str:
    """Strip the emphasis the tables use for weight, leaving the value."""
    return cell.replace("*", "").strip()


class Report:
    def __init__(self) -> None:
        self.problems: list[str] = []
        self.checked: dict[str, int] = {}

    def fail(self, rule: str, detail: str) -> None:
        self.problems.append(f"  [{rule}] {detail}")

    def count(self, what: str, n: int) -> None:
        self.checked[what] = n


# --------------------------------------------------------------- the rules


def check_patterns(root: Path, rep: Report) -> dict[str, dict]:
    """Frontmatter is the source. Everything here validates the source itself."""
    patterns: dict[str, dict] = {}
    files = sorted((root / "patterns").glob("*.md")) if (root / "patterns").is_dir() else []

    for path in files:
        rel = path.relative_to(root)
        meta, _ = frontmatter(path.read_text())
        if not meta:
            rep.fail("frontmatter", f"{rel}: no frontmatter block, or it is malformed")
            continue
        num = meta.get("pattern", "").strip()
        if not num:
            rep.fail("frontmatter", f"{rel}: missing `pattern:` key")
            continue

        status = meta.get("status", "")
        if not valid_status(status):
            rep.fail(
                "status-vocabulary",
                f"{rel}: status {status!r} is outside the vocabulary "
                f"({', '.join(sorted(VOCABULARY))}, {SUPERSEDED}: NN)",
            )

        specimen = meta.get("specimen", "")
        if specimen:
            target = root / "specimens" / specimen
            if not target.is_dir():
                rep.fail(
                    "specimen-key",
                    f"{rel}: specimen {specimen!r} does not resolve to "
                    f"specimens/{specimen}/",
                )
            elif not re.fullmatch(r"\d{2}-[a-z0-9-]+", specimen):
                rep.fail(
                    "specimen-key",
                    f"{rel}: specimen {specimen!r} is not a directory slug "
                    "(convention is NN-lowercase-hyphenated)",
                )

        patterns[num] = {
            "status": status,
            "name": meta.get("name", ""),
            "path": rel,
            "specimen": specimen,
        }

    if not patterns:
        rep.fail("no-patterns", f"no patterns found under {root}/patterns/ — "
                                "a clean result from here would mean nothing")
    rep.count("patterns", len(patterns))
    return patterns


def check_readme_table(root: Path, patterns: dict[str, dict], rep: Report) -> None:
    readme = root / "README.md"
    if not readme.is_file():
        rep.fail("readme", "README.md is missing")
        return
    text = readme.read_text()

    if DISCLAIMER not in text:
        rep.fail("disclaimer", "README.md no longer contains the employer disclaimer")

    seen = 0
    for cells in table_rows(text):
        num = plain(cells[0])
        if num not in patterns or len(cells) < 4:
            continue
        seen += 1
        claimed, actual = plain(cells[-1]), patterns[num]["status"]
        if claimed != actual:
            rep.fail(
                "readme-status",
                f"pattern {num}: README.md says {claimed!r}, "
                f"{patterns[num]['path']} says {actual!r}",
            )
    if seen != len(patterns):
        rep.fail(
            "readme-status",
            f"README.md catalogue table has {seen} rows for {len(patterns)} patterns",
        )
    rep.count("README rows", seen)


def check_skills(root: Path, patterns: dict[str, dict], rep: Report) -> None:
    """A skill may not claim more than the pattern it operationalises. It may
    claim less — a new skill can be draft against a measured pattern."""
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        return

    skills: dict[str, str] = {}
    for path in sorted(skills_dir.glob("*/SKILL.md")):
        rel = path.relative_to(root)
        meta, _ = frontmatter(path.read_text())
        name = meta.get("name", "")
        if name != path.parent.name:
            rep.fail("skill-name", f"{rel}: name {name!r} != directory {path.parent.name!r}")
        status, pattern = meta.get("status", ""), meta.get("pattern", "").strip()

        if pattern not in patterns:
            rep.fail("skill-pattern", f"{rel}: pattern {pattern!r} does not exist")
        else:
            allowed = {"draft", patterns[pattern]["status"]}
            if status not in allowed:
                rep.fail(
                    "skill-status",
                    f"{rel}: status {status!r} but pattern {pattern} is "
                    f"{patterns[pattern]['status']!r} — a skill may be `draft` "
                    "or match its pattern, never claim more",
                )
        skills[path.parent.name] = status

    index = skills_dir / "README.md"
    if index.is_file():
        for cells in table_rows(index.read_text()):
            match = re.search(r"\[([a-z0-9-]+)\]", cells[0])
            if not match or match.group(1) not in skills or len(cells) < 3:
                continue
            name = match.group(1)
            claimed, actual = plain(cells[2]), skills[name]
            if claimed != actual:
                rep.fail(
                    "skills-readme",
                    f"{name}: skills/README.md says {claimed!r}, "
                    f"skills/{name}/SKILL.md says {actual!r}",
                )
    rep.count("skills", len(skills))


def check_triage(root: Path, patterns: dict[str, dict], rep: Report) -> None:
    """Every pattern must be reachable from a symptom a reader would recognise.
    An entry nobody can arrive at is unreachable in practice however good it is,
    and the failure is silent — the catalogue table still lists it."""
    readme = root / "README.md"
    if not readme.is_file():
        return
    section = re.search(r"\n## Start here\n(.*?)(?=\n## )", readme.read_text(), re.S)
    if not section:
        return

    reachable = set(re.findall(r"\(patterns/(\d{2})-", section.group(1)))
    orphans = sorted(set(patterns) - reachable)
    if orphans:
        rep.fail(
            "triage",
            f"pattern(s) {', '.join(orphans)} are in the catalogue but reachable "
            "from no symptom in the Start here table",
        )
    rep.count("triage routes", len(reachable))


def check_evidence(root: Path, patterns: dict[str, dict], rep: Report) -> None:
    """EVIDENCE.md aggregates figures that live in the specimens. It must never
    become a second place where a number is authored — every backticked figure
    has to appear verbatim in the RESULTS.md the row cites, or the summary can
    drift from the working and nothing would notice."""
    evidence = root / "EVIDENCE.md"
    if not evidence.is_file():
        return

    rows = 0
    for cells in table_rows(evidence.read_text()):
        num = plain(cells[0])
        if num not in patterns or len(cells) < 3:
            continue
        rows += 1

        link = re.search(r"\]\(([^)]*RESULTS\.md)\)", cells[-1])
        if not link:
            rep.fail("evidence", f"pattern {num}: row cites no RESULTS.md")
            continue
        source = (root / link.group(1)).resolve()
        if not source.is_file():
            rep.fail("evidence", f"pattern {num}: {link.group(1)} does not exist")
            continue

        text = source.read_text()
        for figure in re.findall(r"`([^`]+)`", " ".join(cells[1:-1])):
            if figure not in text:
                rep.fail(
                    "evidence",
                    f"pattern {num}: figure {figure!r} does not appear in "
                    f"{link.group(1)} — the summary has drifted from the working",
                )

    if rows != len(patterns):
        rep.fail(
            "evidence",
            f"EVIDENCE.md has {rows} rows for {len(patterns)} patterns",
        )
    rep.count("evidence rows", rows)


def check_specimens_index(root: Path, patterns: dict[str, dict], rep: Report) -> None:
    """specimens/README.md is an index, not a status surface.

    It was a fifth copy of the metadata in a vocabulary of its own — every row
    said `built`, and two carried hand-written notes about a prediction not
    holding. By the time anyone read them, five entries had had their central
    claim fail and the table named two. Nothing checked it, because nothing
    read it.

    So the rule is shape, not agreement: one row per pattern, and no status or
    adjudication term anywhere in the table. Asserting the *absence* of the
    vocabulary is what stops the column growing back, which is the failure that
    actually happened."""
    index = root / "specimens" / "README.md"
    if not index.is_file():
        return

    rows = [c for c in table_rows(index.read_text()) if plain(c[0]) in patterns]
    seen = {plain(c[0]) for c in rows}

    for num in sorted(set(patterns) - seen):
        rep.fail("specimens-index", f"pattern {num} has no row in specimens/README.md")
    if len(rows) != len(seen):
        rep.fail("specimens-index", f"{len(rows)} rows for {len(seen)} distinct patterns")

    forbidden = VOCABULARY | ADJUDICATIONS
    for cells in rows:
        for term in sorted(forbidden):
            if any(term in plain(cell) for cell in cells):
                rep.fail(
                    "specimens-index",
                    f"pattern {plain(cells[0])}: the row states {term!r}. Status lives in "
                    "pattern frontmatter and outcomes live in RESULTS.md — a copy here is "
                    "the drift this rule exists to prevent",
                )
    rep.count("specimen index rows", len(rows))


def check_adjudication(root: Path, patterns: dict[str, dict], rep: Report) -> None:
    """The headline claim — how many entries their own specimens revised — used
    to be asserted in five places and derived from nothing. It was the only
    claim in the repository that nothing checked, which made it the exact
    failure the eleventh entry is about.

    Now every RESULTS.md opens with an adjudication, the counts are derived from
    those twelve lines, and every published copy is checked against the
    derivation. `revised` is narrowed + central-claim-failed; `confirmed` is
    neither.

    Note what makes this rule non-vacuous: an unmatched claim pattern is a
    failure, not a skip. A regex that silently stops matching after someone
    rephrases a sentence would check nothing and print what a correct run
    prints."""
    verdicts: dict[str, str] = {}
    # `draft` means written and not yet measured, so there is nothing to
    # adjudicate and demanding a verdict would force one to be invented.
    measured = {n: m for n, m in patterns.items() if m.get("status") != "draft"}

    for num, meta in sorted(measured.items()):
        specimen = meta.get("specimen", "")
        if not specimen:
            continue
        results = root / "specimens" / specimen / "RESULTS.md"
        if not results.is_file():
            rep.fail("adjudication", f"pattern {num}: {specimen}/RESULTS.md does not exist")
            continue

        found = re.search(r"\*\*Adjudication:\s*([a-z-]+)\.\*\*", results.read_text())
        if not found:
            rep.fail(
                "adjudication",
                f"pattern {num}: {specimen}/RESULTS.md carries no `**Adjudication: ...**` "
                "line, so the revision count cannot be derived from it",
            )
            continue
        verdict = found.group(1)
        if verdict not in ADJUDICATIONS:
            rep.fail(
                "adjudication",
                f"pattern {num}: adjudication {verdict!r} is outside the vocabulary "
                f"({', '.join(sorted(ADJUDICATIONS))})",
            )
            continue
        verdicts[num] = verdict

    if len(verdicts) != len(measured):
        rep.fail(
            "adjudication",
            f"{len(verdicts)} adjudications for {len(measured)} measured patterns — "
            "an incomplete count is not a count",
        )
    rep.count("adjudications", len(verdicts))

    # The status vocabulary and the adjudication vocabulary have to describe the
    # same twelve outcomes, or one of them is decorative.
    failed = {n for n, v in verdicts.items() if v == "central-claim-failed"}
    marked = {n for n, m in patterns.items() if m.get("status") == "revised-by-specimen"}
    for num in sorted(failed - marked):
        rep.fail(
            "adjudication",
            f"pattern {num}: adjudicated central-claim-failed but frontmatter says "
            f"{patterns[num]['status']!r}, not 'revised-by-specimen'",
        )
    for num in sorted(marked - failed):
        rep.fail(
            "adjudication",
            f"pattern {num}: frontmatter says 'revised-by-specimen' but its specimen "
            f"adjudicated {verdicts.get(num, '<missing>')!r}",
        )

    derived = {
        "revised": sum(1 for v in verdicts.values() if v in ("narrowed", "central-claim-failed")),
        "failed": len(failed),
        "narrowed": sum(1 for v in verdicts.values() if v == "narrowed"),
        "confirmed": sum(1 for v in verdicts.values() if v == "confirmed"),
    }

    claims = 0
    for filename, pattern, key in COUNT_CLAIMS:
        path = root / filename
        if not path.is_file():
            # Absent surfaces are not this rule's business — a missing METHOD.md
            # is a different problem, caught elsewhere or not a problem at all.
            # A file that *exists* and no longer matches is the dangerous case,
            # and that falls through to the failure below.
            continue
        match = re.search(pattern, path.read_text(), re.S)
        if not match:
            rep.fail(
                "adjudication",
                f"{filename}: no text matched the {key} claim /{pattern}/ — the sentence "
                "was rephrased and this rule silently stopped checking it",
            )
            continue
        claims += 1
        stated = NUMBER_WORDS.get(match.group(1).lower())
        if stated is None:
            rep.fail(
                "adjudication",
                f"{filename}: {match.group(1)!r} is not a number word this rule can read",
            )
        elif stated != derived[key]:
            rep.fail(
                "adjudication",
                f"{filename}: says {match.group(1)!r} for {key}, but the twelve "
                f"RESULTS.md adjudications derive {derived[key]}",
            )
    if verdicts and not claims:
        rep.fail(
            "adjudication",
            f"{len(verdicts)} specimens were adjudicated and not one published count was "
            "checked against them — the derivation exists and nothing reads it",
        )
    rep.count("derived count claims", claims)


def check_falsification(root: Path, patterns: dict[str, dict], rep: Report) -> None:
    """CONTRIBUTING.md says a contradicting result is the most valuable thing
    anyone can send. Three specimens did not say what would contradict them,
    which makes that ask unanswerable for a quarter of the catalogue.

    A heading alone is not enough. An empty section is the absence-test this
    repository is named for, so the section has to carry prose."""
    measured = {n: m for n, m in patterns.items() if m.get("status") != "draft"}
    complete = 0

    for num, meta in sorted(measured.items()):
        specimen = meta.get("specimen", "")
        if not specimen:
            continue
        results = root / "specimens" / specimen / "RESULTS.md"
        if not results.is_file():
            continue

        text = results.read_text()
        section = re.search(
            r"^##[^\n]*\b(falsif\w*)\b[^\n]*$(.*?)(?=^## |\Z)",
            text, re.M | re.I | re.S,
        )
        if not section:
            rep.fail(
                "falsification",
                f"pattern {num}: {specimen}/RESULTS.md names no condition that would "
                "falsify it, while CONTRIBUTING.md asks readers to send exactly that",
            )
            continue
        if len(section.group(2).split()) < FALSIFICATION_MIN_WORDS:
            rep.fail(
                "falsification",
                f"pattern {num}: the falsification section in {specimen}/RESULTS.md is "
                "a heading with nothing under it — an empty absence-test",
            )
            continue
        complete += 1

    rep.count("falsification conditions", complete)


def check_links(root: Path, rep: Report) -> None:
    n = 0
    for path in markdown_files(root):
        for match in re.finditer(r"\]\(([^)]+)\)", path.read_text()):
            target = match.group(1).split("#")[0].strip()
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            n += 1
            if not (path.parent / target).resolve().exists():
                rep.fail(
                    "link",
                    f"{path.relative_to(root)} -> {target} does not resolve",
                )
    rep.count("relative links", n)


def check_make_targets(root: Path, rep: Report) -> None:
    """Only backticked or fenced `make x` is considered. Matching bare prose
    would fire on 'make sure' and train people to ignore the hook.

    docs/ is skipped for the same reason. Planning and audit documents quote
    targets that do not exist yet, and targets that were removed and are being
    described as findings — both legitimate, neither a defect. A rule that
    fires on a document *about* a missing target is the false positive
    CLAUDE.md warns about."""
    makefile = root / "Makefile"
    if not makefile.is_file():
        return
    defined = set(re.findall(r"^([a-z][a-z0-9-]*):", makefile.read_text(), re.M))

    n = 0
    for path in markdown_files(root):
        if "docs" in path.relative_to(root).parts:
            continue
        text = path.read_text()
        referenced = set(re.findall(r"`make ([a-z][a-z0-9-]*)`", text))
        for block in re.findall(r"```[a-z]*\n(.*?)```", text, re.S):
            referenced |= set(re.findall(r"^\s*make ([a-z][a-z0-9-]*)", block, re.M))
        for target in sorted(referenced):
            n += 1
            if target not in defined:
                rep.fail(
                    "make-target",
                    f"{path.relative_to(root)} documents `make {target}`, "
                    "which the Makefile does not define",
                )
    rep.count("make references", n)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=Path(__file__).resolve().parent.parent, type=Path)
    args = ap.parse_args()
    root = args.root.resolve()

    rep = Report()
    patterns = check_patterns(root, rep)
    check_readme_table(root, patterns, rep)
    check_skills(root, patterns, rep)
    check_triage(root, patterns, rep)
    check_evidence(root, patterns, rep)
    check_specimens_index(root, patterns, rep)
    check_adjudication(root, patterns, rep)
    check_falsification(root, patterns, rep)
    check_links(root, rep)
    check_make_targets(root, rep)

    summary = ", ".join(f"{v} {k}" for k, v in rep.checked.items())
    if rep.problems:
        print(f"BLOCKED - {len(rep.problems)} inconsistency(ies) found\n")
        print("\n".join(rep.problems))
        print(f"\n  checked: {summary}")
        return 1

    print(f"  metadata consistent — checked: {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
