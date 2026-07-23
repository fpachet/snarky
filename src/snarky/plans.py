"""Generic ordered plans for progressively applied rule groups."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .engine import (
    GroupExecutionMode,
    GroupRunResult,
    InferenceLimitError,
    InferenceSession,
    StopCondition,
)
from .rules import RuleGroup


class TechniquePlanStatus(StrEnum):
    """Terminal statuses of an ordered rule-group plan."""

    SOLVED = "solved"
    STUCK = "stuck"
    INCONSISTENT = "inconsistent"
    LIMIT_REACHED = "limit_reached"


@dataclass(frozen=True, slots=True)
class TechniquePlanResult:
    """Trace and terminal status of a generic technique plan."""

    status: TechniquePlanStatus
    effective_steps: tuple[GroupRunResult, ...]
    attempted_groups: tuple[str, ...]
    maintenance_runs: tuple[GroupRunResult, ...]


@dataclass(frozen=True, slots=True)
class TechniquePlan:
    """Apply groups in order and restart at the easiest after each change."""

    techniques: tuple[RuleGroup, ...]
    maintenance: tuple[RuleGroup, ...] = ()
    execution_mode: GroupExecutionMode = GroupExecutionMode.FIRST_CHANGE
    max_effective_steps: int = 10_000

    def __post_init__(self) -> None:
        object.__setattr__(self, "techniques", tuple(self.techniques))
        object.__setattr__(self, "maintenance", tuple(self.maintenance))
        if not self.techniques:
            raise ValueError("a technique plan requires at least one group")
        if self.execution_mode is GroupExecutionMode.UNTIL:
            raise ValueError("TechniquePlan cannot use UNTIL without a condition")
        if self.max_effective_steps < 1:
            raise ValueError("max_effective_steps must be positive")

    def solve(
        self,
        session: InferenceSession,
        *,
        solved: StopCondition,
        inconsistent: StopCondition | None = None,
    ) -> TechniquePlanResult:
        """Run until solved, inconsistent, stuck, or explicitly limited."""

        effective: list[GroupRunResult] = []
        attempted: list[str] = []
        maintenance_runs: list[GroupRunResult] = []
        try:
            while len(effective) < self.max_effective_steps:
                for group in self.maintenance:
                    maintenance_runs.append(session.run_group(group))
                if inconsistent is not None and inconsistent(session):
                    return TechniquePlanResult(
                        TechniquePlanStatus.INCONSISTENT,
                        tuple(effective),
                        tuple(attempted),
                        tuple(maintenance_runs),
                    )
                if solved(session):
                    return TechniquePlanResult(
                        TechniquePlanStatus.SOLVED,
                        tuple(effective),
                        tuple(attempted),
                        tuple(maintenance_runs),
                    )

                for group in self.techniques:
                    attempted.append(group.name)
                    result = session.run_group(
                        group,
                        mode=self.execution_mode,
                    )
                    if result.changed:
                        effective.append(result)
                        break
                else:
                    return TechniquePlanResult(
                        TechniquePlanStatus.STUCK,
                        tuple(effective),
                        tuple(attempted),
                        tuple(maintenance_runs),
                    )
        except InferenceLimitError:
            return TechniquePlanResult(
                TechniquePlanStatus.LIMIT_REACHED,
                tuple(effective),
                tuple(attempted),
                tuple(maintenance_runs),
            )
        return TechniquePlanResult(
            TechniquePlanStatus.LIMIT_REACHED,
            tuple(effective),
            tuple(attempted),
            tuple(maintenance_runs),
        )
