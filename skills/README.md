# Skills

The applied layer of the catalogue.

**A skill may only exist for a pattern that has a specimen.** That gate is what keeps this repository
finishable — skills are otherwise open-ended and maintained, and an open-ended maintained thing inside
a bounded finished artifact is how a catalogue becomes a junk drawer. It also means each of these
ships with measured evidence rather than an assertion.

Each carries the `status` of the pattern it operationalises. **A skill cannot claim more than its
pattern does.**

| skill | pattern | status | what it is for |
|---|---|---|---|
| [mutation-check](mutation-check/) | [11 · Green Is Not Evidence](../patterns/11-green-is-not-evidence.md) | field-tested | Prove a test would have failed before trusting that it passed |
| [injection-class-audit](injection-class-audit/) | [04 · Meta-Injection Is Not Content-Relay](../patterns/04-meta-injection-is-not-relay.md) | field-tested | Find the injection class your suite does not cover |
| [weight-flip-share](weight-flip-share/) | [06 · Refuse to Score Unratified Weights](../patterns/06-refuse-unratified-weights.md) | field-tested | Compute what fraction of plausible weightings picks the other candidate |
| [series-reidentification](series-reidentification/) | [12 · Distrust the Sanitization Label](../patterns/12-distrust-the-sanitization-label.md) | field-tested | Test whether "anonymised" data re-identifies, before publishing it |
| [judge-independence-check](judge-independence-check/) | [05 · The Judge Cannot Share a Family](../patterns/05-judge-cannot-share-a-family.md) | **revised-by-specimen** | Check a judge discriminates and is order-stable before trusting its verdict |

`judge-independence-check` carries pattern 05's `revised-by-specimen` status. Its specimen ran and did
not confirm the cross-family claim — no ranking flip, and the apparent self-preference dissolved once cross-family
judges agreed with it. The two checks the skill leads with are the ones that actually fired: judge
saturation, and position instability.

## Why these five

They are the patterns whose specimens produced something you can act on:

- **mutation-check** surfaced a defect in seven of this repository's twelve specimen suites
- **weight-flip-share** computes an exact closed form — 40.6% of the simplex flipped a constructed scorecard with genuine trade-offs
- **series-reidentification** measured four series points identifying one entity in sixty, every trial
- **injection-class-audit** carries fixtures for the class that every model tested relayed
- **judge-independence-check** carries the two checks that disqualified two of three judges

The other seven patterns stay prose. Not every good idea needs a tool.

## Conventions

- `skills/<name>/SKILL.md` — lowercase-hyphenated, matching the directory name
- Body under ~500 lines, with progressive disclosure to `references/` and `scripts/` where needed
- Frontmatter carries `name`, `description` (written so an agent knows *when* to trigger it),
  `pattern:`, and `status:`
- Every skill ends with **Honest limits** before **Prior art**. A skill that cannot say what it fails
  at is selling something

Retired skills move to [`../deprecated/`](../deprecated/) with `superseded-by:` set. Rejected ideas go
to [`../.out-of-scope/`](../.out-of-scope/). Neither is ever deleted.
