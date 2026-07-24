"""Explicit weighted choices and branch-isolated search."""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Protocol

from .engine import InferenceSession, StopCondition
from .facts import Fact
from .instantiation import InstantiationStrategy
from .rules import RuleGroup
from .terms import Term


@dataclass(frozen=True, slots=True)
class ChoiceAlternative:
    """One feasible branch of a declarative choice point."""

    name: str
    facts: tuple[Fact, ...]
    value: Term | None = None
    weight: float = 1.0
    metadata: Mapping[str, object] = field(
        default_factory=dict,
        compare=False,
        hash=False,
    )

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a choice alternative needs a name")
        facts = tuple(self.facts)
        if not facts:
            raise ValueError("a choice alternative must assert at least one fact")
        if not math.isfinite(self.weight) or self.weight < 0:
            raise ValueError("a choice weight must be finite and non-negative")
        object.__setattr__(self, "facts", facts)
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )


@dataclass(frozen=True, slots=True)
class ChoicePoint:
    """A finite set of alternatives emitted from one search state."""

    name: str
    alternatives: tuple[ChoiceAlternative, ...]
    variable: Term | None = None
    metadata: Mapping[str, object] = field(
        default_factory=dict,
        compare=False,
        hash=False,
    )

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a choice point needs a name")
        alternatives = tuple(self.alternatives)
        if not alternatives:
            raise ValueError("a choice point needs at least one alternative")
        names = tuple(alternative.name for alternative in alternatives)
        if len(set(names)) != len(names):
            raise ValueError("choice alternative names must be unique")
        object.__setattr__(self, "alternatives", alternatives)
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )


@dataclass(frozen=True, slots=True)
class ChoiceDecision:
    point: str
    alternative: str
    value: Term | None
    weight: float


class ChoiceEventKind(StrEnum):
    CHOICE = "choice"
    DECISION = "decision"
    CONTRADICTION = "contradiction"
    BACKTRACK = "backtrack"
    SOLUTION = "solution"
    DEAD_END = "dead_end"
    LIMIT = "limit"


@dataclass(frozen=True, slots=True)
class ChoiceEvent:
    sequence: int
    kind: ChoiceEventKind
    depth: int
    point: str = ""
    alternative: str = ""
    detail: str = ""
    log_weight: float = 0.0


class ChoiceTraversal(StrEnum):
    DEPTH_FIRST = "depth_first"
    BREADTH_FIRST = "breadth_first"
    BEST_FIRST = "best_first"


class ChoiceSearchStatus(StrEnum):
    SOLVED = "solved"
    EXHAUSTED = "exhausted"
    LIMIT_REACHED = "limit_reached"


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


type ChoiceProvider = Callable[
    [InferenceSession],
    tuple[ChoicePoint, ...],
]
type StrategyFactory = Callable[[], InstantiationStrategy]


@dataclass(frozen=True, slots=True)
class ChoiceSolution:
    session: InferenceSession
    decisions: tuple[ChoiceDecision, ...]
    log_weight: float


@dataclass(frozen=True, slots=True)
class ChoiceSearchResult:
    status: ChoiceSearchStatus
    solutions: tuple[ChoiceSolution, ...]
    explored_nodes: int
    failed_branches: int
    events: tuple[ChoiceEvent, ...]


@dataclass(slots=True)
class _SearchNode:
    session: InferenceSession
    decisions: tuple[ChoiceDecision, ...]
    log_weight: float
    insertion_order: int
    incoming_point: str = ""
    incoming_alternative: str = ""


@dataclass(frozen=True, slots=True)
class SessionChoiceSearch:
    """Search choices over isolated :class:`InferenceSession` branches."""

    groups: tuple[RuleGroup, ...]
    choices: ChoiceProvider
    goal: StopCondition
    contradiction: StopCondition | None = None
    policy: ChoicePolicy = field(default_factory=MRVChoicePolicy)
    traversal: ChoiceTraversal = ChoiceTraversal.DEPTH_FIRST
    max_nodes: int = 10_000
    max_solutions: int = 1
    max_group_passes: int = 100
    seed: int = 0
    branch_strategy_factory: StrategyFactory | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "groups", tuple(self.groups))
        if self.max_nodes < 1:
            raise ValueError("max_nodes must be positive")
        if self.max_solutions < 1:
            raise ValueError("max_solutions must be positive")
        if self.max_group_passes < 1:
            raise ValueError("max_group_passes must be positive")

    def solve(self, session: InferenceSession) -> ChoiceSearchResult:
        random_source = random.Random(self.seed)
        root = _SearchNode(self._fork(session), (), 0.0, 0)
        pending = [root]
        best_seen: dict[frozenset[Fact], float] = {}
        solutions: list[ChoiceSolution] = []
        events: list[ChoiceEvent] = []
        failed = 0
        explored = 0
        next_order = 1

        def record(
            kind: ChoiceEventKind,
            node: _SearchNode,
            *,
            point: str = "",
            alternative: str = "",
            detail: str = "",
        ) -> None:
            events.append(
                ChoiceEvent(
                    len(events) + 1,
                    kind,
                    len(node.decisions),
                    point,
                    alternative,
                    detail,
                    node.log_weight,
                )
            )

        while (
            pending
            and explored < self.max_nodes
            and len(solutions) < self.max_solutions
        ):
            node = self._pop(pending)
            if node.incoming_alternative:
                record(
                    ChoiceEventKind.DECISION,
                    node,
                    point=node.incoming_point,
                    alternative=node.incoming_alternative,
                )
            self._propagate(node.session)
            state = frozenset(node.session.facts)
            previous_score = best_seen.get(state)
            if previous_score is not None and previous_score >= node.log_weight:
                continue
            best_seen[state] = node.log_weight
            explored += 1

            if self.contradiction is not None and self.contradiction(
                node.session
            ):
                failed += 1
                record(
                    ChoiceEventKind.CONTRADICTION,
                    node,
                    detail="branch contradiction",
                )
                record(
                    ChoiceEventKind.BACKTRACK,
                    node,
                    detail="discard isolated branch",
                )
                continue
            if self.goal(node.session):
                solutions.append(
                    ChoiceSolution(
                        node.session,
                        node.decisions,
                        node.log_weight,
                    )
                )
                record(ChoiceEventKind.SOLUTION, node)
                continue

            points = self.choices(node.session)
            if not points:
                failed += 1
                record(
                    ChoiceEventKind.DEAD_END,
                    node,
                    detail="no choice and goal not reached",
                )
                record(
                    ChoiceEventKind.BACKTRACK,
                    node,
                    detail="discard isolated branch",
                )
                continue
            point = self.policy.select_point(points)
            record(
                ChoiceEventKind.CHOICE,
                node,
                point=point.name,
                detail=f"{len(point.alternatives)} alternatives",
            )
            ordered = self.policy.order_alternatives(point, random_source)
            children: list[_SearchNode] = []
            for alternative in ordered:
                branch = self._fork(node.session)
                branch.assume(
                    *alternative.facts,
                    label=f"choice:{point.name}/{alternative.name}",
                )
                decision = ChoiceDecision(
                    point.name,
                    alternative.name,
                    alternative.value,
                    alternative.weight,
                )
                child = _SearchNode(
                    branch,
                    (*node.decisions, decision),
                    node.log_weight + _log_weight(alternative.weight),
                    next_order,
                    point.name,
                    alternative.name,
                )
                next_order += 1
                children.append(child)
            if self.traversal is ChoiceTraversal.DEPTH_FIRST:
                pending.extend(reversed(children))
            else:
                pending.extend(children)

        limit_reached = bool(pending) and (
            explored >= self.max_nodes
            and len(solutions) < self.max_solutions
        )
        if limit_reached:
            record(
                ChoiceEventKind.LIMIT,
                pending[0],
                detail=f"maximum node count {self.max_nodes} reached",
            )
        status = (
            ChoiceSearchStatus.SOLVED
            if solutions
            else (
                ChoiceSearchStatus.LIMIT_REACHED
                if limit_reached
                else ChoiceSearchStatus.EXHAUSTED
            )
        )
        return ChoiceSearchResult(
            status,
            tuple(solutions),
            explored,
            failed,
            tuple(events),
        )

    def _fork(self, session: InferenceSession) -> InferenceSession:
        if self.branch_strategy_factory is None:
            return session.fork()
        return session.fork(strategy=self.branch_strategy_factory())

    def _pop(self, pending: list[_SearchNode]) -> _SearchNode:
        if self.traversal is ChoiceTraversal.DEPTH_FIRST:
            return pending.pop()
        if self.traversal is ChoiceTraversal.BREADTH_FIRST:
            return pending.pop(0)
        best_index = max(
            range(len(pending)),
            key=lambda index: (
                pending[index].log_weight,
                -pending[index].insertion_order,
            ),
        )
        return pending.pop(best_index)

    def _propagate(self, session: InferenceSession) -> None:
        for _ in range(self.max_group_passes):
            before = session.facts
            for group in self.groups:
                session.run_group(group)
            if session.facts == before:
                return
        raise RuntimeError(
            "choice propagation did not stabilize within "
            f"{self.max_group_passes} group passes"
        )


def _log_weight(weight: float) -> float:
    return math.log(weight) if weight > 0 else float("-inf")
