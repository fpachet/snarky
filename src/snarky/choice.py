"""Explicit weighted choices and branch-isolated search."""

from __future__ import annotations

import math
import random
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass, field
from enum import StrEnum

from .choice_frontier import (
    ChoiceTraversal as ChoiceTraversal,
)
from .choice_frontier import (
    _SearchFrontier,
)
from .choice_policies import (
    ChoicePolicy as ChoicePolicy,
)
from .choice_policies import (
    MRVChoicePolicy as MRVChoicePolicy,
)
from .choice_policies import (
    PriorityMRVChoicePolicy as PriorityMRVChoicePolicy,
)
from .choice_policies import (
    PriorityWeightedRandomChoicePolicy as PriorityWeightedRandomChoicePolicy,
)
from .choice_policies import (
    WeightedRandomChoicePolicy as WeightedRandomChoicePolicy,
)
from .choice_production import (
    ChoiceAlternative as ChoiceAlternative,
)
from .choice_production import (
    ChoicePoint as ChoicePoint,
)
from .choice_production import (
    ChoiceProvider as ChoiceProvider,
)
from .choice_production import (
    RuleChoiceProvider as RuleChoiceProvider,
)
from .engine import InferenceSession, SessionCheckpoint, StopCondition
from .facts import Fact
from .instantiation import (
    BranchableInstantiationStrategy,
    InstantiationStrategy,
)
from .rules import RuleGroup
from .terms import Term


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


class ChoiceSearchStatus(StrEnum):
    SOLVED = "solved"
    EXHAUSTED = "exhausted"
    LIMIT_REACHED = "limit_reached"


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


@dataclass(slots=True)
class _ChoiceFrame:
    """A suspended DFS choice whose next sibling has not been forked yet."""

    parent: _SearchNode
    point: ChoicePoint
    alternatives: tuple[ChoiceAlternative, ...]
    next_index: int = 0


@dataclass(frozen=True, slots=True)
class _DeferredBranch:
    """A frontier entry whose isolated session is materialized on demand."""

    parent: _SearchNode
    point: ChoicePoint
    alternative: ChoiceAlternative
    insertion_order: int

    @property
    def decisions(self) -> tuple[ChoiceDecision, ...]:
        decision = ChoiceDecision(
            self.point.name,
            self.alternative.name,
            self.alternative.value,
            self.alternative.weight,
        )
        return (*self.parent.decisions, decision)

    @property
    def log_weight(self) -> float:
        return self.parent.log_weight + _log_weight(
            self.alternative.weight
        )


@dataclass(frozen=True, slots=True)
class _TrailChoiceFrame:
    parent: _SearchNode
    point: ChoicePoint
    checkpoint: SessionCheckpoint
    strategy_template: InstantiationStrategy


@dataclass(frozen=True, slots=True)
class _TrailAlternative:
    frame: _TrailChoiceFrame
    alternative: ChoiceAlternative


@dataclass(frozen=True, slots=True)
class _TrailRelease:
    frame: _TrailChoiceFrame


type _PendingItem = (
    _SearchNode
    | _ChoiceFrame
    | _DeferredBranch
    | _TrailAlternative
    | _TrailRelease
)


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
    reversible_depth_first: bool = True
    lazy_frontier: bool = True

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
        pending = _SearchFrontier[_PendingItem](self.traversal)
        pending.push(root)
        open_checkpoints: list[
            tuple[
                InferenceSession,
                SessionCheckpoint,
                InstantiationStrategy,
            ]
        ] = []
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

        try:
            while (
                pending
                and explored < self.max_nodes
                and len(solutions) < self.max_solutions
            ):
                item = pending.pop()
                if isinstance(item, _TrailRelease):
                    trail_session = item.frame.parent.session
                    trail_session.rollback(
                        item.frame.checkpoint,
                        invalidate_strategy=False,
                    )
                    trail_session.strategy = item.frame.strategy_template
                    trail_session.release(item.frame.checkpoint)
                    (
                        released_session,
                        released_checkpoint,
                        released_strategy,
                    ) = (
                        open_checkpoints.pop()
                    )
                    if (
                        released_session is not trail_session
                        or released_checkpoint != item.frame.checkpoint
                        or released_strategy
                        is not item.frame.strategy_template
                    ):
                        raise AssertionError(
                            "reversible choice checkpoints are not nested"
                        )
                    continue
                if isinstance(item, _TrailAlternative):
                    frame = item.frame
                    alternative = item.alternative
                    branch = frame.parent.session
                    branch.rollback(
                        frame.checkpoint,
                        invalidate_strategy=False,
                    )
                    branch.strategy = self._reversible_branch_strategy(
                        frame.strategy_template
                    )
                    branch.assume(
                        *alternative.facts,
                        label=(
                            f"choice:{frame.point.name}/"
                            f"{alternative.name}"
                        ),
                    )
                    decision = ChoiceDecision(
                        frame.point.name,
                        alternative.name,
                        alternative.value,
                        alternative.weight,
                    )
                    pending.push(
                        _SearchNode(
                            branch,
                            (*frame.parent.decisions, decision),
                            frame.parent.log_weight
                            + _log_weight(alternative.weight),
                            next_order,
                            frame.point.name,
                            alternative.name,
                        )
                    )
                    next_order += 1
                    continue
                if isinstance(item, _ChoiceFrame):
                    alternative = item.alternatives[item.next_index]
                    next_index = item.next_index + 1
                    if next_index < len(item.alternatives):
                        pending.push(
                            _ChoiceFrame(
                                item.parent,
                                item.point,
                                item.alternatives,
                                next_index,
                            )
                        )
                    branch = self._fork(item.parent.session)
                    branch.assume(
                        *alternative.facts,
                        label=(
                            f"choice:{item.point.name}/{alternative.name}"
                        ),
                    )
                    decision = ChoiceDecision(
                        item.point.name,
                        alternative.name,
                        alternative.value,
                        alternative.weight,
                    )
                    pending.push(
                        _SearchNode(
                            branch,
                            (*item.parent.decisions, decision),
                            item.parent.log_weight
                            + _log_weight(alternative.weight),
                            next_order,
                            item.point.name,
                            alternative.name,
                        )
                    )
                    next_order += 1
                    continue
                if isinstance(item, _DeferredBranch):
                    branch = self._fork(item.parent.session)
                    branch.assume(
                        *item.alternative.facts,
                        label=(
                            f"choice:{item.point.name}/"
                            f"{item.alternative.name}"
                        ),
                    )
                    node = _SearchNode(
                        branch,
                        item.decisions,
                        item.log_weight,
                        item.insertion_order,
                        item.point.name,
                        item.alternative.name,
                    )
                else:
                    node = item
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
                if (
                    previous_score is not None
                    and previous_score >= node.log_weight
                ):
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
                        detail=self._backtrack_detail,
                    )
                    continue
                if self.goal(node.session):
                    solution_session = (
                        self._fork(node.session)
                        if self._uses_reversible_dfs
                        else node.session
                    )
                    solutions.append(
                        ChoiceSolution(
                            solution_session,
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
                        detail=self._backtrack_detail,
                    )
                    continue
                point = self.policy.select_point(points)
                record(
                    ChoiceEventKind.CHOICE,
                    node,
                    point=point.name,
                    detail=f"{len(point.alternatives)} alternatives",
                )
                ordered = self.policy.order_alternatives(
                    point,
                    random_source,
                )
                if self._uses_reversible_dfs:
                    checkpoint = node.session.checkpoint()
                    frame = _TrailChoiceFrame(
                        node,
                        point,
                        checkpoint,
                        node.session.strategy,
                    )
                    open_checkpoints.append(
                        (
                            node.session,
                            checkpoint,
                            frame.strategy_template,
                        )
                    )
                    pending.push(_TrailRelease(frame))
                    pending.extend(
                        tuple(
                            _TrailAlternative(frame, alternative)
                            for alternative in reversed(ordered)
                        )
                    )
                    continue
                if self.traversal is ChoiceTraversal.DEPTH_FIRST:
                    pending.push(
                        _ChoiceFrame(node, point, tuple(ordered))
                    )
                    continue
                if self.lazy_frontier:
                    for alternative in ordered:
                        pending.push(
                            _DeferredBranch(
                                node,
                                point,
                                alternative,
                                next_order,
                            )
                        )
                        next_order += 1
                    continue
                children: list[_SearchNode] = []
                for alternative in ordered:
                    branch = self._fork(node.session)
                    branch.assume(
                        *alternative.facts,
                        label=(
                            f"choice:{point.name}/{alternative.name}"
                        ),
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
                        node.log_weight
                        + _log_weight(alternative.weight),
                        next_order,
                        point.name,
                        alternative.name,
                    )
                    next_order += 1
                    children.append(child)
                pending.extend(children)
        finally:
            for (
                trail_session,
                checkpoint,
                strategy_template,
            ) in reversed(open_checkpoints):
                trail_session.rollback(
                    checkpoint,
                    invalidate_strategy=False,
                )
                trail_session.strategy = strategy_template
                trail_session.release(checkpoint)

        limit_reached = bool(pending) and (
            explored >= self.max_nodes
            and len(solutions) < self.max_solutions
        )
        if limit_reached:
            record(
                ChoiceEventKind.LIMIT,
                self._pending_node(pending.first()),
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
        if self.branch_strategy_factory is not None:
            return session.fork(strategy=self.branch_strategy_factory())
        strategy = session.strategy
        if isinstance(strategy, BranchableInstantiationStrategy):
            return session.fork(strategy=strategy.fork_for_branch())
        return session.fork()

    def _reversible_branch_strategy(
        self,
        template: InstantiationStrategy,
    ) -> InstantiationStrategy:
        if isinstance(template, BranchableInstantiationStrategy):
            return template.fork_for_branch()
        if self.branch_strategy_factory is not None:
            return self.branch_strategy_factory()
        return deepcopy(template)

    @staticmethod
    def _pending_node(
        item: (
            _SearchNode
            | _ChoiceFrame
            | _DeferredBranch
            | _TrailAlternative
            | _TrailRelease
        ),
    ) -> _SearchNode:
        if isinstance(item, _ChoiceFrame):
            return item.parent
        if isinstance(item, (_TrailAlternative, _TrailRelease)):
            return item.frame.parent
        if isinstance(item, _DeferredBranch):
            return _SearchNode(
                item.parent.session,
                item.decisions,
                item.log_weight,
                item.insertion_order,
                item.point.name,
                item.alternative.name,
            )
        return item

    @property
    def _uses_reversible_dfs(self) -> bool:
        return (
            self.reversible_depth_first
            and self.traversal is ChoiceTraversal.DEPTH_FIRST
        )

    @property
    def _backtrack_detail(self) -> str:
        if self._uses_reversible_dfs:
            return "rollback reversible branch"
        return "discard isolated branch"

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
