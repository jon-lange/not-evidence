"""One input boundary, three ways of drawing it.

A documentation build tool resolves references found in source files — images,
includes, links. A reference is modelled here as five independent fields, which
is enough structure for the thing this specimen measures and no more:

    scheme   ''https' 'http' 'file' 'data' ... and two evasive spellings
    host     the doc hosts, a CDN, link-local metadata, an attacker domain
    kind     the content type implied by the extension
    size_kb  the declared size
    form     'ok', or one of four structural malformations

The product is 48,000 references. Every validator below is a predicate over
exactly that space, so 'the accepted set' is a finite object that can be
compared against a prober's guess by enumeration rather than by argument.

Three boundaries:

  ACCRETED    the allowlist that grew by accretion. Six ordered rules over
              eighteen table entries, each entry added after somebody found a
              way past the last one. It contains a real bug — the host check is
              a suffix match — which is not decoration: it is the enumeration
              race, and the prober finds it.

  CARVE_OUT   the same shape with one narrow exception: local docs, plus PNG
              thumbnails from one CDN at one size. Same six-rule structure, but
              the accepted regions do not touch. That geometry turns out to be
              what the uniform-error result depends on.

  CLASS       the refusal. No scheme, no host, and the path resolves inside the
              docs root. Two rules, no tables, and the remote-dereference class
              is gone rather than filtered.

Each boundary is exposed through two error channels — `helpful`, which names
the rule that fired, and `uniform`, which returns one identical code for every
rejection. The accepted set is *identical* across the two, by construction: the
only difference is what a rejected caller is told.

`costly=True` makes each rule do real work, increasing down the chain, so that
short-circuit evaluation is observable on the clock. `constant_work=True` runs
every rule regardless of the outcome — the mitigation.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from itertools import product
from typing import Callable

# ── the reference space ──────────────────────────────────────────────────────

SCHEMES = ("", "https", "http", "file", "data", "ftp", "mailto", "javascript",
           "ws", "s3", "HTTPS", "htt ps")
HOSTS = ("", "docs.example.com", "cdn.example.com", "raw.githubusercontent.com",
         "evil-docs.example.com", "assets.internal", "169.254.169.254", "localhost",
         "example.com", "attacker.net")
KINDS = ("md", "txt", "png", "jpg", "svg", "pdf", "html", "js", "zip", "unknown")
SIZES = (1, 16, 64, 256, 512, 1024, 4096, 16384)
FORMS = ("ok", "traversal", "null_byte", "double_scheme", "fragment_only")

DIMS = ("scheme", "host", "kind", "size_kb", "form")
VALUES = {"scheme": SCHEMES, "host": HOSTS, "kind": KINDS, "size_kb": SIZES, "form": FORMS}


@dataclass(frozen=True, order=True)
class Ref:
    scheme: str
    host: str
    kind: str
    size_kb: int
    form: str

    def with_(self, dim: str, value) -> "Ref":
        return replace(self, **{dim: value})

    def __str__(self) -> str:
        where = f"{self.scheme}://{self.host}/" if self.scheme else "./"
        return f"{where}doc.{self.kind} [{self.size_kb} KB, {self.form}]"


def iter_space():
    for values in product(*(VALUES[d] for d in DIMS)):
        yield Ref(*values)


SPACE = tuple(iter_space())
SPACE_SIZE = len(SPACE)


# ── the rules ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Rule:
    """One check. `entries` is how many table rows a reviewer has to read.

    The distinction matters for the rule count: a predicate is a decision, an
    entry is a decision about a specific value that somebody had to think of.
    """

    code: str
    entries: int
    test: Callable[[Ref], bool]
    what: str


@dataclass(frozen=True)
class Boundary:
    name: str
    rules: tuple[Rule, ...]

    @property
    def predicates(self) -> int:
        return len(self.rules)

    @property
    def entries(self) -> int:
        return sum(r.entries for r in self.rules)

    def codes(self) -> tuple[str, ...]:
        return tuple(r.code for r in self.rules)


BAD_FORMS = ("traversal", "null_byte", "double_scheme", "fragment_only")
SCHEME_ALLOWLIST = ("", "https", "http")
HOST_ALLOWLIST = ("docs.example.com", "cdn.example.com", "raw.githubusercontent.com")
KIND_ALLOWLIST = ("md", "txt", "png", "jpg")
INSECURE_OK_KINDS = ("png", "jpg")
SIZE_CAPS = {"md": 256, "txt": 256, "png": 4096, "jpg": 4096}


def _host_allowed(host: str) -> bool:
    """Suffix match. This is the bug, and it is deliberate.

    `'evil-docs.example.com'.endswith('docs.example.com')` is True, so a host
    nobody put on the list is on the list. It is the most common shape of
    allowlist bypass there is, it survives code review because the list itself
    reads correctly, and it is exactly what 'enumeration is unwinnable' means:
    the entry is right and the matcher is wrong, and no additional entry fixes
    that.
    """
    return any(host.endswith(allowed) for allowed in HOST_ALLOWLIST)


ACCRETED = Boundary(
    "accreted allowlist",
    (
        Rule("E_MALFORMED", len(BAD_FORMS), lambda r: r.form == "ok",
             "reject four known-bad reference forms"),
        Rule("E_SCHEME", len(SCHEME_ALLOWLIST), lambda r: r.scheme in SCHEME_ALLOWLIST,
             "scheme allowlist"),
        Rule("E_HOST", len(HOST_ALLOWLIST),
             lambda r: (r.host == "") if r.scheme == "" else (r.host != "" and _host_allowed(r.host)),
             "host allowlist, and a relative reference carries no host"),
        Rule("E_TYPE", len(KIND_ALLOWLIST), lambda r: r.kind in KIND_ALLOWLIST,
             "content-type allowlist"),
        Rule("E_INSECURE_TYPE", len(INSECURE_OK_KINDS),
             lambda r: r.scheme != "http" or r.kind in INSECURE_OK_KINDS,
             "over plain http, images only"),
        Rule("E_SIZE", len(set(SIZE_CAPS.values())),
             lambda r: r.size_kb <= SIZE_CAPS.get(r.kind, 0),
             "per-type size cap"),
    ),
)

CARVE_OUT = Boundary(
    "narrow carve-out",
    (
        Rule("E_MALFORMED", len(BAD_FORMS), lambda r: r.form == "ok",
             "reject four known-bad reference forms"),
        Rule("E_SCHEME", 2, lambda r: r.scheme in ("", "https"), "scheme allowlist"),
        Rule("E_HOST", 1,
             lambda r: (r.host == "") if r.scheme == "" else (r.host == "cdn.example.com"),
             "one permitted host"),
        Rule("E_TYPE", 3,
             lambda r: (r.kind in ("md", "txt")) if r.scheme == "" else (r.kind == "png"),
             "local docs are text, the remote exception is a thumbnail"),
        Rule("E_SIZE", 2,
             lambda r: (r.size_kb <= 256) if r.scheme == "" else (r.size_kb == 512),
             "size cap, and one exact thumbnail size"),
    ),
)

CLASS = Boundary(
    "class refusal",
    (
        Rule("E_REFUSED", 0, lambda r: r.scheme == "" and r.host == "",
             "no scheme and no host: remote references are not a thing here"),
        Rule("E_REFUSED", 0, lambda r: r.form == "ok",
             "the path resolves, unescaped, inside the docs root"),
    ),
)

BOUNDARIES = {"accreted": ACCRETED, "carve-out": CARVE_OUT, "class": CLASS}


# ── the two error channels ───────────────────────────────────────────────────

UNIFORM_CODE = "E_REFUSED"
ACCEPT_CODE = "OK"


@dataclass(frozen=True)
class Verdict:
    ok: bool
    code: str


# Work per rule, in SHA-256 iterations over 64 bytes. Tripling down the chain:
# a cheap syntactic check, then a table lookup, then a type sniff, then a size
# read that has to touch the object. Only used when `costly` is set.
COSTS = (4, 12, 36, 108, 324, 972)


def _burn(units: int) -> None:
    block = b"reference-validator-cost-model-64-bytes-of-padding-aaaaaaaaaaaaaa"
    for _ in range(units):
        block = hashlib.sha256(block).digest() * 2


class Validator:
    """A boundary plus an error channel.

    `uniform=False` returns the code of the rule that fired. `uniform=True`
    returns one identical code for every rejection. The accepted set does not
    depend on the flag, and `test_validator.py` asserts that over all 48,000
    references — otherwise the probe-count comparison would be measuring two
    different boundaries rather than two ways of describing one.
    """

    def __init__(self, boundary: Boundary, *, uniform: bool,
                 costly: bool = False, constant_work: bool = False):
        self.boundary = boundary
        self.uniform = uniform
        self.costly = costly
        self.constant_work = constant_work
        self.calls = 0

    def __call__(self, ref: Ref) -> Verdict:
        self.calls += 1
        failed = None
        for i, rule in enumerate(self.boundary.rules):
            if failed is not None and not self.constant_work:
                break
            if self.costly:
                _burn(COSTS[i])
            # Under constant_work the predicate is evaluated too, not just the
            # expensive part. Skipping it leaves a residual signal: the rule
            # that fired first skips more predicate calls than the rule that
            # fired last, and the difference is measurable once the loud part
            # is flat.
            passed = rule.test(ref)
            if not passed and failed is None:
                failed = rule
        if failed is None:
            return Verdict(True, ACCEPT_CODE)
        return Verdict(False, UNIFORM_CODE if self.uniform else failed.code)


def accepted_set(boundary: Boundary) -> frozenset[Ref]:
    """Ground truth, by enumeration. Never given to a prober."""
    validator = Validator(boundary, uniform=True)
    return frozenset(ref for ref in SPACE if validator(ref).ok)


def rejection_code(boundary: Boundary, ref: Ref) -> str:
    return Validator(boundary, uniform=False)(ref).code


def bypass_refs(boundary: Boundary) -> frozenset[Ref]:
    """Accepted references whose host is on nobody's list.

    Not a hypothetical. `evil-docs.example.com` is accepted by ACCRETED because
    the host check is a suffix match, and it is rejected by CLASS because CLASS
    has no host check to get past.
    """
    return frozenset(r for r in accepted_set(boundary) if r.host == "evil-docs.example.com")
