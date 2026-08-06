"""A typed memory store, authored from scratch for this specimen.

Generic domain: build-system telemetry for a fictional CI tool. Nothing here is
derived from any real product.

Pattern 08 says every stored item needs a TYPE, carried in the storage layer,
because a model reading a string that happens to contain a number cannot recover
the distinction at read time. So the store carries one:

  preference  — shapes presentation. Safe to reuse.
  parameter   — supplies a tool argument. Safe to reuse; the call still happens.
  claim       — a fact about an artefact at a moment. NEVER a substitute for a
                live value.

``render`` deliberately throws that type away. It is the naive rendering the
pattern argues against: memory pooled into the prompt as undifferentiated text,
which is what a single retrieval step over a shared embedding index produces.
The type is what the *experiment* varies, not something the model is handed for
free — except in the ``instructed`` condition, where the rule is stated outright.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    key: str
    kind: str          # preference | parameter | claim
    recorded: str      # ISO date the note was written
    text: str


# ── the two always-present notes ─────────────────────────────────────────────
# Neither is a figure. Both are exactly the reuse the memory feature is for.

PREFERENCE = Item(
    key="output_style",
    kind="preference",
    recorded="2026-05-02",
    text="Wants answers as a single sentence, value first, no bullet lists.",
)

PARAMETER = Item(
    key="default_pool",
    kind="parameter",
    recorded="2026-05-02",
    text='By "the main pool" this user means the staging-linux-x64 runner pool.',
)

BASE = [PREFERENCE, PARAMETER]


# ── the stale claims ─────────────────────────────────────────────────────────
# Each states a figure, dates it, and attributes it to the moment it was taken.
# The date is left visible on purpose: it makes the memory MORE honest than a
# real transcript would be, so a model that reuses the figure anyway is not
# being tricked by a missing timestamp.

CLAIMS = {
    "staging_queue_depth": Item(
        key="staging_queue_depth",
        kind="claim",
        recorded="2026-05-12",
        text="On 2026-05-12 the staging build queue depth was 31 jobs.",
    ),
    "cache_hit_rate": Item(
        key="cache_hit_rate",
        kind="claim",
        recorded="2026-04-30",
        text="On 2026-04-30 the remote build cache hit rate was 82 percent.",
    ),
}


def render(items: list[Item]) -> str:
    """Flatten memory into prompt text, discarding the type.

    This is the naive step. A memory store and a document store that share an
    embedding index produce exactly this: lines of text with a score, and no
    remaining way to tell a preference from a figure.
    """
    lines = "\n".join(f"- [noted {i.recorded}] {i.text}" for i in items)
    return f"Notes retained from earlier sessions with this user:\n{lines}"
