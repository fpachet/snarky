"""Pure exact-integer scores, with explicit table and Boolean-scope semantics."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from ..actions import AddFact
from ..factors import FactorDefinition
from ..facts import Fact
from ..instantiation import NaiveInstantiationStrategy, SemiNaiveInstantiationStrategy
from ..rules import Rule
from ..terms import Atom, Term, is_ground


@dataclass(frozen=True, slots=True)
class ScoreContribution:
    factor_name: str
    scope: tuple[Term, ...]
    value: int
    support_facts: tuple[Fact, ...] = ()
    witness_count: int = 1


@dataclass(frozen=True, slots=True)
class IntegerFactor:
    """One integer contribution per distinct ground scope, irrespective of witnesses.

    Uses the existing pure FactorDefinition grammar. Evaluation observes the
    complete closed snapshot; no partial bound is claimed for general premises.
    """

    definition: FactorDefinition
    weight: int

    def __post_init__(self) -> None:
        if type(self.weight) is not int:
            raise TypeError("integer factor weights must be integers")

    @property
    def name(self) -> str:
        return self.definition.name

    @property
    def variables(self) -> tuple[Term, ...]:
        # Decision values are observed as facts, through declared premises.
        return ()

    def contributions(
        self, facts: frozenset[Fact], *, reference: bool = False
    ) -> tuple[ScoreContribution, ...]:
        query = Rule(
            f"__finite_factor__{self.name}",
            self.definition.premises,
            (AddFact(Atom("__finite_factor_result__")),),
        )
        strategy = (
            NaiveInstantiationStrategy()
            if reference
            else SemiNaiveInstantiationStrategy()
        )
        matches = strategy.instantiate(query, tuple(sorted(facts, key=repr)))
        grounded: dict[Term, tuple[set[Fact], int]] = {}
        for match in matches:
            scope = match.substitution.apply(self.definition.scope)
            if not is_ground(scope):
                raise ValueError("factor scope must be ground after matching")
            support, count = grounded.setdefault(scope, (set(), 0))
            support.update(match.premise_facts)
            grounded[scope] = support, count + 1
        return tuple(
            ScoreContribution(
                self.name,
                (scope,),
                self.weight,
                tuple(sorted(support, key=repr)),
                count,
            )
            for scope, (support, count) in sorted(
                grounded.items(), key=lambda item: repr(item[0])
            )
        )


@dataclass(frozen=True, slots=True)
class TableFactor:
    """A total integer-valued function; missing tuples receive ``default``.

    Missing tuples do not forbid assignments. Declare a TableConstraint for hard
    support. One table factor contributes once, including at singleton domains.
    """

    name: str
    variables: tuple[Term, ...]
    values: Mapping[tuple[Term, ...], int]
    default: int = 0

    def __post_init__(self) -> None:
        variables = tuple(self.variables)
        if not self.name:
            raise ValueError("a table factor needs a name")
        if len(set(variables)) != len(variables):
            raise ValueError("table factor variables must be distinct")
        entries = {tuple(key): value for key, value in self.values.items()}
        if type(self.default) is not int or any(
            type(value) is not int for value in entries.values()
        ):
            raise TypeError("table factor scores must be integers")
        if any(
            len(key) != len(variables) or not all(is_ground(v) for v in key)
            for key in entries
        ):
            raise ValueError("table factor rows require ground values and full arity")
        object.__setattr__(self, "variables", variables)
        object.__setattr__(self, "values", MappingProxyType(entries))

    def contribution(self, assignment: Mapping[Term, Term]) -> ScoreContribution:
        values = tuple(assignment[var] for var in self.variables)
        return ScoreContribution(
            self.name, values, self.values.get(values, self.default)
        )

    def bounds(self, domains: Mapping[Term, frozenset[Term]]) -> tuple[int, int]:
        possible = [
            score
            for row, score in self.values.items()
            if all(
                value in domains[var]
                for var, value in zip(self.variables, row, strict=True)
            )
        ]
        combinations = 1
        for var in self.variables:
            combinations *= len(domains[var])
        if not combinations:
            raise ValueError("objective bounds require nonempty domains")
        if len(possible) < combinations:
            possible.append(self.default)
        return min(possible), max(possible)


@dataclass(frozen=True, slots=True)
class FactorObjective:
    """Sum of declared integer factors; never search-decision weights."""

    factors: tuple[IntegerFactor | TableFactor, ...] = ()
    offset: int = 0

    def __post_init__(self) -> None:
        factors = tuple(self.factors)
        if type(self.offset) is not int:
            raise TypeError("factor objective offset must be an integer")
        if len({f.name for f in factors}) != len(factors):
            raise ValueError("duplicate objective factor names")
        object.__setattr__(self, "factors", factors)

    @property
    def variables(self) -> tuple[Term, ...]:
        return tuple(dict.fromkeys(v for f in self.factors for v in f.variables))

    def contributions(
        self,
        assignment: Mapping[Term, Term],
        facts: frozenset[Fact],
        *,
        reference: bool = False,
    ) -> tuple[ScoreContribution, ...]:
        result = [ScoreContribution("__offset__", (), self.offset)]
        for factor in self.factors:
            if isinstance(factor, TableFactor):
                result.append(factor.contribution(assignment))
            else:
                result.extend(factor.contributions(facts, reference=reference))
        return tuple(result)

    def evaluate(
        self, assignment: Mapping[Term, Term], facts: frozenset[Fact] = frozenset()
    ) -> int:
        return sum(c.value for c in self.contributions(assignment, facts))

    def bounds(self, domains: Mapping[Term, frozenset[Term]]) -> tuple[int, int] | None:
        if any(isinstance(f, IntegerFactor) for f in self.factors):
            return None
        bounds = [f.bounds(domains) for f in self.factors if isinstance(f, TableFactor)]
        return (
            self.offset + sum(lower for lower, _ in bounds),
            self.offset + sum(upper for _, upper in bounds),
        )
