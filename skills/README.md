# Skills

The applied layer of the catalogue. Each skill operationalises **one pattern that has a specimen** —
that gate is what keeps this repo finishable, and it is why these ship with measured evidence rather
than assertions.

| skill | pattern | evidence |
|---|---|---|
| [mutation-check](mutation-check/) | [11 · Green Is Not Evidence](../patterns/11-green-is-not-evidence.md) | found defects in 12 of 12 suites built for this repo |

Conventions: `skills/<name>/SKILL.md`, lowercase-hyphenated matching the directory. Body under ~500
lines with progressive disclosure to `references/` and `scripts/`. Frontmatter carries `pattern:` and
the same `status:` vocabulary as patterns.

Retired skills move to [`../deprecated/`](../deprecated/); rejected ideas to
[`../.out-of-scope/`](../.out-of-scope/). Neither is ever deleted.
