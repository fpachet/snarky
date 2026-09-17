"""Declared probability measure, separate from integer optimization and CHOICE."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType

from ..factors import FactorModel
from ..terms import Term, is_ground
from .factors import FactorObjective, TableFactor


@dataclass(frozen=True, slots=True)
class WeightTable:
    """A nonnegative base-measure factor, with exact rational entries.

    Pass Fraction for rational values. Float inputs are interpreted as their
    exact binary rational value. Missing rows receive the declared default.
    """

    name: str
    variables: tuple[Term, ...]
    values: Mapping[tuple[Term, ...], Fraction | int | float]
    default: Fraction | int | float = 0

    def __post_init__(self) -> None:
        variables = tuple(self.variables)
        if not self.name or len(set(variables)) != len(variables):
            raise ValueError("weight tables need a name and distinct variables")
        entries = {tuple(row): Fraction(value) for row, value in self.values.items()}
        default = Fraction(self.default)
        if default < 0 or any(value < 0 for value in entries.values()):
            raise ValueError("base measure weights cannot be negative")
        if any(
            len(row) != len(variables) or not all(is_ground(v) for v in row)
            for row in entries
        ):
            raise ValueError("weight table rows need ground values and full arity")
        object.__setattr__(self, "variables", variables)
        object.__setattr__(self, "values", MappingProxyType(entries))
        object.__setattr__(self, "default", default)

    def weight(self, assignment: Mapping[Term, Term]) -> Fraction:
        row = tuple(assignment[var] for var in self.variables)
        return Fraction(self.values.get(row, self.default))


@dataclass(frozen=True, slots=True)
class Measure:
    """Product of base tables times exp(sum of declared log-score factors).

    No measure declaration means uniform weights on hard-feasible assignments.
    Integer optimization objectives are not implicitly probability factors.
    General pure FactorModel premises observe the complete deterministic closure.
    """

    base: tuple[WeightTable, ...] = ()
    log_tables: tuple[TableFactor, ...] = ()
    factors: FactorModel | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "base", tuple(self.base))
        object.__setattr__(self, "log_tables", tuple(self.log_tables))
        names = [table.name for table in self.base]
        names += [table.name for table in self.log_tables]
        if self.factors is not None:
            names += [f.name for group in self.factors.groups for f in group.factors]
        if len(set(names)) != len(names):
            raise ValueError("duplicate measure component names")

    @property
    def variables(self) -> tuple[Term, ...]:
        variables = [v for table in self.base for v in table.variables]
        variables += [v for table in self.log_tables for v in table.variables]
        return tuple(dict.fromkeys(variables))

    @property
    def rational(self) -> bool:
        return not self.log_tables and self.factors is None


def negative_log2_measure(objective: FactorObjective) -> Measure:
    """Explicitly interpret integer table costs as -log2 unnormalized mass.

    This is exact for dyadic source probabilities. It is not a conversion from
    arbitrary rounded costs back to their original real-valued probabilities.
    """
    base = [WeightTable("cost/offset", (), {(): Fraction(2) ** -objective.offset})]
    for factor in objective.factors:
        if not isinstance(factor, TableFactor):
            raise ValueError("negative_log2_measure requires table costs")
        base.append(
            WeightTable(
                f"cost/{factor.name}",
                factor.variables,
                {row: Fraction(2) ** -value for row, value in factor.values.items()},
                default=Fraction(2) ** -factor.default,
            )
        )
    return Measure(tuple(base))
