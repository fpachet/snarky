"""Premise types evaluated by rule instantiation strategies."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .facts import Fact
from .matching import PatternMatcher
from .substitutions import Substitution
from .terms import Number, Status, Term, is_ground


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


Premise = FactPremise | ComparisonPremise


def _ordered_value(term: Term) -> int | float:
    if isinstance(term, Number):
        return term.value
    raise TypeError("ordered comparisons currently require Number operands")
