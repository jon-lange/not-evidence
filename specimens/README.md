# Specimens

Small, self-contained demonstrations attached to the patterns whose claims are more convincing
shown than argued. The rest are prose, deliberately.

Each is a **reference implementation, not maintained software**. Don't depend on them; read them,
run them, and take the idea.

| # | Specimen | Pattern |
|---|---|---|
| 01 | [grounded-or-refuse](01-grounded-or-refuse/) | Grounded or Refuse |
| 02 | [refuse-the-class](02-refuse-the-class/) | Refuse the Class, Not the Case |
| 03 | [deterministic-over-prompted](03-deterministic-over-prompted/) | Deterministic Over Prompted |
| 04 | [injection-classes](04-injection-classes/) | Meta-Injection Is Not Content-Relay |
| 05 | [judge-family](05-judge-family/) | The Judge Cannot Share a Family |
| 06 | [unratified-weights](06-unratified-weights/) | Refuse to Score Unratified Weights |
| 07 | [over-refusal](07-over-refusal/) | Gate Over-Refusal Separately |
| 08 | [remembered-is-not-current](08-remembered-is-not-current/) | A Remembered Figure Is Never a Current Figure |
| 09 | [modality-surface](09-modality-surface/) | Keep New Modalities Off the Reasoning Path |
| 10 | [lossy-transducer](10-lossy-transducer/) | Never Auto-Commit a Lossy Transducer |
| 11 | [mutation-check](11-mutation-check/) | Green Is Not Evidence |
| 12 | [sanitization-label](12-sanitization-label/) | Distrust the Sanitization Label |

**This table deliberately carries no outcome column.** It used to, in a private vocabulary — every
row said `built`, and two of them carried a hand-written note about the prediction not holding. Those
notes were correct when written and wrong by the time anyone read them: five entries had their
central claim fail, and the table named two. A fifth copy of the status, maintained by hand and
checked by nothing, in the repository whose subject is exactly that.

What each specimen found is in its own `RESULTS.md`, which opens with the adjudication. All twelve on
one page are in [`EVIDENCE.md`](../EVIDENCE.md), and the status of each entry is in its pattern's
frontmatter. `scripts/check-consistency.py` asserts that this table stays a list — one row per
pattern, and no status or adjudication term anywhere in it.

`make test` runs every suite and `make demo` runs every offline demonstration — no cloud account
required. Eleven need nothing but Python; specimen 09 needs Pillow to rasterise its fixtures.
