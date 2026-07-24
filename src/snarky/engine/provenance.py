"""Derivation records and minimal proof-depth calculation."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from ..facts import Fact
from ..substitutions import Substitution


@dataclass(frozen=True, slots=True)
class Derivation:
    fact: Fact
    rule_name: str
    substitution: Substitution
    premises: tuple[Fact, ...]
    cycle: int
    proof_depth: int
    rule_group: str = "default"


@dataclass(frozen=True, slots=True)
class ProvenanceCheckpoint:
    """Opaque position in a reversible provenance mutation trail."""

    owner: int
    token: int
    trail_size: int


@dataclass(frozen=True, slots=True)
class _ProvenanceMutation:
    fact: Fact
    derivation: Derivation | None
    had_depth: bool
    previous_depth: int


class Provenance:
    """Store every distinct known derivation for each fact."""

    def __init__(self, initial_facts: tuple[Fact, ...] = ()) -> None:
        self._depths: dict[Fact, int] = {fact: 0 for fact in initial_facts}
        self._derivations: defaultdict[Fact, list[Derivation]] = defaultdict(list)
        self._trail: list[_ProvenanceMutation] = []
        self._checkpoints: list[int] = []
        self._next_checkpoint_token = 0

    def depth(self, fact: Fact) -> int:
        try:
            return self._depths[fact]
        except KeyError as error:
            raise KeyError(f"no proof depth is known for {fact!r}") from error

    def assume(self, fact: Fact) -> None:
        """Register an externally asserted fact as a depth-zero premise."""

        if fact in self._depths:
            return
        if self._checkpoints:
            self._trail.append(
                _ProvenanceMutation(fact, None, False, 0)
            )
        self._depths[fact] = 0

    def record(
        self,
        fact: Fact,
        rule_name: str,
        substitution: Substitution,
        premises: tuple[Fact, ...],
        cycle: int,
        rule_group: str = "default",
    ) -> Derivation:
        depth = 1 + max((self.depth(premise) for premise in premises), default=0)
        derivation = Derivation(
            fact,
            rule_name,
            substitution,
            premises,
            cycle,
            depth,
            rule_group,
        )
        previous = self._depths.get(fact)
        derivations = self._derivations[fact]
        added_derivation = derivation not in derivations
        depth_changed = previous is None or depth < previous
        if self._checkpoints and (added_derivation or depth_changed):
            self._trail.append(
                _ProvenanceMutation(
                    fact,
                    derivation if added_derivation else None,
                    previous is not None,
                    previous or 0,
                )
            )
        if added_derivation:
            derivations.append(derivation)
        if previous is None or depth < previous:
            self._depths[fact] = depth
        return derivation

    def checkpoint(self) -> ProvenanceCheckpoint:
        """Start a nested reversible provenance scope."""

        self._next_checkpoint_token += 1
        token = self._next_checkpoint_token
        self._checkpoints.append(token)
        return ProvenanceCheckpoint(id(self), token, len(self._trail))

    def rollback(self, checkpoint: ProvenanceCheckpoint) -> None:
        """Undo provenance recorded since *checkpoint*."""

        self._validate_checkpoint(checkpoint)
        while len(self._trail) > checkpoint.trail_size:
            mutation = self._trail.pop()
            if mutation.derivation is not None:
                derivations = self._derivations[mutation.fact]
                derivations.remove(mutation.derivation)
                if not derivations:
                    self._derivations.pop(mutation.fact, None)
            if mutation.had_depth:
                self._depths[mutation.fact] = mutation.previous_depth
            else:
                self._depths.pop(mutation.fact, None)

    def release(self, checkpoint: ProvenanceCheckpoint) -> None:
        """Close *checkpoint* after its state is no longer needed."""

        self._validate_checkpoint(checkpoint)
        self._checkpoints.pop()
        if not self._checkpoints:
            self._trail.clear()

    def _validate_checkpoint(
        self,
        checkpoint: ProvenanceCheckpoint,
    ) -> None:
        if (
            checkpoint.owner != id(self)
            or not self._checkpoints
            or self._checkpoints[-1] != checkpoint.token
            or checkpoint.trail_size > len(self._trail)
        ):
            raise ValueError(
                "checkpoint is not the active provenance checkpoint"
            )

    def derivations(self, fact: Fact) -> tuple[Derivation, ...]:
        return tuple(self._derivations.get(fact, ()))

    def minimal_derivation(self, fact: Fact) -> Derivation | None:
        derivations = self._derivations.get(fact)
        if not derivations:
            return None
        return min(derivations, key=lambda derivation: derivation.proof_depth)

    def clone(self) -> Provenance:
        """Return an isolated copy without active rollback scopes."""

        clone = Provenance()
        clone._depths = self._depths.copy()
        clone._derivations = defaultdict(
            list,
            {
                fact: derivations.copy()
                for fact, derivations in self._derivations.items()
            },
        )
        return clone
