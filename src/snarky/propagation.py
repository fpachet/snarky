"""Observable and reversible finite-domain propagation state."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, MutableMapping
from dataclasses import dataclass
from types import MappingProxyType

from .terms import Term, Variable


@dataclass(frozen=True, slots=True)
class PropagationReason:
    """Machine-readable origin of one reduction or contradiction."""

    kind: str
    source: str = ""


@dataclass(frozen=True, slots=True)
class DomainReduction:
    """Values removed from one variable domain for one reason."""

    variable: Variable
    removed: frozenset[Term]
    reason: PropagationReason


@dataclass(frozen=True, slots=True)
class PropagationContradiction:
    """An explicit reason why the current propagation state is impossible."""

    message: str
    reason: PropagationReason
    variable: Variable | None = None


@dataclass(frozen=True, slots=True)
class PropagationResult:
    """Immutable result and explanation of one propagation run."""

    domains: Mapping[Variable, frozenset[Term]]
    reductions: tuple[DomainReduction, ...]
    contradiction: PropagationContradiction | None = None

    @property
    def consistent(self) -> bool:
        return self.contradiction is None

    @property
    def changed_variables(self) -> frozenset[Variable]:
        return frozenset(reduction.variable for reduction in self.reductions)


@dataclass(frozen=True, slots=True)
class DomainCheckpoint:
    """Opaque rollback position in a :class:`DomainStore`."""

    trail_size: int
    reduction_size: int
    contradiction: PropagationContradiction | None


class DomainStore(MutableMapping[Variable, set[Term]]):
    """Mutable domains whose reductions are explained and reversible."""

    __slots__ = (
        "_contradiction",
        "_default_reason",
        "_domains",
        "_record_trail",
        "_reductions",
        "_trail",
    )

    def __init__(
        self,
        domains: Mapping[Variable, set[Term] | frozenset[Term]],
        *,
        record_trail: bool = True,
    ) -> None:
        self._domains = {
            variable: set(values) for variable, values in domains.items()
        }
        self._trail: list[tuple[Variable, frozenset[Term]]] = []
        self._record_trail = record_trail
        self._reductions: list[DomainReduction] = []
        self._contradiction: PropagationContradiction | None = None
        self._default_reason = PropagationReason("propagator")
        for variable, values in self._domains.items():
            if not values:
                self.fail(
                    PropagationReason("initial-domain"),
                    f"domain ${variable.name} is empty",
                    variable,
                )
                break

    def __getitem__(self, variable: Variable) -> set[Term]:
        return self._domains[variable]

    def __setitem__(self, variable: Variable, values: set[Term]) -> None:
        self.retain(variable, values, self._default_reason)

    def __delitem__(self, variable: Variable) -> None:
        raise TypeError("domains cannot be deleted from a DomainStore")

    def __iter__(self) -> Iterator[Variable]:
        return iter(self._domains)

    def __len__(self) -> int:
        return len(self._domains)

    @property
    def contradiction(self) -> PropagationContradiction | None:
        return self._contradiction

    @property
    def default_reason(self) -> PropagationReason:
        return self._default_reason

    @default_reason.setter
    def default_reason(self, reason: PropagationReason) -> None:
        self._default_reason = reason

    def checkpoint(self) -> DomainCheckpoint:
        if not self._record_trail:
            raise RuntimeError("trail recording is disabled")
        return DomainCheckpoint(
            len(self._trail),
            len(self._reductions),
            self._contradiction,
        )

    def rollback(self, checkpoint: DomainCheckpoint) -> None:
        if not self._record_trail:
            raise RuntimeError("trail recording is disabled")
        if (
            checkpoint.trail_size > len(self._trail)
            or checkpoint.reduction_size > len(self._reductions)
        ):
            raise ValueError("checkpoint belongs to a future domain state")
        while len(self._trail) > checkpoint.trail_size:
            variable, previous = self._trail.pop()
            self._domains[variable] = set(previous)
        del self._reductions[checkpoint.reduction_size :]
        self._contradiction = checkpoint.contradiction

    def retain(
        self,
        variable: Variable,
        supported: set[Term] | frozenset[Term],
        reason: PropagationReason,
    ) -> frozenset[Term]:
        current = self._domains[variable]
        reduced = current & supported
        if reduced == current:
            return frozenset()
        previous = frozenset(current)
        removed = previous - reduced
        if self._record_trail:
            self._trail.append((variable, previous))
        self._domains[variable] = reduced
        self._reductions.append(
            DomainReduction(variable, removed, reason)
        )
        if not reduced:
            self.fail(
                reason,
                f"domain ${variable.name} became empty",
                variable,
            )
        return removed

    def remove(
        self,
        variable: Variable,
        value: Term,
        reason: PropagationReason,
    ) -> bool:
        if value not in self._domains[variable]:
            return False
        self.retain(
            variable,
            self._domains[variable] - {value},
            reason,
        )
        return True

    def restrict(
        self,
        variable: Variable,
        value: Term,
        reason: PropagationReason,
    ) -> bool:
        before = self._domains[variable]
        self.retain(variable, {value}, reason)
        return self._domains[variable] != before

    def fail(
        self,
        reason: PropagationReason,
        message: str,
        variable: Variable | None = None,
    ) -> None:
        if self._contradiction is None:
            self._contradiction = PropagationContradiction(
                message,
                reason,
                variable,
            )

    def result(self) -> PropagationResult:
        return PropagationResult(
            MappingProxyType(
                {
                    variable: frozenset(values)
                    for variable, values in self._domains.items()
                }
            ),
            tuple(self._reductions),
            self._contradiction,
        )


@dataclass(frozen=True, slots=True)
class PropagationCheckpoint:
    """Rollback position covering domains and active table masks."""

    domains: DomainCheckpoint
    mask_trail_size: int


class PropagationState:
    """Branch-local domains and active masks over shared table definitions."""

    __slots__ = ("_active_masks", "_mask_trail", "domains")

    def __init__(
        self,
        domains: DomainStore,
        active_masks: Mapping[int, int] | None = None,
    ) -> None:
        self.domains = domains
        self._active_masks = (
            {} if active_masks is None else dict(active_masks)
        )
        self._mask_trail: list[tuple[int, int | None]] = []

    @property
    def active_masks(self) -> Mapping[int, int]:
        return MappingProxyType(self._active_masks)

    def checkpoint(self) -> PropagationCheckpoint:
        return PropagationCheckpoint(
            self.domains.checkpoint(),
            len(self._mask_trail),
        )

    def set_active_mask(self, table: int, mask: int) -> None:
        previous = self._active_masks.get(table)
        if previous == mask:
            return
        self._mask_trail.append((table, previous))
        self._active_masks[table] = mask

    def rollback(self, checkpoint: PropagationCheckpoint) -> None:
        if checkpoint.mask_trail_size > len(self._mask_trail):
            raise ValueError("checkpoint belongs to a future mask state")
        while len(self._mask_trail) > checkpoint.mask_trail_size:
            table, previous = self._mask_trail.pop()
            if previous is None:
                self._active_masks.pop(table, None)
            else:
                self._active_masks[table] = previous
        self.domains.rollback(checkpoint.domains)
