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

## check-consistency.py

Pattern frontmatter is the single source of truth. The README table, the skills
table and the generated site are copies, and copies drift. Before this existed
two patterns were published as `field-tested` while the README called them
`draft` — the *published* surface disagreed with the local index, which is the
version a reader sees.

It asserts: statuses are in the vocabulary and every copy agrees; a skill never
claims more than its pattern; `specimen:` resolves to a real directory and
follows the slug convention; every relative link resolves; every documented
`make` target exists; the employer disclaimer is still present.

Failures print as a diff — what the source says, what the copy says. A checker
that reports `FAILED` without saying what teaches people to bypass it.

### Mutation-checked

A checker that passed because it looked at nothing prints the same thing as one
that passed because the tree was clean. Each rule was disabled in turn and the
harness was required to catch it. Thirteen deliberate breakages, all caught:

| Mutation | Tests failed |
|---|---|
| `Report.fail` becomes a no-op — every failure swallowed | 13 |
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

Reproduce by editing one rule to `if False:` and running
`python3 scripts/test_check_consistency.py`.

### Scope

It checks that the copies agree with the source. It cannot check that the source
is *right* — a pattern whose status is honestly wrong is consistent with a README
that repeats it. That judgement stays with the specimens.
