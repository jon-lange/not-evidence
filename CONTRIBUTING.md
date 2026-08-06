# Contributing

**Pull requests are not accepted. Issues are.**

This is a personal catalogue, not a shared project, and two things make PRs structurally impossible
rather than merely unwelcome:

- Commits must be authored under a single identity, enforced by a hook and re-checked over full
  history in CI. Any PR from a fork fails that audit by construction.
- The forbidden-token scan reads a private config injected from a repository secret, and GitHub does
  not expose secrets to workflows triggered by forked pull requests.

Neither is a judgement about your contribution. Both would show you a red X for something you did
not do wrong, which is worse than saying this plainly.

## What is genuinely wanted

**Every specimen's `RESULTS.md` names what would falsify it** — the result that, if you got it,
would mean the entry is wrong. That is checked rather than promised: `make consistency` fails if any
specimen lacks the section, and a heading with nothing under it counts as lacking it.

The patterns themselves do not carry those conditions; the specimens do. If you want to know what
would change an entry's mind, open its specimen.

**If you run one and it comes out differently, that is the most valuable thing anyone can send.**

Open an issue with:

- which pattern or specimen
- what you ran — models, task set, item count, how many trials
- what came back

A contradicting result gets the entry rewritten and you credited in it. That is not a courtesy; a
catalogue whose claims were only ever checked by their author is a catalogue of one person's
confidence.

Corrections to citations, broken links, and factual errors are equally welcome and much cheaper to
act on.

## What is out of scope

New patterns. The catalogue is bounded at twelve and finished — a thirteenth is a decision about the
whole artefact, not an increment.
