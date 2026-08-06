# Method

How this repository is written, and why it can be.

I work on AI platforms for a living. That is where the understanding behind these patterns came
from, and it is also the reason this document exists. Experience is portable; an employer's work
product is not. This is the discipline that keeps the line clear — published because a method you
can inspect is worth more than an assurance you have to take on faith.

## The rule

**1. The pattern is written before the code.**
Prose first, stating the general principle. If I can't state it without referring to a specific
implementation, I don't understand it well enough to publish it.

**2. The source is closed before anything is built.**
Specimens are written from the pattern statement, not alongside an original. A translation is a
derivative work; writing in a different language while reading the source is not independence, it
is transcription.

**3. Generic domains, always.**
Never a regulated vertical. A specimen written against a
domain is making a claim about a particular system. These patterns are general or they are nothing.

**4. Fresh abstractions.**
Different decomposition, different names, different structure. Where a specimen resembles something
that exists elsewhere, it's because the problem constrains the solution — not because the shape was
carried over.

**5. Public prior art, cited per pattern.**
Every entry names the public sources it builds on. This is the most important rule here and the
easiest to skip. A pattern traceable to published work is, by construction, not secret — and the
citation is what lets a reader verify that rather than trust it.

**6. No numbers from systems I didn't build for this repo.**
No percentages, no ratios, no orders of magnitude, no "we cut latency by X." Measurements are the
one category with no abstraction defense — a figure is either yours to publish or it isn't, and
rounding doesn't change that. Where a specimen reports a benchmark, it was generated on my own
hardware and the harness ships with it so you can rerun it.

## Why the numbers rule is absolute

Prose generalizes. Code can be rewritten. A number cannot be abstracted — it is uniquely
identifying, it can be matched against a dashboard with certainty, and in a regulated industry an
operational figure can be material non-public information regardless of whether it's anyone's
intellectual property. It is the highest-risk category and it is also the easiest to simply not do.

## Enforcement

Discipline that depends on remembering is not enforcement. This repository runs:

- **A forbidden-token scanner** on every commit and every push, against a private list of terms that
  must never appear here. That list is deliberately **not** in this repository — a file enumerating
  what you're trying to avoid saying is worse than the thing it prevents.
- **An identity guard** that blocks any commit authored from a work address.
- **CI that re-runs both over full history** on every push, because a local hook can be bypassed and
  history is the part you cannot cleanly fix later.
- **A quarterly adversarial read** of the whole repository, because each entry can be individually
  clean while the corpus, read by someone who knows the industry, is not. That's the failure mode
  that per-file review cannot catch.

## Corrections

If something here is wrong, or too close to a line, I'd rather know. Open an issue or write to me.

**The pattern states the current claim; the specimen records how it was reached.** An entry is a
reference, not a lab notebook — it says what I believe now and why, revised freely as evidence
arrives. The measurement record lives in each specimen's `RESULTS.md`: what was run, what came back,
what the scope was, and what result would falsify the claim.

That separation is deliberate. A reader wants the best current statement; an auditor wants the
evidence. Both are here, in the place each belongs.

A pattern that is retired rather than revised moves to `deprecated/` with `superseded-by:` set, so
inbound links keep resolving.
