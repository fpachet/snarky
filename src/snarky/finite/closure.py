"""Finite, function-free positive closure for declarative models.

This small evaluator is an independent semantic oracle, not the production
matcher. The operational rule engine retains its broader language unchanged.
"""

from __future__ import annotations

from collections.abc import Mapping
from time import perf_counter

from ..actions import AddFact
from ..facts import Fact
from ..matching import PatternMatcher
from ..premises import ComparisonPremise, FactPremise
from ..substitutions import Substitution
from ..terms import Atom, Number, Status, Term, Triple, Variable, variables_in
from .model import VALUE, FiniteModel


def _scalar(value: object) -> bool:
    return isinstance(value, (Atom, Number, Status))


def _flat(value: Term) -> bool:
    return isinstance(value, Triple) and all(
        _scalar(part) or isinstance(part, Variable)
        for part in (value.subject, value.relation, value.object)
    )


def validate_rules(model: FiniteModel) -> None:
    names = {var.name for var in model.variables}
    for fact in model.context:
        entity = fact.entity
        if (
            isinstance(entity, Triple)
            and entity.subject in names
            and entity.relation == VALUE
        ):
            raise ValueError("context cannot supply a decision variable's value facts")
    if not model.rules:
        return
    if any(
        not _flat(fact.entity) or not _scalar(fact.status) for fact in model.context
    ):
        raise ValueError("scoreable rules require flat context triples")
    if any(not _scalar(value) for var in model.variables for value in var.domain):
        raise ValueError("scoreable rules require scalar decision values")
    for group in model.rules:
        for rule in group.rules:
            bound: set[Variable] = set()
            for premise in rule.premises:
                if isinstance(premise, FactPremise):
                    if (
                        not _flat(premise.entity)
                        or not (
                            _scalar(premise.status)
                            or isinstance(premise.status, Variable)
                        )
                        or premise.focused
                    ):
                        raise ValueError(
                            "scoreable rules require unfocused flat premises"
                        )
                    bound.update(
                        variables_in(premise.entity) | variables_in(premise.status)
                    )
                elif isinstance(premise, ComparisonPremise):
                    if not all(
                        _scalar(v) or isinstance(v, Variable)
                        for v in (premise.left, premise.right)
                    ):
                        raise ValueError(
                            "scoreable comparisons require scalar operands"
                        )
                    assert isinstance(premise.left, (Atom, Number, Status, Variable))
                    assert isinstance(premise.right, (Atom, Number, Status, Variable))
                    needed = variables_in(premise.left) | variables_in(premise.right)
                    if not needed <= bound:
                        raise ValueError("scoreable comparisons must already be bound")
                else:
                    raise ValueError("unsupported premise in scoreable positive rules")
            for action in rule.actions:
                if not isinstance(action, AddFact):
                    raise ValueError("scoreable rules allow ADD only")
                if not _flat(action.entity) or not (
                    _scalar(action.status) or isinstance(action.status, Variable)
                ):
                    raise ValueError("scoreable rules cannot construct recursive terms")
                assert isinstance(action.entity, Triple)
                if (
                    not isinstance(action.entity.relation, Atom)
                    or action.entity.relation == VALUE
                ):
                    raise ValueError(
                        "rule heads need a fixed relation other than value"
                    )
                needed = variables_in(action.entity) | variables_in(action.status)
                if not needed <= bound:
                    raise ValueError("scoreable ADD variables must be range restricted")


def reference_closure(
    model: FiniteModel,
    assignment: Mapping[Term, Term],
    *,
    deadline: float | None = None,
) -> frozenset[Fact]:
    """Compute the least fixed point with direct joins and no inference session."""
    facts = list(
        dict.fromkeys(
            (
                *model.context,
                *(Fact(Triple(var, VALUE, value)) for var, value in assignment.items()),
            )
        )
    )
    known = set(facts)
    matcher = PatternMatcher()
    while True:
        before = len(facts)
        for group in model.rules:
            for rule in group.rules:
                substitutions = [Substitution()]
                for premise in rule.premises:
                    selected = []
                    for substitution in substitutions:
                        if deadline is not None and perf_counter() >= deadline:
                            raise TimeoutError("deterministic closure time limit")
                        if isinstance(premise, FactPremise):
                            for fact in facts:
                                match = premise.match(fact, substitution, matcher)
                                if match is not None:
                                    selected.append(match)
                        else:
                            assert isinstance(premise, ComparisonPremise)
                            if premise.evaluate(substitution):
                                selected.append(substitution)
                    substitutions = selected
                for substitution in substitutions:
                    for action in rule.actions:
                        assert isinstance(action, AddFact)
                        fact = action.instantiate(substitution)
                        if fact not in known:
                            known.add(fact)
                            facts.append(fact)
        if len(facts) == before:
            return frozenset(facts)
