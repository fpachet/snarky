"""Persistent narrowing-only constraints over Snarky candidate facts.

Root ``candidate`` facts define finite domains. Persistent constraints remove
unsupported candidates, forward rules observe the filtered facts, and explicit
``CHOICE`` decisions trigger another propagation closure. Session rollback
restores the visible domains; the propagator detects that widening and safely
rebuilds its branch-local cache.
"""

from __future__ import annotations

import math
from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass, field
from weakref import WeakKeyDictionary

from snarky import (
    Atom,
    Fact,
    InferenceSession,
    Number,
    Term,
    Triple,
)

from .finite_domain_projection import FiniteDomainProjection

CANDIDATE = Atom("candidate")
STATE = Atom("state")
CONTRADICTION = Atom("contradiction")
VIOLATED_CONSTRAINT = Atom("violated_constraint")
EMPTY_DOMAIN = Atom("empty_domain")


@dataclass(frozen=True, slots=True)
class AllDifferentConstraint:
    """Require the scoped variables to take pairwise-distinct values."""

    name: Atom
    variables: tuple[Term, ...]

    def __post_init__(self) -> None:
        _validate_scope("ALL_DIFFERENT", self.variables)
        object.__setattr__(self, "variables", tuple(self.variables))


@dataclass(frozen=True, slots=True)
class SumConstraint:
    """Require the scoped integer variables to sum exactly to ``target``."""

    name: Atom
    variables: tuple[Term, ...]
    target: int

    def __post_init__(self) -> None:
        _validate_scope("SUM", self.variables)
        object.__setattr__(self, "variables", tuple(self.variables))


@dataclass(frozen=True, slots=True)
class GlobalCardinalityConstraint:
    """Bound the number of occurrences of selected values in a scope.

    ``bounds`` contains ``(value, lower, upper)`` triples. Values without an
    explicit entry retain the default interval ``[0, number of variables]``.
    """

    name: Atom
    variables: tuple[Term, ...]
    bounds: tuple[tuple[Term, int, int], ...]

    def __post_init__(self) -> None:
        _validate_scope("GCC", self.variables)
        bounds = tuple(self.bounds)
        values = tuple(value for value, _, _ in bounds)
        if len(set(values)) != len(values):
            raise ValueError("GCC values must have unique bounds")
        for _, lower, upper in bounds:
            if lower < 0 or upper < lower:
                raise ValueError("GCC bounds require 0 <= lower <= upper")
        object.__setattr__(self, "variables", tuple(self.variables))
        object.__setattr__(self, "bounds", bounds)


@dataclass(frozen=True, slots=True)
class TableConstraint:
    """Require the scoped variables to match one allowed tuple."""

    name: Atom
    variables: tuple[Term, ...]
    allowed: tuple[tuple[Term, ...], ...]

    def __post_init__(self) -> None:
        _validate_scope("TABLE", self.variables)
        allowed = tuple(tuple(row) for row in self.allowed)
        if not allowed:
            raise ValueError("TABLE requires at least one allowed tuple")
        if any(len(row) != len(self.variables) for row in allowed):
            raise ValueError("TABLE tuple arity must match its scope")
        object.__setattr__(self, "variables", tuple(self.variables))
        object.__setattr__(self, "allowed", tuple(dict.fromkeys(allowed)))


@dataclass(frozen=True, slots=True)
class LexLessEqualConstraint:
    """Require one sequence of numeric variables to be lexicographically <= another."""

    name: Atom
    left: tuple[Term, ...]
    right: tuple[Term, ...]

    def __post_init__(self) -> None:
        left = tuple(self.left)
        right = tuple(self.right)
        if not left or len(left) != len(right):
            raise ValueError(
                "LEX_LESS_EQUAL requires non-empty sequences of equal length"
            )
        object.__setattr__(self, "left", left)
        object.__setattr__(self, "right", right)

    @property
    def variables(self) -> tuple[Term, ...]:
        """Return the distinct variables observed by this constraint."""

        return tuple(dict.fromkeys((*self.left, *self.right)))


type PersistentConstraint = (
    AllDifferentConstraint
    | SumConstraint
    | GlobalCardinalityConstraint
    | TableConstraint
    | LexLessEqualConstraint
)


@dataclass(frozen=True, slots=True)
class CandidateRemovalExplanation:
    """Identify the constraint that removed one candidate value."""

    variable: Term
    value: Term
    constraint: Atom


@dataclass(slots=True)
class _CachedPropagationState:
    domains: dict[Term, set[Term]]
    violated: PersistentConstraint | None = None
    removal_causes: dict[tuple[Term, Term], Atom] = field(
        default_factory=dict
    )
    generation: int = 0
    all_different_matchings: dict[int, dict[Term, Term]] = field(
        default_factory=dict
    )


class PersistentConstraintPropagator:
    """Maintain a joint fixed point for persistent finite-domain constraints.

    The immutable adjacency graph is shared. Cached domains are isolated by
    ``InferenceSession`` identity. Domain removals schedule only incident
    constraints; a rollback or other widening rebuilds the affected session
    state from its restored candidate facts.
    """

    watched_relations = frozenset((CANDIDATE,))

    def __init__(
        self,
        problem: Atom,
        constraints: tuple[PersistentConstraint, ...],
        projection: FiniteDomainProjection | None = None,
    ) -> None:
        self.problem = problem
        self.projection = projection or FiniteDomainProjection()
        self.constraints = tuple(constraints)
        names = tuple(constraint.name for constraint in self.constraints)
        if len(set(names)) != len(names):
            raise ValueError("persistent constraint names must be unique")
        scoped = {
            variable
            for constraint in self.constraints
            for variable in constraint.variables
        }
        self._variables = frozenset(scoped)
        adjacency: dict[Term, list[int]] = {
            variable: [] for variable in scoped
        }
        for index, constraint in enumerate(self.constraints):
            for variable in constraint.variables:
                adjacency[variable].append(index)
        self._adjacency = {
            variable: tuple(indices)
            for variable, indices in adjacency.items()
        }
        self._states: WeakKeyDictionary[
            InferenceSession,
            _CachedPropagationState,
        ] = WeakKeyDictionary()

    def __call__(self, session: InferenceSession) -> None:
        if not self.constraints:
            return
        snapshot = self.projection.snapshot(session)
        visible = {
            variable: set(candidates)
            for variable, candidates in snapshot.candidates.items()
        }
        current = {
            variable: set(visible.get(variable, ()))
            for variable in self._variables
        }
        state = self._states.get(session)
        if (
            state is not None
            and state.generation != snapshot.cursor.generation
        ):
            # A rollback starts another journal generation. Causes from the
            # abandoned branch must never be attributed to its sibling.
            state.removal_causes.clear()
            state.generation = snapshot.cursor.generation
        widened = state is None or any(
            current[variable] - state.domains[variable]
            for variable in self._variables
        )
        queued: set[int]

        if widened:
            reusable_matchings = (
                {}
                if state is None
                else state.all_different_matchings
            )
            state = _CachedPropagationState(
                {
                    variable: set(values)
                    for variable, values in current.items()
                },
                generation=snapshot.cursor.generation,
                all_different_matchings=reusable_matchings,
            )
            self._states[session] = state
            pending = deque(range(len(self.constraints)))
            queued = set(pending)
        else:
            assert state is not None
            externally_changed: set[Term] = set()
            for variable in self._variables:
                removed = state.domains[variable] - current[variable]
                if removed:
                    state.domains[variable].difference_update(removed)
                    externally_changed.add(variable)
            if not externally_changed:
                return
            pending = deque()
            queued = set()
            for variable in sorted(externally_changed, key=repr):
                _schedule(
                    self._adjacency[variable],
                    pending,
                    queued,
                )

        state.violated = None
        while pending and state.violated is None:
            index = pending.popleft()
            queued.remove(index)
            constraint = self.constraints[index]
            changed, removed, consistent = _revise(
                constraint,
                state.domains,
                index=index,
                state=state,
            )
            for variable, value in removed:
                state.removal_causes[(variable, value)] = constraint.name
            if not consistent:
                state.violated = constraint
                break
            for variable in sorted(changed, key=repr):
                _schedule(
                    self._adjacency[variable],
                    pending,
                    queued,
                )

        removals = tuple(
            Fact(Triple(variable, CANDIDATE, value))
            for variable in sorted(self._variables, key=repr)
            for value in sorted(
                current[variable] - state.domains[variable],
                key=repr,
            )
        )
        if removals:
            session.retract(*removals, label="persistent-constraint")
        if state.violated is not None:
            session.assume(
                Fact(Triple(self.problem, STATE, CONTRADICTION)),
                Fact(
                    Triple(
                        self.problem,
                        VIOLATED_CONSTRAINT,
                        state.violated.name,
                    )
                ),
                label=f"constraint:{state.violated.name.name}",
            )
        state.generation = session.event_cursor().generation

    def removal_explanations(
        self,
        session: InferenceSession,
    ) -> tuple[CandidateRemovalExplanation, ...]:
        """Return current branch-local candidate-removal explanations."""

        state = self._states.get(session)
        if state is None:
            return ()
        return tuple(
            CandidateRemovalExplanation(variable, value, constraint)
            for (variable, value), constraint in sorted(
                state.removal_causes.items(),
                key=lambda item: (
                    repr(item[0][0]),
                    repr(item[0][1]),
                    item[1].name,
                ),
            )
        )

    def failure_constraints(
        self,
        session: InferenceSession,
    ) -> tuple[Atom, ...]:
        """Return the constraints that explain the current failed state."""

        state = self._states.get(session)
        if state is None:
            return ()
        if state.violated is not None:
            return (state.violated.name,)
        empty_variables = {
            fact.entity.object
            for fact in session.facts
            if isinstance(fact.entity, Triple)
            and fact.entity.subject == self.problem
            and fact.entity.relation == EMPTY_DOMAIN
        }
        return tuple(
            dict.fromkeys(
                constraint
                for (variable, _), constraint in sorted(
                    state.removal_causes.items(),
                    key=lambda item: (
                        repr(item[0][0]),
                        repr(item[0][1]),
                        item[1].name,
                    ),
                )
                if variable in empty_variables
            )
        )


def _validate_scope(kind: str, variables: tuple[Term, ...]) -> None:
    variables = tuple(variables)
    if not variables:
        raise ValueError(f"{kind} requires at least one variable")
    if len(set(variables)) != len(variables):
        raise ValueError(f"{kind} variables must be distinct")


def _schedule(
    indices: tuple[int, ...],
    pending: deque[int],
    queued: set[int],
) -> None:
    for index in indices:
        if index not in queued:
            pending.append(index)
            queued.add(index)


def _candidate_domains(
    facts: tuple[Fact, ...],
) -> dict[Term, set[Term]]:
    domains: dict[Term, set[Term]] = {}
    for fact in facts:
        entity = fact.entity
        if isinstance(entity, Triple) and entity.relation == CANDIDATE:
            domains.setdefault(entity.subject, set()).add(entity.object)
    return domains


def _revise(
    constraint: PersistentConstraint,
    domains: dict[Term, set[Term]],
    *,
    index: int | None = None,
    state: _CachedPropagationState | None = None,
) -> tuple[set[Term], set[tuple[Term, Term]], bool]:
    before = {
        variable: frozenset(domains[variable])
        for variable in constraint.variables
    }
    if isinstance(constraint, AllDifferentConstraint):
        previous_matching = (
            None
            if index is None or state is None
            else state.all_different_matchings.get(index)
        )
        consistent, matching = _revise_all_different_with_matching(
            constraint,
            domains,
            previous_matching,
        )
        if index is not None and state is not None:
            if matching is None:
                state.all_different_matchings.pop(index, None)
            else:
                state.all_different_matchings[index] = matching
    elif isinstance(constraint, SumConstraint):
        consistent = _revise_sum(constraint, domains)
    elif isinstance(constraint, GlobalCardinalityConstraint):
        consistent = _revise_gcc(constraint, domains)
    elif isinstance(constraint, TableConstraint):
        consistent = _revise_table(constraint, domains)
    else:
        consistent = _revise_lex_less_equal(constraint, domains)
    changed = {
        variable
        for variable, previous in before.items()
        if domains[variable] != previous
    }
    removed = {
        (variable, value)
        for variable, previous in before.items()
        for value in previous - domains[variable]
    }
    return changed, removed, consistent


def _revise_all_different(
    constraint: AllDifferentConstraint,
    domains: dict[Term, set[Term]],
) -> bool:
    consistent, _ = _revise_all_different_with_matching(
        constraint,
        domains,
    )
    return consistent


def _revise_all_different_with_matching(
    constraint: AllDifferentConstraint,
    domains: dict[Term, set[Term]],
    previous_matching: Mapping[Term, Term] | None = None,
) -> tuple[bool, dict[Term, Term] | None]:
    scoped = {
        variable: domains[variable]
        for variable in constraint.variables
    }
    matching = _maximum_matching(scoped, previous_matching)
    if matching is None:
        return False, None

    # Régin filtering represented on the value graph. For each variable,
    # direct its matched value toward every alternative value. An alternative
    # is supported iff it belongs to an alternating cycle or can lead to a
    # free value.
    all_values = {
        value for values in scoped.values() for value in values
    }
    matched_values = frozenset(matching.values())
    graph: dict[Term, set[Term]] = {
        value: set() for value in all_values
    }
    for variable, matched in matching.items():
        graph[matched].update(scoped[variable] - {matched})
    components = _strongly_connected_components(graph)
    free_values = all_values - matched_values
    can_reach_free = _nodes_reaching(graph, free_values)

    for variable, matched in matching.items():
        supported = {
            value
            for value in scoped[variable]
            if (
                value == matched
                or components[value] == components[matched]
                or value in can_reach_free
            )
        }
        domains[variable].intersection_update(supported)
        if not domains[variable]:
            return False, None
    return True, matching


def _maximum_matching(
    domains: Mapping[Term, set[Term]],
    initial: Mapping[Term, Term] | None = None,
) -> dict[Term, Term] | None:
    """Return a complete variable-to-value matching using Hopcroft--Karp."""

    variables = tuple(
        sorted(domains, key=lambda item: (len(domains[item]), repr(item)))
    )
    if any(not domains[variable] for variable in variables):
        return None
    pair_variable: dict[Term, Term | None] = {
        variable: None for variable in variables
    }
    pair_value: dict[Term, Term] = {}
    if initial is not None:
        for variable in variables:
            value = initial.get(variable)
            if (
                value is None
                or value not in domains[variable]
                or value in pair_value
            ):
                continue
            pair_variable[variable] = value
            pair_value[value] = variable
    distance: dict[Term, int] = {}
    infinity = len(variables) + 1

    def breadth_first() -> bool:
        queue: deque[Term] = deque()
        found = False
        for variable in variables:
            if pair_variable[variable] is None:
                distance[variable] = 0
                queue.append(variable)
            else:
                distance[variable] = infinity
        while queue:
            variable = queue.popleft()
            for value in domains[variable]:
                owner = pair_value.get(value)
                if owner is None:
                    found = True
                elif distance[owner] == infinity:
                    distance[owner] = distance[variable] + 1
                    queue.append(owner)
        return found

    def depth_first(variable: Term) -> bool:
        for value in sorted(domains[variable], key=repr):
            owner = pair_value.get(value)
            if owner is None or (
                distance[owner] == distance[variable] + 1
                and depth_first(owner)
            ):
                pair_variable[variable] = value
                pair_value[value] = variable
                return True
        distance[variable] = infinity
        return False

    cardinality = len(pair_value)
    while breadth_first():
        for variable in variables:
            if pair_variable[variable] is None and depth_first(variable):
                cardinality += 1
    if cardinality != len(variables):
        return None
    return {
        variable: value
        for variable, value in pair_variable.items()
        if value is not None
    }


def _strongly_connected_components(
    graph: Mapping[Term, set[Term]],
) -> dict[Term, int]:
    index = 0
    indices: dict[Term, int] = {}
    lowlinks: dict[Term, int] = {}
    stack: list[Term] = []
    on_stack: set[Term] = set()
    output: dict[Term, int] = {}
    component = 0

    def visit(node: Term) -> None:
        nonlocal component, index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for successor in graph[node]:
            if successor not in indices:
                visit(successor)
                lowlinks[node] = min(lowlinks[node], lowlinks[successor])
            elif successor in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[successor])
        if lowlinks[node] != indices[node]:
            return
        while True:
            member = stack.pop()
            on_stack.remove(member)
            output[member] = component
            if member == node:
                break
        component += 1

    for node in graph:
        if node not in indices:
            visit(node)
    return output


def _nodes_reaching(
    graph: Mapping[Term, set[Term]],
    targets: set[Term],
) -> frozenset[Term]:
    reverse: dict[Term, set[Term]] = {
        node: set() for node in graph
    }
    for node, successors in graph.items():
        for successor in successors:
            reverse[successor].add(node)
    reached = set(targets)
    pending = deque(targets)
    while pending:
        node = pending.popleft()
        for predecessor in reverse[node]:
            if predecessor not in reached:
                reached.add(predecessor)
                pending.append(predecessor)
    return frozenset(reached)


def _revise_sum(
    constraint: SumConstraint,
    domains: dict[Term, set[Term]],
) -> bool:
    numeric_domains: list[tuple[Term, dict[Term, int]]] = []
    for variable in constraint.variables:
        converted: dict[Term, int] = {}
        for value in domains[variable]:
            if not isinstance(value, Number) or not isinstance(value.value, int):
                raise TypeError(
                    f"SUM constraint {constraint.name.name!r} requires "
                    "integer Number candidates"
                )
            converted[value] = value.value
        if not converted:
            return False
        numeric_domains.append((variable, converted))

    if constraint.target >= 0 and all(
        all(value >= 0 for value in values.values())
        for _, values in numeric_domains
    ):
        maximum_sum = sum(
            max(values.values()) for _, values in numeric_domains
        )
        if constraint.target > maximum_sum:
            return False
        if maximum_sum <= 1_000_000:
            return _revise_nonnegative_sum_bitsets(
                constraint,
                domains,
                numeric_domains,
            )

    prefix: list[set[int]] = [{0}]
    for _, values in numeric_domains:
        prefix.append(
            {
                partial + value
                for partial in prefix[-1]
                for value in values.values()
            }
        )
    if constraint.target not in prefix[-1]:
        return False

    suffix: list[set[int]] = [set() for _ in range(len(numeric_domains) + 1)]
    suffix[-1] = {0}
    for index in range(len(numeric_domains) - 1, -1, -1):
        suffix[index] = {
            value + partial
            for value in numeric_domains[index][1].values()
            for partial in suffix[index + 1]
        }

    for index, (variable, values) in enumerate(numeric_domains):
        possible_remainders = {
            left_sum + right_sum
            for left_sum in prefix[index]
            for right_sum in suffix[index + 1]
        }
        supported = {
            term
            for term, numeric_value in values.items()
            if constraint.target - numeric_value in possible_remainders
        }
        domains[variable].intersection_update(supported)
        if not domains[variable]:
            return False
    return True


def _revise_lex_less_equal(
    constraint: LexLessEqualConstraint,
    domains: dict[Term, set[Term]],
) -> bool:
    """Establish GAC for disjoint sequences, with safe alias-aware bounds."""

    variables = constraint.variables
    if any(not domains[variable] for variable in variables):
        return False
    numeric_domains = {
        variable: {
            value: _lex_numeric_value(constraint, value)
            for value in domains[variable]
        }
        for variable in variables
    }
    if len(variables) == 2 * len(constraint.left):
        return _revise_disjoint_lex_less_equal(
            constraint,
            domains,
            numeric_domains,
        )
    return _revise_aliased_lex_less_equal_bounds(
        constraint,
        domains,
        numeric_domains,
    )


def _revise_disjoint_lex_less_equal(
    constraint: LexLessEqualConstraint,
    domains: dict[Term, set[Term]],
    numeric_domains: Mapping[Term, Mapping[Term, int | float]],
) -> bool:
    """Establish GAC when every sequence position has distinct variables."""

    size = len(constraint.left)
    equality_possible = [False] * size
    strict_possible = [False] * size
    suffix_feasible = [False] * (size + 1)
    suffix_feasible[size] = True
    for position in range(size - 1, -1, -1):
        left = constraint.left[position]
        right = constraint.right[position]
        equality_possible[position] = bool(
            domains[left] & domains[right]
        )
        strict_possible[position] = (
            min(numeric_domains[left].values())
            < max(numeric_domains[right].values())
        )
        suffix_feasible[position] = (
            strict_possible[position]
            or (
                equality_possible[position]
                and suffix_feasible[position + 1]
            )
        )
    if not suffix_feasible[0]:
        return False

    prefix_equal = True
    prefix_less = False
    for position, (left, right) in enumerate(
        zip(constraint.left, constraint.right, strict=True)
    ):
        if not prefix_less:
            left_min = min(numeric_domains[left].values())
            right_max = max(numeric_domains[right].values())
            supported_left = {
                value
                for value, numeric in numeric_domains[left].items()
                if prefix_equal
                and (
                    numeric < right_max
                    or (
                        value in domains[right]
                        and suffix_feasible[position + 1]
                    )
                )
            }
            supported_right = {
                value
                for value, numeric in numeric_domains[right].items()
                if prefix_equal
                and (
                    left_min < numeric
                    or (
                        value in domains[left]
                        and suffix_feasible[position + 1]
                    )
                )
            }
            domains[left].intersection_update(supported_left)
            domains[right].intersection_update(supported_right)
            if not domains[left] or not domains[right]:
                return False
        prefix_less = prefix_less or (
            prefix_equal and strict_possible[position]
        )
        prefix_equal = (
            prefix_equal and equality_possible[position]
        )
    return True


def _revise_aliased_lex_less_equal_bounds(
    constraint: LexLessEqualConstraint,
    domains: dict[Term, set[Term]],
    numeric_domains: Mapping[Term, Mapping[Term, int | float]],
) -> bool:
    """Apply numeric bounds filtering at the first non-fixed position.

    The linear propagator is intentionally conservative after an ambiguous
    equality: representing both the equal and strictly-less continuations
    would require reification. It is exact once the preceding pairs are fixed
    equal, and is cheap enough for large symmetry-breaking vectors.
    """

    for left, right in zip(constraint.left, constraint.right, strict=True):
        if left == right:
            continue
        left_values = numeric_domains[left]
        right_values = numeric_domains[right]
        left_min = min(left_values.values())
        left_max = max(left_values.values())
        right_min = min(right_values.values())
        right_max = max(right_values.values())
        if left_max < right_min:
            return True
        if left_min > right_max:
            return False

        domains[left].intersection_update(
            value
            for value, numeric in left_values.items()
            if numeric <= right_max
        )
        domains[right].intersection_update(
            value
            for value, numeric in right_values.items()
            if numeric >= left_min
        )
        if not domains[left] or not domains[right]:
            return False
        if (
            len(domains[left]) == 1
            and domains[left] == domains[right]
        ):
            continue
        return True
    return True


def _lex_numeric_value(
    constraint: LexLessEqualConstraint,
    value: Term,
) -> int | float:
    if (
        not isinstance(value, Number)
        or isinstance(value.value, bool)
        or not isinstance(value.value, (int, float))
        or not math.isfinite(value.value)
    ):
        raise TypeError(
            f"LEX_LESS_EQUAL constraint {constraint.name.name!r} requires "
            "numeric Number candidates"
        )
    return value.value


def _revise_nonnegative_sum_bitsets(
    constraint: SumConstraint,
    domains: dict[Term, set[Term]],
    numeric_domains: list[tuple[Term, dict[Term, int]]],
) -> bool:
    """Establish exact support with integer reachable-sum bitsets."""

    prefix = [1]
    for _, values in numeric_domains:
        reachable = 0
        for value in values.values():
            reachable |= prefix[-1] << value
        prefix.append(reachable)
    if not prefix[-1] & (1 << constraint.target):
        return False

    suffix = [0] * (len(numeric_domains) + 1)
    suffix[-1] = 1
    for index in range(len(numeric_domains) - 1, -1, -1):
        reachable = 0
        for value in numeric_domains[index][1].values():
            reachable |= suffix[index + 1] << value
        suffix[index] = reachable

    for index, (variable, values) in enumerate(numeric_domains):
        remainders = _bitset_sumset(
            prefix[index],
            suffix[index + 1],
            constraint.target,
        )
        supported = {
            term
            for term, value in values.items()
            if (
                constraint.target >= value
                and remainders
                & (1 << (constraint.target - value))
            )
        }
        domains[variable].intersection_update(supported)
        if not domains[variable]:
            return False
    return True


def _bitset_sumset(left: int, right: int, limit: int) -> int:
    """Return reachable pairwise sums up to *limit* as one bitset."""

    if limit < 0:
        return 0
    if left.bit_count() > right.bit_count():
        left, right = right, left
    reachable = 0
    candidates = left
    while candidates:
        least = candidates & -candidates
        reachable |= right << (least.bit_length() - 1)
        candidates ^= least
    return reachable & ((1 << (limit + 1)) - 1)


def _revise_gcc(
    constraint: GlobalCardinalityConstraint,
    domains: dict[Term, set[Term]],
) -> bool:
    scoped = {
        variable: domains[variable]
        for variable in constraint.variables
    }
    explicit = {
        value: (lower, upper)
        for value, lower, upper in constraint.bounds
    }
    if not _has_gcc_assignment(scoped, explicit):
        return False
    for variable in constraint.variables:
        supported = {
            value
            for value in domains[variable]
            if _has_gcc_assignment(
                scoped,
                explicit,
                forced=(variable, value),
            )
        }
        domains[variable].intersection_update(supported)
        if not domains[variable]:
            return False
    return True


def _revise_table(
    constraint: TableConstraint,
    domains: dict[Term, set[Term]],
) -> bool:
    active = tuple(
        row
        for row in constraint.allowed
        if all(
            value in domains[variable]
            for variable, value in zip(
                constraint.variables,
                row,
                strict=True,
            )
        )
    )
    if not active:
        return False
    for position, variable in enumerate(constraint.variables):
        domains[variable].intersection_update(
            row[position] for row in active
        )
        if not domains[variable]:
            return False
    return True


def _has_gcc_assignment(
    domains: Mapping[Term, set[Term]],
    explicit_bounds: Mapping[Term, tuple[int, int]],
    *,
    forced: tuple[Term, Term] | None = None,
) -> bool:
    restricted = {
        variable: set(values) for variable, values in domains.items()
    }
    if forced is not None:
        variable, value = forced
        if value not in restricted[variable]:
            return False
        restricted[variable] = {value}
    if any(not values for values in restricted.values()):
        return False

    all_values = {
        value for values in restricted.values() for value in values
    } | explicit_bounds.keys()
    size = len(restricted)
    bounds = {
        value: explicit_bounds.get(value, (0, size))
        for value in all_values
    }
    if sum(lower for lower, _ in bounds.values()) > size:
        return False
    if sum(upper for _, upper in bounds.values()) < size:
        return False

    source = ("gcc-source",)
    sink = ("gcc-sink",)
    edges: list[tuple[object, object, int, int]] = []
    for variable, values in restricted.items():
        variable_node = ("variable", variable)
        edges.append((source, variable_node, 1, 1))
        edges.extend(
            (variable_node, ("value", value), 0, 1)
            for value in values
        )
    edges.extend(
        (
            ("value", value),
            sink,
            lower,
            min(upper, size),
        )
        for value, (lower, upper) in bounds.items()
    )
    edges.append((sink, source, 0, size))
    return _has_feasible_circulation(edges)


@dataclass(slots=True)
class _FlowEdge:
    target: int
    reverse: int
    capacity: int


def _has_feasible_circulation(
    edges: list[tuple[object, object, int, int]],
) -> bool:
    nodes = {
        node
        for source, target, _, _ in edges
        for node in (source, target)
    }
    super_source = ("super-source",)
    super_sink = ("super-sink",)
    nodes.update((super_source, super_sink))
    indices = {
        node: index
        for index, node in enumerate(sorted(nodes, key=repr))
    }
    graph: list[list[_FlowEdge]] = [[] for _ in indices]
    demands = {node: 0 for node in nodes}

    def add_edge(source: object, target: object, capacity: int) -> None:
        source_index = indices[source]
        target_index = indices[target]
        forward = _FlowEdge(target_index, len(graph[target_index]), capacity)
        backward = _FlowEdge(source_index, len(graph[source_index]), 0)
        graph[source_index].append(forward)
        graph[target_index].append(backward)

    for source, target, lower, upper in edges:
        if upper < lower:
            return False
        add_edge(source, target, upper - lower)
        demands[source] -= lower
        demands[target] += lower

    required = 0
    for node, demand in demands.items():
        if node in {super_source, super_sink}:
            continue
        if demand > 0:
            add_edge(super_source, node, demand)
            required += demand
        elif demand < 0:
            add_edge(node, super_sink, -demand)
    return (
        _maximum_flow(
            graph,
            indices[super_source],
            indices[super_sink],
        )
        == required
    )


def _maximum_flow(
    graph: list[list[_FlowEdge]],
    source: int,
    sink: int,
) -> int:
    total = 0
    while True:
        levels = [-1] * len(graph)
        levels[source] = 0
        pending = deque((source,))
        while pending:
            node = pending.popleft()
            for edge in graph[node]:
                if edge.capacity > 0 and levels[edge.target] < 0:
                    levels[edge.target] = levels[node] + 1
                    pending.append(edge.target)
        if levels[sink] < 0:
            return total
        positions = [0] * len(graph)

        def send(
            node: int,
            available: int,
            *,
            phase_levels: list[int] = levels,
            phase_positions: list[int] = positions,
        ) -> int:
            if node == sink:
                return available
            while phase_positions[node] < len(graph[node]):
                edge = graph[node][phase_positions[node]]
                if (
                    edge.capacity > 0
                    and phase_levels[edge.target] == phase_levels[node] + 1
                ):
                    sent = send(edge.target, min(available, edge.capacity))
                    if sent:
                        edge.capacity -= sent
                        graph[edge.target][edge.reverse].capacity += sent
                        return sent
                phase_positions[node] += 1
            return 0

        while (sent := send(source, 1 << 60)) > 0:
            total += sent
