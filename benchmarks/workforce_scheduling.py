"""Self-contained synthetic workforce demo: python -m benchmarks.workforce_scheduling.

Five fictional workers, ten tasks, one day in hourly slots. No IATP installation
or external data is needed; the context facts stand in for persona attributes.
"""

from dataclasses import dataclass, replace

from snarky import Atom, Fact, Number, Triple, Variable, parse_rule_groups
from snarky.factors import FactorDefinition
from snarky.finite import (
    Capacity,
    FactorObjective,
    FiniteModel,
    FiniteVariable,
    IntegerFactor,
    Precedence,
    Query,
    QueryKind,
    ResultStatus,
    TableFactor,
    Task,
    Workload,
    availability_constraints,
    no_overlap_constraints,
    solve,
)
from snarky.finite.model import Constraint, Solution
from snarky.finite.predicates import integer
from snarky.premises import FactPremise


@dataclass(frozen=True)
class Worker:
    name: str
    skill: str
    available: tuple[int, int]
    commute: int = 15
    transport: str = "car"
    young_children: bool = False
    avoids_weekends: bool = False


WORKERS = (
    Worker("alice", "electrical", (6, 20), 60, "public_transport"),
    Worker("bob", "electrical", (6, 20), young_children=True),
    Worker("chloe", "logistics", (8, 18)),
    Worker("diego", "logistics", (6, 18), avoids_weekends=True),
    Worker("erin", "care", (8, 20), young_children=True),
)

RULES = parse_rule_groups("""
GROUP persona_preferences
    RULE long_commute
    WHEN
        ($worker commute $minutes)
        ($worker transport public_transport)
        $minutes > 45
    THEN
        ADD ($worker avoid early)
    END
    RULE family_time
    WHEN
        ($worker young_children yes)
    THEN
        ADD ($worker prefer finish_by_18)
    END
    RULE early_shift_penalty
    WHEN
        ($task worker_variable $wv)
        ($wv value $worker)
        ($worker avoid early)
        ($task start_variable $sv)
        ($sv value $start)
        $start < 8
    THEN
        ADD ($task penalty early)
    END
    RULE late_shift_penalty
    WHEN
        ($task worker_variable $wv)
        ($wv value $worker)
        ($worker prefer finish_by_18)
        ($task latest_family_start $latest)
        ($task start_variable $sv)
        ($sv value $start)
        $start > $latest
    THEN
        ADD ($task penalty late)
    END
    RULE weekend_penalty
    WHEN
        ($task worker_variable $wv)
        ($wv value $worker)
        ($worker avoids_weekends yes)
        ($task day weekend)
    THEN
        ADD ($task penalty weekend)
    END
END_GROUP
""")


def build_model(
    human_weight: int = 1, *, wide_starts: bool = False, prune_pairs: bool = True
) -> tuple[FiniteModel, tuple[Task, ...]]:
    """Operational costs + human_weight * rule-derived preference penalties."""
    # Candidate resources are filtered by skills below. Fixed choices represent
    # existing commitments; four tasks still have time/worker alternatives.
    specs = (
        ("inspection", "electrical", (6, 8), 2, ("alice", "bob")),
        ("repair", "electrical", (10,), 2, ("bob",)),
        ("delivery", "logistics", (8,), 2, ("diego", "chloe")),
        ("loading", "logistics", (6,), 2, ("diego",)),
        ("care_visit", "care", (8,), 2, ("erin",)),
        ("signoff", "electrical", (14,), 2, ("alice",)),
        ("report", "electrical", (18, 16), 1, ("bob",)),
        ("stocktake", "logistics", (12,), 2, ("chloe",)),
        ("dispatch", "logistics", (14,), 2, ("diego",)),
        ("care_notes", "care", (18, 16), 1, ("erin",)),
    )
    tasks: list[Task] = []
    variables: list[FiniteVariable] = []
    constraints: list[Constraint] = []
    context: list[Fact] = []
    operational: list[TableFactor] = []
    for worker in WORKERS:
        for key, value in (
            ("commute", Number(worker.commute)),
            ("transport", Atom(worker.transport)),
            ("young_children", Atom("yes" if worker.young_children else "no")),
            ("avoids_weekends", Atom("yes" if worker.avoids_weekends else "no")),
        ):
            context.append(Fact(Triple(Atom(worker.name), Atom(key), value)))
    for name, skill, starts, duration, candidates in specs:
        domain_starts = tuple(range(6, 19)) if wide_starts else starts
        start, resource = Atom(name + "_start"), Atom(name + "_worker")
        task = Task(name, start, duration, resource)
        tasks.append(task)
        eligible = tuple(
            Atom(w.name) for w in WORKERS if w.skill == skill and w.name in candidates
        )
        # Preserve the declared choice order to make the hard-only baseline clear.
        eligible = tuple(Atom(w) for w in candidates if Atom(w) in eligible)
        variables.extend(
            (
                FiniteVariable(start, tuple(map(Number, domain_starts))),
                FiniteVariable(resource, eligible),
            )
        )
        windows = {
            Atom(w.name): w.available for w in WORKERS if Atom(w.name) in eligible
        }
        constraints.extend(availability_constraints(task, windows))
        context.extend(
            (
                Fact(Triple(Atom(name), Atom("start_variable"), start)),
                Fact(Triple(Atom(name), Atom("worker_variable"), resource)),
                Fact(
                    Triple(
                        Atom(name), Atom("latest_family_start"), Number(18 - duration)
                    )
                ),
                Fact(Triple(Atom(name), Atom("day"), Atom("weekend"))),
            )
        )
        operational.append(
            TableFactor(
                "operations:" + name,
                (start,),
                {(Number(s),): (1 if name == "inspection" else 2) for s in starts[1:]},
            )
        )
        if name in ("inspection", "delivery"):
            operational.append(
                TableFactor(
                    "operations:assignment:" + name,
                    (resource,),
                    {(eligible[1],): 3 if name == "inspection" else 1},
                )
            )
    constraints.extend(Precedence(tasks[i], tasks[i + 5]) for i in range(5))
    if prune_pairs:
        constraints.extend(
            no_overlap_constraints(tasks, {v.name: v.domain for v in variables})
        )
    else:
        from itertools import combinations

        from snarky.finite import NoOverlap

        constraints.extend(
            NoOverlap(a, b, when_same_resource=True) for a, b in combinations(tasks, 2)
        )
    constraints.append(Capacity(tasks, capacity=3, name=Atom("shared_equipment")))
    constraints.extend(
        Workload(tasks, Atom(worker.name), maximum=6) for worker in WORKERS
    )
    preferences = tuple(
        IntegerFactor(
            FactorDefinition(
                "human:" + kind,
                Variable("task"),
                (FactPremise(Triple(Variable("task"), Atom("penalty"), Atom(kind))),),
            ),
            human_weight * penalty,
        )
        for kind, penalty in (("early", 5), ("late", 5), ("weekend", 3))
    )
    return FiniteModel(
        "workforce",
        tuple(variables),
        tuple(constraints),
        tuple(context),
        RULES,
        FactorObjective((*operational, *preferences)),
    ), tuple(tasks)


def costs(model: FiniteModel, solution: Solution) -> tuple[int, int]:
    assert isinstance(model.objective, FactorObjective)
    contributions = model.objective.contributions(solution.assignment, solution.facts)
    return (
        sum(c.value for c in contributions if c.factor_name.startswith("operations:")),
        sum(c.value for c in contributions if c.factor_name.startswith("human:")),
    )


def run_demo() -> None:
    model, tasks = build_model()
    baseline = solve(replace(model, objective=None))
    optimized = solve(model, Query(QueryKind.MINIMIZE), value_policy="objective")
    assert baseline.incumbent is not None
    assert optimized.status is ResultStatus.OPTIMAL and optimized.incumbent is not None
    for label, result in (
        ("A: hard constraints only", baseline),
        ("B: operational + human preference costs", optimized),
    ):
        solution = result.incumbent
        assert solution is not None
        op, human = costs(model, solution)
        print(f"\nSchedule {label} ({result.status})")
        print(f"operational cost = {op}; human penalty = {human}; total = {op + human}")
        print(f"{'Task':14} {'Worker':8} {'Interval':8}")
        for task in tasks:
            assert task.resource is not None
            worker = solution.assignment[task.resource]
            assert isinstance(worker, Atom)
            start = integer(solution.assignment[task.start])
            print(
                f"{task.name:14} {worker.name:8} "
                f"{start:02d}–{start + task.duration:02d}"
            )
    assert baseline.incumbent.assignment != optimized.incumbent.assignment
    assert costs(model, optimized.incumbent)[1] < costs(model, baseline.incumbent)[1]
    penalties = [
        c
        for c in model.objective.contributions(
            baseline.incumbent.assignment, baseline.incumbent.facts
        )
        if c.factor_name.startswith("human:")
    ]
    print("\nBaseline preference explanations (rule derivations are also retained):")
    for c in penalties:
        print(
            f"  {c.factor_name}: +{c.value}, scope={c.scope}, "
            f"supports={c.support_facts}"
        )


if __name__ == "__main__":
    run_demo()
