#!/usr/bin/env python3
"""Emit this catalogue as an Open Knowledge Format bundle.

    python3 scripts/emit-okf.py            # write okf/
    python3 scripts/emit-okf.py --check    # fail if okf/ is not current

OKF v0.2 is a directory of markdown files with YAML frontmatter, designed so a
knowledge corpus is portable across tools and readable by agents without a
bespoke SDK. Spec: https://github.com/GoogleCloudPlatform/knowledge-catalog

This repository turned out to already be one, structurally: markdown concepts,
frontmatter, and a cross-linked graph that something already validates. What
this producer adds is the vocabulary — and the mapping is close enough to be
worth stating, because it is the argument for the whole exercise:

    pattern              -> type: Pattern
    specimen             -> type: Attested Computation
    probe.py / tests     -> executor.resource
    scripts/check-consistency.py -> attester.resource
    status:              -> verified[] and a trust tier
    prior art citations  -> sources[]
    adjudication         -> producer extension, preserved verbatim

`Attested Computation` is the fit worth noticing. The spec defines it as a
concept carrying "a sanctioned way to compute a value, so a consumer can confirm
the value was produced by running it" — which is what a specimen is, and why
every figure in this catalogue ships with the harness that produced it.

The bundle is committed rather than generated on demand, because OKF's own
argument is that a bundle should be clonable and browsable. Committed generated
output drifts, so `--check` runs in CI and fails when it has.
"""

from __future__ import annotations

import argparse
import posixpath
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "okf"

REPO_URL = "https://github.com/jon-lange/not-evidence"
SITE_URL = "https://jon-lange.github.io/not-evidence"

# The producer, in OKF's actor convention (SPEC §7).
PRODUCER = "process:emit-okf/0.1"
AUTHOR = "human:jon-lange"


def frontmatter(text: str) -> tuple[dict, str]:
    """Same naive parser as site/build.py and check-consistency.py, on purpose.
    Three parsers disagreeing about what a file says is how a published surface
    ends up asserting something the source does not."""
    if not text.startswith("---"):
        return {}, text
    _, block, body = text.split("---", 2)
    meta = {}
    for line in block.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.split("#")[0].strip().strip('"')
    return meta, body.lstrip()


def yaml_str(value: str) -> str:
    """Quote only when the value could be misread. Unquoted where safe keeps the
    frontmatter readable, which is the format's entire selling point."""
    if value == "" or re.search(r'[:#\[\]{}",\n]|^\s|\s$', value):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return value


def git_iso(path: Path) -> str:
    """Last commit touching this file, as the content's last meaningful change."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", str(path.relative_to(ROOT))],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        return out or "1970-01-01T00:00:00Z"
    except (subprocess.CalledProcessError, OSError):
        return "1970-01-01T00:00:00Z"


def citations(body: str) -> list[tuple[str, str]]:
    """Prior-art links, as (url, title). Every one was fetched and verified
    before publication, which is what makes them usable as `sources`."""
    found = []
    section = re.search(r"^## Prior art(.*?)(?=^## |\Z)", body, re.M | re.S)
    # Group 1 is the link text, group 2 the URL. Naming them is not decoration:
    # the first version bound them the other way round and emitted every source
    # with `resource` and `title` transposed.
    for text, href in re.findall(r"\[([^\]]+)\]\((https?://[^)]+)\)",
                                 section.group(1) if section else ""):
        found.append((text, href))
    return found


def adjudication(results: str) -> str:
    m = re.search(r"\*\*Adjudication:\s*([a-z-]+)\.\*\*", results)
    return m.group(1) if m else ""


def falsification(results: str) -> str:
    m = re.search(r"^##[^\n]*\bfalsif\w*\b[^\n]*$(.*?)(?=^## |\Z)",
                  results, re.M | re.I | re.S)
    return m.group(1).strip() if m else ""


# ------------------------------------------------------------------ emitting


def pattern_concept(num: str, meta: dict, body: str, path: Path,
                    adj: str, specimen: str) -> str:
    """A pattern is a claim about how a system should behave."""
    title = meta.get("name", "")
    refuses = meta.get("refuses", "")
    status = meta.get("status", "")

    lines = [
        "---",
        "type: Pattern",
        f"title: {yaml_str(f'{num} · {title}')}",
        f"description: {yaml_str('Refuses ' + refuses + '.' if refuses else title)}",
        f"resource: {SITE_URL}/patterns/{path.stem}.html",
        f"tags: [pattern, {status}]",
        # Producer extensions. The spec invites these and requires consumers to
        # tolerate them (§4.1).
        f"pattern_status: {status}",
    ]
    if adj:
        lines.append(f"adjudication: {adj}")
    lines += [
        f"generated: {{ by: {AUTHOR}, at: {git_iso(path)} }}",
        # Trust tiers (§5.3): a specimen measuring the claim is a machine
        # confirmation; the author reading the result is the human one.
        "verified:",
        f"  - {{ by: process:specimen/{specimen}, at: {git_iso(path)} }}",
        f"  - {{ by: {AUTHOR}, at: {git_iso(path)} }}",
    ]

    sources = citations(body)
    if sources:
        lines.append("sources:")
        for i, (title_, url) in enumerate(sources, 1):
            lines.append(f"  - id: ref-{i}")
            lines.append(f"    resource: {url}")
            lines.append(f"    title: {yaml_str(title_)}")
    lines.append("---")

    lines += [
        "",
        f"# {num} · {title}",
        "",
        f"> **Refuses {refuses}.**" if refuses else "",
        "",
        f"**Status:** `{status}`"
        + (f" · **Adjudication:** `{adj}`" if adj else ""),
        "",
        f"Measured by [{specimen}](../specimens/{specimen}.md).",
        "",
        "The full entry — Context, Forces, The Refusal, Consequences, the naive",
        "approach it beats, and prior art — is in the source document:",
        "",
        f"- [Read the pattern]({REPO_URL}/blob/main/patterns/{path.name})",
        f"- [Rendered]({SITE_URL}/patterns/{path.stem}.html)",
        "",
    ]
    return "\n".join(l for l in lines if l is not None) + "\n"


def specimen_concept(num: str, slug: str, pattern_name: str, pattern_stem: str,
                     results_path: Path, adj: str, falsif: str) -> str:
    """A specimen is an Attested Computation: the sanctioned way to compute the
    figure, shipped so a consumer can confirm it rather than trust it."""
    offline = slug in {
        "02-refuse-the-class", "06-unratified-weights",
        "11-mutation-check", "12-sanitization-label",
    }
    runner = "probe.py" if (ROOT / "specimens" / slug / "probe.py").is_file() else "test_*.py"

    lines = [
        "---",
        "type: Attested Computation",
        f"title: {yaml_str(f'Specimen {num} · {pattern_name}')}",
        f"description: {yaml_str('The measurement behind pattern ' + num + '.')}",
        f"resource: {REPO_URL}/tree/main/specimens/{slug}",
        f"tags: [specimen, measurement, {'offline' if offline else 'live'}]",
        "runtime: python",
        "executor:",
        f"  resource: {REPO_URL}/blob/main/specimens/{slug}/{runner}",
        "  receipt: [results_jsonl, stdout, exit_code]",
        "attester:",
        # check-consistency.py is deterministic, LLM-free, and returns a verdict
        # — which is what §10.2 asks an attester to be.
        f"  resource: {REPO_URL}/blob/main/scripts/check-consistency.py",
    ]
    if adj:
        lines.append(f"adjudication: {adj}")
    lines += [
        f"generated: {{ by: {AUTHOR}, at: {git_iso(results_path)} }}",
        "verified:",
        f"  - {{ by: {PRODUCER}, at: {git_iso(results_path)} }}",
        f"  - {{ by: {AUTHOR}, at: {git_iso(results_path)} }}",
        "---",
        "",
        f"# Specimen {num} · {pattern_name}",
        "",
        f"Measures [pattern {num}](../patterns/{pattern_stem}.md).",
        "",
        "# Computation",
        "",
        "```bash",
        f"cd specimens/{slug}",
    ]
    lines.append("python3 probe.py            # offline, no key, no network"
                 if offline else
                 "python3 probe.py            # live: needs credentials, costs money")
    lines += ["```", ""]

    if adj:
        lines += [f"**Adjudication:** `{adj}` — whether the pattern's central "
                  "claim survived measurement.", ""]
    if falsif:
        lines += ["# What would falsify this", "", falsif, ""]

    lines += [
        "# Full record",
        "",
        f"- [RESULTS.md]({REPO_URL}/blob/main/specimens/{slug}/RESULTS.md) — what was "
        "run, what came back, the scope, and the falsification condition",
        f"- [Specimen source]({REPO_URL}/tree/main/specimens/{slug})",
        "",
    ]
    return "\n".join(lines) + "\n"


def build(root: Path) -> dict[str, str]:
    """Return {relative path: content} for the whole bundle."""
    files: dict[str, str] = {}
    patterns = sorted((root / "patterns").glob("*.md"))
    rows = []

    for path in patterns:
        meta, body = frontmatter(path.read_text())
        num = meta.get("pattern", "")
        slug = meta.get("specimen", "")
        results = root / "specimens" / slug / "RESULTS.md"
        results_text = results.read_text() if results.is_file() else ""
        adj = adjudication(results_text)

        files[f"patterns/{path.stem}.md"] = pattern_concept(
            num, meta, body, path, adj, slug)
        files[f"specimens/{slug}.md"] = specimen_concept(
            num, slug, meta.get("name", ""), path.stem,
            results if results.is_file() else path,
            adj, falsification(results_text))
        rows.append((num, meta.get("name", ""), meta.get("status", ""), adj,
                     path.stem, slug))

    files["patterns/index.md"] = index_page(
        "Patterns",
        "Twelve claims about systems that have to decline correctly. Each states "
        "a refusal so it can be violated, and each is measured by a specimen.",
        [(f"{n} · {name}", f"{stem}.md", f"`{status}`"
          + (f" · adjudication `{adj}`" if adj else ""))
         for n, name, status, adj, stem, _ in rows],
    )
    files["specimens/index.md"] = index_page(
        "Specimens",
        "One Attested Computation per pattern. Each ships the harness that "
        "produced its figures, so a consumer can confirm rather than trust.",
        [(f"Specimen {n} · {name}", f"{slug}.md",
          f"adjudication `{adj}`" if adj else "")
         for n, name, _, adj, _, slug in rows],
    )
    files["index.md"] = root_index(rows)

    # Exactly one trailing newline per file. Without this the producer emits a
    # blank final line, pre-commit's end-of-file-fixer strips it, and the next
    # `--check` reports drift the producer immediately undoes — a generator and
    # a formatter taking turns reverting each other forever.
    return {rel: content.rstrip("\n") + "\n" for rel, content in files.items()}


def index_page(title: str, description: str,
               entries: list[tuple[str, str, str]]) -> str:
    lines = [
        "---",
        "type: Index",
        f"title: {yaml_str(title)}",
        f"description: {yaml_str(description)}",
        "---",
        "",
        f"# {title}",
        "",
        description,
        "",
    ]
    for label, href, note in entries:
        lines.append(f"- [{label}]({href})" + (f" — {note}" if note else ""))
    lines.append("")
    return "\n".join(lines) + "\n"


def root_index(rows: list[tuple]) -> str:
    revised = sum(1 for r in rows if r[3] in ("narrowed", "central-claim-failed"))
    failed = sum(1 for r in rows if r[3] == "central-claim-failed")
    return f"""---
type: Index
title: Not Evidence
description: {yaml_str(
    'Twelve signals that look like evidence and are not, each paired with the '
    'refusal that closes it and the measurement that tested it.')}
resource: {SITE_URL}/
tags: [evaluation, guardrails, llm, agents, testing]
---

# Not Evidence

An OKF bundle of {len(rows)} patterns and {len(rows)} attested computations.

The guardrail that refused the obvious attack. The green test that never ran.
The judge that shares the subject's lineage. The label that says "sanitized."
Every one is reassuring, every one is routinely accepted as proof, and none is
evidence of the thing it is taken to prove.

Every claim here was put in front of a specimen before publication.
**{revised} of {len(rows)} entries were revised by their own specimens**, and
{failed} had their central claim fail. No figure appears that was not generated
in the source repository.

- [Patterns](patterns/index.md) — the claims
- [Specimens](specimens/index.md) — the measurements, as Attested Computations

Each specimen names what would falsify it. A contradicting result is the most
useful thing anyone can send.

Source: [{REPO_URL}]({REPO_URL}) · Rendered: [{SITE_URL}]({SITE_URL})
"""


RESERVED = {"index.md", "log.md"}


def conformance(files: dict[str, str]) -> list[str]:
    """Check the emitted bundle against the parts of OKF v0.2 that are rules
    rather than recommendations.

    Standard library only, like everything else here. Frontmatter is parsed with
    the same naive reader the rest of the repository uses — three parsers
    disagreeing about a document is how a published surface ends up asserting
    something its source does not."""
    problems: list[str] = []

    for rel, content in sorted(files.items()):
        name = Path(rel).name
        if not content.startswith("---\n"):
            problems.append(f"{rel}: no frontmatter block")
            continue
        meta, body = frontmatter(content)
        # §4.1: `type` is the only always-required key.
        if not meta.get("type"):
            problems.append(f"{rel}: missing required key `type`")
        # §3.1: reserved filenames must be the thing they say they are.
        if name == "index.md" and meta.get("type") != "Index":
            problems.append(f"{rel}: index.md must be the directory listing")
        if name not in RESERVED and meta.get("type") == "Index":
            problems.append(f"{rel}: type Index on a non-index document")
        # §10.2: runtime is REQUIRED on an Attested Computation.
        if meta.get("type") == "Attested Computation" and not meta.get("runtime"):
            problems.append(f"{rel}: Attested Computation without `runtime`")
        # §6: bundle-relative links have to resolve, or the graph is a claim.
        for _, href in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", body):
            if href.startswith(("http://", "https://", "#", "mailto:")):
                continue
            # Lexical, and normalised so `../` actually resolves. Purely
            # lexical because the bundle is a dict here, not a directory —
            # checking what will be written rather than what happens to be
            # on disk from a previous run.
            target = posixpath.normpath(
                posixpath.join(posixpath.dirname(rel), href.split("#")[0]))
            if target not in files:
                problems.append(f"{rel}: link -> {href} resolves to nothing in the bundle")

    for required in ("index.md", "patterns/index.md", "specimens/index.md"):
        if required not in files:
            problems.append(f"missing {required}")

    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="fail if the committed bundle is not current")
    args = ap.parse_args()

    files = build(ROOT)

    if args.check:
        # Conformance first, then currency. A bundle that is byte-identical to
        # what the producer emits is still worthless if the producer emits
        # something the spec rejects — the diff would agree with itself and
        # prove nothing.
        bad = conformance(files)
        if bad:
            print(f"BLOCKED - {len(bad)} OKF conformance problem(s)\n")
            for line in bad:
                print(f"  {line}")
            return 1

        stale = []
        for rel, content in sorted(files.items()):
            existing = OUT / rel
            if not existing.is_file() or existing.read_text() != content:
                stale.append(rel)
        orphans = [str(p.relative_to(OUT)) for p in OUT.rglob("*.md")
                   if str(p.relative_to(OUT)) not in files] if OUT.is_dir() else []
        if stale or orphans:
            print("BLOCKED - the committed OKF bundle is not current\n")
            for rel in stale:
                print(f"  stale:  {rel}")
            for rel in orphans:
                print(f"  orphan: {rel}")
            print("\n  Regenerate with: make okf")
            return 1
        print(f"  OKF bundle current — {len(files)} concepts")
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        dest = OUT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content)
    print(f"  {len(files)} concepts -> {OUT.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
