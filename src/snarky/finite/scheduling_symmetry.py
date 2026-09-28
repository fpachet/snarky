"""Explicitly certified symmetry reduction for scheduling optimization models."""

from collections.abc import Collection, Mapping, Sequence

from ..terms import Atom, Term, is_ground
from .constraints import AnyOfConstraint, TableConstraint, Task
from .predicates import integer


def interchangeable_task_constraints(
    tasks: Sequence[Task],
    domains: Mapping[Term, Collection[Term]],
    *,
    resource_order: Sequence[Term],
    certified: bool,
    private_resources: Mapping[str, Term] | None = None,
    distinct_resources: bool = False,
    name: Atom | None = None,
) -> tuple[TableConstraint | AnyOfConstraint, ...]:
    """Order resources within a caller-certified interchangeable task group.

    The caller certifies that permuting whole task assignments (including starts)
    and renaming private resources with their tasks preserves every hard constraint
    and the objective. Structural checks here cannot prove that global property.
    ``distinct_resources=True`` additionally certifies that a shared resource can
    occur at most once in this group. Otherwise repeated shared resources remain
    allowed. Private alternatives sort after shared resources and may repeat ranks.

    This creates a reduced model preserving an optimal value and a witness under
    the certification. Do not add these constraints to a model used for original
    solution counts, enumeration or probability queries. No solver policy applies
    them automatically. Optional tasks and shared task variables are unsupported.
    """
    if certified is not True:
        raise ValueError("interchangeability requires explicit caller certification")
    if type(distinct_resources) is not bool:
        raise ValueError("distinct_resources must be Boolean")
    tasks = tuple(tasks)
    order = tuple(resource_order)
    if len(set(order)) != len(order) or any(not is_ground(x) for x in order):
        raise ValueError("resource_order must contain unique ground values")
    names = {t.name for t in tasks}
    if len(names) != len(tasks):
        raise ValueError("interchangeable task names must be distinct")
    private = dict(private_resources or {})
    if private and set(private) != names:
        raise ValueError("private_resources must map every task name exactly once")
    if (
        len(set(private.values())) != len(private)
        or set(private.values()) & set(order)
        or any(not is_ground(x) for x in private.values())
    ):
        raise ValueError(
            "private resources must be unique ground values outside the order"
        )
    used: set[Term] = set()
    starts: frozenset[Term] | None = None
    eligible: frozenset[Term] | None = None
    resources: list[Term] = []
    values: list[tuple[Term, ...]] = []
    for task in tasks:
        if task.present is not None or task.resource is None:
            raise ValueError(
                "symmetry requires mandatory tasks with resource variables"
            )
        if task.start == task.resource or used & {task.start, task.resource}:
            raise ValueError("symmetry requires distinct task variables")
        used.update((task.start, task.resource))
        if task.start not in domains or task.resource not in domains:
            raise ValueError("all task variables require declared domains")
        current_starts = frozenset(domains[task.start])
        if not current_starts:
            raise ValueError("start domains must be nonempty")
        for value in current_starts:
            integer(value)
        if task.duration != tasks[0].duration or (
            starts is not None and current_starts != starts
        ):
            raise ValueError(
                "interchangeable tasks require equal durations and start domains"
            )
        starts = current_starts
        candidates = frozenset(domains[task.resource])
        own = {private[task.name]} if private else set()
        if not candidates or not own <= candidates or candidates - set(order) - own:
            raise ValueError(
                "resource domain contains missing or undeclared alternatives"
            )
        shared = candidates - own
        if eligible is not None and shared != eligible:
            raise ValueError("interchangeable tasks require equal shared eligibility")
        eligible = shared
        resources.append(task.resource)
        # Use the explicit order, not potentially unordered domain iteration.
        values.append(tuple(x for x in order if x in shared) + tuple(own))
    ranks = {value: i for i, value in enumerate(order)}
    ranks.update((value, len(order)) for value in private.values())
    prefix = (name or Atom("interchangeable")).name
    result: list[TableConstraint | AnyOfConstraint] = []
    for i, (left, right) in enumerate(zip(tasks, tasks[1:], strict=False)):
        constraint_name = Atom(f"{prefix}:{left.name}:{right.name}")
        allowed = tuple(
            (a, b)
            for a in values[i]
            for b in values[i + 1]
            if ranks[a] < ranks[b]
            or ranks[a] == ranks[b]
            and (not distinct_resources or ranks[a] == len(order))
        )
        result.append(
            TableConstraint(constraint_name, (resources[i], resources[i + 1]), allowed)
            if allowed
            else AnyOfConstraint(constraint_name, ())
        )
    return tuple(result)
