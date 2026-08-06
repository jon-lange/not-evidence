"""Build a static mirror with metadata GitHub cannot emit.

A GitHub blob page titles itself with the file path, shares the repository's
meta description across every file, generates an identical preview image for
all of them, and carries no canonical tag. For a link pasted into Slack or
LinkedIn — which is where these actually travel — that renders as a generic
repository card, every time.

This emits one page per pattern and per skill with its own <title>, its own
description, its own OG card, and a canonical URL pointing at a domain you own.
Markdown in the repo stays the source of truth; this is a projection of it.

Usage:
    python3 build.py --base-url https://your-domain.example
    python3 build.py --check          # verify metadata without writing

One build dependency (`markdown`). Nothing at runtime — the output is static
HTML with no JavaScript.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "_build"

# Description length that survives both Slack's unfurl and a search result.
DESC_MAX = 200


def frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    _, block, body = text.split("---", 2)
    meta = {}
    for line in block.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.split("#")[0].strip().strip('"')
    return meta, body.lstrip()


def description(body: str, meta: dict | None = None) -> str:
    """Prefer a purpose-written description, then the claim blockquote.

    Skills carry a frontmatter `description` written to tell an agent when to
    trigger them — which reads well as a summary and is already the author's
    own one-line statement. Patterns carry the claim as a blockquote under the
    H1. Falling through to the first paragraph produces something generic, so
    it is the last resort rather than the default.
    """
    if meta and meta.get("description"):
        d = re.sub(r"\s+", " ", meta["description"]).strip()
        return (d[:DESC_MAX].rsplit(" ", 1)[0] + "…") if len(d) > DESC_MAX else d
    m = re.search(r"^>\s*\*\*(.+?)\*\*", body, re.M)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()
    for para in body.split("\n\n"):
        p = para.strip()
        if p and not p.startswith(("#", ">", "|", "-", "`")):
            flat = re.sub(r"[*_`\[\]]", "", re.sub(r"\s+", " ", p))
            return (flat[:DESC_MAX] + "…") if len(flat) > DESC_MAX else flat
    return ""


def title_of(body: str, fallback: str) -> str:
    m = re.search(r"^#\s+(.+)$", body, re.M)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else fallback


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Refusal Engineering</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="Refusal Engineering">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<style>
:root{{--fg:#16181d;--mut:#5b6270;--line:#e3e6ea;--bg:#fff;--accent:#0b5fff}}
@media(prefers-color-scheme:dark){{:root{{--fg:#e6e8ec;--mut:#9aa3b2;--line:#2a2f37;--bg:#14161a;--accent:#7aa2ff}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);
 font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}}
main{{max-width:44rem;margin:0 auto;padding:3rem 1.25rem 6rem}}
h1{{font-size:1.9rem;line-height:1.25;margin:0 0 .4rem}}
h2{{font-size:1.15rem;margin:2.4rem 0 .6rem;padding-top:1.2rem;border-top:1px solid var(--line)}}
h3{{font-size:1rem;margin:1.6rem 0 .4rem}}
blockquote{{margin:0 0 2rem;padding:.6rem 0 .6rem 1rem;border-left:3px solid var(--accent);color:var(--mut)}}
blockquote p{{margin:0}}
table{{border-collapse:collapse;width:100%;display:block;overflow-x:auto;margin:1.2rem 0;font-size:.92rem}}
th,td{{border:1px solid var(--line);padding:.45rem .6rem;text-align:left}}
th{{background:color-mix(in srgb,var(--fg) 6%,transparent)}}
code{{font-size:.9em;background:color-mix(in srgb,var(--fg) 8%,transparent);padding:.1rem .3rem;border-radius:3px}}
pre{{overflow-x:auto;padding:.9rem;border:1px solid var(--line);border-radius:6px}}
pre code{{background:none;padding:0}}
a{{color:var(--accent)}}
nav{{font-size:.9rem;margin-bottom:2.5rem}}
nav a{{text-decoration:none}}
footer{{margin-top:4rem;padding-top:1.2rem;border-top:1px solid var(--line);color:var(--mut);font-size:.85rem}}
</style>
</head>
<body><main>
<nav><a href="{root}">Refusal Engineering</a></nav>
{content}
<footer>
<p>{status_line}</p>
<p>Source: <a href="{source}">{source_label}</a>. Views my own; nothing here is derived from or
discloses confidential information of any employer.</p>
</footer>
</main></body>
</html>
"""


def render(md_text: str) -> str:
    import markdown

    return markdown.markdown(
        md_text, extensions=["tables", "fenced_code", "toc", "sane_lists"]
    )


def build(base_url: str, check_only: bool = False) -> int:
    base = base_url.rstrip("/")
    pages, problems = [], []

    sources = [(p, "patterns") for p in sorted((ROOT / "patterns").glob("*.md"))]
    sources += [
        (p, "skills")
        for p in sorted((ROOT / "skills").glob("*/SKILL.md"))
    ]

    for path, kind in sources:
        meta, body = frontmatter(path.read_text())
        slug = path.stem if kind == "patterns" else path.parent.name
        title = title_of(body, slug)
        desc = description(body, meta)

        if not desc:
            problems.append(f"{path.relative_to(ROOT)}: no description could be derived")
        if len(title) > 90:
            problems.append(f"{path.relative_to(ROOT)}: title over 90 chars")

        rel = f"{kind}/{slug}.html"
        canonical = f"{base}/{rel}"
        status = meta.get("status", "")
        status_line = (
            f"Status: <strong>{html.escape(status)}</strong>." if status else ""
        )
        if meta.get("specimen") and meta["specimen"] not in ("none", "planned"):
            status_line += f" Measured by specimen <code>{html.escape(meta['specimen'])}</code>."

        src_rel = str(path.relative_to(ROOT))
        page = PAGE.format(
            title=html.escape(title),
            desc=html.escape(desc),
            canonical=canonical,
            root=base + "/",
            content=render(body),
            status_line=status_line,
            source=f"https://github.com/langej117/refusal-engineering/blob/main/{src_rel}",
            source_label=html.escape(src_rel),
        )
        pages.append((rel, page, title, desc))

    if check_only:
        for rel, _, title, desc in pages:
            print(f"  {rel:<46} {len(desc):>3}ch  {title[:44]}")
        print(f"\n  {len(pages)} pages")
        if problems:
            print("\nPROBLEMS:")
            for p in problems:
                print(f"  {p}")
            return 1
        print("  every page has its own title, description and canonical URL")
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    for rel, page, _, _ in pages:
        dest = OUT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(page)

    index = ROOT / "README.md"
    meta, body = frontmatter(index.read_text())
    (OUT / "index.html").write_text(
        PAGE.format(
            title="Refusal Engineering",
            desc="Twelve patterns for AI systems that have to decline correctly. "
                 "Every claim measured before publication.",
            canonical=base + "/",
            root=base + "/",
            content=render(body),
            status_line="",
            source="https://github.com/langej117/refusal-engineering",
            source_label="langej117/refusal-engineering",
        )
    )
    (OUT / ".nojekyll").write_text("")
    print(f"  {len(pages) + 1} pages → {OUT.relative_to(ROOT)}")
    return 1 if problems else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    # Defaults to the Pages URL rather than a domain that may not be registered.
    # A canonical tag pointing somewhere you do not control is worse than none.
    ap.add_argument("--base-url",
                    default="https://langej117.github.io/refusal-engineering")
    ap.add_argument("--check", action="store_true", help="verify metadata, write nothing")
    a = ap.parse_args()
    sys.exit(build(a.base_url, a.check))
