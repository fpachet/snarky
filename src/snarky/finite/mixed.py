"""Coordinate native domains and the existing incremental positive rule engine."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from time import perf_counter

from ..choice_fixed_point import _changed_relations, _group_watch, _is_affected
from ..engine.forward import ForwardEngine
from ..engine.group_execution import GroupExecutionMode
from ..engine.session_state import SessionCheckpoint
from ..facts import Fact
from ..instantiation import SemiNaiveInstantiationStrategy
from ..terms import Atom, Term
from .constraints import LinearSumConstraint
from .model import FactConstraint, FiniteModel, Solution, score_solution
from .propagation import NativeCheckpoint, NativeState


@dataclass(frozen=True, slots=True)
class MixedCheckpoint:
    domains: NativeCheckpoint
    session: SessionCheckpoint


class MixedState:
    """Facts receive singleton assignments; constraints consume positive guards.

    Domain values remain in the native domain store, not candidate facts. The
    session owns derived facts and provenance; one checkpoint spans both stores.
    """

    def __init__(self, model: FiniteModel, *, numeric_masks: bool = True) -> None:
        self.model = model
        self._native = NativeState(model, numeric_masks=numeric_masks)
        self.domains = self._native.domains
        self.session = ForwardEngine(
            (),
            strategy=SemiNaiveInstantiationStrategy(),
        ).create_session(model.context)
        self._watches = tuple(_group_watch(group) for group in model.rules)

    @property
    def failure(self) -> Atom | None:
        return self._native.failure

    @property
    def revisions(self) -> int:
        return self._native.revisions

    def checkpoint(self) -> MixedCheckpoint:
        return MixedCheckpoint(self._native.checkpoint(), self.session.checkpoint())

    def rollback(self, checkpoint: MixedCheckpoint) -> None:
        # Validate the session handle before mutating either component.
        self.session._validate_checkpoint(checkpoint.session)
        self._native.rollback(checkpoint.domains)
        self.session.rollback(checkpoint.session)

    def release(self, checkpoint: MixedCheckpoint) -> None:
        self.session._validate_checkpoint(checkpoint.session)
        self._native.release(checkpoint.domains)
        self.session.release(checkpoint.session)

    def restrict(self, variable: Term, value: Term) -> None:
        self._native.restrict(variable, value)

    def _close_rules(self, deadline: float | None) -> None:
        additions = self._native.closed_facts() - frozenset(self.session.facts)
        # Keep context and variable order deterministic rather than iterating a set.
        if additions:
            ordered = sorted(additions, key=repr)
            self.session.assume(*ordered, label="finite-assignment")
        pending = deque(range(len(self.model.rules)))
        queued = set(pending)
        while pending:
            if deadline is not None and perf_counter() >= deadline:
                raise TimeoutError("mixed rule closure time limit")
            index = pending.popleft()
            queued.remove(index)
            before = self.session.event_count
            # One cycle permits deadline checks between deterministic rule rounds.
            # Positive, function-free validation ensures a finite least fixed point.
            self.session.run_group(
                self.model.rules[index],
                mode=GroupExecutionMode.ONE_CYCLE,
                materialize_result=False,
            )
            changed = _changed_relations(self.session.events_since(before))
            if changed == frozenset():
                continue
            for target, watch in enumerate(self._watches):
                if target not in queued and _is_affected(watch, changed):
                    queued.add(target)
                    pending.append(target)

    def propagate(
        self,
        *,
        deadline: float | None = None,
        objective_cut: LinearSumConstraint | None = None,
    ) -> bool:
        while True:
            before_removals = len(self.domains.removals)
            before_events = self.session.event_count
            if not self._native.propagate(
                deadline=deadline,
                facts=frozenset(self.session.facts),
                objective_cut=objective_cut,
            ):
                return False
            self._close_rules(deadline)
            facts = frozenset(self.session.facts)
            for constraint in self.model.constraints:
                if (
                    isinstance(constraint, FactConstraint)
                    and set(constraint.forbidden) & facts
                ):
                    self._native.failure = constraint.name
                    return False
            if (
                len(self.domains.removals) == before_removals
                and self.session.event_count == before_events
            ):
                return True

    def closed_facts(self) -> frozenset[Fact]:
        return frozenset(self.session.facts)

    def solution(self) -> Solution:
        assignment = self._native.assignment()
        snapshot = self.session.snapshot()
        facts = frozenset(snapshot.facts)
        score, contributions = score_solution(self.model, assignment, facts)
        return Solution(
            assignment,
            facts,
            score,
            derivations=snapshot.derivations,
            reductions=self.domains.removals,
            contributions=contributions,
        )
