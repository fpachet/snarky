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


class Provenance:
    """Store every distinct known derivation for each fact."""

    def __init__(self, initial_facts: tuple[Fact, ...] = ()) -> None:
        self._depths: dict[Fact, int] = {fact: 0 for fact in initial_facts}
        self._derivations: defaultdict[Fact, list[Derivation]] = defaultdict(list)

    def depth(self, fact: Fact) -> int:
        try:
            return self._depths[fact]
        except KeyError as error:
            raise KeyError(f"no proof depth is known for {fact!r}") from error

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
        if derivation not in self._derivations[fact]:
            self._derivations[fact].append(derivation)
        previous = self._depths.get(fact)
        if previous is None or depth < previous:
            self._depths[fact] = depth
        return derivation

    def derivations(self, fact: Fact) -> tuple[Derivation, ...]:
        return tuple(self._derivations.get(fact, ()))

    def minimal_derivation(self, fact: Fact) -> Derivation | None:
        derivations = self._derivations.get(fact)
        if not derivations:
            return None
        return min(derivations, key=lambda derivation: derivation.proof_depth)
