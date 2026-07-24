"""Premise types evaluated by rule instantiation strategies."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .facts import Fact
from .matching import PatternMatcher
from .substitutions import Substitution, TermBindings
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
        return matcher.match_ground_pair(
            self.entity,
            fact.entity,
            self.status,
            fact.status,
            substitution,
        )


class ComparisonOperator(StrEnum):
    EQ = "=="
    NE = "!="
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="
    DIVISIBLE = "DIVISIBLE_BY"


@dataclass(frozen=True, slots=True)
class ComparisonPremise:
    """A comparison evaluated after applying the current substitution."""

    left: Term
    operator: ComparisonOperator
    right: Term

    def evaluate(self, substitution: TermBindings) -> bool:
        left = substitution.apply(self.left)
        right = substitution.apply(self.right)
        if not is_ground(left) or not is_ground(right):
            return False
        if self.operator is ComparisonOperator.EQ:
            return left == right
        if self.operator is ComparisonOperator.NE:
            return left != right
        if self.operator is ComparisonOperator.DIVISIBLE:
            dividend = _integer_value(left)
            divisor = _integer_value(right)
            if divisor == 0:
                raise ValueError("DIVISIBLE divisor cannot be zero")
            return dividend % divisor == 0
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


@dataclass(frozen=True, slots=True)
class CountPremise:
    """Compare the number of local satisfying substitutions to an integer."""

    premises: tuple[Premise, ...]
    operator: ComparisonOperator
    expected: int

    def __post_init__(self) -> None:
        premises = tuple(self.premises)
        if not premises:
            raise ValueError("COUNT requires at least one premise")
        if self.expected < 0:
            raise ValueError("COUNT expected value must be non-negative")
        object.__setattr__(self, "premises", premises)

    def accepts(self, count: int) -> bool:
        if self.operator is ComparisonOperator.EQ:
            return count == self.expected
        if self.operator is ComparisonOperator.NE:
            return count != self.expected
        if self.operator is ComparisonOperator.LT:
            return count < self.expected
        if self.operator is ComparisonOperator.LE:
            return count <= self.expected
        if self.operator is ComparisonOperator.GT:
            return count > self.expected
        if self.operator is ComparisonOperator.GE:
            return count >= self.expected
        raise ValueError(f"unsupported comparison operator: {self.operator}")


@dataclass(frozen=True, slots=True)
class UniquePremise:
    """Succeed when a local conjunction has exactly one solution."""

    premises: tuple[Premise, ...]

    def __post_init__(self) -> None:
        premises = tuple(self.premises)
        if not premises:
            raise ValueError("UNIQUE requires at least one premise")
        object.__setattr__(self, "premises", premises)


@dataclass(frozen=True, slots=True)
class CollectPremise:
    """Bind a finite set to the projection of a correlated local query."""

    target: Variable
    projection: Term
    premises: tuple[Premise, ...]

    def __post_init__(self) -> None:
        premises = tuple(self.premises)
        if not premises:
            raise ValueError("COLLECT requires at least one premise")
        object.__setattr__(self, "premises", premises)


type Premise = (
    FactPremise
    | ComparisonPremise
    | ExistsPremise
    | NotExistsPremise
    | CountPremise
    | UniquePremise
    | CollectPremise
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
        if isinstance(premise, CollectPremise):
            if premise.target in bound:
                raise ValueError(
                    f"COLLECT target ${premise.target.name} is already bound"
                )
            nested_bound = validate_premise_bindings(
                premise.premises,
                frozenset(bound),
                require_bound_comparisons=True,
            )
            required = variables_in(premise.projection)
            missing = required - nested_bound
            if missing:
                names = ", ".join(
                    f"${variable.name}"
                    for variable in sorted(missing, key=lambda item: item.name)
                )
                raise ValueError(
                    f"COLLECT projection uses unbound variables: {names}"
                )
            local_to_existential.update(nested_bound - bound)
            bound.add(premise.target)
            local_to_existential.discard(premise.target)
            continue
        if isinstance(
            premise,
            (
                ExistsPremise,
                NotExistsPremise,
                CountPremise,
                UniquePremise,
            ),
        ):
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


def count(
    expected: int,
    *premises: Premise,
    operator: ComparisonOperator = ComparisonOperator.EQ,
) -> CountPremise:
    """Construct a correlated cardinality premise."""

    return CountPremise(tuple(premises), operator, expected)


def unique(*premises: Premise) -> UniquePremise:
    """Construct a correlated exact-one premise."""

    return UniquePremise(tuple(premises))


def collect(
    target: Variable,
    projection: Term,
    *premises: Premise,
) -> CollectPremise:
    """Construct a correlated finite-set collection premise."""

    return CollectPremise(target, projection, tuple(premises))


def divisible(left: Term, right: Term) -> ComparisonPremise:
    """Construct an integer divisibility premise."""

    return ComparisonPremise(left, ComparisonOperator.DIVISIBLE, right)


def _ordered_value(term: Term) -> int | float:
    if isinstance(term, Number):
        return term.value
    raise TypeError("ordered comparisons currently require Number operands")


def _integer_value(term: Term) -> int:
    if isinstance(term, Number) and isinstance(term.value, int):
        return term.value
    raise TypeError("DIVISIBLE currently requires integer Number operands")
