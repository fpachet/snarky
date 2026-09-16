"""Sound NValue bounds and budgeted cover feasibility, shared by both runtimes.

Complete-state semantics live independently in predicates.py. This propagator
is not generally domain consistent: an exhausted cover budget proves nothing.
All scratch state is local to a revision, so rollback needs no cache repair.
"""

from __future__ import annotations

from collections import Counter

from ..terms import Number, Term
from .constraints import AllDifferentConstraint, NValueConstraint
from .predicates import integer

_COVER_NODES = 2_000
_COVER_WIDTH = 256
_COVER_DEPTH = 16


def _maximum_new_values(domains: list[set[Term]], mandatory: set[Term]) -> int:
    """Maximum partial matching into values not already counted as mandatory."""
    edges = [values - mandatory for values in domains if len(values) > 1]
    edges.sort(key=len)
    owner: dict[Term, int] = {}

    for start in range(len(edges)):
        pending = [start]
        parents: dict[int, tuple[int, Term]] = {}
        seen: set[Term] = set()
        augmented = False
        while pending and not augmented:
            index = pending.pop()
            for value in edges[index]:
                if value in seen:
                    continue
                seen.add(value)
                if value not in owner:
                    while True:
                        owner[value] = index
                        if index == start:
                            break
                        index, value = parents[index]
                    augmented = True
                    break
                other = owner[value]
                if other != start and other not in parents:
                    parents[other] = (index, value)
                    pending.append(other)
    return len(owner)


def _cover_possible(domains: list[set[Term]], slots: int, budget: int) -> bool | None:
    """Can at most slots values cover every domain? None means unproved.

    Used only as a necessary test for exact NValue. A cover at most k does not
    itself prove an assignment with exactly k distinct values.
    """
    if not domains:
        return True
    if slots <= 0:
        return False
    if slots >= len(domains):
        return True
    if len(domains) > _COVER_WIDTH or slots > _COVER_DEPTH or budget <= 0:
        return None
    masks: dict[Term, int] = {}
    for index, values in enumerate(domains):
        for value in values:
            masks[value] = masks.get(value, 0) | (1 << index)
    covers = sorted(set(masks.values()), key=lambda x: (-x.bit_count(), x))
    if len(covers) > _COVER_WIDTH:
        return None
    # Dominated columns may be removed for feasibility (not candidate pruning).
    maximal: list[int] = []
    for cover in covers:
        if not any(cover & other == cover for other in maximal):
            maximal.append(cover)
    choices = tuple(
        tuple(cover for cover in maximal if cover & (1 << index))
        for index in range(len(domains))
    )
    failed: set[tuple[int, int]] = set()
    remaining_budget = budget

    def visit(uncovered: int, available: int) -> bool | None:
        nonlocal remaining_budget
        if not uncovered:
            return True
        if not available:
            return False
        if remaining_budget <= 0:
            return None
        remaining_budget -= 1
        key = (uncovered, available)
        if key in failed:
            return False
        capacity = max((cover & uncovered).bit_count() for cover in maximal)
        if capacity * available < uncovered.bit_count():
            failed.add(key)
            return False
        # A complete cover must select one of the values covering this row.
        bits = uncovered
        selected = None
        while bits:
            bit = bits & -bits
            options = choices[bit.bit_length() - 1]
            if selected is None or len(options) < len(selected):
                selected = options
            bits ^= bit
        assert selected is not None
        unknown = False
        for cover in sorted(selected, key=lambda c: -(c & uncovered).bit_count()):
            outcome = visit(uncovered & ~cover, available - 1)
            if outcome is True:
                return True
            if outcome is None:
                unknown = True
                # The shared node budget has been consumed; do not explore
                # siblings or mislabel their unexplored subtrees as failures.
                break
        if unknown:
            return None
        failed.add(key)
        return False

    return visit((1 << len(domains)) - 1, slots)


def revise_nvalue(constraint: NValueConstraint, domains: dict[Term, set[Term]]) -> bool:
    """Sound pruning; exact for complete assignments and the stated special cases."""
    if any(not domains[var] for var in constraint.variables):
        return False
    if isinstance(constraint.count, int):
        counts = {constraint.count}
    else:
        counts = {integer(value) for value in domains[constraint.count]}
    scoped = [domains[var] for var in constraint.scope]
    mandatory = set(constraint.constants)
    mandatory.update(next(iter(values)) for values in scoped if len(values) == 1)
    uncovered = [values for values in scoped if not values & mandatory]

    # Pairwise disjoint domains require distinct additional values. A coverage
    # capacity bound is independent and sometimes stronger than this packing.
    selected: set[Term] = set()
    packing = 0
    for values in sorted(
        uncovered, key=lambda d: (len(d), tuple(sorted(map(repr, d))))
    ):
        if not selected & values:
            selected.update(values)
            packing += 1
    occurrences = Counter(value for values in uncovered for value in values)
    capacity = max(occurrences.values(), default=1)
    lower = len(mandatory) + max(packing, (len(uncovered) + capacity - 1) // capacity)
    upper = len(mandatory) + _maximum_new_values(scoped, mandatory)
    counts = {count for count in counts if lower <= count <= upper}
    if not counts:
        return False
    if not isinstance(constraint.count, int):
        domains[constraint.count].intersection_update(Number(count) for count in counts)

    # If every available value must occur, a sole occurrence is forced.
    alphabet = set(constraint.constants).union(*scoped)
    if min(counts) == len(alphabet):
        for value in alphabet - mandatory:
            possible = [var for var in constraint.scope if value in domains[var]]
            if not possible:
                return False
            if len(possible) == 1:
                domains[possible[0]].intersection_update((value,))
        if any(not domains[var] for var in constraint.variables):
            return False

    maximum = max(counts)
    if maximum == 1:
        common = set.intersection(*scoped) if scoped else set(constraint.constants)
        if constraint.constants:
            common.intersection_update(constraint.constants)
        for var in constraint.scope:
            domains[var].intersection_update(common)
        return all(domains[var] for var in constraint.variables)

    if len(counts) == 1 and maximum == len(constraint.scope) + len(
        constraint.constants
    ):
        # Every scoped variable must add a new value, distinct from all literals.
        for var in constraint.scope:
            domains[var].difference_update(constraint.constants)
        if not constraint.scope:
            return True
        from .kernels import _revise_all_different

        return _revise_all_different(
            AllDifferentConstraint(constraint.name, constraint.scope), domains
        )

    available = maximum - len(mandatory)
    if available == 0:
        for var in constraint.scope:
            domains[var].intersection_update(mandatory)
    elif available == 1 and uncovered:
        common = set.intersection(*uncovered)
        if not common:
            return False
        allowed = mandatory | common
        for var in constraint.scope:
            domains[var].intersection_update(allowed)
    elif _cover_possible(uncovered, available, _COVER_NODES) is False:
        return False
    return all(domains[var] for var in constraint.variables)
