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

        patterns[num] = {"status": status, "name": meta.get("name", ""), "path": rel}

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
    check_evidence(root, patterns, rep)
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
