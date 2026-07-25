"""Choice-point selection and alternative-ordering policies."""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Protocol

from .choice_production import ChoiceAlternative, ChoicePoint
from .engine import InferenceSession
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
class ChoicePropagationObservation:
    """Observed effect of one real choice after fixed-point propagation."""

    point: str
    alternative: str
    variable: Term | None
    value: Term | None
    before_log_volume: float
    after_log_volume: float | None
    failed: bool = False
    solved: bool = False


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


@dataclass(slots=True)
class DomWdegChoicePolicy:
    """MRV refined by dynamically weighted failing constraints."""

    constraint_scopes: Mapping[Term, tuple[Term, ...]]
    failure_constraints: Callable[
        [InferenceSession],
        Sequence[Term],
    ]
    prefer_high_weight: bool = True
    weights: dict[Term, int] = field(init=False)

    def __post_init__(self) -> None:
        self.constraint_scopes = MappingProxyType(
            {
                constraint: tuple(variables)
                for constraint, variables in self.constraint_scopes.items()
            }
        )
        self.weights = {
            constraint: 1 for constraint in self.constraint_scopes
        }

    def select_point(
        self,
        points: Sequence[ChoicePoint],
    ) -> ChoicePoint:
        if not points:
            raise ValueError("cannot select from an empty choice set")
        active = {
            point.variable
            for point in points
            if point.variable is not None
        }

        def score(point: ChoicePoint) -> tuple[float, int, int, str]:
            weighted_degree = self._weighted_degree(
                point.variable,
                active,
            )
            return (
                len(point.alternatives) / weighted_degree,
                len(point.alternatives),
                -weighted_degree,
                point.name,
            )

        return min(points, key=score)

    def order_alternatives(
        self,
        point: ChoicePoint,
        random_source: random.Random,
    ) -> tuple[ChoiceAlternative, ...]:
        return MRVChoicePolicy(
            prefer_high_weight=self.prefer_high_weight
        ).order_alternatives(point, random_source)

    def observe_failure(self, session: InferenceSession) -> None:
        """Increase weights of constraints explaining one failed branch."""

        for constraint in self.failure_constraints(session):
            if constraint in self.weights:
                self.weights[constraint] += 1

    def _weighted_degree(
        self,
        variable: Term | None,
        active: set[Term],
    ) -> int:
        if variable is None:
            return 1
        degree = sum(
            self.weights[constraint]
            for constraint, scope in self.constraint_scopes.items()
            if variable in scope
            and any(
                other != variable and other in active
                for other in scope
            )
        )
        return max(1, degree)


@dataclass(frozen=True, slots=True)
class PropagationGuidedChoicePolicy:
    """Order small value sets by the state obtained after propagation.

    The wrapped policy still selects the choice point and supplies the stable
    fallback order. Alternatives are probed only when their count is within
    ``maximum_alternatives``. Contradictory probes are placed last.
    """

    base: ChoicePolicy
    score_session: Callable[[InferenceSession], float]
    maximum_alternatives: int = 8
    prefer_high_score: bool = True

    def __post_init__(self) -> None:
        if self.maximum_alternatives < 1:
            raise ValueError("maximum_alternatives must be positive")

    def select_point(
        self,
        points: Sequence[ChoicePoint],
    ) -> ChoicePoint:
        return self.base.select_point(points)

    def order_alternatives(
        self,
        point: ChoicePoint,
        random_source: random.Random,
    ) -> tuple[ChoiceAlternative, ...]:
        return self.base.order_alternatives(point, random_source)

    def order_alternatives_with_propagation(
        self,
        point: ChoicePoint,
        random_source: random.Random,
        probe: Callable[
            [ChoiceAlternative],
            tuple[bool, InferenceSession],
        ],
    ) -> tuple[ChoiceAlternative, ...]:
        """Probe and rank a bounded set of alternatives."""

        ordered = self.order_alternatives(point, random_source)
        if len(ordered) > self.maximum_alternatives:
            return ordered
        scored: list[tuple[bool, float, int, ChoiceAlternative]] = []
        for index, alternative in enumerate(ordered):
            contradiction, session = probe(alternative)
            score = self.score_session(session)
            scored.append(
                (
                    contradiction,
                    -score if self.prefer_high_score else score,
                    index,
                    alternative,
                )
            )
        scored.sort(key=lambda row: row[:3])
        return tuple(row[3] for row in scored)

    def observe_failure(self, session: InferenceSession) -> None:
        """Forward failure feedback when the wrapped policy accepts it."""

        observer = getattr(self.base, "observe_failure", None)
        if callable(observer):
            observer(session)


@dataclass(slots=True)
class LearnedImpactChoicePolicy:
    """Order values by impacts learned from real, non-speculative branches."""

    base: ChoicePolicy
    initial_impact: float = 0.5
    impacts: dict[
        tuple[str, Term | None, Term | None, str],
        float,
    ] = field(
        init=False
    )
    observation_counts: dict[
        tuple[str, Term | None, Term | None, str],
        int,
    ] = field(init=False)

    def __post_init__(self) -> None:
        if not 0 <= self.initial_impact <= 1:
            raise ValueError("initial_impact must be between zero and one")
        self.impacts = {}
        self.observation_counts = {}

    def select_point(
        self,
        points: Sequence[ChoicePoint],
    ) -> ChoicePoint:
        return self.base.select_point(points)

    def order_alternatives(
        self,
        point: ChoicePoint,
        random_source: random.Random,
    ) -> tuple[ChoiceAlternative, ...]:
        ordered = self.base.order_alternatives(point, random_source)
        ranks = {
            alternative.name: index
            for index, alternative in enumerate(ordered)
        }
        return tuple(
            sorted(
                ordered,
                key=lambda alternative: (
                    self.impacts.get(
                        self._key(point, alternative),
                        self.initial_impact,
                    ),
                    ranks[alternative.name],
                ),
            )
        )

    def observe_propagation(
        self,
        observation: ChoicePropagationObservation,
    ) -> None:
        """Update a running mean impact for one variable/value choice."""

        key = (
            observation.point,
            observation.variable,
            observation.value,
            observation.alternative,
        )
        if observation.failed:
            sample = 1.0
        elif observation.solved:
            sample = 0.0
        elif observation.after_log_volume is None:
            return
        else:
            remaining_ratio = math.exp(
                min(
                    0.0,
                    observation.after_log_volume
                    - observation.before_log_volume,
                )
            )
            sample = 1.0 - remaining_ratio
        count = self.observation_counts.get(key, 0) + 1
        previous = self.impacts.get(key, 0.0)
        self.impacts[key] = previous + (sample - previous) / count
        self.observation_counts[key] = count

    def observe_failure(self, session: InferenceSession) -> None:
        """Forward failure feedback to the wrapped point policy."""

        observer = getattr(self.base, "observe_failure", None)
        if callable(observer):
            observer(session)

    @staticmethod
    def _key(
        point: ChoicePoint,
        alternative: ChoiceAlternative,
    ) -> tuple[str, Term | None, Term | None, str]:
        return (
            point.name,
            point.variable,
            alternative.value,
            alternative.name,
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
