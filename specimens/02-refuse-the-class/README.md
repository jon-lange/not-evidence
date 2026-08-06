# Specimen 02 — the second half is worth about ten

Demonstrates [pattern 02 · Refuse the Class, Not the Case](../../patterns/02-refuse-the-class.md).

A documentation build tool decides which references it will resolve. 48,000 possible references, one
boundary, two error channels: six distinct messages, or one identical refusal for everything. The
accepted set is the same in both. An automated prober tries to discover exactly what gets through.

```
 boundary        errors       first accept  complete           range   ratio   uniform costs more
 accreted        distinct               85     2,298       445-9,706       -                    -
 accreted        one code              713    24,592    1,078-39,976   10.7x                92.8%

 carve-out       distinct              117       488       174-2,252       -                    -
 carve-out       one code            5,508    26,885    1,326-47,789   55.1x                99.7%

 class           distinct            1,020     1,114       104-4,997       -                    -
 class           one code            1,020     1,114       104-4,997    1.0x                48.0%
```

**One identical error costs a prober about ten times as many probes on the boundary that looks like
real code, and fifty-five times on the one with an isolated exception.** Measured output across
three boundaries, two error channels and twenty-five seeds: **[RESULTS.md](RESULTS.md)**.

## The finding

**The second half is real, and it is smaller than the pattern implies.**

Pattern 02 says a prober who gets different messages for *unsupported scheme*, *host not permitted*
and *content type rejected* "has been handed a map of your filter, drawn by you, for free." Free is
not what it costs. The map costs about 2,298 probes with the messages and about 24,592 without them.
Six error classes do not buy six probes; they buy a hill-climb — a rejection whose code differs from
the last one means a different rule fired, which means the previous rule is now satisfied, and
following that walks straight down the rule chain to an accepted input. Collapse the codes and the
climb has no gradient, so it degenerates into scanning the neighbourhood.

**And the size of the win turns out to be geometry.** The accreted boundary's accepted regions sit
two single-field edits apart — local Markdown and remote Markdown differ in scheme and host — so a
prober with no signal at all expands outward from one and falls into the next. The carve-out's remote
exception sits four edits from anything else accepted and is one reference in 48,000; nothing short
of blind search finds it. Same prober, same rules, 10.7× against 55.1×.

The uncomfortable reading is that **uniform errors pay off in proportion to how badly the first half
was violated.** A boundary that accepts one contiguous thing gains nothing from silence — the class
refusal here is mapped in 1,114 probes whichever channel it uses, and that is fine, because "local
files only" is a map you would print in the documentation.

## Timing is not a weaker channel. It is the same channel

Both validators below return exactly one string for every rejection. One short-circuits on the first
failing rule, which is what any validator does unless somebody stopped it.

| rule that fired | short-circuit | constant work |
|---|---|---|
| E_MALFORMED | 1.5 µs | 351.3 µs |
| E_SCHEME | 4.4 µs | 347.2 µs |
| E_HOST | 13.1 µs | 347.6 µs |
| E_TYPE | 38.7 µs | 348.0 µs |
| E_INSECURE_TYPE | 115.8 µs | 350.0 µs |
| E_SIZE | 352.2 µs | 349.0 µs |

Nearest-centroid on latency alone recovers which rule fired **100% of the time** against 16.7%
chance. Then the same prober again, reading the clock instead of the message:

| | seed 0 | seed 1 | seed 2 |
|---|---|---|---|
| message-guided, six distinct codes | 1,212 | 4,199 | 815 |
| clock-guided, one identical code | **1,212** | **4,199** | **815** |
| clock-guided, one code + constant work | >8,000 | >8,000 | >8,000 |

**Run for run, seed for seed, the same numbers.** Making the strings identical changed nothing while
the evaluation order survived. The leak is loud because 80% of all references fail the first and
cheapest rule, so the modal rejection costs almost nothing and everything else stands out against
it — which is true of most real validators, since the syntactic checks go first.

## Half one: the class refusal is a smaller rule

| Boundary | predicates | table entries | accepted | unintended |
|---|---|---|---|---|
| accreted allowlist | 6 | 18 | 166 | **36** |
| class refusal | **2** | **0** | 80 | 0 |

The `unintended` column is one ordinary bug: the host check is `host.endswith(allowed)`, so
`evil-docs.example.com` satisfies a list that names three hosts and not that one. It accounts for
**21.7% of everything the boundary accepts**, and no additional allowlist entry fixes it, because no
entry was wrong. The class refusal has no host check to get past.

It also has **one error code without being asked**. Not discipline — it has one thing to say. That is
the link between the pattern's two halves that the entry does not draw: six rules mean six codes
somebody has to remember to collapse on every future edit, and to keep collapsed in the latency
envelope as well. Two rules mean one code, forever, by construction. **Refusing the class is what
makes the second half cheap to keep.**

What it costs: remote images. A docs tool that refuses remote references cannot render a badge from
a CDN, and this specimen names that rather than pretending the gap is not there.

## Run it

```bash
python3 probe.py            # about a minute; writes _generated/runs.jsonl
python3 probe.py --quick    # fewer seeds, fewer timing repetitions
```

No network, no API key, no dependencies, no configuration. The claim is about a validator's own code
rather than about a model, so everything is local. The probe-count rows are deterministic — seeds are
fixed — and only the latency rows move between runs. Per-run rows are written to
`_generated/runs.jsonl` before any table is computed.

## Tests

```bash
python3 test_validator.py     # 18 tests
python3 test_prober.py        # 19 tests
# or: python3 -m pytest -q
```

The load-bearing one is `test_the_error_channel_does_not_move_the_boundary`: the helpful and uniform
validators must accept identical references across all 48,000, or the comparison is between two
boundaries rather than two descriptions of one. Next to it,
`test_the_prober_reads_codes_as_opaque_labels` renames every code and requires the run to be
unchanged — if the prober were quietly reading their meaning, the measured advantage would be an
artefact of how these particular strings are spelled.

**Mutation-checked.** Twenty-five deliberate breakages:

| Mutation | Tests failed |
|---|---|
| Coordinate descent only looks at the first field | 11 |
| The helpful channel returns one code | 8 |
| The class refusal grows a host allowlist | 7 |
| The prober is never reported complete | 6 |
| The scheme allowlist admits everything | 5 |
| The uniform channel leaks the real code | 4 |
| Plain http may carry any allowed type | 4 |
| The climb takes any move, gradient or not | 4 |
| The climb never moves | 4 |
| The proposed box is trusted instead of confirmed | 4 |
| The cost model does no work | 3 |
| One size cap for every type | 3 |
| The host check is an exact match (the bypass is closed) | 2 |
| Evaluation never short-circuits | 2 |
| The carve-out sits beside the local branch | 2 |
| Latency is measured as a constant | 2 |
| constant_work is ignored | 1 |
| Every rule costs the same | 1 |
| `bypass_refs` finds nothing | 1 |
| The oracle does not cache | 1 |
| A reference is its own neighbour | 1 |
| The oracle ignores the relabelling hook | 1 |
| `dominance` counts ties as wins | 1 |
| The latency classifier always answers the same class | 1 |
| The climb does not stop on an accepted reference | **0 — see below** |

**The mutation check found a hole in the guard on the published numbers.** A wasteful hill-climb that
keeps scanning after it has already found an accepted reference moved the accreted helpful median
from 869 to 1,287 and passed every test, because the suite guarded the *ratio* and not the
numerator — so a change that made the message-guided prober lazy would have lowered the published
ratio while RESULTS.md went on quoting the old numerator. `test_the_gradient_walk_stays_cheap` closes
that.

It is left in the table at zero because after the fix it is still the mutation nearest the edge, and
a suite tight enough to catch a 1.5× efficiency change on a distribution running from 665 to 4,199
would be flaky. **These probe counts are guarded to about a factor of two, and that is the honest
statement of what the tests prove.**

One other mutation is worth recording: making the cost model's inner statement a no-op left the loop
itself running, so the per-rule work stayed proportional and the timing tests correctly stayed green.
That is a mutation that never landed, not an unproven assertion — the two are indistinguishable from
inside the check, and this specimen produced one of each.

## Where this is weaker than pattern 02 claims

**"For free" is wrong, and so is "the filter can't be mapped."** Distinct errors cost a prober about
2,298 probes here, not six. Uniform errors cost about 24,592 — an order of magnitude, and every
uniform run in this specimen still produced a complete and correct map. The honest claim is *the
filter costs an order of magnitude more to map*, not that it cannot be.

**The multiplier depends on something the entry does not mention.** 10.7× when the accepted regions
are adjacent, 55.1× when the exception is isolated, 1.0× when the boundary already has one thing to
say. Pattern 02 states the refusal unconditionally.

**The latency clause is buried and should not be.** The entry says "same string, same code, same
latency envelope" and puts the timing requirement third in a list. On this boundary the clock is not
a weaker channel than the message — it is an exact substitute, reproducing the message-guided attack
seed for seed. A team that collapses its error strings and ships has changed nothing.

## Scope

**One space, one prober, one machine.** Five fields with 12/10/10/8/5 values, three boundaries, at
most six rules. Every probe count is a property of this space's size and this accept set's geometry,
both of which were chosen. **"Ten times" is a measurement of this boundary, not a constant** — the
specimen's own second boundary moves it to fifty-five.

**The result that would falsify the pattern** is a uniform-error boundary that is no more expensive
to map than the helpful-error version of itself. The full list, with the observed value beside each,
is in [RESULTS.md](RESULTS.md).

## What this specimen deliberately does not do

**It does not search over probers.** The measured advantage is what one opaque-label hill-climb
extracts. A better attacker against the silent boundary — modelling the accept set as a union of
boxes, choosing probes by expected information gain rather than by neighbourhood expansion — would
narrow the gap. A better attacker against the helpful boundary, one that *reads* the messages instead
of comparing them for equality, would widen it. Both directions are open, and the conservative
reading was taken.

**It measures probes, not time or money.** A rate limit, a per-request price, or an alert on twenty
thousand rejections from one client changes the economics completely and is not modelled. Probes are
the part of the argument that does not depend on your deployment.

**The cost model is synthetic.** SHA-256 iterations stand in for a syntactic check, a table lookup, a
type sniff and a size read. The ~230x spread between the cheapest and most expensive rejection is a
design choice; what generalises is the *ordering*, which every short-circuiting validator has.

**The allowlist bug is planted.** `endswith` on a host list is real and common, but it is here
because it was put here. The specimen shows that such a bug is invisible in the rule table and absent
by construction from the class refusal. How often real allowlists carry one is not something it can
establish.

**Nothing here is about a model.** Pattern 02's motivating case is a URL handed to a provider that
dereferences it from its own network. This measures the validator standing in front of that, which is
the part that is yours.

---

Reference implementation. Not maintained.
