"""Bound positive rule factors through a bounded, grounded Horn relaxation.

The ordinary engine still computes scores and explanations. This compiler only
builds must/may bounds: singleton assignment facts under-approximate any completion,
while all remaining candidate facts over-approximate it. Positive closure and
positive factor queries preserve inclusion, including recursive/alternative proofs.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from time import perf_counter

from ..actions import AddFact
from ..facts import Fact
from ..matching import PatternMatcher
from ..premises import ComparisonPremise, FactPremise, Premise
from ..substitutions import Substitution
from ..terms import Term, Triple, is_ground
from .factors import FactorObjective, IntegerFactor, TableFactor
from .model import VALUE, FiniteModel


class _BudgetExceeded(Exception):
    pass


class PositiveFactorBound:
    """Immutable ground clauses, with a bounded cache of branch-independent closures."""

    def __init__(self, model: FiniteModel, *, budget: int, deadline: float | None):
        assert isinstance(model.objective, FactorObjective)
        self.objective = model.objective
        self.deadline = deadline
        self._remaining = budget
        self._ids: dict[Fact, int] = {}
        self._matcher = PatternMatcher()
        self._clauses: set[tuple[int, int]] = set()
        self._cache: dict[int, int] = {}
        self._context = 0
        for fact in model.context:
            self._context |= self._bit(fact)
        self._values: dict[Term, dict[Term, int]] = {
            v.name: {x: self._bit(Fact(Triple(v.name, VALUE, x))) for x in v.domain}
            for v in model.variables
        }
        # Include all candidate values at once. This is a relaxation, never a
        # claim that two different assignments to a variable are jointly feasible.
        while True:
            before = len(self._ids)
            for group in model.rules:
                for rule in group.rules:
                    for substitution, support in self._matches(rule.premises):
                        for action in rule.actions:
                            assert isinstance(action, AddFact)
                            self._clauses.add(
                                (support, self._bit(action.instantiate(substitution)))
                            )
            if len(self._ids) == before:
                break
        self._queries: list[tuple[int, tuple[tuple[int, ...], ...]]] = []
        for factor in self.objective.factors:
            if not isinstance(factor, IntegerFactor):
                continue
            scopes: dict[Term, set[int]] = {}
            for substitution, support in self._matches(factor.definition.premises):
                scope = substitution.apply(factor.definition.scope)
                scopes.setdefault(scope, set()).add(support)
            self._queries.append(
                (factor.weight, tuple(tuple(sorted(s)) for s in scopes.values()))
            )
        self._ordered_clauses = tuple(sorted(self._clauses))

    def _check(self) -> None:
        if self.deadline is not None and perf_counter() >= self.deadline:
            raise TimeoutError("rule factor bound time limit")

    def _tick(self) -> None:
        self._check()
        self._remaining -= 1
        if self._remaining < 0:
            raise _BudgetExceeded

    def _bit(self, fact: Fact) -> int:
        if fact not in self._ids:
            self._tick()
            if len(self._ids) >= 4096:
                raise _BudgetExceeded
            self._ids[fact] = 1 << len(self._ids)
        return self._ids[fact]

    def _matches(
        self, premises: tuple[Premise, ...]
    ) -> Iterator[tuple[Substitution, int]]:
        # Stream joins with an operation limit rather than materializing a large
        # Cartesian join. Match/evaluation semantics are the existing premise API.
        facts = tuple(self._ids.items())
        relations: dict[Term, list[tuple[Fact, int]]] = {}
        subjects: dict[tuple[Term, Term], list[tuple[Fact, int]]] = {}
        for fact, bit in facts:
            if isinstance(fact.entity, Triple):
                fact_entity = fact.entity
                relations.setdefault(fact_entity.relation, []).append((fact, bit))
                subjects.setdefault(
                    (fact_entity.subject, fact_entity.relation), []
                ).append((fact, bit))
        stack = [(0, Substitution(), 0)]
        while stack:
            self._tick()
            index, substitution, support = stack.pop()
            if index == len(premises):
                yield substitution, support
                continue
            premise = premises[index]
            if isinstance(premise, FactPremise):
                entity = substitution.apply(premise.entity)
                candidates = facts
                if isinstance(entity, Triple) and is_ground(entity.relation):
                    candidates = (
                        tuple(subjects.get((entity.subject, entity.relation), ()))
                        if is_ground(entity.subject)
                        else tuple(relations.get(entity.relation, ()))
                    )
                for fact, bit in candidates:
                    self._tick()
                    match = premise.match(fact, substitution, self._matcher)
                    if match is not None:
                        stack.append((index + 1, match, support | bit))
            else:
                assert isinstance(premise, ComparisonPremise)
                if premise.evaluate(substitution):
                    stack.append((index + 1, substitution, support))

    def _close(self, initial: int) -> int:
        if initial in self._cache:
            return self._cache[initial]
        known = initial
        while True:
            previous = known
            for body, head in self._ordered_clauses:
                self._check()
                if body & known == body:
                    known |= head
            if known == previous:
                break
        if len(self._cache) < 256:
            self._cache[initial] = known
        return known

    def __call__(self, domains: Mapping[Term, frozenset[Term]]) -> tuple[int, int]:
        self._check()
        must = may = self._context
        for var, values in domains.items():
            if not values:
                raise ValueError("objective bounds require nonempty domains")
            bits = 0
            for value in values:
                bits |= self._values[var][value]
            may |= bits
            if len(values) == 1:
                must |= bits
        must, may = self._close(must), self._close(may)
        lower = upper = self.objective.offset
        for factor in self.objective.factors:
            if isinstance(factor, TableFactor):
                lo, hi = factor.bounds(domains)
                lower += lo
                upper += hi
        for weight, scopes in self._queries:
            lo = sum(
                any(body & must == body for body in alternatives)
                for alternatives in scopes
            )
            hi = sum(
                any(body & may == body for body in alternatives)
                for alternatives in scopes
            )
            lower += weight * (lo if weight >= 0 else hi)
            upper += weight * (hi if weight >= 0 else lo)
        return lower, upper


def compile_positive_factor_bound(
    model: FiniteModel, *, budget: int = 100_000, deadline: float | None = None
) -> PositiveFactorBound | None:
    """Unsupported queries or excessive grounding retain the existing fallback."""
    if not isinstance(model.objective, FactorObjective):
        return None
    integers = tuple(f for f in model.objective.factors if isinstance(f, IntegerFactor))
    if not integers or any(
        not isinstance(p, (FactPremise, ComparisonPremise))
        or isinstance(p, FactPremise)
        and p.focused
        for factor in integers
        for p in factor.definition.premises
    ):
        return None
    try:
        return PositiveFactorBound(model, budget=budget, deadline=deadline)
    except (_BudgetExceeded, ValueError, TypeError, ArithmeticError):
        return None
