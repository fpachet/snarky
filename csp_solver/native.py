"""Explicit adapter from legacy candidate facts to a native finite model."""

from __future__ import annotations

from snarky import Atom, Fact, Status, Triple
from snarky.finite import FiniteModel, FiniteVariable, LinearObjective

from .solver import (
    BINARY_CONSTRAINT,
    CANDIDATE,
    CHOICE_WEIGHT,
    CSP_PROBLEM,
    CSP_VARIABLE,
    DECISION,
    KIND,
    VALUE,
    VARIABLE,
    FiniteCSP,
)


def native_model(
    model: FiniteCSP,
    *,
    objective: LinearObjective | None = None,
) -> FiniteModel:
    """Compile persistent constraints; reject rules and implicit binary relations.

    Legacy weights are search priorities and are not copied into the objective.
    Domain and protocol facts are not materialized in the native domain store.
    """
    if model.groups:
        raise ValueError(
            "legacy rule groups require an explicit mixed-model translation"
        )
    if Fact(Triple(model.problem, KIND, CSP_PROBLEM)) not in model.facts:
        raise ValueError("legacy problem kind is missing")
    variables = tuple(
        dict.fromkeys(
            fact.entity.object
            for fact in model.facts
            if isinstance(fact.entity, Triple)
            and fact.status is Status.VRAI
            and fact.entity.subject == model.problem
            and fact.entity.relation == VARIABLE
        )
    )
    domains = {var: [] for var in variables}
    if any(
        Fact(Triple(var, KIND, CSP_VARIABLE)) not in model.facts for var in variables
    ):
        raise ValueError("legacy variable kind is missing")
    context = []
    for fact in model.facts:
        entity = fact.entity
        if isinstance(entity, Triple) and fact.status is Status.VRAI:
            if entity.relation == KIND and entity.object == BINARY_CONSTRAINT:
                raise ValueError(
                    "compile binary relation facts to table constraints first"
                )
            if entity.subject in domains:
                if entity.relation in (VALUE, DECISION):
                    raise ValueError(
                        "adapt initial domains, not an active legacy search state"
                    )
                if entity.relation == CANDIDATE:
                    domains[entity.subject].append(entity.object)
                    continue
                if entity.relation in (KIND, CHOICE_WEIGHT):
                    continue
            if entity.subject == model.problem and entity.relation in (KIND, VARIABLE):
                continue
        context.append(fact)
    if any(not isinstance(var, Atom) for var in variables):
        raise ValueError("native decision variable identifiers must be atoms")
    return FiniteModel(
        model.problem.name,
        tuple(FiniteVariable(var, tuple(values)) for var, values in domains.items()),
        constraints=model.constraints,
        context=tuple(context),
        objective=objective,
    )
