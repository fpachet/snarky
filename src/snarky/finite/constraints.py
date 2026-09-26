"""Immutable finite-domain constraint definitions, independent of inference sessions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ..terms import Atom, Term, is_ground


@dataclass(frozen=True, slots=True)
class AllDifferentConstraint:
    """Require the scoped variables to take pairwise-distinct values."""

    name: Atom
    variables: tuple[Term, ...]

    def __post_init__(self) -> None:
        _validate_scope("ALL_DIFFERENT", self.variables)
        object.__setattr__(self, "variables", tuple(self.variables))


@dataclass(frozen=True, slots=True)
class SumConstraint:
    """Require the scoped integer variables to sum exactly to ``target``."""

    name: Atom
    variables: tuple[Term, ...]
    target: int

    def __post_init__(self) -> None:
        _validate_scope("SUM", self.variables)
        object.__setattr__(self, "variables", tuple(self.variables))


class ConstraintOperator(StrEnum):
    """Comparison operators shared by numeric aggregate constraints."""

    EQUAL = "EQUAL"
    LESS_EQUAL = "LESS_EQUAL"
    GREATER_EQUAL = "GREATER_EQUAL"


class BinaryComparisonOperator(StrEnum):
    """Operators supported by persistent binary comparisons."""

    LESS_EQUAL = "LESS_EQUAL"
    LESS_THAN = "LESS_THAN"
    NOT_EQUAL = "NOT_EQUAL"


@dataclass(frozen=True, slots=True)
class LinearSumConstraint:
    """Constrain an integer weighted sum with ``=``, ``<=``, or ``>=``."""

    name: Atom
    terms: tuple[tuple[int, Term], ...]
    operator: ConstraintOperator
    target: int

    def __post_init__(self) -> None:
        terms = tuple(self.terms)
        if not terms:
            raise ValueError("LINEAR_SUM requires at least one term")
        if any(
            isinstance(coefficient, bool)
            or not isinstance(coefficient, int)
            or coefficient == 0
            for coefficient, _ in terms
        ):
            raise ValueError("LINEAR_SUM coefficients must be non-zero integers")
        variables = tuple(variable for _, variable in terms)
        _validate_scope("LINEAR_SUM", variables)
        if isinstance(self.target, bool) or not isinstance(self.target, int):
            raise ValueError("LINEAR_SUM target must be an integer")
        object.__setattr__(self, "terms", terms)
        object.__setattr__(
            self,
            "operator",
            ConstraintOperator(self.operator),
        )

    @property
    def variables(self) -> tuple[Term, ...]:
        """Return the variables participating in the weighted sum."""

        return tuple(variable for _, variable in self.terms)


@dataclass(frozen=True, slots=True)
class BinaryComparisonConstraint:
    """Compare two finite-domain variables."""

    name: Atom
    left: Term
    right: Term
    operator: BinaryComparisonOperator

    def __post_init__(self) -> None:
        if self.left == self.right:
            raise ValueError("binary comparison variables must be distinct")
        object.__setattr__(
            self,
            "operator",
            BinaryComparisonOperator(self.operator),
        )

    @property
    def variables(self) -> tuple[Term, Term]:
        """Return the two compared variables."""

        return (self.left, self.right)


@dataclass(frozen=True, slots=True)
class ElementConstraint:
    """Require ``value`` to equal ``array[index]`` using one-based indices."""

    name: Atom
    index: Term
    array: tuple[Term, ...]
    value: Term

    def __post_init__(self) -> None:
        array = tuple(self.array)
        _validate_scope("ELEMENT array", array)
        variables = (self.index, *array, self.value)
        if len(set(variables)) != len(variables):
            raise ValueError(
                "ELEMENT index, array, and value variables must be distinct"
            )
        object.__setattr__(self, "array", array)

    @property
    def variables(self) -> tuple[Term, ...]:
        """Return index, array, and result variables."""

        return (self.index, *self.array, self.value)


@dataclass(frozen=True, slots=True)
class CountConstraint:
    """Count occurrences of one value in a finite-domain scope."""

    name: Atom
    variables: tuple[Term, ...]
    value: Term
    operator: ConstraintOperator
    target: int

    def __post_init__(self) -> None:
        _validate_scope("COUNT", self.variables)
        if isinstance(self.target, bool) or not isinstance(self.target, int):
            raise ValueError("COUNT target must be an integer")
        object.__setattr__(self, "variables", tuple(self.variables))
        object.__setattr__(
            self,
            "operator",
            ConstraintOperator(self.operator),
        )


@dataclass(frozen=True, slots=True)
class NValueConstraint:
    """Count distinct values of ``scope`` plus literal ``constants``.

    ``count`` is a Python integer or a decision-variable name. Repeated scope
    references and constants are deduplicated; an empty scope is permitted.
    The count variable may also occur in the scope.
    """

    name: Atom
    scope: tuple[Term, ...]
    count: int | Term
    constants: tuple[Term, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.count, bool):
            raise ValueError("NVALUE count must be an integer or a variable")
        if any(not is_ground(value) for value in self.constants):
            raise ValueError("NVALUE constants must be ground terms")
        object.__setattr__(self, "scope", tuple(dict.fromkeys(self.scope)))
        object.__setattr__(self, "constants", tuple(dict.fromkeys(self.constants)))

    @property
    def variables(self) -> tuple[Term, ...]:
        return tuple(
            dict.fromkeys(
                self.scope if isinstance(self.count, int) else (*self.scope, self.count)
            )
        )


@dataclass(frozen=True, slots=True)
class GlobalCardinalityConstraint:
    """Bound the number of occurrences of selected values in a scope.

    ``bounds`` contains ``(value, lower, upper)`` triples. Values without an
    explicit entry retain the default interval ``[0, number of variables]``.
    """

    name: Atom
    variables: tuple[Term, ...]
    bounds: tuple[tuple[Term, int, int], ...]

    def __post_init__(self) -> None:
        _validate_scope("GCC", self.variables)
        bounds = tuple(self.bounds)
        values = tuple(value for value, _, _ in bounds)
        if len(set(values)) != len(values):
            raise ValueError("GCC values must have unique bounds")
        for _, lower, upper in bounds:
            if lower < 0 or upper < lower:
                raise ValueError("GCC bounds require 0 <= lower <= upper")
        object.__setattr__(self, "variables", tuple(self.variables))
        object.__setattr__(self, "bounds", bounds)


@dataclass(frozen=True, slots=True)
class TableConstraint:
    """Require the scoped variables to match one allowed tuple."""

    name: Atom
    variables: tuple[Term, ...]
    allowed: tuple[tuple[Term, ...], ...]

    def __post_init__(self) -> None:
        _validate_scope("TABLE", self.variables)
        allowed = tuple(tuple(row) for row in self.allowed)
        if not allowed:
            raise ValueError("TABLE requires at least one allowed tuple")
        if any(len(row) != len(self.variables) for row in allowed):
            raise ValueError("TABLE tuple arity must match its scope")
        object.__setattr__(self, "variables", tuple(self.variables))
        object.__setattr__(self, "allowed", tuple(dict.fromkeys(allowed)))


@dataclass(frozen=True, slots=True)
class LexLessEqualConstraint:
    """Require one sequence of numeric variables to be lexicographically <= another."""

    name: Atom
    left: tuple[Term, ...]
    right: tuple[Term, ...]

    def __post_init__(self) -> None:
        left = tuple(self.left)
        right = tuple(self.right)
        if not left or len(left) != len(right):
            raise ValueError(
                "LEX_LESS_EQUAL requires non-empty sequences of equal length"
            )
        object.__setattr__(self, "left", left)
        object.__setattr__(self, "right", right)

    @property
    def variables(self) -> tuple[Term, ...]:
        """Return the distinct variables observed by this constraint."""

        return tuple(dict.fromkeys((*self.left, *self.right)))


@dataclass(frozen=True, slots=True)
class AnyOfConstraint:
    """Require at least one ordinary constraint; an empty disjunction is false.

    Propagation retains the union of each alternative's supported domains.
    Alternatives are persistent constraints, not fact guards or callbacks.
    """

    name: Atom
    alternatives: tuple[PersistentConstraint, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "alternatives", tuple(self.alternatives))

    @property
    def variables(self) -> tuple[Term, ...]:
        return tuple(dict.fromkeys(v for c in self.alternatives for v in c.variables))


@dataclass(frozen=True, slots=True)
class AllOfConstraint:
    """Conjoin persistent constraints; an empty conjunction is true."""

    name: Atom
    constraints: tuple[PersistentConstraint, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "constraints", tuple(self.constraints))

    @property
    def variables(self) -> tuple[Term, ...]:
        return tuple(dict.fromkeys(v for c in self.constraints for v in c.variables))


@dataclass(frozen=True, slots=True)
class Task:
    """A positive-duration interval [start, start + duration).

    Fields reference ordinary finite variables. ``present``, when supplied,
    uses integer Number(0/1) values. No variables or constraints are posted here.
    """

    name: str
    start: Atom
    duration: int
    resource: Atom | None = None
    present: Atom | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a task needs a name")
        if type(self.duration) is not int or self.duration <= 0:
            raise ValueError("task duration must be a positive integer")
        if not isinstance(self.start, Atom) or any(
            v is not None and not isinstance(v, Atom)
            for v in (self.resource, self.present)
        ):
            raise TypeError("task fields must reference finite variable names (atoms)")


@dataclass(frozen=True, slots=True)
class CapacityConstraint:
    """Bound the total demand of present tasks at every discrete time slot.

    This is one shared pool, independent of the tasks' resource assignments.
    """

    name: Atom
    tasks: tuple[Task, ...]
    capacity: int
    demands: tuple[int, ...]

    def __post_init__(self) -> None:
        tasks, demands = tuple(self.tasks), tuple(self.demands)
        if type(self.capacity) is not int or self.capacity < 0:
            raise ValueError("capacity must be a nonnegative integer")
        if len(demands) != len(tasks) or any(
            type(d) is not int or d < 0 for d in demands
        ):
            raise ValueError("demands must contain one nonnegative integer per task")
        if len({task.name for task in tasks}) != len(tasks):
            raise ValueError("capacity task names must be distinct")
        object.__setattr__(self, "tasks", tasks)
        object.__setattr__(self, "demands", demands)

    @property
    def variables(self) -> tuple[Term, ...]:
        return tuple(
            dict.fromkeys(
                v
                for task in self.tasks
                for v in (task.start, task.present)
                if v is not None
            )
        )


def _task_scope(
    tasks: tuple[Task, ...], *, starts: bool = True, resources: bool = True
) -> tuple[Term, ...]:
    return tuple(
        dict.fromkeys(
            v
            for t in tasks
            for v in (
                t.start if starts else None,
                t.resource if resources else None,
                t.present,
            )
            if v is not None
        )
    )


def _window(window: tuple[int, ...]) -> None:
    if (
        len(window) != 2
        or any(type(v) is not int for v in window)
        or window[0] > window[1]
    ):
        raise ValueError("window requires integer open <= close")


def _load_limits(minimum: int, maximum: int | None) -> None:
    if (
        type(minimum) is not int
        or minimum < 0
        or maximum is not None
        and (type(maximum) is not int or maximum < minimum)
    ):
        raise ValueError("load bounds require 0 <= minimum <= maximum")


@dataclass(frozen=True, slots=True)
class AvailabilityConstraint:
    """Present task must fit in the union of its assigned resource's windows."""

    name: Atom
    task: Task
    windows: tuple[tuple[Term, tuple[tuple[int, int], ...]], ...]

    def __post_init__(self) -> None:
        if self.task.resource is None:
            raise ValueError("availability requires a resource variable")
        result = []
        for resource, windows in self.windows:
            if not is_ground(resource):
                raise ValueError("availability resources must be ground")
            merged: list[tuple[int, int]] = []
            for window in sorted(tuple(w) for w in windows):
                _window(window)
                lo, hi = window
                if merged and lo <= merged[-1][1]:
                    merged[-1] = (merged[-1][0], max(hi, merged[-1][1]))
                else:
                    merged.append((lo, hi))
            result.append((resource, tuple(merged)))
        if len({r for r, _ in result}) != len(result):
            raise ValueError("availability resources must be distinct")
        object.__setattr__(self, "windows", tuple(result))

    @property
    def variables(self) -> tuple[Term, ...]:
        return _task_scope((self.task,))


@dataclass(frozen=True, slots=True)
class ResourceLoadConstraint:
    """Per-slot lower/upper load, optionally selecting assigned resources.

    Coverage counts active tasks, not distinct workers. Combine with worker
    non-overlap for staffing. A finite window is required for a positive minimum.
    """

    name: Atom
    tasks: tuple[Task, ...]
    minimum: int = 0
    maximum: int | None = None
    window: tuple[int, int] | None = None
    resources: tuple[Term, ...] | None = None
    demands: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        tasks = tuple(self.tasks)
        _load_limits(self.minimum, self.maximum)
        if self.minimum and self.window is None:
            raise ValueError("positive coverage requires a finite window")
        if self.window is not None:
            _window(self.window)
            object.__setattr__(self, "window", tuple(self.window))
        if self.resources is not None:
            if any(t.resource is None for t in tasks):
                raise ValueError("resource load requires resource variables")
            if any(not is_ground(r) for r in self.resources):
                raise ValueError("resource selectors must be ground")
            object.__setattr__(self, "resources", tuple(dict.fromkeys(self.resources)))
        demands = tuple(self.demands) if self.demands else (1,) * len(tasks)
        # Share demand/task validation with the original capacity contract.
        CapacityConstraint(self.name, tasks, 0, demands)
        object.__setattr__(self, "tasks", tasks)
        object.__setattr__(self, "demands", demands)

    @property
    def variables(self) -> tuple[Term, ...]:
        return _task_scope(self.tasks, resources=self.resources is not None)


@dataclass(frozen=True, slots=True)
class WorkloadConstraint:
    """Total assigned working time; optionally count overlap with a time window."""

    name: Atom
    tasks: tuple[Task, ...]
    resource: Term
    maximum: int
    minimum: int = 0
    window: tuple[int, int] | None = None

    def __post_init__(self) -> None:
        _load_limits(self.minimum, self.maximum)
        tasks = tuple(self.tasks)
        if any(t.resource is None for t in tasks) or not is_ground(self.resource):
            raise ValueError(
                "workload requires resource variables and a ground resource"
            )
        if len({t.name for t in tasks}) != len(tasks):
            raise ValueError("workload task names must be distinct")
        if self.window is not None:
            _window(self.window)
            object.__setattr__(self, "window", tuple(self.window))
        object.__setattr__(self, "tasks", tasks)

    @property
    def variables(self) -> tuple[Term, ...]:
        return _task_scope(self.tasks, starts=self.window is not None)


type PersistentConstraint = (
    AllDifferentConstraint
    | SumConstraint
    | LinearSumConstraint
    | BinaryComparisonConstraint
    | ElementConstraint
    | CountConstraint
    | NValueConstraint
    | GlobalCardinalityConstraint
    | TableConstraint
    | LexLessEqualConstraint
    | AnyOfConstraint
    | CapacityConstraint
    | AllOfConstraint
    | AvailabilityConstraint
    | ResourceLoadConstraint
    | WorkloadConstraint
)


def _validate_scope(kind: str, variables: tuple[Term, ...]) -> None:
    variables = tuple(variables)
    if not variables:
        raise ValueError(f"{kind} requires at least one variable")
    if len(set(variables)) != len(variables):
        raise ValueError(f"{kind} variables must be distinct")
