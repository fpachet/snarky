"""Explicitly registered, side-effect-free computed predicates."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field

from .substitutions import Substitution, TermBindings
from .terms import Term, Variable, is_ground

type PredicateFunction = Callable[[tuple[Term, ...]], Term | bool]


@dataclass(frozen=True, slots=True, eq=False)
class ComputedPredicate:
    """A named trusted function exposed to rules without using ``eval``."""

    name: str
    function: PredicateFunction = field(repr=False)

    def __post_init__(self) -> None:
        if not self.name or not self.name.replace("_", "").isalnum():
            raise ValueError("computed predicate name must be an identifier")

    def evaluate(self, arguments: tuple[Term, ...]) -> Term | bool:
        return self.function(arguments)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, ComputedPredicate)
            and self.name == other.name
            and self.function is other.function
        )

    def __hash__(self) -> int:
        return hash((self.name, id(self.function)))


class PredicateRegistry:
    """An explicit allow-list of computed predicates."""

    def __init__(self, predicates: Iterable[ComputedPredicate] = ()) -> None:
        self._predicates: dict[str, ComputedPredicate] = {}
        for predicate in predicates:
            self.register(predicate)

    def register(self, predicate: ComputedPredicate) -> None:
        if predicate.name in self._predicates:
            raise ValueError(f"duplicate computed predicate {predicate.name!r}")
        self._predicates[predicate.name] = predicate

    def resolve(self, name: str) -> ComputedPredicate:
        try:
            return self._predicates[name]
        except KeyError as error:
            raise KeyError(f"unregistered computed predicate {name!r}") from error

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(self._predicates)


@dataclass(frozen=True, slots=True)
class ComputedPremise:
    """Evaluate a registered pure function as a guard or value binding."""

    predicate: ComputedPredicate
    arguments: tuple[Term, ...]
    target: Variable | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "arguments", tuple(self.arguments))

    def apply(self, substitution: Substitution) -> Substitution | None:
        accepted, result = self.resolve(substitution)
        if not accepted:
            return None
        if self.target is None:
            return substitution
        assert result is not None
        try:
            return substitution.bind(self.target, result)
        except ValueError:
            return None

    def resolve(
        self,
        bindings: TermBindings,
    ) -> tuple[bool, Term | None]:
        """Evaluate against either an immutable substitution or join frame."""

        arguments = tuple(
            bindings.apply(argument) for argument in self.arguments
        )
        if not all(is_ground(argument) for argument in arguments):
            return False, None
        result = self.predicate.evaluate(arguments)
        if self.target is None:
            if not isinstance(result, bool):
                raise TypeError(
                    f"guard predicate {self.predicate.name!r} must return bool"
                )
            return result, None
        if isinstance(result, bool) or not is_ground(result):
            raise TypeError(
                f"value predicate {self.predicate.name!r} must return "
                "a ground Term"
            )
        return True, result


def computed(
    predicate: ComputedPredicate,
    *arguments: Term,
    target: Variable | None = None,
) -> ComputedPremise:
    """Build a safe computed guard or value-binding premise."""

    return ComputedPremise(predicate, tuple(arguments), target)
