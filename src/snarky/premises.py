"""Premise types evaluated by rule instantiation strategies."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .facts import Fact
from .matching import PatternMatcher
from .substitutions import Substitution
from .terms import Number, Status, Term, Variable, is_ground, variables_in


@dataclass(frozen=True, slots=True)
class FactPremise:
    """A pattern over both the entity and status of a fact."""

    entity: Term
    status: Term = Status.VRAI

    def match(
        self,
        fact: Fact,
        substitution: Substitution,
        matcher: PatternMatcher,
    ) -> Substitution | None:
        matched_entity = matcher.match(self.entity, fact.entity, substitution)
        if matched_entity is None:
            return None
        return matcher.match(self.status, fact.status, matched_entity)


class ComparisonOperator(StrEnum):
    EQ = "=="
    NE = "!="
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="


@dataclass(frozen=True, slots=True)
class ComparisonPremise:
    """A comparison evaluated after applying the current substitution."""

    left: Term
    operator: ComparisonOperator
    right: Term

    def evaluate(self, substitution: Substitution) -> bool:
        left = substitution.apply(self.left)
        right = substitution.apply(self.right)
        if not is_ground(left) or not is_ground(right):
            return False
        if self.operator is ComparisonOperator.EQ:
            return left == right
        if self.operator is ComparisonOperator.NE:
            return left != right
        left_value = _ordered_value(left)
        right_value = _ordered_value(right)
        if self.operator is ComparisonOperator.LT:
            return left_value < right_value
        if self.operator is ComparisonOperator.LE:
            return left_value <= right_value
        if self.operator is ComparisonOperator.GT:
            return left_value > right_value
        if self.operator is ComparisonOperator.GE:
            return left_value >= right_value
        raise ValueError(f"unsupported comparison operator: {self.operator}")


@dataclass(frozen=True, slots=True)
class ExistsPremise:
    """Succeed when a correlated local premise conjunction has a witness."""

    premises: tuple[Premise, ...]

    def __post_init__(self) -> None:
        premises = tuple(self.premises)
        if not premises:
            raise ValueError("EXISTS requires at least one premise")
        object.__setattr__(self, "premises", premises)


@dataclass(frozen=True, slots=True)
class NotExistsPremise:
    """Succeed when a correlated local premise conjunction has no witness."""

    premises: tuple[Premise, ...]

    def __post_init__(self) -> None:
        premises = tuple(self.premises)
        if not premises:
            raise ValueError("NOT EXISTS requires at least one premise")
        object.__setattr__(self, "premises", premises)


type Premise = (
    FactPremise | ComparisonPremise | ExistsPremise | NotExistsPremise
)


def validate_premise_bindings(
    premises: tuple[Premise, ...],
    initially_bound: frozenset[Variable] = frozenset(),
    *,
    require_bound_comparisons: bool = False,
) -> frozenset[Variable]:
    """Validate sequential variable scope and return outer bound variables."""

    bound = set(initially_bound)
    local_to_existential: set[Variable] = set()
    for premise in premises:
        if isinstance(premise, FactPremise):
            introduced = variables_in(premise.entity) | variables_in(premise.status)
            bound.update(introduced)
            local_to_existential.difference_update(introduced)
            continue
        if isinstance(premise, ComparisonPremise):
            required = variables_in(premise.left) | variables_in(premise.right)
            missing = required - bound
            if missing and (
                require_bound_comparisons
                or not missing.isdisjoint(local_to_existential)
            ):
                names = ", ".join(
                    f"${variable.name}"
                    for variable in sorted(missing, key=lambda item: item.name)
                )
                raise ValueError(f"comparison uses unbound variables: {names}")
            continue
        if isinstance(premise, (ExistsPremise, NotExistsPremise)):
            nested_bound = validate_premise_bindings(
                premise.premises,
                frozenset(bound),
                require_bound_comparisons=True,
            )
            local_to_existential.update(nested_bound - bound)
            continue
        raise TypeError(f"unsupported premise: {premise!r}")
    return frozenset(bound)


def exists(*premises: Premise) -> ExistsPremise:
    """Construct a correlated existential premise."""

    return ExistsPremise(tuple(premises))


def not_exists(*premises: Premise) -> NotExistsPremise:
    """Construct a correlated negative existential premise."""

    return NotExistsPremise(tuple(premises))


def _ordered_value(term: Term) -> int | float:
    if isinstance(term, Number):
        return term.value
    raise TypeError("ordered comparisons currently require Number operands")
