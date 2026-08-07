# not-evidence

## What this is

A **bounded catalogue** of twelve signals that look like evidence and aren't, each paired with the
refusal that closes it, plus small runnable specimens that test the claims. Twelve, then it is
finished — adding a thirteenth is a decision, not an increment.

The repository is named for the problem; each entry is named for the response. That is why every
pattern still carries a `## The Refusal` section and a `refuses:` key — the refusal is what you *do*
about a signal that isn't evidence, and renaming the catalogue never changed that.

It is not a framework, not a library, and not a blog. Specimens are reference implementations,
explicitly unmaintained.

The through-line: **a system declining correctly when the reassuring signal is the one that's
lying.** The guardrail that refused the obvious attack. The green test that never ran. The judge that
shares the subject's lineage. The label that says "sanitized."

---

## Behavioral guidelines

> **Tradeoff:** these bias toward caution over speed. For trivial tasks, use judgment.

### Think before coding
Don't assume. Don't hide confusion. Surface tradeoffs.
- State assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### Simplicity first
Minimum code that solves the problem. Nothing speculative.
- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask: *"Would a senior engineer say this is overcomplicated?"* If yes, simplify.

### Surgical changes
Touch only what you must. Clean up only your own mess.
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.
- Remove imports and variables *your* changes made unused; leave pre-existing dead code alone.

The test: every changed line traces directly to the request.

### Goal-driven execution
Define success criteria. Loop until verified.
- *"Add validation"* → write tests for invalid inputs, then make them pass.
- *"Fix the bug"* → write a test that reproduces it, then make it pass.
- For multi-step work, state a brief plan with a verify check per step.

---

## The two rules that gate publication

Everything else is style. These two decide whether this repository can be published at all.

### 1. Read nothing outside this repository

Work only from files under this repo, plus public sources you fetch and verify. Other directories on
this machine are employer-owned; this catalogue is written **from principle with those sources
closed**, which is the commitment [METHOD.md](METHOD.md) makes publicly.

*Stated as an allow-list on purpose.* Enumerating the directories to avoid would mean committing
their names — the exact class of leak this repo exists to prevent. Same reason the identity guard in
`scripts/` asserts the expected address rather than listing forbidden ones.

Consulting internal sources would not help anyway: `field-tested` means *an experiment ran and the
claim held*, never *this matches an internal implementation*.

### 2. Never publish a number you did not generate here

No percentages, latencies, costs, accuracy rates, or orders of magnitude from anywhere but a specimen
in this repo. Numbers are uniquely identifying, have no abstraction defence, and in a regulated
industry can be material non-public information. Regenerate benchmarks locally and check in the
harness.

Related: **generic domains only.** Build systems, caches, docs tools, databases. Never a regulated
vertical — a specimen written against one is making a claim about a particular system rather than a
general one. Stated as an allow-list for the same reason as the identity guard: enumerating the
domains to avoid is itself a list of the domains worth avoiding, and that narrows a work history.

---

## Architecture

```
patterns/       01..12, the catalogue. ADR-shaped: one claim per file.
specimens/      runnable demonstrations, one directory per pattern that has one
skills/         installable skills — the applied layer (see the gate below)
okf/            the catalogue as an Open Knowledge Format bundle (generated)
tools/          the one file meant to be taken — standalone, no repo imports
scripts/        guards — identity, forbidden tokens, metadata consistency, portability
site/           static mirror — real titles, OG cards, canonical URLs
EVIDENCE.md     every measured figure on one page, checked against its RESULTS.md
.out-of-scope/  ideas deliberately not pursued, and why
deprecated/     entries that were live and no longer are
```

**Why `.out-of-scope/` exists:** rejected ideas need a home *outside* the live catalogue, or they
accumulate inside it. That is how a bounded artifact becomes a junk drawer.

A private forbidden-token list lives at `~/.config/re-denylist.toml`, outside every git tree. It is
never committed — a file enumerating what must not be said is worse than the leak it prevents.

## Skills — the applied layer

The catalogue is complete — all twelve patterns carry a specimen — so the deferral that used to sit
here is discharged. Five skills exist. See [skills/README.md](skills/README.md).

### The gate

**A skill may only exist for a pattern that has a specimen.**

That single rule is what keeps this repo finishable. Skills are otherwise open-ended and maintained,
and an open-ended maintained thing inside a bounded finished artifact is how a catalogue becomes a
junk drawer — a stale skill sitting beside the patterns makes the patterns look stale too.

Tied to measured patterns, skills inherit the catalogue's boundary: at most twelve, realistically
four or five. And it is the differentiator — most skills repos ship assertions; these ship with
evidence behind them.

### Conventions

- Spec-compliant: `skills/<name>/SKILL.md`, lowercase-hyphenated, matching directory name
- `SKILL.md` body under ~500 lines, with progressive disclosure to `references/` and `scripts/`
- Frontmatter carries `pattern:` — the entry it operationalises — and the same `status:` vocabulary
  as patterns (`draft` / `field-tested` / `revised-by-specimen` / `superseded-by:`). A skill may be
  `draft` or match its pattern; it may never claim more. `scripts/check-consistency.py` enforces this
- Retired skills move to `deprecated/`, never deleted. Rejected ideas go in `.out-of-scope/`

### Skills carry more IP risk than patterns

Patterns abstract; skills operationalise, and operationalised knowledge is the thing employers
actually claim. A skill encoding *how to build evals* sits much closer to real work product than an
abstracted principle does — it carries rule ordering, refusal language, and domain framing that a
colleague would recognise instantly even after rewording.

So the method applies harder here: written from the pattern doc with the source closed, generic
domain throughout, and reviewed against the question *"would someone I work with read this and know
where it came from?"* If yes, rewrite it.

## Local dev

Each specimen is standalone with its own `.venv`. No repo-wide install.

```bash
cd specimens/<name>
python3 probe.py --offline          # where offered: no keys, no network
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./.venv/bin/python probe.py         # live
```

Live specimens read `~/.config/openai-key` and `~/.config/anthropic-key`, or the matching env vars.
**Never write a key into a file inside this repo, including `.env`.**

**Repo code is path-independent; venvs are not.** Everything tracked here anchors on
`Path(__file__)` or `git rev-parse --show-toplevel`, and `make portable` proves it by exporting the
tree to a differently-named, deeper path containing a space and re-running the checks there. A venv
is the exception by construction: `.venv/bin/pip` and `.venv/bin/activate` hardcode an absolute
shebang, so after a move or rename they point at a tree that no longer exists. `./.venv/bin/python`
survives — it is a symlink, and that is the only interpreter the `Makefile` invokes, so `make test`
and `make demo` are unaffected. Recreate the venv when you next need `pip`; nothing else needs doing.

Model overrides are env vars (`LLM_MODEL`, `STT_MODEL`, `LLM_BASE_URL`) so any OpenAI-compatible
endpoint works.

## Testing

```bash
python3 test_*.py                   # also runs under pytest
make consistency                    # metadata agrees with itself, and the rules are live
```

Three rules that are not negotiable:

**Mutation-check every suite.** Break the guarded behaviour on purpose, confirm the tests fail *for
the right reason*, restore, and record which mutations were tried and how many tests each broke. A
passing absence-test proves nothing until you have watched it fail. That is pattern 11, and it
applies to this repo's own code — specimen 11 found a vacuous test inside its own suite, and the
mutation run on `scripts/check-consistency.py` found three tests passing for the wrong reason, each
satisfied by a different rule than the one it named. Any of the three rules could have been deleted
with the suite still green.

**Don't mock the model.** A mocked judge or transcriber only proves the mock returns what it was told
to. Measure live, record the output in `RESULTS.md`, and test the deterministic parts offline.

**Persist per-item results before aggregating.** JSONL, one row per item per judge per dimension. A
harness storing only means has discarded what paired comparison and interval estimation need — and
retrofitting means re-running everything. Both analysis bugs in specimen 05 were fixed and recomputed
from persisted records without re-spending a cent.

## Writing a pattern

Fixed section order. Deviating breaks reading across entries:

```
## Context · ## Forces · ## The Refusal · ## Consequences
## The naive approach it beats · ## Prior art · ## Specimen
```

- **The Refusal** is the load-bearing paragraph — the rule stated so it *can* be violated. Bold it.
- **The naive approach it beats** must name a genuinely attractive wrong answer and the precise
  mechanism of its failure. No attractive wrong answer means it is a description, not a pattern.
- **Target 650–950 words.** Several entries currently exceed this and should come *down*, not be
  matched.
- **Verify every citation.** Fetch arXiv `citation_title`, resolve DOIs through Crossref, fetch
  anything else. Omit what you cannot verify. A repository arguing that green is not evidence cannot
  ship a fabricated reference.

### Status

`status:` stays `draft` until a specimen has measured it. Promote on evidence, never on confidence.

- **`draft`** — written, not yet measured
- **`field-tested`** — a specimen ran and the claim held
- **`revised-by-specimen`** — a specimen ran and the claim *did not* hold. The entry now states what
  the evidence supports; `RESULTS.md` says what was predicted and what happened
- **`superseded-by: NN`** — retired in favour of another entry, moved to `deprecated/`

The distinction between the middle two is whether the **central** claim survived. An entry merely
narrowed by measurement stays `field-tested` and says where in its `RESULTS.md`. Ten entries were
revised by their specimens; five had their central claim fail.

**The counts are derived, never typed.** Each `RESULTS.md` opens with `**Adjudication: <verdict>.**`
where the verdict is `confirmed`, `narrowed`, or `central-claim-failed`. `revised` means the last
two. `scripts/check-consistency.py` derives the totals from those twelve lines, asserts that the set
of `revised-by-specimen` patterns equals the set whose adjudication is `central-claim-failed`, and
fails on any published copy that disagrees.

**Pattern frontmatter is the single source of truth for status.** The README table, the skills
table and the generated site are copies. Never hand-edit a copy to agree with the source — fix the
source and let `make consistency` prove the rest. Four hand-maintained copies is exactly how two
patterns came to be published as `field-tested` while the README called them `draft`.

**The entry states the current claim. The specimen records how it was reached.** When measurement
contradicts a pattern, rewrite the pattern to what the evidence supports — do not narrate the
revision in the entry. A reader wants the best current statement, not its history.

The history is not lost: `RESULTS.md` in each specimen carries what was run, what came back, the
scope, and what would falsify the claim. That is the auditable record.

A pattern retired rather than revised moves to `deprecated/` with `superseded-by:` set.

## Reporting results

**Two of the first four measured claims did not survive their specimens.** Both entries were
rewritten around what actually happened, and that is the repository's most valuable feature.

When a specimen contradicts its pattern: **rewrite the claim to what the evidence supports**, and
record the full measurement in the specimen's `RESULTS.md` — including scope and the falsification
condition. The entry carries the conclusion; the specimen carries the working.

What is not acceptable is narrowing a claim silently *and* leaving no record. If the entry changes,
`RESULTS.md` must say why anyone would believe the new version.

## Gotchas

**Pre-commit fixers abort the commit.** `end-of-file-fixer` and `trailing-whitespace` rewrite files
and fail the run. Re-stage and commit again — and **verify `HEAD` actually moved**, because a
subsequent `git push` will report success on nothing.

**`git push` succeeds when there is nothing to push.** Check `git rev-parse HEAD` before and after.

**Scanner false positives are a real failure mode, not just noise.** A `[A-Za-z]:\\` rule once
matched `r:\n` inside an ordinary string literal. A rule that fires on prose trains you to bypass the
hook. When one fires, verify *both* directions before adjusting: prose must pass, and a real instance
must still be caught.

**Branch protection is unavailable** — GitHub Free does not offer it on private repos, via classic
rules or rulesets. The local hooks plus CI are the control until this goes public, at which point
protection becomes free.

**GitHub's own secret scanning does not run on private repos** on a free account. Until publication,
the gitleaks layer is doing all of the work.

**CI can pass vacuously.** The first run went green scanning against an empty config because the
secret was not yet set. CI now plants a canary and requires the scanner to catch it before trusting
a clean result.
