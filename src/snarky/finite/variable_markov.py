"""Exact variable-order Markov objectives and sparse suffix-state compilation.

Training boundaries never create transitions. The first generated symbol has
unit weight by default (a conditioned start); marginal starts are explicit.
A forbidden order k rejects observed words of length k+1. Integer algebraic
scores and rational probability products are never rounded to log costs.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import Literal

from ..terms import Atom, Number, Term, is_ground
from .constraints import TableConstraint
from .factors import FactorObjective, TableFactor
from .measure import WeightTable
from .model import Constraint, FiniteModel, FiniteVariable
from .product_objective import RationalProductObjective

type MarkovMode = Literal["fixed", "smoothing", "max_order", "algebraic"]
type Score = int | Fraction
type State = tuple[Term, ...]


@dataclass(frozen=True, slots=True)
class NGramModel:
    """Immutable empirical conditional probabilities, indexed by Markov order."""

    probabilities: tuple[Mapping[State, Fraction], ...]

    def __post_init__(self) -> None:
        tables = tuple(dict(table) for table in self.probabilities)
        if not tables or not tables[0]:
            raise ValueError("training requires at least one symbol")
        alphabet = {word[0] for word in tables[0] if len(word) == 1}
        for order, table in enumerate(tables):
            if any(
                len(word) != order + 1
                or any(not is_ground(v) or v not in alphabet for v in word)
                or not isinstance(p, Fraction)
                or not 0 < p <= 1
                for word, p in table.items()
            ):
                raise ValueError(
                    "ngram tables require ground symbols and positive Fractions"
                )
            totals: dict[State, Fraction] = {}
            for word, probability in table.items():
                if order and (
                    word[:-1] not in tables[order - 1]
                    or word[1:] not in tables[order - 1]
                ):
                    raise ValueError("ngram support must contain every subword")
                totals[word[:-1]] = totals.get(word[:-1], Fraction(0)) + probability
            if any(total != 1 for total in totals.values()):
                raise ValueError("conditional probabilities must sum to one")
        object.__setattr__(
            self, "probabilities", tuple(MappingProxyType(t) for t in tables)
        )

    @classmethod
    def train(cls, sequences: Sequence[Sequence[Term]], max_order: int) -> NGramModel:
        if type(max_order) is not int or max_order < 1:
            raise ValueError("max_order must be a positive integer")
        corpus = tuple(tuple(s) for s in sequences)
        tables: list[Mapping[State, Fraction]] = []
        for order in range(max_order + 1):
            counts = Counter(
                seq[i : i + order + 1]
                for seq in corpus
                for i in range(len(seq) - order)
            )
            totals: Counter[State] = Counter()
            for word, count in counts.items():
                totals[word[:-1]] += count
            tables.append(
                {word: Fraction(n, totals[word[:-1]]) for word, n in counts.items()}
            )
        return cls(tuple(tables))

    @property
    def alphabet(self) -> tuple[Term, ...]:
        return tuple(word[0] for word in self.probabilities[0])


@dataclass(frozen=True, slots=True)
class MarkovGeneration:
    """Finite generation request; extra CSP constraints belong on compile().

    Startup uses only available history. Smoothing averages orders 1..d,
    including zero terms, where d is the currently eligible order. Max-order
    selects the highest supported continuation. Algebraic adds its order squared.
    All modes require first-order support once a preceding symbol exists.

    A rational contour tradeoff alpha=a/b maximizes P**a * 2**(-(b-a)*D),
    equivalent to alpha*log2(P)-(1-alpha)*D. Algebraic mode instead maximizes
    a*S-(b-a)*D. D is squared integer pitch distance. Prefix notes provide
    context, but are neither rescored nor checked for earlier forbidden words.
    """

    source: NGramModel
    domains: tuple[tuple[Term, ...], ...]
    mode: MarkovMode = "max_order"
    order: int = 4
    forbidden_order: int | None = None
    prefix: State = ()
    initial: Literal["unit", "marginal"] = "unit"
    contour: tuple[int, ...] | None = None
    alpha: Fraction = Fraction(1)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "domains", tuple(tuple(dict.fromkeys(d)) for d in self.domains)
        )
        object.__setattr__(self, "prefix", tuple(self.prefix))
        if self.contour is not None:
            object.__setattr__(self, "contour", tuple(self.contour))
        if self.mode not in ("fixed", "smoothing", "max_order", "algebraic"):
            raise ValueError("unknown Markov scoring mode")
        if type(self.order) is not int or self.order < 1:
            raise ValueError("order must be a positive integer")
        if self.forbidden_order is not None and (
            type(self.forbidden_order) is not int or self.forbidden_order < 1
        ):
            raise ValueError("forbidden_order must be a positive integer")
        if self.memory >= len(self.source.probabilities):
            raise ValueError("training does not cover the requested orders")
        if not self.domains:
            raise ValueError("generation requires at least one position")
        if any(
            v not in self.source.alphabet
            for d in (*self.domains, self.prefix)
            for v in d
        ):
            raise ValueError("generation symbols must belong to the training alphabet")
        if self.initial not in ("unit", "marginal"):
            raise ValueError("initial must be unit or marginal")
        if not isinstance(self.alpha, Fraction) or not 0 <= self.alpha <= 1:
            raise ValueError("alpha must be a Fraction between zero and one")
        if self.contour is not None:
            if len(self.contour) != len(self.domains) or any(
                type(v) is not int for v in self.contour
            ):
                raise ValueError("contour requires one integer target per position")
            if any(
                not isinstance(v, Number) or type(v.value) is not int
                for d in self.domains
                for v in d
            ):
                raise ValueError("contour requires integer Number domains")
        elif self.alpha != 1:
            raise ValueError("alpha requires a contour")

    @property
    def memory(self) -> int:
        return max(self.order, self.forbidden_order or 0)

    def _step(self, history: State, symbol: Term, position: int) -> Score | None:
        tables = self.source.probabilities
        f = self.forbidden_order
        if f is not None and len(history) >= f and (*history[-f:], symbol) in tables[f]:
            return None
        eligible = min(self.order, len(self.prefix) + position)
        probabilities = [tables[0].get((symbol,), Fraction(0))]
        for k in range(1, eligible + 1):
            probabilities.append(
                tables[k].get((*history[-k:], symbol), Fraction(0))
                if len(history) >= k
                else Fraction(0)
            )
        if not probabilities[0] or (eligible and not probabilities[1]):
            return None
        supported = max(k for k, p in enumerate(probabilities) if p)
        value: Score
        if self.mode == "algebraic":
            value = supported**2
        elif not eligible:
            value = probabilities[0] if self.initial == "marginal" else Fraction(1)
        elif self.mode == "fixed":
            value = probabilities[eligible]
            if not value:
                return None
        elif self.mode == "smoothing":
            value = sum(probabilities[1:], Fraction(0)) / eligible
        else:
            value = probabilities[supported]
        if self.contour is not None:
            assert isinstance(symbol, Number) and isinstance(symbol.value, int)
            distance = (symbol.value - self.contour[position]) ** 2
            a, b = self.alpha.numerator, self.alpha.denominator
            value = (
                a * value - (b - a) * distance
                if self.mode == "algebraic"
                else Fraction(value) ** a * Fraction(2) ** (-(b - a) * distance)
            )
        return value

    def score(self, sequence: Sequence[Term]) -> Score | None:
        """Score every generated position exactly once, independently of search."""
        if len(sequence) != len(self.domains):
            raise ValueError("sequence length must match generation domains")
        total: Score = 0 if self.mode == "algebraic" else Fraction(1)
        history = self.prefix
        for i, symbol in enumerate(sequence):
            if symbol not in self.domains[i]:
                return None
            value = self._step(history, symbol, i)
            if value is None:
                return None
            total = total + value if self.mode == "algebraic" else total * value
            history = (*history, symbol)[-self.memory :]
        return total

    def graph(self) -> MarkovGraph:
        """Compile reachable longest-observed-suffix states, then prune dead ends."""
        contexts: set[State] = {()}
        for table in self.source.probabilities[: self.memory]:
            contexts.update(table)

        def suffix(word: State) -> State:
            for k in range(min(len(word), self.memory), 0, -1):
                if word[-k:] in contexts:
                    return word[-k:]
            return ()

        start = suffix(self.prefix)
        states = {start}
        layers: list[tuple[MarkovEdge, ...]] = []
        # Scores depend on position only during startup or for contour targets.
        cache: dict[tuple[State, Term, int], tuple[State, Score] | None] = {}
        for i, domain in enumerate(self.domains):
            edges = []
            for state in sorted(states, key=repr):
                for symbol in domain:
                    phase = (
                        i
                        if self.contour is not None and self.alpha != 1
                        else min(i, self.order)
                    )
                    key = state, symbol, phase
                    if key not in cache:
                        value = self._step(state, symbol, i)
                        cache[key] = (
                            None if value is None else (suffix((*state, symbol)), value)
                        )
                    result = cache[key]
                    if result is not None:
                        target, value = result
                        edges.append(MarkovEdge(state, target, symbol, value))
            layers.append(tuple(edges))
            states = {edge.target for edge in edges}
        for i in range(len(layers) - 1, -1, -1):
            layers[i] = tuple(edge for edge in layers[i] if edge.target in states)
            states = {edge.source for edge in layers[i]}
        return MarkovGraph(self, start, tuple(layers))


@dataclass(frozen=True, slots=True)
class MarkovEdge:
    source: State
    target: State
    symbol: Term
    score: Score


@dataclass(frozen=True, slots=True)
class MarkovOptimum:
    score: Score
    sequence: State


@dataclass(frozen=True, slots=True)
class MarkovGraph:
    """A layered automaton. DP handles these controls; compile adds arbitrary CSP."""

    request: MarkovGeneration
    start: State
    layers: tuple[tuple[MarkovEdge, ...], ...]

    def optimum(self) -> MarkovOptimum | None:
        """Exact DP for this request only; does not accept extra CSP constraints."""
        algebraic = self.request.mode == "algebraic"
        identity: Score = 0 if algebraic else Fraction(1)
        current = {self.start: MarkovOptimum(identity, ())}
        for layer in self.layers:
            following: dict[State, MarkovOptimum] = {}
            for edge in layer:
                partial = current.get(edge.source)
                if partial is None:
                    continue
                score = (
                    partial.score + edge.score
                    if algebraic
                    else partial.score * edge.score
                )
                if edge.target not in following or score > following[edge.target].score:
                    following[edge.target] = MarkovOptimum(
                        score, (*partial.sequence, edge.symbol)
                    )
            current = following
        return max(current.values(), key=lambda v: v.score) if current else None

    def compile(
        self, *, name: str = "variable_markov", constraints: tuple[Constraint, ...] = ()
    ) -> FiniteModel:
        """Ordinary CSP: x0..xN notes, state0..stateN deterministic auxiliaries.

        Add constraints on the x variables, or replace the resulting model to
        attach rules/context. Maximization must be requested explicitly.
        """
        state_ids: dict[State, Term] = {}
        for layer in self.layers:
            for edge in layer:
                if edge.target not in state_ids:
                    state_ids[edge.target] = Number(len(state_ids))
        variables = []
        hard: list[Constraint] = list(constraints)
        integers: list[TableFactor] = []
        weights: list[WeightTable] = []
        for i, layer in enumerate(self.layers):
            state_name = Atom(f"state{i}")
            scope: tuple[Term, ...] = (
                (state_name,) if i == 0 else (Atom(f"state{i - 1}"), state_name)
            )
            values: dict[tuple[Term, ...], Score] = {}
            projections = set()
            for edge in layer:
                row = (
                    (state_ids[edge.target],)
                    if i == 0
                    else (state_ids[edge.source], state_ids[edge.target])
                )
                values[row] = edge.score
                projections.add((state_ids[edge.target], edge.symbol))
            variables.append(
                FiniteVariable(
                    state_name, tuple(dict.fromkeys(state_ids[e.target] for e in layer))
                )
            )
            identifier = f"ngram/{i}"
            if values:
                hard.append(TableConstraint(Atom(identifier), scope, tuple(values)))
                hard.append(
                    TableConstraint(
                        Atom(f"ngram/project/{i}"),
                        (state_name, Atom(f"x{i}")),
                        tuple(sorted(projections, key=repr)),
                    )
                )
            if self.request.mode == "algebraic":
                integers.append(
                    TableFactor(
                        identifier, scope, {row: int(v) for row, v in values.items()}
                    )
                )
            else:
                weights.append(WeightTable(identifier, scope, values))
        variables.extend(
            FiniteVariable(Atom(f"x{i}"), domain)
            for i, domain in enumerate(self.request.domains)
        )
        objective = (
            FactorObjective(tuple(integers))
            if self.request.mode == "algebraic"
            else RationalProductObjective(tuple(weights))
        )
        return FiniteModel(name, tuple(variables), tuple(hard), objective=objective)

    def assignment(self, sequence: Sequence[Term]) -> dict[Term, Term]:
        """Complete auxiliary assignment for a feasible sequence (e.g. warm start)."""
        if self.request.score(sequence) is None:
            raise ValueError("sequence is not feasible for this request")
        state_ids = dict.fromkeys(
            edge.target for layer in self.layers for edge in layer
        )
        ids = {state: Number(i) for i, state in enumerate(state_ids)}
        current = self.start
        assignment: dict[Term, Term] = {}
        for i, (symbol, layer) in enumerate(zip(sequence, self.layers, strict=True)):
            edge = next(e for e in layer if e.source == current and e.symbol == symbol)
            current = edge.target
            assignment[Atom(f"x{i}")] = symbol
            assignment[Atom(f"state{i}")] = ids[current]
        return assignment
