# Scripts

The guards. Three of them block, one advises, and one checks that the
repository's own metadata is telling the truth.

| script | when | blocks? |
|---|---|---|
| `assert-identity.sh` | pre-commit | yes — an allow-list of one address |
| `scan-staged.sh` | pre-commit | yes — forbidden tokens, staged content |
| `scan-tree.sh` | pre-push | yes — forbidden tokens, whole tree |
| `review.sh` | `make scan` | no — numbers and ambiguous words need eyes |
| `check-consistency.py` | pre-commit, CI, `make check` | yes — metadata drift |
| `emit-okf.py` | `make okf` / `make check` | yes — bundle conformance and drift |
| `test-portability.sh` | `make portable` | yes — but not on every commit |

## check-consistency.py

Pattern frontmatter is the single source of truth. The README table, the skills
table and the generated site are copies, and copies drift. Before this existed
two patterns were published as `field-tested` while the README called them
`draft` — the *published* surface disagreed with the local index, which is the
version a reader sees.

It asserts: statuses are in the vocabulary and every copy agrees; a skill never
claims more than its pattern; `specimen:` resolves to a real directory and
follows the slug convention; every relative link resolves; every documented
`make` target exists; the employer disclaimer is still present; every pattern is
reachable from a symptom in the README's *Start here* table; every
figure in [`EVIDENCE.md`](../EVIDENCE.md) appears verbatim in the `RESULTS.md`
its row cites, so the summary can never drift from the working; `specimens/README.md`
stays an index and never regrows a status column; every measured specimen states what
would falsify it in a section with prose under it; and every
measured specimen carries an `**Adjudication:**` verdict from which the
catalogue's revision counts are derived and against which every published copy
of them is checked.

Failures print as a diff — what the source says, what the copy says. A checker
that reports `FAILED` without saying what teaches people to bypass it.

### Mutation-checked

A checker that passed because it looked at nothing prints the same thing as one
that passed because the tree was clean. Each rule was disabled in turn and the
harness was required to catch it.

Thirty-one deliberate breakages across four rounds, all caught. The first
seventeen, covering the original rule set:

| Mutation | Tests failed |
|---|---|
| `Report.fail` becomes a no-op — every failure swallowed | 17 |
| Status vocabulary accepts anything | 1 |
| README status mismatch never reported | 1 |
| README row-count guard removed | 1 |
| A skill may claim more than its pattern | 1 |
| skills/README table never compared | 1 |
| Specimen directory need not exist | 1 |
| Specimen slug convention unenforced | 1 |
| Broken links ignored | 1 |
| Undefined `make` targets ignored | 1 |
| Employer disclaimer unchecked | 1 |
| Empty tree reports clean | 1 |
| Malformed frontmatter skipped silently | 1 |
| Orphaned patterns in the triage table ignored | 1 |
| Evidence figures never compared to their source | 1 |
| Evidence row-count guard removed | 1 |
| Evidence rows citing no `RESULTS.md` accepted | 1 |

**The first run had four survivors, and three were tests passing for the wrong
reason** — the shape pattern 11 is about, in the harness written to enforce it:

- `test_a_specimen_key_pointing_nowhere_is_caught` was satisfied by the **link**
  rule, because the fixture's body link was built from the same key as the
  frontmatter. The specimen rule could have been deleted with every test green.
  The fixture now holds the body link valid so only one rule can fire.
- `test_a_bare_numeric_specimen_key_is_caught` was satisfied by the
  **directory-exists** rule, never reaching the convention it named. A second
  test now uses a directory that exists but violates the slug convention.
- `test_malformed_frontmatter_...` asserted on the word `frontmatter`, which the
  missing-`pattern:`-key message also contains. It now asserts the branch.
- The README **row-count** guard had no test at all. A table with a row silently
  dropped is invisible to a row-by-row comparison.

Adding the `EVIDENCE.md` rules produced one more survivor, of the same shape:
nothing tested a row that cites no `RESULTS.md` at all. A row with a figure and
no working is an assertion, which is the one thing that file exists not to be.

### Falsification completeness, mutation-checked

`CONTRIBUTING.md` asks readers to send a result that contradicts an entry.
`EVIDENCE.md` said three specimens carried no falsification condition. Both
numbers were arrived at by eye and both were wrong: **four** lacked a named
section, and of those only **one** genuinely lacked the substance — 04, 05 and
09 had stated their condition inside `## Scope`, where nothing looking for one
would find it.

| Mutation | Tests failed |
|---|---|
| Missing falsification section tolerated | 1 |
| Empty section accepted as a condition | 1 |
| Word floor set to zero | 1 |

No survivors. The word floor matters more than it looks: a heading with nothing
under it reads, from any index, exactly like one that states a condition.

### The specimens index, mutation-checked

`specimens/README.md` was a fifth copy of the metadata in a vocabulary of its
own — every row said `built`, two carried hand-written notes about a prediction
not holding, and nothing read the file. By the time anyone did, five entries had
had their central claim fail and the table named two.

The outcome column is gone rather than corrected. A column whose every cell said
the same word carried no information, and keeping it is how the hand-written
notes appeared in the first place. The rule now asserts shape: one row per
pattern, and the *absence* of any status or adjudication term.

| Mutation | Tests failed |
|---|---|
| Forbidden vocabulary not asserted | 2 |
| Index row-count guard removed | 1 |
| Only status forbidden, not adjudication | 1 |
| Duplicate rows tolerated | 1 |

**One survivor, the same shape as the last two.** The duplicate guard broke no
test: a pattern listed twice satisfies every-pattern-has-a-row completely, so
only the count sees it. Test added.

### The adjudication rule, mutation-checked

The revision count — *ten of twelve* — was the last claim in the repository that
nothing derived. It was typed into five files. Seven more breakages, all caught:

| Mutation | Tests failed |
|---|---|
| Published count never compared to the derivation | 2 |
| A rephrased claim silently stops being checked | 1 |
| `central-claim-failed` need not be `revised-by-specimen` | 1 |
| `revised-by-specimen` need not have failed centrally | 1 |
| Adjudication vocabulary unenforced | 1 |
| A missing adjudication line tolerated | 1 |
| Completeness of the adjudication set not required | 1 |

**One survivor, and it was the interesting one.** Disabling the completeness
check broke no test: the only test that dropped an adjudication also tripped the
per-specimen rule, so completeness was never the thing being proven. It fires
alone in exactly one case — a *measured* pattern with no `specimen:` key
contributes no verdict, fires none of the per-specimen rules, and the totals then
derive from a smaller set than the catalogue while every published number still
matches. Same shape as the README row-count guard: only the count sees it.

The rephrasing mutation is the one worth understanding. These rules read English
sentences, so rewording one makes its regex stop matching. A rule that quietly
checks nothing prints what a correct run prints, so an unmatched claim is a
failure rather than a skip.

Reproduce by editing one rule to `if False:` and running
`python3 scripts/test_check_consistency.py`.

### Scope

It checks that the copies agree with the source. It cannot check that the source
is *right* — a pattern whose status is honestly wrong is consistent with a README
that repeats it. That judgement stays with the specimens.
