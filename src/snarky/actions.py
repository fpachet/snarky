"""Monotone rule actions supported by the reference engine."""

from __future__ import annotations

from dataclasses import dataclass

from .facts import Fact
from .substitutions import Substitution
from .terms import Status, Term


@dataclass(frozen=True, slots=True)
class AddFact:
    """Instantiate and add a fact to the store."""

    entity: Term
    status: Term = Status.VRAI

    def instantiate(self, substitution: Substitution) -> Fact:
        return Fact(
            entity=substitution.apply(self.entity),
            status=substitution.apply(self.status),
        )


Action = AddFact


def add(entity: Term, status: Term = Status.VRAI) -> AddFact:
    """Public convenience constructor mirroring the documented API."""

    return AddFact(entity, status)
