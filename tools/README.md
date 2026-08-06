# tools

One file, meant to be taken.

[`mutcheck.py`](mutcheck.py) is standard library only and imports nothing from
this repository. Copy it next to your tests. Nothing else here needs to come
with it.

```bash
python3 mutcheck.py --demo
```

Sixty seconds, no account, no dependency, no reading required first.

## What it is not

**Not a mutation-testing framework.** No operator catalogue, no AST rewriting,
no coverage integration, and no attempt to find mutations for you.
[mutmut](https://github.com/boxed/mutmut) and
[cosmic-ray](https://github.com/sixty-north/cosmic-ray) do that, and they do it
better than a two-hundred-line file ever will. Use them.

They answer a different question. *Which of my assertions are weak?* is a
question you ask occasionally, across a whole suite, offline. This answers **is
*this* assertion, guarding *this* property, actually watching it?** — which
belongs in the suite, on the line below the assertion it is about, running every
time.

That is the whole design. Every constraint — single file, no config, no plugins,
standard library — exists so it can be copied rather than adopted.

## Using it

```python
from mutcheck import require_live

def test_the_secret_is_redacted():
    require_live(logger, "redact", lambda event: event, absence_check)
```

Read that as: *with redaction reduced to a no-op, this test must fail.* If it
passes, the assertion was never watching the thing it names, and `require_live`
raises `MutationSurvived` — an `AssertionError` subclass, so your existing
runner reports it as the failed test it is.

`mutate()` is the same thing without the opinion: it returns a `MutationReport`
and lets you decide.

## Honest limits

1. **The mutation is yours to choose.** This requires you to already name the
   breakage that matters. Pick the wrong one and you get a green liveness proof
   for an assertion that is live against something else. Weaker than a tool that
   enumerates mutations; far stronger than nothing.

2. **Its own failure mode is the one it detects.** The swap rebinds a name on a
   module object, so it reaches only call sites that look that name up through
   the module at call time. A caller holding its own reference — `from subject
   import redact` — never sees the replacement. The test then passes and this
   reports the assertion as vacuous, because from here *a mutation that never
   landed* and *an assertion that was never live* are indistinguishable. Treat a
   survivor as "one of two things is wrong" and find out which.

3. **A crash counts as caught, and is not the same as a caught assertion.** A
   crash proves the mutated code ran, which rules out vacuity. It does not prove
   your assertion was the thing watching. The report says which happened; read
   the detail line.

4. **Substring absence only, in the demonstration.** The sharper case — *the mock
   was never called* — is the same failure and is not demonstrated here.

## Why it exists

[Pattern 11 · Green Is Not Evidence](../patterns/11-green-is-not-evidence.md), and
the measurement is in
[specimen 11's RESULTS](../specimens/11-mutation-check/RESULTS.md). Two of six
variants there passed while the property they guarded was broken. `--demo`
reproduces that result — one live assertion, two vacuums — and
`test_the_demo_runs_and_reproduces_the_specimen_result` asserts it stays
reproduced.

[`specimens/11-mutation-check/mutation.py`](../specimens/11-mutation-check/mutation.py)
is the reference this was extracted from and stays where it is, so the
specimen's recorded results remain reproducible.
`test_it_agrees_with_the_specimen_it_was_extracted_from` asserts the two behave
identically rather than trusting that they do — two copies of one idea drift,
and this repository is not entitled to assume otherwise about its own.

## Mutation record

A mutation checker that is not mutation-checked is the joke this repository
exists to prevent.

```bash
python3 test_mutcheck.py       # 14 tests
python3 mutation_record.py     # break the tool, count what notices
```

Seven deliberate breakages, no survivors on the first run:

| Mutation | Tests failed |
|---|---|
| Every mutation reports as caught | 4 |
| The original is never restored | 3 |
| An empty assertion message renders blank | 2 |
| A survivor no longer raises | 1 |
| A crash is reported as an assertion failure | 1 |
| A missing attribute is tolerated | 1 |
| The label is dropped | 1 |

`mutation_record.py` refuses to run against a red suite and says why — a
mutation score against a failing baseline is meaningless. It also reports
`ANCHOR NOT FOUND` rather than scoring a mutation it could not apply, because a
breakage that never landed and a breakage nothing caught would otherwise print
the same.

## Licence

Apache 2.0, same as the rest of the code here. Take it.
