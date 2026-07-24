"""Compiled premise plans for allocation-light indexed matching."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from typing import Protocol

from ..premises import (
    CollectPremise,
    ComparisonPremise,
    CountPremise,
    ExistsPremise,
    FactPremise,
    NotExistsPremise,
    Premise,
    UniquePremise,
)
from ..rules import Rule
from ..substitutions import BindingFrame, TermBindings
from ..terms import Term, Triple, Variable, is_ground, variables_in


class PatternNode(Protocol):
    def match(self, candidate: Term, frame: BindingFrame) -> bool: ...


@dataclass(frozen=True, slots=True)
class ConstantNode:
    value: Term

    def match(self, candidate: Term, frame: BindingFrame) -> bool:
        del frame
        return self.value == candidate


@dataclass(frozen=True, slots=True)
class VariableNode:
    variable: Variable

    def match(self, candidate: Term, frame: BindingFrame) -> bool:
        return frame.bind_ground(self.variable, candidate)


@dataclass(frozen=True, slots=True)
class TripleNode:
    subject: PatternNode
    relation: PatternNode
    object: PatternNode

    def match(self, candidate: Term, frame: BindingFrame) -> bool:
        return (
            isinstance(candidate, Triple)
            and self.subject.match(candidate.subject, frame)
            and self.relation.match(candidate.relation, frame)
            and self.object.match(candidate.object, frame)
        )


class ValueResolver(Protocol):
    def resolve(self, bindings: TermBindings) -> Term | None: ...


@dataclass(frozen=True, slots=True)
class ConstantResolver:
    value: Term

    def resolve(self, bindings: TermBindings) -> Term:
        del bindings
        return self.value


@dataclass(frozen=True, slots=True)
class VariableResolver:
    variable: Variable

    def resolve(self, bindings: TermBindings) -> Term | None:
        if self.variable not in bindings:
            return None
        return bindings.apply(self.variable)


@dataclass(frozen=True, slots=True)
class StructuredResolver:
    term: Triple

    def resolve(self, bindings: TermBindings) -> Term | None:
        resolved = bindings.apply(self.term)
        return resolved if is_ground(resolved) else None


@dataclass(frozen=True, slots=True)
class CompiledFactPremise:
    source: FactPremise
    entity_pattern: PatternNode
    status_pattern: PatternNode
    entity: ValueResolver
    status: ValueResolver
    triple_parts: (
        tuple[ValueResolver, ValueResolver, ValueResolver] | None
    )

    def match(
        self,
        entity: Term,
        status: Term,
        frame: BindingFrame,
    ) -> bool:
        return self.entity_pattern.match(
            entity,
            frame,
        ) and self.status_pattern.match(status, frame)


@dataclass(frozen=True, slots=True)
class CompiledComparisonPremise:
    source: ComparisonPremise


@dataclass(frozen=True, slots=True)
class CompiledExistentialPremise:
    source: ExistsPremise | NotExistsPremise
    block: CompiledBlock
    negated: bool


@dataclass(frozen=True, slots=True)
class CompiledAggregatePremise:
    source: CountPremise | UniquePremise
    block: CompiledBlock


@dataclass(frozen=True, slots=True)
class CompiledCollectPremise:
    source: CollectPremise
    block: CompiledBlock


type CompiledPremise = (
    CompiledFactPremise
    | CompiledComparisonPremise
    | CompiledExistentialPremise
    | CompiledAggregatePremise
    | CompiledCollectPremise
)


@dataclass(frozen=True, slots=True)
class CompiledBlock:
    source: tuple[Premise, ...]
    premises: tuple[CompiledPremise, ...]
    correlated_variables: tuple[Variable, ...]


@dataclass(frozen=True, slots=True)
class CompiledRule:
    source: Rule
    block: CompiledBlock


@cache
def compile_rule(rule: Rule) -> CompiledRule:
    return CompiledRule(rule, compile_block(rule.premises))


@cache
def compile_block(premises: tuple[Premise, ...]) -> CompiledBlock:
    variables: set[Variable] = set()
    compiled: list[CompiledPremise] = []
    for premise in premises:
        if isinstance(premise, FactPremise):
            variables.update(variables_in(premise.entity))
            variables.update(variables_in(premise.status))
            compiled.append(compile_fact_premise(premise))
        elif isinstance(premise, ComparisonPremise):
            variables.update(variables_in(premise.left))
            variables.update(variables_in(premise.right))
            compiled.append(CompiledComparisonPremise(premise))
        elif isinstance(premise, (ExistsPremise, NotExistsPremise)):
            nested = compile_block(premise.premises)
            variables.update(nested.correlated_variables)
            compiled.append(
                CompiledExistentialPremise(
                    premise,
                    nested,
                    isinstance(premise, NotExistsPremise),
                )
            )
        elif isinstance(premise, (CountPremise, UniquePremise)):
            nested = compile_block(premise.premises)
            variables.update(nested.correlated_variables)
            compiled.append(CompiledAggregatePremise(premise, nested))
        elif isinstance(premise, CollectPremise):
            nested = compile_block(premise.premises)
            variables.update(nested.correlated_variables)
            variables.update(variables_in(premise.projection))
            variables.add(premise.target)
            compiled.append(CompiledCollectPremise(premise, nested))
        else:
            raise TypeError(f"unsupported premise: {premise!r}")
    ordered = tuple(sorted(variables, key=lambda variable: variable.name))
    return CompiledBlock(premises, tuple(compiled), ordered)


@cache
def compile_fact_premise(premise: FactPremise) -> CompiledFactPremise:
    triple_parts: tuple[ValueResolver, ValueResolver, ValueResolver] | None
    if isinstance(premise.entity, Triple):
        triple_parts = (
            _compile_resolver(premise.entity.subject),
            _compile_resolver(premise.entity.relation),
            _compile_resolver(premise.entity.object),
        )
    else:
        triple_parts = None
    return CompiledFactPremise(
        source=premise,
        entity_pattern=_compile_pattern(premise.entity),
        status_pattern=_compile_pattern(premise.status),
        entity=_compile_resolver(premise.entity),
        status=_compile_resolver(premise.status),
        triple_parts=triple_parts,
    )


@cache
def negative_fact_plans(
    block: CompiledBlock,
    *,
    inside_negative: bool = False,
) -> tuple[CompiledFactPremise, ...]:
    dependencies: list[CompiledFactPremise] = []
    for premise in block.premises:
        if isinstance(premise, CompiledFactPremise):
            if inside_negative:
                dependencies.append(premise)
        elif isinstance(premise, CompiledExistentialPremise):
            dependencies.extend(
                negative_fact_plans(
                    premise.block,
                    inside_negative=inside_negative or premise.negated,
                )
            )
        elif isinstance(
            premise,
            (CompiledAggregatePremise, CompiledCollectPremise),
        ):
            dependencies.extend(
                negative_fact_plans(
                    premise.block,
                    inside_negative=True,
                )
            )
    return tuple(dependencies)


@cache
def all_fact_plans(
    block: CompiledBlock,
) -> tuple[CompiledFactPremise, ...]:
    dependencies: list[CompiledFactPremise] = []
    for premise in block.premises:
        if isinstance(premise, CompiledFactPremise):
            dependencies.append(premise)
        elif isinstance(
            premise,
            (
                CompiledExistentialPremise,
                CompiledAggregatePremise,
                CompiledCollectPremise,
            ),
        ):
            dependencies.extend(all_fact_plans(premise.block))
    return tuple(dependencies)


def simple_fact_plan(
    block: CompiledBlock,
) -> CompiledFactPremise | None:
    if (
        len(block.premises) == 1
        and isinstance(block.premises[0], CompiledFactPremise)
    ):
        return block.premises[0]
    return None


def _compile_pattern(term: Term) -> PatternNode:
    if isinstance(term, Variable):
        return VariableNode(term)
    if isinstance(term, Triple):
        return TripleNode(
            _compile_pattern(term.subject),
            _compile_pattern(term.relation),
            _compile_pattern(term.object),
        )
    return ConstantNode(term)


def _compile_resolver(term: Term) -> ValueResolver:
    if isinstance(term, Variable):
        return VariableResolver(term)
    if isinstance(term, Triple):
        return StructuredResolver(term)
    return ConstantResolver(term)
