"""Choice-point selection and alternative-ordering policies."""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Protocol

from .choice_production import ChoiceAlternative, ChoicePoint
from .terms import Term


class ChoicePolicy(Protocol):
    """Select a point and order its values without changing feasibility."""

    def select_point(
        self,
        points: Sequence[ChoicePoint],
    ) -> ChoicePoint: ...

    def order_alternatives(
        self,
        point: ChoicePoint,
        random_source: random.Random,
    ) -> tuple[ChoiceAlternative, ...]: ...


@dataclass(frozen=True, slots=True)
class MRVChoicePolicy:
    """First-fail variable choice with deterministic value ordering."""

    prefer_high_weight: bool = True

    def select_point(
        self,
        points: Sequence[ChoicePoint],
    ) -> ChoicePoint:
        if not points:
            raise ValueError("cannot select from an empty choice set")
        return min(
            points,
            key=lambda point: (len(point.alternatives), point.name),
        )

    def order_alternatives(
        self,
        point: ChoicePoint,
        random_source: random.Random,
    ) -> tuple[ChoiceAlternative, ...]:
        del random_source
        if self.prefer_high_weight:
            return tuple(
                sorted(
                    point.alternatives,
                    key=lambda alternative: (
                        -alternative.weight,
                        alternative.name,
                    ),
                )
            )
        return tuple(
            sorted(
                point.alternatives,
                key=lambda alternative: alternative.name,
            )
        )


@dataclass(frozen=True, slots=True)
class PriorityMRVChoicePolicy:
    """Respect explicit variable phases, then apply MRV inside each phase."""

    priorities: Mapping[Term, int]
    prefer_high_weight: bool = True
    default_priority: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "priorities",
            MappingProxyType(dict(self.priorities)),
        )

    def select_point(
        self,
        points: Sequence[ChoicePoint],
    ) -> ChoicePoint:
        if not points:
            raise ValueError("cannot select from an empty choice set")
        return min(
            points,
            key=lambda point: (
                (
                    self.default_priority
                    if point.variable is None
                    else self.priorities.get(
                        point.variable,
                        self.default_priority,
                    )
                ),
                len(point.alternatives),
                point.name,
            ),
        )

    def order_alternatives(
        self,
        point: ChoicePoint,
        random_source: random.Random,
    ) -> tuple[ChoiceAlternative, ...]:
        return MRVChoicePolicy(
            prefer_high_weight=self.prefer_high_weight
        ).order_alternatives(point, random_source)


@dataclass(frozen=True, slots=True)
class PriorityWeightedRandomChoicePolicy:
    """Respect variable phases and sample each domain by current weights."""

    priorities: Mapping[Term, int]
    default_priority: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "priorities",
            MappingProxyType(dict(self.priorities)),
        )

    def select_point(
        self,
        points: Sequence[ChoicePoint],
    ) -> ChoicePoint:
        return _select_priority_point(
            points,
            self.priorities,
            self.default_priority,
        )

    def order_alternatives(
        self,
        point: ChoicePoint,
        random_source: random.Random,
    ) -> tuple[ChoiceAlternative, ...]:
        return WeightedRandomChoicePolicy().order_alternatives(
            point,
            random_source,
        )


@dataclass(frozen=True, slots=True)
class WeightedRandomChoicePolicy:
    """MRV point choice and seeded weighted sampling without replacement."""

    def select_point(
        self,
        points: Sequence[ChoicePoint],
    ) -> ChoicePoint:
        return MRVChoicePolicy().select_point(points)

    def order_alternatives(
        self,
        point: ChoicePoint,
        random_source: random.Random,
    ) -> tuple[ChoiceAlternative, ...]:
        remaining = list(point.alternatives)
        ordered: list[ChoiceAlternative] = []
        while remaining:
            total = sum(alternative.weight for alternative in remaining)
            if total <= 0:
                remaining.sort(key=lambda alternative: alternative.name)
                random_source.shuffle(remaining)
                ordered.extend(remaining)
                break
            target = random_source.random() * total
            cumulative = 0.0
            selected = len(remaining) - 1
            for index, alternative in enumerate(remaining):
                cumulative += alternative.weight
                if target < cumulative:
                    selected = index
                    break
            ordered.append(remaining.pop(selected))
        return tuple(ordered)


def _select_priority_point(
    points: Sequence[ChoicePoint],
    priorities: Mapping[Term, int],
    default_priority: int,
) -> ChoicePoint:
    if not points:
        raise ValueError("cannot select from an empty choice set")
    return min(
        points,
        key=lambda point: (
            (
                default_priority
                if point.variable is None
                else priorities.get(point.variable, default_priority)
            ),
            len(point.alternatives),
            point.name,
        ),
    )
