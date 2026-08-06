"""The task set. Generic domain, authored for this specimen.

Twelve short explanation tasks. They are deliberately the kind of question where
answers differ in quality along axes a rubric can name — completeness, accuracy,
and whether the answer commits to a claim or hedges — rather than questions with
a single correct token.

Small on purpose. Twelve items cannot resolve a small difference, and the
analysis says so rather than pretending otherwise.
"""

from __future__ import annotations

ITEMS: list[str] = [
    "Why does adding an index sometimes make a database query slower?",
    "What is the difference between a mutex and a semaphore?",
    "Why is floating-point addition not associative?",
    "What problem does a bloom filter solve, and what does it give up?",
    "Why can't you cleanly rewrite public git history?",
    "What does 'eventual consistency' actually promise?",
    "Why is UTF-8 self-synchronising, and why does that matter?",
    "What is the difference between latency and throughput?",
    "Why do connection pools have a maximum size?",
    "What does a copy-on-write filesystem snapshot actually copy?",
    "Why is parsing HTML with a regular expression unreliable?",
    "What is the difference between a cache miss and a cache invalidation?",
]
