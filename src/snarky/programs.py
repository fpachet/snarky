"""Inspectable orchestration manifests for modular rule bases."""

from __future__ import annotations

from dataclasses import dataclass

from .rules import RuleGroup


@dataclass(frozen=True, slots=True)
class RuleProgram:
    """Declare the groups participating in preparation and choice search.

    The program does not impose CSP semantics.  In particular,
    ``choice_groups`` may contain any rule using Snarky's general ``CHOICE``
    action.  Search repeatedly saturates choice, propagation and
    interpretation groups in the declared order.
    """

    name: str
    preparation_groups: tuple[RuleGroup, ...] = ()
    choice_groups: tuple[RuleGroup, ...] = ()
    propagation_groups: tuple[RuleGroup, ...] = ()
    interpretation_groups: tuple[RuleGroup, ...] = ()

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a rule program needs a name")
        for field_name in (
            "preparation_groups",
            "choice_groups",
            "propagation_groups",
            "interpretation_groups",
        ):
            object.__setattr__(self, field_name, tuple(getattr(self, field_name)))
        names = tuple(group.name for group in self.all_groups)
        if len(names) != len(set(names)):
            raise ValueError("a rule program cannot contain duplicate group names")

    @property
    def search_groups(self) -> tuple[RuleGroup, ...]:
        """Groups repeatedly saturated while exploring choices."""

        return (
            *self.choice_groups,
            *self.propagation_groups,
            *self.interpretation_groups,
        )

    @property
    def all_groups(self) -> tuple[RuleGroup, ...]:
        """Every group in its visible execution order."""

        return (*self.preparation_groups, *self.search_groups)

    def manifest(self) -> tuple[tuple[str, tuple[str, ...]], ...]:
        """Return a stable, serializable description for docs and diagnostics."""

        return (
            (
                "preparation",
                tuple(group.name for group in self.preparation_groups),
            ),
            ("choice", tuple(group.name for group in self.choice_groups)),
            (
                "propagation",
                tuple(group.name for group in self.propagation_groups),
            ),
            (
                "interpretation",
                tuple(group.name for group in self.interpretation_groups),
            ),
        )
