# Specimens

Small, self-contained demonstrations attached to the patterns whose claims are more convincing
shown than argued. The rest are prose, deliberately.

Each is a **reference implementation, not maintained software**. Don't depend on them; read them,
run them, and take the idea.

| # | Specimen | Pattern | Status |
|---|---|---|---|
| 01 | [grounded-or-refuse](01-grounded-or-refuse/) | Grounded or Refuse | **built** — *prediction did not hold* |
| 03 | [deterministic-over-prompted](03-deterministic-over-prompted/) | Deterministic Over Prompted | **built** |
| 04 | [injection-classes](04-injection-classes/) | Meta-Injection Is Not Content-Relay | **built** |
| 05 | [judge-family](05-judge-family/) | The Judge Cannot Share a Family | **built** |
| 06 | [unratified-weights](06-unratified-weights/) | Refuse to Score Unratified Weights | **built** |
| 07 | [over-refusal](07-over-refusal/) | Gate Over-Refusal Separately | **built** — *"newer refuses more" did not reproduce* |
| 08 | [remembered-is-not-current](08-remembered-is-not-current/) | A Remembered Figure Is Never a Current Figure | **built** |
| 09 | [modality-surface](09-modality-surface/) | Keep New Modalities Off the Reasoning Path | **built** |
| 10 | [lossy-transducer](10-lossy-transducer/) | Never Auto-Commit a Lossy Transducer | **built** |
| 11 | [mutation-check](11-mutation-check/) | Green Is Not Evidence | **built** |
| 12 | [sanitization-label](12-sanitization-label/) | Distrust the Sanitization Label | **built** |

`make dev` boots all of them together against a mock inference path — no cloud account required for
the demo path.
