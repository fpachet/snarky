"""Explicit weighted choices and branch-isolated search."""

from __future__ import annotations

import heapq
import math
import random
from collections import deque
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Protocol

from .actions import Action, AddFact, Choice, ForEach
from .engine import InferenceSession, SessionCheckpoint, StopCondition
from .facts import Fact
from .instantiation import (
    Activation,
    BranchableInstantiationStrategy,
    IndexedInstantiationStrategy,
    InstantiationStrategy,
    QueryableInstantiationStrategy,
)
from .premises import BindPremise, FactPremise, Premise
from .rules import Rule, RuleGroup
from .substitutions import Substitution
from .terms import (
    Atom,
    Term,
    Triple,
    render_term,
    variables_in,
)


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


type ChoiceProvider = Callable[
    [InferenceSession],
    tuple[ChoicePoint, ...],
]
type StrategyFactory = Callable[[], InstantiationStrategy]


class RuleChoiceProvider:
    """Expose ``CHOICE`` actions from rules as search choice points.

    Choice rules are excluded from ordinary forward chaining. Their ``WHEN``
    part establishes one stable object context; each sequential ``CHOICE``
    instantiates one target fact inside a branch.
    """

    def __init__(self, groups: Sequence[RuleGroup]) -> None:
        self.groups = tuple(groups)
        choice_rules: list[tuple[str, Rule, tuple[Choice, ...]]] = []
        propagation_groups: list[RuleGroup] = []
        for group in self.groups:
            deterministic: list[Rule] = []
            for rule in group.rules:
                if any(
                    isinstance(action, ForEach)
                    and _contains_nested_choice(action)
                    for action in rule.actions
                ):
                    raise ValueError(
                        "CHOICE inside FOR EACH is not supported"
                    )
                choices: list[Choice] = []
                terminal_actions: list[Action] = []
                terminal_started = False
                for action in rule.actions:
                    if isinstance(action, Choice):
                        if terminal_started:
                            raise ValueError(
                                f"choice rule {rule.name!r} cannot place "
                                "CHOICE after deterministic actions"
                            )
                        choices.append(action)
                    else:
                        terminal_started = True
                        terminal_actions.append(action)
                if not choices:
                    deterministic.append(rule)
                    continue
                choice_rules.append(
                    (group.name, rule, tuple(choices))
                )
                if terminal_actions:
                    completion_name = f"{rule.name}__after_choices"
                    deterministic.append(
                        Rule(
                            completion_name,
                            (
                                *rule.premises,
                                *(
                                    premise
                                    for choice in choices
                                    for premise in (
                                        FactPremise(
                                            choice.entity,
                                            choice.status,
                                        ),
                                        *choice.premises,
                                    )
                                ),
                            ),
                            tuple(terminal_actions),
                            {
                                **rule.metadata,
                                "choice_completion_of": rule.name,
                            },
                        )
                    )
            if deterministic:
                propagation_groups.append(
                    RuleGroup(group.name, tuple(deterministic))
                )
        self.choice_rules = tuple(choice_rules)
        self.propagation_groups = tuple(propagation_groups)

    def __call__(
        self,
        session: InferenceSession,
    ) -> tuple[ChoicePoint, ...]:
        facts = session.facts
        query_strategy = _choice_query_strategy(session)
        points: dict[str, ChoicePoint] = {}
        for group_name, rule, actions in self.choice_rules:
            outer_activations = query_strategy.instantiate(
                rule,
                facts,
            )
            for activation in outer_activations:
                contexts: tuple[Substitution, ...] = (
                    activation.substitution,
                )
                for action_index, action in enumerate(actions):
                    continuing: list[Substitution] = []
                    for context in contexts:
                        existing = _query_premises(
                            (FactPremise(action.entity, action.status),),
                            facts,
                            context,
                            query_strategy,
                        )
                        if existing:
                            continuing.extend(
                                item.substitution for item in existing
                            )
                            continue
                        point = _choice_point_from_action(
                            group_name,
                            rule,
                            action_index,
                            action,
                            context,
                            facts,
                            query_strategy,
                        )
                        if point is not None:
                            previous = points.get(point.name)
                            points[point.name] = (
                                point
                                if previous is None
                                else _merge_choice_points(previous, point)
                            )
                    contexts = tuple(continuing)
                    if not contexts:
                        break
        return tuple(points.values())


def _choice_query_strategy(
    session: InferenceSession,
) -> InstantiationStrategy:
    strategy = session.strategy
    if isinstance(strategy, QueryableInstantiationStrategy):
        return strategy.query_view()
    return IndexedInstantiationStrategy()


def _contains_nested_choice(action: ForEach) -> bool:
    return any(
        isinstance(nested, Choice)
        or (
            isinstance(nested, ForEach)
            and _contains_nested_choice(nested)
        )
        for nested in action.actions
    )


def _choice_point_from_action(
    group_name: str,
    rule: Rule,
    action_index: int,
    action: Choice,
    context: Substitution,
    facts: tuple[Fact, ...],
    strategy: InstantiationStrategy,
) -> ChoicePoint | None:
    candidates = _query_premises(
        action.premises,
        facts,
        context,
        strategy,
    )
    alternatives_by_fact: dict[Fact, ChoiceAlternative] = {}
    introduced = tuple(
        sorted(
            (
                variable
                for variable in (
                    variables_in(action.entity)
                    | variables_in(action.status)
                )
                if variable not in context
            ),
            key=lambda variable: variable.name,
        )
    )
    for candidate in candidates:
        fact = action.instantiate(candidate.substitution)
        value: Term = (
            candidate.substitution.apply(introduced[0])
            if len(introduced) == 1
            else fact.entity
        )
        alternative = ChoiceAlternative(
            render_term(value),
            (fact,),
            value,
            action.resolved_weight(candidate.substitution),
            {
                "rule": rule.name,
                "rule_group": group_name,
                "substitution": candidate.substitution,
                "supports": candidate.premise_facts,
            },
        )
        previous = alternatives_by_fact.get(fact)
        if previous is not None and previous.weight != alternative.weight:
            raise ValueError(
                "the same CHOICE fact has conflicting weights: "
                f"{render_term(fact.entity)}"
            )
        alternatives_by_fact[fact] = alternative
    if not alternatives_by_fact:
        return None
    context_label = ",".join(
        f"{name}={render_term(value)}" for name, value in context.key
    )
    point_name = (
        f"{group_name}:{rule.name}:{action_index}"
        f"[{context_label}]"
    )
    target = context.apply(action.entity)
    decision_variable = (
        target.subject if isinstance(target, Triple) else target
    )
    return ChoicePoint(
        point_name,
        tuple(alternatives_by_fact.values()),
        decision_variable,
        {
            "rule": rule.name,
            "rule_group": group_name,
            "action_index": action_index,
            "substitution": context,
        },
    )


def _merge_choice_points(
    left: ChoicePoint,
    right: ChoicePoint,
) -> ChoicePoint:
    alternatives = {
        alternative.name: alternative
        for alternative in left.alternatives
    }
    for alternative in right.alternatives:
        previous = alternatives.get(alternative.name)
        if previous is not None and previous.facts != alternative.facts:
            raise ValueError(
                f"CHOICE alternative {alternative.name!r} is ambiguous"
            )
        alternatives[alternative.name] = alternative
    return ChoicePoint(
        left.name,
        tuple(alternatives.values()),
        left.variable,
        left.metadata,
    )


def _query_premises(
    premises: tuple[Premise, ...],
    facts: tuple[Fact, ...],
    initial: Substitution,
    strategy: InstantiationStrategy,
) -> tuple[Activation, ...]:
    bindings = tuple(
        BindPremise(variable, initial.apply(value))
        for variable, value in initial.items()
    )
    query = Rule(
        "__choice_query__",
        (*bindings, *premises),
        (AddFact(Atom("__choice_query_result__")),),
    )
    return strategy.instantiate(query, facts)


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


class _SearchFrontier:
    """Traversal-specific pending storage with a stable best-first heap."""

    def __init__(self, traversal: ChoiceTraversal) -> None:
        self.traversal = traversal
        self._items: list[_PendingItem] = []
        self._queue: deque[_PendingItem] = deque()
        self._heap: list[tuple[float, int, _PendingItem]] = []

    def push(self, item: _PendingItem) -> None:
        if self.traversal is ChoiceTraversal.BEST_FIRST:
            if isinstance(item, (_DeferredBranch, _SearchNode)):
                log_weight = item.log_weight
                insertion_order = item.insertion_order
            else:
                raise AssertionError("DFS frames cannot enter best-first")
            heapq.heappush(
                self._heap,
                (-log_weight, insertion_order, item),
            )
            return
        if self.traversal is ChoiceTraversal.BREADTH_FIRST:
            self._queue.append(item)
            return
        self._items.append(item)

    def extend(self, items: Sequence[_PendingItem]) -> None:
        for item in items:
            self.push(item)

    def pop(self) -> _PendingItem:
        if self.traversal is ChoiceTraversal.BEST_FIRST:
            return heapq.heappop(self._heap)[2]
        if self.traversal is ChoiceTraversal.BREADTH_FIRST:
            return self._queue.popleft()
        return self._items.pop()

    def first(self) -> _PendingItem:
        if self.traversal is ChoiceTraversal.BEST_FIRST:
            return self._heap[0][2]
        if self.traversal is ChoiceTraversal.BREADTH_FIRST:
            return self._queue[0]
        return self._items[0]

    def __bool__(self) -> bool:
        if self.traversal is ChoiceTraversal.BEST_FIRST:
            return bool(self._heap)
        if self.traversal is ChoiceTraversal.BREADTH_FIRST:
            return bool(self._queue)
        return bool(self._items)


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
        pending = _SearchFrontier(self.traversal)
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
