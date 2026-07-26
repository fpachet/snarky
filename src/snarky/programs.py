"""Inspectable orchestration manifests for modular rule bases."""

from __future__ import annotations

from dataclasses import dataclass

from .choice_fixed_point import SessionPropagator
from .rules import RuleGroup


@dataclass(frozen=True, slots=True)
class RuleStep:
    """One reversible sequential step of a rule program.

    A step reaches a joint fixed point, exposes only the ``CHOICE`` actions
    declared by its groups, and advances when no such choice remains. Search
    frames created in an earlier step remain available for backtracking.
    """

    name: str
    groups: tuple[RuleGroup, ...]
    constraint_names: tuple[str, ...] = ()
    propagators: tuple[SessionPropagator, ...] = ()

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a rule step needs a name")
        object.__setattr__(self, "groups", tuple(self.groups))
        object.__setattr__(
            self,
            "constraint_names",
            tuple(self.constraint_names),
        )
        object.__setattr__(self, "propagators", tuple(self.propagators))
        names = tuple(group.name for group in self.groups)
        if len(names) != len(set(names)):
            raise ValueError(
                f"rule step {self.name!r} cannot contain duplicate group names"
            )


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
    steps: tuple[RuleStep, ...] = ()

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a rule program needs a name")
        for field_name in (
            "preparation_groups",
            "choice_groups",
            "propagation_groups",
            "interpretation_groups",
            "steps",
        ):
            object.__setattr__(self, field_name, tuple(getattr(self, field_name)))
        if self.steps and self.choice_groups:
            raise ValueError(
                "a staged rule program declares choices inside steps, "
                "not in choice_groups"
            )
        step_names = tuple(step.name for step in self.steps)
        if len(step_names) != len(set(step_names)):
            raise ValueError("a rule program cannot contain duplicate step names")
        names = tuple(group.name for group in self.all_groups)
        if len(names) != len(set(names)):
            raise ValueError("a rule program cannot contain duplicate group names")

    @property
    def search_groups(self) -> tuple[RuleGroup, ...]:
        """Groups repeatedly saturated while exploring choices."""

        return (
            *(
                group
                for step in self.steps
                for group in step.groups
            ),
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

        sections: list[tuple[str, tuple[str, ...]]] = [
            (
                "preparation",
                tuple(group.name for group in self.preparation_groups),
            )
        ]
        sections.extend(
            (
                f"step:{step.name}",
                (
                    *(group.name for group in step.groups),
                    *(
                        f"CONSTRAINT {name}"
                        for name in step.constraint_names
                    ),
                ),
            )
            for step in self.steps
        )
        if not self.steps:
            sections.append(
                ("choice", tuple(group.name for group in self.choice_groups))
            )
        sections.extend(
            (
                (
                    "propagation",
                    tuple(group.name for group in self.propagation_groups),
                ),
                (
                    "interpretation",
                    tuple(group.name for group in self.interpretation_groups),
                ),
            )
        )
        return tuple(sections)
