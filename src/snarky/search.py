"""Optional explicit hypothesis search built on isolated inference forks."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from .engine import InferenceSession, StopCondition
from .facts import Fact
from .rules import RuleGroup


@dataclass(frozen=True, slots=True)
class Hypothesis:
    """One named set of facts asserted together on a search branch."""

    name: str
    facts: tuple[Fact, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a hypothesis name cannot be empty")
        facts = tuple(self.facts)
        if not facts:
            raise ValueError("a hypothesis must assert at least one fact")
        object.__setattr__(self, "facts", facts)


class SearchTraversal(StrEnum):
    BREADTH_FIRST = "breadth_first"
    DEPTH_FIRST = "depth_first"


class SearchStatus(StrEnum):
    SOLVED = "solved"
    EXHAUSTED = "exhausted"
    LIMIT_REACHED = "limit_reached"


type HypothesisGenerator = Callable[
    [InferenceSession, tuple[Hypothesis, ...]],
    tuple[Hypothesis, ...],
]


@dataclass(frozen=True, slots=True)
class SearchNode:
    session: InferenceSession
    hypotheses: tuple[Hypothesis, ...]


@dataclass(frozen=True, slots=True)
class HypothesisSearchResult:
    status: SearchStatus
    solution: SearchNode | None
    explored_nodes: int
    rejected_paths: tuple[tuple[Hypothesis, ...], ...]


@dataclass(frozen=True, slots=True)
class HypothesisSearch:
    """Explore alternatives without adding implicit backtracking to rules."""

    groups: tuple[RuleGroup, ...]
    expand: HypothesisGenerator
    goal: StopCondition
    contradiction: StopCondition | None = None
    traversal: SearchTraversal = SearchTraversal.BREADTH_FIRST
    max_nodes: int = 10_000

    def __post_init__(self) -> None:
        object.__setattr__(self, "groups", tuple(self.groups))
        if self.max_nodes < 1:
            raise ValueError("max_nodes must be positive")

    def solve(self, session: InferenceSession) -> HypothesisSearchResult:
        root = SearchNode(session.fork(), ())
        pending = [root]
        visited: set[frozenset[Fact]] = set()
        rejected: list[tuple[Hypothesis, ...]] = []
        explored = 0
        while pending and explored < self.max_nodes:
            node = (
                pending.pop(0)
                if self.traversal is SearchTraversal.BREADTH_FIRST
                else pending.pop()
            )
            for group in self.groups:
                node.session.run_group(group)
            state = frozenset(node.session.facts)
            if state in visited:
                continue
            visited.add(state)
            explored += 1
            if self.contradiction is not None and self.contradiction(
                node.session
            ):
                rejected.append(node.hypotheses)
                continue
            if self.goal(node.session):
                return HypothesisSearchResult(
                    SearchStatus.SOLVED,
                    node,
                    explored,
                    tuple(rejected),
                )
            children: list[SearchNode] = []
            for hypothesis in self.expand(node.session, node.hypotheses):
                branch = node.session.fork()
                branch.assume(*hypothesis.facts, label=hypothesis.name)
                children.append(
                    SearchNode(
                        branch,
                        (*node.hypotheses, hypothesis),
                    )
                )
            if self.traversal is SearchTraversal.DEPTH_FIRST:
                pending.extend(reversed(children))
            else:
                pending.extend(children)
        status = (
            SearchStatus.LIMIT_REACHED
            if pending
            else SearchStatus.EXHAUSTED
        )
        return HypothesisSearchResult(
            status,
            None,
            explored,
            tuple(rejected),
        )
