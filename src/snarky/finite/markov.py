"""Fixed-order Markov cost models compiled to ordinary constraints and factors.

Costs are declared integers, not inferred probabilities. Missing rows have zero
support. No implicit smoothing, backoff, or variable-order activation is applied.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType

from ..facts import Fact
from ..rules import RuleGroup
from ..terms import Atom, Term, is_ground
from .constraints import TableConstraint
from .factors import FactorObjective, TableFactor
from .model import Constraint, FiniteModel, FiniteVariable


@dataclass(frozen=True, slots=True)
class MarkovCosts:
    """An initial order-k block, subsequent k+1 windows, and optional final block.

    Every initial, transition and terminal factor contributes exactly once at
    its declared position. An absent terminal table means no terminal condition
    or cost. Order zero has the unique empty initial block, normally of cost 0.
    For order k>0, shorter-than-k requests are rejected; marginalizing a source
    to shorter sequences is a separate, explicit operation.
    """

    alphabet: tuple[Term, ...]
    order: int
    initial: Mapping[tuple[Term, ...], int]
    transitions: Mapping[tuple[Term, ...], int]
    terminal: Mapping[tuple[Term, ...], int] | None = None

    def __post_init__(self) -> None:
        alphabet = tuple(dict.fromkeys(self.alphabet))
        if not alphabet or any(not is_ground(v) for v in alphabet):
            raise ValueError("Markov alphabet requires ground symbols")
        if type(self.order) is not int or self.order < 0:
            raise ValueError("Markov order must be a nonnegative integer")
        object.__setattr__(self, "alphabet", alphabet)
        for name, arity in (
            ("initial", self.order),
            ("transitions", self.order + 1),
            ("terminal", self.order),
        ):
            raw = getattr(self, name)
            if raw is None:
                if name == "terminal":
                    continue
                raise TypeError(f"{name} must be a table")
            entries = {tuple(row): cost for row, cost in raw.items()}
            if any(
                len(row) != arity or any(v not in alphabet for v in row)
                for row in entries
            ):
                raise ValueError(f"{name} rows must match order and alphabet")
            if any(type(cost) is not int for cost in entries.values()):
                raise TypeError("Markov costs must be exact integers")
            if arity == 0 and set(entries) != {()}:
                raise ValueError("order-zero boundary tables require the empty tuple")
            object.__setattr__(self, name, MappingProxyType(entries))

    def sequence_cost(self, sequence: Sequence[Term]) -> int | None:
        """Direct path scoring; None means zero support, not a large penalty."""
        symbols = tuple(sequence)
        if len(symbols) < self.order:
            raise ValueError("sequence shorter than the declared Markov order")
        if any(v not in self.alphabet for v in symbols):
            return None
        initial = self.initial.get(symbols[: self.order])
        if initial is None:
            return None
        total = initial
        for position in range(self.order, len(symbols)):
            cost = self.transitions.get(symbols[position - self.order : position + 1])
            if cost is None:
                return None
            total += cost
        if self.terminal is not None:
            context = symbols[-self.order :] if self.order else ()
            terminal = self.terminal.get(context)
            if terminal is None:
                return None
            total += terminal
        return total


def markov_model(
    source: MarkovCosts,
    length: int,
    *,
    name: str = "markov",
    names: tuple[Atom, ...] | None = None,
    constraints: tuple[Constraint, ...] = (),
    rules: tuple[RuleGroup, ...] = (),
    context: tuple[Fact, ...] = (),
) -> FiniteModel:
    """Compile an ordinary finite model with explicit integer cost minimization.

    The returned objective can be extended with additional declared factors.
    Generated identifiers start with ``markov/``; conflicting user identifiers
    are rejected by ordinary model validation.
    """
    if type(length) is not int or length < source.order:
        raise ValueError("length must be an integer at least the Markov order")
    names = (
        tuple(Atom(f"x{i}") for i in range(length)) if names is None else tuple(names)
    )
    if len(names) != length or len(set(names)) != length:
        raise ValueError("names must contain one distinct identifier per position")
    hard: list[Constraint] = list(constraints)
    factors: list[TableFactor] = []
    offset = 0
    impossible = False

    def add_table(
        label: str, scope: tuple[Term, ...], entries: Mapping[tuple[Term, ...], int]
    ) -> None:
        nonlocal offset, impossible
        if not scope:
            offset += entries[()]
            return
        if not entries:
            impossible = True
            return
        identifier = f"markov/{label}"
        hard.append(TableConstraint(Atom(identifier), scope, tuple(entries)))
        # Missing rows are already forbidden by the hard table. Choosing the
        # smallest allowed cost as their total-function extension avoids an
        # artificial zero lowering the independent factor bound.
        factors.append(
            TableFactor(identifier, scope, entries, default=min(entries.values()))
        )

    add_table("initial", names[: source.order], source.initial)
    for position in range(source.order, length):
        add_table(
            f"transition/{position}",
            names[position - source.order : position + 1],
            source.transitions,
        )
    if source.terminal is not None:
        add_table(
            "terminal", names[-source.order :] if source.order else (), source.terminal
        )
    variables = tuple(
        FiniteVariable(var, () if impossible and index == 0 else source.alphabet)
        for index, var in enumerate(names)
    )
    return FiniteModel(
        name,
        variables,
        tuple(hard),
        context,
        rules,
        FactorObjective(tuple(factors), offset),
    )
