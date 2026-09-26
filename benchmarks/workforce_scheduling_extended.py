"""Five workers, twelve tasks: breaks, rest, coverage and an optional alternative.

Run: python -m benchmarks.workforce_scheduling_extended
The query has an explicit time limit and reports whether optimality was proved.
"""

from dataclasses import replace

from benchmarks.workforce_scheduling import WORKERS, build_model, costs
from snarky import Atom, Fact, Number, Triple, Variable
from snarky.finite import (
    Capacity,
    Coverage,
    ExactlyOne,
    FactorObjective,
    FiniteModel,
    FiniteVariable,
    Precedence,
    Query,
    QueryKind,
    StartWindow,
    TableFactor,
    Task,
    Workload,
    availability_constraints,
    no_overlap_constraints,
    solve,
)
from snarky.finite.model import Constraint
from snarky.finite.predicates import integer
from snarky.premises import FactPremise


def build_extended_model() -> tuple[FiniteModel, tuple[Task, ...]]:
    base, original = build_model(wide_starts=True)
    always = Atom("mandatory_presence")
    variables = [*base.variables, FiniteVariable(always, (Number(1),))]
    tasks = list(original)
    extra_costs = []
    for label, starts in (("early", (14, 15)), ("late", (16, 17))):
        start, resource, present = (
            Atom(f"followup_{label}_{field}")
            for field in ("start", "worker", "present")
        )
        task = Task("followup_" + label, start, 1, resource, present)
        tasks.append(task)
        variables.extend(
            (
                FiniteVariable(start, tuple(map(Number, starts))),
                FiniteVariable(resource, (Atom("alice"), Atom("bob"))),
                FiniteVariable(present, (Number(0), Number(1))),
            )
        )
        extra_costs.append(
            TableFactor(
                "operations:" + task.name,
                (present, start),
                {(Number(1), Number(s)): 1 + s - starts[0] for s in starts},
            )
        )
    constraints: list[Constraint] = []
    windows = {
        Atom(w.name): ((max(w.available[0], 6), 12), (14, min(w.available[1], 20)))
        for w in WORKERS
    }
    for task in tasks:
        constraints.extend(availability_constraints(task, windows))
    constraints.extend(StartWindow(t, 6, 12) for t in tasks[:5])
    constraints.extend(StartWindow(t, 14, 20) for t in tasks[5:10])
    constraints.extend(
        Precedence(tasks[i], tasks[i + 5], min_lag=2, max_lag=8) for i in range(5)
    )
    constraints.extend(
        Precedence(tasks[0], t, min_lag=2, max_lag=8) for t in tasks[10:]
    )
    constraints.extend(
        no_overlap_constraints(tasks, {v.name: v.domain for v in variables}, min_gap=1)
    )
    constraints.extend(
        (
            Capacity(tasks, 3),
            ExactlyOne(tasks[10:]),
            Coverage(tasks, (8, 10), 2, name=Atom("morning_coverage")),
            Coverage(tasks, (16, 17), 2, name=Atom("afternoon_coverage")),
        )
    )
    constraints.extend(Workload(tasks, Atom(w.name), 6, minimum=1) for w in WORKERS)
    context = list(base.context)
    for task in tasks:
        subject = Atom(task.name)
        context.append(
            Fact(Triple(subject, Atom("presence_variable"), task.present or always))
        )
        if task in original:
            continue
        assert task.resource is not None
        context.extend(
            (
                Fact(Triple(subject, Atom("start_variable"), task.start)),
                Fact(Triple(subject, Atom("worker_variable"), task.resource)),
                Fact(
                    Triple(
                        subject, Atom("latest_family_start"), Number(18 - task.duration)
                    )
                ),
                Fact(Triple(subject, Atom("day"), Atom("weekend"))),
            )
        )
    # A positive presence premise keeps absent alternatives out of all penalties.
    presence = (
        FactPremise(
            Triple(Variable("task"), Atom("presence_variable"), Variable("pv"))
        ),
        FactPremise(Triple(Variable("pv"), Atom("value"), Number(1))),
    )
    rules = tuple(
        replace(
            group,
            rules=tuple(
                replace(rule, premises=(*presence, *rule.premises))
                if rule.name.endswith("_penalty")
                else rule
                for rule in group.rules
            ),
        )
        for group in base.rules
    )
    assert isinstance(base.objective, FactorObjective)
    objective = replace(base.objective, factors=(*base.objective.factors, *extra_costs))
    return FiniteModel(
        "extended_workforce",
        tuple(variables),
        tuple(constraints),
        tuple(context),
        rules,
        objective,
    ), tuple(tasks)


def main() -> None:
    model, tasks = build_extended_model()
    result = solve(
        model,
        Query(QueryKind.MINIMIZE, time_limit_seconds=10),
        value_policy="objective",
    )
    print(
        f"{result.status}; {result.termination}; nodes={result.explored_nodes}; "
        f"bound={result.objective_bound}"
    )
    if result.incumbent is None:
        return
    print("operational cost, human penalty:", costs(model, result.incumbent))
    assignment = result.incumbent.assignment
    for task in tasks:
        if task.present is not None and assignment[task.present] == Number(0):
            print(task.name, "absent")
            continue
        start = integer(assignment[task.start])
        assert task.resource is not None
        print(
            task.name,
            assignment[task.resource],
            f"{start:02d}–{start + task.duration:02d}",
        )


if __name__ == "__main__":
    main()
