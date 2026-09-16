"""Persistent narrowing-only constraints over Snarky candidate facts.

Root ``candidate`` facts define finite domains. Persistent constraints remove
unsupported candidates, forward rules observe the filtered facts, and explicit
``CHOICE`` decisions trigger another propagation closure. Session rollback
restores the visible domains; the propagator detects that widening and safely
rebuilds its branch-local cache.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from weakref import WeakKeyDictionary

from snarky import (
    Atom,
    Fact,
    InferenceSession,
    Term,
    Triple,
)
from snarky.finite.constraints import (
    AllDifferentConstraint as AllDifferentConstraint,
)
from snarky.finite.constraints import (
    BinaryComparisonConstraint as BinaryComparisonConstraint,
)
from snarky.finite.constraints import (
    BinaryComparisonOperator as BinaryComparisonOperator,
)
from snarky.finite.constraints import (
    ConstraintOperator as ConstraintOperator,
)
from snarky.finite.constraints import (
    CountConstraint as CountConstraint,
)
from snarky.finite.constraints import (
    ElementConstraint as ElementConstraint,
)
from snarky.finite.constraints import (
    GlobalCardinalityConstraint as GlobalCardinalityConstraint,
)
from snarky.finite.constraints import (
    LexLessEqualConstraint as LexLessEqualConstraint,
)
from snarky.finite.constraints import (
    LinearSumConstraint as LinearSumConstraint,
)
from snarky.finite.constraints import (
    PersistentConstraint as PersistentConstraint,
)
from snarky.finite.constraints import (
    SumConstraint as SumConstraint,
)
from snarky.finite.constraints import (
    TableConstraint as TableConstraint,
)
from snarky.finite.kernels import (
    _aggregate_accepts as _aggregate_accepts,
)
from snarky.finite.kernels import (
    _bitset_sumset as _bitset_sumset,
)
from snarky.finite.kernels import (
    _FlowEdge as _FlowEdge,
)
from snarky.finite.kernels import (
    _has_feasible_circulation as _has_feasible_circulation,
)
from snarky.finite.kernels import (
    _has_gcc_assignment as _has_gcc_assignment,
)
from snarky.finite.kernels import (
    _integer_candidate as _integer_candidate,
)
from snarky.finite.kernels import (
    _interval_can_satisfy as _interval_can_satisfy,
)
from snarky.finite.kernels import (
    _lex_numeric_value as _lex_numeric_value,
)
from snarky.finite.kernels import (
    _maximum_flow as _maximum_flow,
)
from snarky.finite.kernels import (
    _maximum_matching as _maximum_matching,
)
from snarky.finite.kernels import (
    _nodes_reaching as _nodes_reaching,
)
from snarky.finite.kernels import (
    _numeric_candidate as _numeric_candidate,
)
from snarky.finite.kernels import (
    _revise_aliased_lex_less_equal_bounds as _revise_aliased_lex_less_equal_bounds,
)
from snarky.finite.kernels import (
    _revise_all_different as _revise_all_different,
)
from snarky.finite.kernels import (
    _revise_all_different_with_matching as _revise_all_different_with_matching,
)
from snarky.finite.kernels import (
    _revise_binary_comparison as _revise_binary_comparison,
)
from snarky.finite.kernels import (
    _revise_count as _revise_count,
)
from snarky.finite.kernels import (
    _revise_disjoint_lex_less_equal as _revise_disjoint_lex_less_equal,
)
from snarky.finite.kernels import (
    _revise_element as _revise_element,
)
from snarky.finite.kernels import (
    _revise_gcc as _revise_gcc,
)
from snarky.finite.kernels import (
    _revise_lex_less_equal as _revise_lex_less_equal,
)
from snarky.finite.kernels import (
    _revise_linear_sum as _revise_linear_sum,
)
from snarky.finite.kernels import (
    _revise_nonnegative_sum_bitsets as _revise_nonnegative_sum_bitsets,
)
from snarky.finite.kernels import (
    _revise_sum as _revise_sum,
)
from snarky.finite.kernels import (
    _revise_table as _revise_table,
)
from snarky.finite.kernels import (
    _strongly_connected_components as _strongly_connected_components,
)

from .finite_domain_projection import FiniteDomainProjection

CANDIDATE = Atom("candidate")
STATE = Atom("state")
CONTRADICTION = Atom("contradiction")
VIOLATED_CONSTRAINT = Atom("violated_constraint")
EMPTY_DOMAIN = Atom("empty_domain")


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
    removal_causes: dict[tuple[Term, Term], Atom] = field(default_factory=dict)
    generation: int = 0
    all_different_matchings: dict[int, dict[Term, Term]] = field(default_factory=dict)


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
        adjacency: dict[Term, list[int]] = {variable: [] for variable in scoped}
        for index, constraint in enumerate(self.constraints):
            for variable in constraint.variables:
                adjacency[variable].append(index)
        self._adjacency = {
            variable: tuple(indices) for variable, indices in adjacency.items()
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
            variable: set(visible.get(variable, ())) for variable in self._variables
        }
        state = self._states.get(session)
        if state is not None and state.generation != snapshot.cursor.generation:
            # A rollback starts another journal generation. Causes from the
            # abandoned branch must never be attributed to its sibling.
            state.removal_causes.clear()
            state.generation = snapshot.cursor.generation
        widened = state is None or any(
            current[variable] - state.domains[variable] for variable in self._variables
        )
        queued: set[int]

        if widened:
            reusable_matchings = {} if state is None else state.all_different_matchings
            state = _CachedPropagationState(
                {variable: set(values) for variable, values in current.items()},
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
        variable: frozenset(domains[variable]) for variable in constraint.variables
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
    elif isinstance(constraint, LinearSumConstraint):
        consistent = _revise_linear_sum(constraint, domains)
    elif isinstance(constraint, BinaryComparisonConstraint):
        consistent = _revise_binary_comparison(constraint, domains)
    elif isinstance(constraint, ElementConstraint):
        consistent = _revise_element(constraint, domains)
    elif isinstance(constraint, CountConstraint):
        consistent = _revise_count(constraint, domains)
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
