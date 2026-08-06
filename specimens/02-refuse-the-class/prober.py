"""One prober, two oracles.

The experiment holds the attacker constant and varies only what a rejected
probe is told. The same `characterise()` runs against the helpful-error
validator and the uniform-error validator; the probe counts differ only because
of the error channel.

The prober treats error codes as **opaque labels**. It never parses them, never
maps a code to a field, and never assumes an ordering. The only operation it
performs on a code is equality with another code. That is the weakest possible
reading of 'helpful errors' — a validator whose messages actually name the
offending field leaks strictly more than this — and it is deliberate: an
advantage that survives the opaque reading is an advantage that does not depend
on how the message is worded.

The algorithm:

  1. From a rejected reference, hill-climb: mutate one field at a time and
     keep any move that produces a **label this climb has not seen**. A new
     label means a different rule fired, which means the previous rule is now
     satisfied. That is a gradient, and following it walks down the rule chain
     to an accepted reference. Under the uniform oracle there is one label, no
     move is ever taken, and the same climb degenerates into an exhaustive scan
     of the neighbourhood.

  2. On an accepted reference not already covered by the model, run coordinate
     descent — for each field, which values keep it accepted — and record the
     resulting box.

  3. Coordinate descent probes every single-field neighbour of the accepted
     reference on the way past, so the neighbourhood is expanded for free.
     Rejected neighbours go back into step 1.

  4. When there is nothing left to walk, sample an unprobed reference at random.

Steps 3 and 4 are what an attacker does with no signal at all, and they are
available to both oracles. The prober is therefore not a straw man for the
uniform case: it expands outwards from known accepts, which is the right prior
when accepted regions are contiguous, and only falls back to blind sampling
when that is exhausted.

Scoring is external. The model is graded against the true accepted set by
enumeration after every change, and the reported number is the probe count at
which the model **first agreed with the boundary everywhere**. The prober is
not required to know it has finished. That is generous, and it is more generous
to the uniform oracle than to the helpful one, so the comparison is
conservative.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field
from itertools import product

from validator import DIMS, SPACE, SPACE_SIZE, VALUES, Ref, Verdict

MAX_BOX_POINTS = 20_000  # a soundness guard, not a tuning knob; see `descend`
MAX_CLIMB_STEPS = 12     # a climb cannot usefully exceed one step per distinct code


class Oracle:
    """Counts distinct references submitted. Repeats are free.

    Caching favours the uniform side — a prober with no gradient revisits far
    more often — which is again the conservative direction.
    """

    def __init__(self, validator, label_of=None):
        self.validator = validator
        self.label_of = label_of or (lambda ref, verdict: verdict.code)
        self.cache: dict[Ref, Verdict] = {}
        self.probes = 0

    def query(self, ref: Ref) -> Verdict:
        hit = self.cache.get(ref)
        if hit is not None:
            return hit
        self.probes += 1
        verdict = self.validator(ref)
        verdict = Verdict(verdict.ok, self.label_of(ref, verdict))
        self.cache[ref] = verdict
        return verdict


@dataclass(frozen=True)
class Box:
    """An axis-aligned region of the reference space."""

    values: tuple[tuple[str, frozenset], ...]

    def points(self):
        dims = dict(self.values)
        for combo in product(*(sorted(dims[d], key=str) for d in DIMS)):
            yield Ref(*combo)

    def size(self) -> int:
        n = 1
        for _, vs in self.values:
            n *= len(vs)
        return n


@dataclass
class Run:
    """What one characterisation attempt produced."""

    probes: int
    probes_to_first_accept: int | None
    probes_to_complete: int | None
    boxes: int
    history: list = field(default_factory=list)
    unsound_boxes: int = 0
    model: frozenset = frozenset()


def neighbours(ref: Ref):
    for dim in DIMS:
        current = getattr(ref, dim)
        for value in VALUES[dim]:
            if value != current:
                yield ref.with_(dim, value)


def descend(ref: Ref, see) -> Box:
    """Coordinate descent: for each field, which values keep this accepted."""
    values = []
    for dim in DIMS:
        allowed = {getattr(ref, dim)}
        for value in VALUES[dim]:
            if value != getattr(ref, dim) and see(ref.with_(dim, value)).ok:
                allowed.add(value)
        values.append((dim, frozenset(allowed)))
    return Box(tuple(values))


def characterise(validator, truth: frozenset, *, seed: int = 0,
                 budget: int = SPACE_SIZE, label_of=None,
                 stop_when_complete: bool = True) -> Run:
    rng = random.Random(seed)
    oracle = Oracle(validator, label_of=label_of)

    open_accepts: deque[Ref] = deque()
    open_rejects: deque[tuple[Ref, str]] = deque()
    known_accepts: set[Ref] = set()
    covered: set[Ref] = set()
    run = Run(probes=0, probes_to_first_accept=None, probes_to_complete=None, boxes=0)

    def see(ref: Ref) -> Verdict:
        """Submit a reference, and queue it for follow-up the first time only."""
        hit = oracle.cache.get(ref)
        if hit is not None:
            return hit
        verdict = oracle.query(ref)
        if verdict.ok:
            known_accepts.add(ref)
            open_accepts.append(ref)
            if run.probes_to_first_accept is None:
                run.probes_to_first_accept = oracle.probes
        else:
            open_rejects.append((ref, verdict.code))
        return verdict

    def record() -> bool:
        disagreements = len(truth.symmetric_difference(covered))
        run.history.append((oracle.probes, len(covered), disagreements))
        if disagreements == 0 and run.probes_to_complete is None:
            run.probes_to_complete = oracle.probes
        return disagreements == 0

    def climb(ref: Ref, label: str) -> None:
        """Hill-climb from a rejected reference, using the label as the gradient.

        A move is taken when it produces a label this climb has not seen yet: a
        new label means a different rule fired, which means the previous one is
        now satisfied. Refusing to revisit a label is the whole heuristic — it
        is semantics-free, it needs no idea what any code means, and it bounds
        the climb at one pass per distinct code.

        Under a uniform oracle there is exactly one code, so no move is ever
        taken and this degenerates into a full scan of the neighbourhood. That
        degeneration is the measurement.
        """
        current, seen_labels = ref, {label}
        for _ in range(MAX_CLIMB_STEPS):
            order = list(neighbours(current))
            rng.shuffle(order)
            moved = False
            for candidate in order:
                if oracle.probes >= budget:
                    return
                verdict = see(candidate)
                if verdict.ok:
                    return
                if verdict.code not in seen_labels:
                    seen_labels.add(verdict.code)
                    current = candidate
                    moved = True
                    break
            if not moved:
                return

    # Blind sampling is without replacement: re-drawing a reference you have
    # already sent tells you nothing, and no attacker would pay for it.
    pool = list(SPACE)
    rng.shuffle(pool)
    pool_at = 0

    def next_unprobed():
        nonlocal pool_at
        while pool_at < len(pool):
            ref = pool[pool_at]
            pool_at += 1
            if ref not in oracle.cache:
                return ref
        return None

    see(next_unprobed())

    complete = False
    while oracle.probes < budget and not (complete and stop_when_complete):
        if open_accepts:
            ref = open_accepts.popleft()
            if ref in covered:
                continue
            box = descend(ref, see)
            run.boxes += 1
            # Coordinate descent proposes a box; it does not prove one. From an
            # accepted reference at a corner, the per-field answers can combine
            # into a region that is not entirely accepted — measured here, not
            # assumed: the unverified model over-claimed on 2 of 10 accreted
            # runs. So the box is confirmed point by point, and only confirmed
            # points enter the model. The cost is identical under both oracles.
            if box.size() <= MAX_BOX_POINTS:
                confirmed = {p for p in box.points() if see(p).ok}
                if len(confirmed) < box.size():
                    run.unsound_boxes += 1
            else:
                confirmed = {ref}
            covered |= confirmed
            complete = record()
        elif open_rejects:
            ref, label = open_rejects.popleft()
            climb(ref, label)
        else:
            ref = next_unprobed()
            if ref is None:
                break
            see(ref)

    run.probes = oracle.probes
    run.model = frozenset(covered)
    if not run.history:
        record()
    return run
