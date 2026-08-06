# Observed results

**Run 2026-08-05, one machine, no network, no key.** A reference space of 48,000 items — 12 schemes
× 10 hosts × 10 content types × 8 declared sizes × 5 structural forms — and three ways of drawing a
boundary across it. Nothing here came from a real system; the space is defined in `validator.py` and
enumerated in process. The whole run takes about a minute.

Every prober run and every latency measurement is written to `_generated/runs.jsonl` **before** any
of these tables are computed — 444 rows carrying boundary, error channel, seed, probe count, first
accept, completion point, and, for the timing rows, the true class, the guessed class and the
seconds. The tables are aggregates of that file.

The probe-count rows are deterministic: seeds are fixed, so a rerun reproduces them exactly. Only
the latency rows move between runs.

## The setup

A documentation build tool decides which references it will resolve. Three boundaries:

| Boundary | What it is |
|---|---|
| **accreted allowlist** | six ordered rules over eighteen table entries — forms, schemes, hosts, content types, an http-only-images rule, per-type size caps |
| **narrow carve-out** | local docs, plus one exception: PNG thumbnails from one CDN at one size |
| **class refusal** | no scheme, no host, and the path resolves inside the docs root |

Each is exposed through two error channels, `distinct` and `one code`. **The accepted set is
identical across the two channels by construction**, asserted over all 48,000 references in
`test_validator.py`; the only difference is what a rejected caller is told.

## Half 1 — the class refusal is a smaller rule

| Boundary | predicates | table entries | accepted | of 48,000 | unintended |
|---|---|---|---|---|---|
| accreted allowlist | 6 | 18 | 166 | 0.3% | **36** |
| narrow carve-out | 5 | 12 | 9 | 0.0% | 0 |
| class refusal | **2** | **0** | 80 | 0.2% | 0 |

**Two predicates and no tables, against six predicates over eighteen entries.** "This boundary
accepts exactly one input type" is a sentence a reviewer can check; the accreted boundary needs
eighteen individual values to be right, and one matcher.

The `unintended` column is that matcher. The host check is `host.endswith(allowed)` — the most
ordinary allowlist bug there is — so `evil-docs.example.com` satisfies a list naming three hosts and
not that one. It accounts for **36 of the 166 references the boundary accepts, 21.7% of everything
that gets through**. No additional allowlist entry fixes it, because no entry was wrong.

The class refusal has no host check to get past. It also has **one error code, and not out of
discipline** — it has one thing to say, so there is no second string to keep identical.

That is the connection between the pattern's two halves that the entry does not draw: **the second
half is a maintenance burden proportional to the first.** Six rules mean six error codes somebody
has to remember to collapse, on every future edit. Two rules mean one.

## Half 2 — what a distinct error message costs

One prober, two oracles. The same `characterise()` runs against both channels of the same boundary.
It treats codes as **opaque labels** — equality comparison only, no parsing, no field names, no
assumed ordering — which is the weakest possible reading of "helpful errors" and is asserted by
`test_the_prober_reads_codes_as_opaque_labels`.

`complete` is the probe count at which the prober's model first agreed with the boundary on all
48,000 references. 25 seeds.

| Boundary | errors | first accept | complete | range | ratio | uniform costs more |
|---|---|---|---|---|---|---|
| accreted | distinct | 85 | 2,298 | 445–9,706 | — | — |
| accreted | one code | 713 | **24,592** | 1,078–39,976 | **10.7×** | 92.8% |
| carve-out | distinct | 117 | 488 | 174–2,252 | — | — |
| carve-out | one code | 5,508 | **26,885** | 1,326–47,789 | **55.1×** | 99.7% |
| class | distinct | 1,020 | 1,114 | 104–4,997 | — | — |
| class | one code | 1,020 | 1,114 | 104–4,997 | 1.0× | 48.0% |

**The headline is 10.7× on the boundary that looks like real code, and 55.1× on the one with an
isolated exception.** The last column is the honest reading of distributions this wide: over all
25 × 25 seed pairs, the uniform run was the more expensive one 92.8% and 99.7% of the time.

The class rows are the control. That boundary has one code either way, so those two rows are the
same experiment run twice, and two identical distributions put the dominance column at a coin toss —
which is what it reads.

### Why the two multipliers differ

The prober's advantage under distinct errors is a **hill-climb**: a rejection whose code differs from
the last one means a different rule fired, which means the previous rule is now satisfied. Follow
that and you walk down the rule chain to an accepted reference. Under one code there is no gradient,
and the same climb degenerates into an exhaustive scan of the neighbourhood.

But a scan of the neighbourhood is not nothing. The accreted boundary's accepted regions sit
**two single-field edits apart** — local Markdown and remote Markdown differ in scheme and host —
so a prober with no signal at all expands outward from one region and falls into the next. The
carve-out's remote exception sits **four edits away** from anything else accepted, and it is one
reference in 48,000: nothing short of blind search reaches it. Both distances are asserted in
`test_validator.py`, because they are the parameter the headline turns on.

**Geometry decides the multiplier, and pattern 02 does not mention geometry.**

### What the prober does, and what that costs both sides

Coordinate descent *proposes* a box and does not prove one: from an accepted reference at a corner,
the per-field answers combine into a region containing rejected points. Measured, not assumed —
`test_coordinate_descent_over_claims_and_the_prober_checks_it` pins a reference where it happens,
and an earlier version of this specimen reported completion on 8 of 10 accreted runs because the
unverified model over-claimed. The prober therefore confirms every box point by point. That cost is
identical under both oracles.

Two further choices are deliberately generous to the uniform side, so the measured advantage is a
lower bound:

- **Repeat queries are free.** Only distinct references are counted, and the prober with no gradient
  revisits far more.
- **The prober is not required to know it has finished.** Completion is graded externally, at the
  moment the model first became correct. A real attacker against a silent boundary has no such
  signal and would keep going.

## Timing — the same map, drawn from the clock

Both validators below return exactly one string, `E_REFUSED`, for every rejection. The left column
short-circuits on the first failing rule, which is what any validator does unless someone stopped it.
The right column evaluates every rule regardless of the outcome.

| rule that fired | short-circuit | constant work |
|---|---|---|
| E_MALFORMED | 1.5 µs | 351.3 µs |
| E_SCHEME | 4.4 µs | 347.2 µs |
| E_HOST | 13.1 µs | 347.6 µs |
| E_TYPE | 38.7 µs | 348.0 µs |
| E_INSECURE_TYPE | 115.8 µs | 350.0 µs |
| E_SIZE | 352.2 µs | 349.0 µs |

|  | accuracy | slowest/fastest class |
|---|---|---|
| short-circuit | **100.0%** | ~230× |
| constant work | 18.8% | 1.01× |

Nearest-centroid on latency alone, 24 held-out references per class, six classes, chance 16.7%.
Accuracy is the attacker's number; the spread is the robust one, because a classifier over centroids
that are not separated is a coin toss whose accuracy wanders around chance between runs.

Then the same prober again, reading the clock instead of the message:

| | seed 0 | seed 1 | seed 2 |
|---|---|---|---|
| message-guided, distinct codes | 1,212 | 4,199 | 815 |
| clock-guided, one identical code | **1,212** | **4,199** | **815** |
| clock-guided, one code + constant work | >8,000 | >8,000 | >8,000 |

**Run for run, seed for seed, the same numbers.** Recovery of the failing rule from latency is good
enough that the clock-guided prober takes exactly the path the message-guided one takes. Collapsing
six strings into one changed nothing at all while the ordering survived. Running every rule
regardless of outcome flattens the spread to 1.01× and the clock-guided prober stops finishing.

The reason the leak is this loud is in the space: **80% of all references fail the first and
cheapest rule**, so the modal rejection is the one that costs almost nothing, and everything else
stands out against it. That is a property of most real validators, which put the syntactic checks
first for exactly the reason that makes them audible.

## Where this is weaker than pattern 02 claims

**1. Distinct errors do not hand over the filter in six probes.** The entry says a prober who gets
different responses "has been handed a map of your filter, drawn by you, for free." Measured, the map
costs about 2,298 probes with the messages and about 24,592 without them. Free is not the word for
either; both are an afternoon and a loop. The number of distinct error classes is not the number of
probes — it is the *branching factor of a hill-climb* over a space whose size sets the real cost.

**2. The advantage depends on geometry the entry does not mention.** 10.7× when the accepted regions
are adjacent, 55.1× when the exception is isolated. A boundary whose accepted set is one contiguous
region gains almost nothing from silence — and the class refusal is exactly such a boundary, mapped
in 1,114 probes either way. Uniform errors are worth most precisely where the accept set is a
scattered accretion of carve-outs, which is to say **the second half pays off in proportion to how
badly the first half was violated.**

**3. Uniform errors raise the price; they do not close the oracle.** Every uniform run in this
specimen eventually produced a complete and correct map. Silence is a cost multiplier on an attack
that still succeeds, and an entry that reads as "the filter can't be mapped" — pattern 02's
Consequences section says exactly that — is overstating it. The honest claim is *the filter costs an
order of magnitude more to map*.

**4. The pattern says "same string, same code, same latency envelope" and puts the latency clause
last.** On this boundary the latency channel is not a weaker version of the message channel; it is
an exact substitute, reproducing the message-guided attack seed for seed. A team that collapses its
error strings and ships has changed nothing.

None of that overturns the refusal. It sharpens what it buys.

## What would falsify pattern 02

Measured on a boundary and space of this kind:

1. **A uniform-error boundary that is no more expensive to map.** If the ratio came out at or below
   1, the second half would be decoration. Observed: 10.7× and 55.1×, with the uniform run more
   expensive in 92.8% and 99.7% of seed pairs.
2. **A distinct-error boundary mapped in roughly the number of error classes.** This is what the
   pattern's "for free" implies, and it is the claim that did *not* survive. Observed: 2,298 probes
   against 6 error classes.
3. **A class refusal that is not smaller than the allowlist it replaces.** If refusing the class took
   as many rules and entries as filtering the cases, the first half would be a preference rather
   than an argument. Observed: 2 predicates and 0 entries against 6 and 18.
4. **An allowlist with no unintended acceptances.** The enumeration argument rests on the claim that
   a list of values plus a matcher admits things nobody listed. Observed: 36 of 166, from one
   `endswith`.
5. **A timing channel that is materially weaker than the message channel.** If constant messages with
   short-circuit evaluation had degraded the attack, "same string, same code" would be sufficient
   advice. Observed: identical probe counts, seed for seed.

## What the mutation check found

Twenty-five deliberate breakages across `validator.py`, `prober.py` and `probe.py`; the table is in
[README.md](README.md). Twenty-three were caught on the first pass.

**The first survivor was a hole in the guard on the published numbers.** *"The climb does not stop
on an accepted reference"* — a wasteful hill-climb that keeps scanning after it has already won —
changed the accreted helpful median from 869 to 1,287 and passed every test, because the suite
guarded the *ratio* and not the numerator. A change that made the message-guided prober lazy would
have lowered the published ratio while RESULTS.md went on quoting the old numerator.
`test_the_gradient_walk_stays_cheap` now pins it.

**The second survivor was a mutation that did not land**, and it is worth recording as such. Making
the cost model's inner statement a no-op left the loop itself running, so the per-rule work stayed
proportional and the timing tests correctly stayed green. Rewritten as `range(0)`, it is caught by
three tests. A surviving mutation is *one of two things*: an unproven assertion, or a breakage that
never happened. This specimen had one of each.

**And one mutation still survives after the fix**, deliberately left in the table: the wasteful climb
above, re-run, is caught — but a suite tight enough to catch a 1.5× efficiency change on a
distribution spanning 665 to 4,199 would be flaky. The published probe counts are guarded to about a
factor of two and not more, and that is the honest statement of what these tests prove.

## Reproducing

```bash
python3 probe.py             # about a minute; writes _generated/runs.jsonl
python3 probe.py --quick     # fewer seeds, fewer timing repetitions
python3 test_validator.py    # 18 tests
python3 test_prober.py       # 19 tests   (or: python3 -m pytest -q)
```

No network, no key, no dependencies, no configuration.

## Scope

**One space, one prober, one language, one machine.** Five fields with 12/10/10/8/5 values, three
boundaries, six rules at most. Every probe count above is a property of *this* space's size and
*this* accept set's geometry, and both were chosen. The multiplier is not a constant, and the
specimen's own second boundary exists to show how far it moves — a factor of five between two
boundaries of the same shape.

**One prober is not a search over probers.** The measured advantage of distinct errors is what *this*
hill-climb extracts. A better attacker against the uniform oracle — one that models the accept set as
a union of boxes and picks probes by expected information gain rather than by neighbourhood
expansion — would narrow the gap, and a better attacker against the distinct oracle, one that reads
the messages instead of comparing them for equality, would widen it. The opaque-label reading is
deliberately the conservative one.

**The advantage is measured as probes, not as time or money.** A rate limit, a per-request cost, or
an alert on 20,000 rejected references from one client changes this economics completely and is not
modelled here. The specimen measures information, and information is the part of the argument that
does not depend on your deployment.

**Latency numbers are machine-specific and the only rows that move between runs.** The cost model is
synthetic — SHA-256 iterations standing in for a syntactic check, a table lookup, a type sniff and a
size read. The ~230x spread is a design choice; what generalises is the *ordering*, which any
short-circuiting validator has.

**The bug is planted.** `endswith` on a host allowlist is a real and common bug, but it is here
because it was put here. The specimen shows that such a bug is invisible in the rule table and
absent by construction from the class refusal. It does not establish how often allowlists carry one.
