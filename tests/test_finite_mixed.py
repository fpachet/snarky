"""Bidirectional rule/domain propagation checked against complete enumeration."""

from dataclasses import replace
from itertools import permutations

import pytest

from snarky import Atom, EngineLimits, Fact, Number, Triple, parse_rule_groups
from snarky.finite import (
    FactConstraint,
    FiniteModel,
    FiniteVariable,
    GuardedConstraint,
    LinearObjective,
    Query,
    QueryKind,
    ResultStatus,
    Termination,
    enumerate_model,
    solve,
)
from snarky.finite.constraints import AllDifferentConstraint, TableConstraint
from snarky.finite.mixed import MixedState
from snarky.finite.search import search

X, Y, Z = (Atom(name) for name in ("x", "y", "z"))
CONSTRAINED = Fact(Triple(Atom("mode"), Atom("branch"), Atom("constrained")))
NARROW = Fact(Triple(Atom("job"), Atom("permission"), Atom("narrow")))
BAD = Fact(Triple(Atom("plan"), Atom("state"), Atom("bad")))


def allocation():
    rules = parse_rule_groups("""
        GROUP classify
            RULE choose_mode
            WHEN
                (x value 1)
            THEN
                ADD (mode branch constrained)
            END
            RULE grant
            WHEN
                (y value 2)
            THEN
                ADD (job permission narrow)
            END
        END_GROUP
        GROUP reject
            RULE impossible_plan
            WHEN
                (mode branch constrained)
                (z value 3)
            THEN
                ADD (plan state bad)
            END
        END_GROUP
    """)
    return FiniteModel(
        "allocation",
        (
            FiniteVariable(X, (Number(0), Number(1))),
            FiniteVariable(Y, (Number(1), Number(2))),
            FiniteVariable(Z, (Number(1), Number(2), Number(3))),
        ),
        (
            AllDifferentConstraint(Atom("distinct"), (X, Y, Z)),
            GuardedConstraint(
                Atom("mode_requires_two"),
                CONSTRAINED,
                TableConstraint(Atom("two"), (Y,), ((Number(2),),)),
            ),
            GuardedConstraint(
                Atom("permission_requires_three"),
                NARROW,
                TableConstraint(Atom("three"), (Z,), ((Number(3),),)),
            ),
            FactConstraint(Atom("no_bad_plan"), forbidden=(BAD,)),
        ),
        rules=rules,
        objective=LinearObjective(((10, X), (2, Y), (1, Z))),
    )


def project(result):
    return {
        tuple(solution.assignment[var] for var in (X, Y, Z)): solution.facts
        for solution in result.solutions
    }


def test_mixed_search_facts_solutions_and_optima_match_independent_oracle():
    model = allocation()
    oracle = enumerate_model(model, Query(QueryKind.ENUMERATE))
    assert len(oracle.solutions) == 3
    for order in permutations((X, Y, Z)):
        for reverse in (True, False):
            actual = solve(
                model,
                Query(QueryKind.ENUMERATE),
                variable_order=order,
                reverse_values=reverse,
            )
            assert actual.complete
            assert project(actual) == project(oracle)
            best = solve(
                model,
                Query(QueryKind.MINIMIZE),
                variable_order=order,
                reverse_values=reverse,
            )
            assert best.status is ResultStatus.OPTIMAL
            assert best.incumbent.objective_value == best.objective_bound == 4


def test_progress_observer_exception_restores_mixed_facts_and_domains():
    state = MixedState(allocation())
    before = state.domains.snapshot()
    facts = tuple(state.session.facts)

    def observe(event):
        if event.event == "incumbent":
            raise RuntimeError("observer interrupted mixed search")

    with pytest.raises(RuntimeError, match="observer interrupted"):
        search(state, Query(QueryKind.MINIMIZE), on_progress=observe)
    assert state.domains.snapshot() == before
    assert tuple(state.session.facts) == facts
    assert state.domains.removals == ()


def test_failed_derivations_and_restrictions_restore_together_across_siblings():
    state = MixedState(allocation())
    assert state.propagate()
    before_domains = state.domains.snapshot()
    before_facts = state.session.snapshot()
    root = state.checkpoint()
    state.restrict(X, Number(1))
    assert not state.propagate()
    assert state.domains.values(Y) == (Number(2),)
    assert state.domains.values(Z) == (Number(3),)
    assert BAD in state.session.facts
    assert state.failure == Atom("no_bad_plan")
    state.rollback(root)
    assert state.domains.snapshot() == before_domains
    assert state.session.snapshot().facts == before_facts.facts
    assert state.session.snapshot().derivations == before_facts.derivations
    state.restrict(X, Number(0))
    assert state.propagate()
    inner = state.checkpoint()
    state.restrict(Y, Number(2))
    assert state.propagate()
    assert NARROW in state.session.facts and BAD not in state.session.facts
    assert state.domains.values(Z) == (Number(3),)
    saved = state.solution()
    assert saved.derivations
    assert any(
        removal.cause == Atom("permission_requires_three")
        for removal in saved.reductions
    )
    state.rollback(inner)
    state.release(inner)
    assert NARROW not in state.session.facts
    assert NARROW in saved.facts  # saved solution/explanations own stable snapshots
    state.rollback(root)
    state.release(root)
    assert state.domains.snapshot() == before_domains


def test_rule_schedule_changes_preserve_declarative_results():
    model = allocation()
    reversed_groups = replace(
        model,
        rules=tuple(
            replace(group, rules=group.rules[::-1]) for group in model.rules[::-1]
        ),
    )
    query = Query(QueryKind.ENUMERATE)
    assert project(solve(model, query)) == project(solve(reversed_groups, query))


def test_wildcard_rule_watch_terminates_after_no_changes():
    rules = parse_rule_groups("""
        GROUP wildcard
            RULE observe
            WHEN
                ($entity $relation $object)
            THEN
                ADD ($entity observed yes)
            END
        END_GROUP
    """)
    seed = Fact(Triple(X, Atom("kind"), Atom("thing")))
    model = FiniteModel("wildcard", context=(seed,), rules=rules)
    result = solve(model, Query(QueryKind.ENUMERATE, time_limit_seconds=1))
    assert result.complete
    assert result.incumbent.facts == frozenset(
        (seed, Fact(Triple(X, Atom("observed"), Atom("yes"))))
    )


def test_guarded_constraint_works_without_rule_engine():
    model = replace(
        allocation(),
        rules=(),
        constraints=(
            GuardedConstraint(
                Atom("value_guard"),
                Fact(Triple(X, Atom("value"), Number(1))),
                TableConstraint(Atom("two"), (Y,), ((Number(2),),)),
            ),
        ),
    )
    query = Query(QueryKind.ENUMERATE)
    assert project(solve(model, query)) == project(enumerate_model(model, query))


def test_rule_engine_resource_guard_is_unknown_not_infeasible_and_restores_state():
    state = MixedState(allocation())
    state.session.limits = EngineLimits(max_facts=1)
    before = state.domains.snapshot()
    result = search(state, Query(QueryKind.MINIMIZE), variable_order=(X, Y, Z))
    assert result.status is ResultStatus.UNKNOWN
    assert result.termination is Termination.RESOURCE_LIMIT
    assert result.diagnostic
    assert state.domains.snapshot() == before
    assert state.session.facts == ()


def test_generated_nested_event_sequences_restore_facts_domains_and_proofs():
    from random import Random

    from snarky.finite.closure import reference_closure

    rng = Random(260916)
    names = tuple(Atom(f"v{i}") for i in range(5))
    for instance in range(8):
        rules = []
        constraints = []
        for index, var in enumerate(names):
            trigger = rng.randrange(3)
            target = names[(index + 1) % len(names)]
            flag = Fact(Triple(var, Atom("selected"), Number(trigger)))
            rules.append(f"""RULE r{index}
WHEN
({var.name} value {trigger})
THEN
ADD ({var.name} selected {trigger})
END""")
            allowed = tuple((Number(v),) for v in range(3) if v != rng.randrange(3))
            # At least one permitted value; independent witnesses need not agree.
            if not allowed:
                allowed = ((Number(0),),)
            constraints.append(
                GuardedConstraint(
                    Atom(f"g{index}"),
                    flag,
                    TableConstraint(Atom(f"t{index}"), (target,), allowed),
                )
            )
        model = FiniteModel(
            f"generated_{instance}",
            tuple(FiniteVariable(v, tuple(Number(i) for i in range(3))) for v in names),
            tuple(constraints),
            rules=parse_rule_groups("GROUP g\n" + "\n".join(rules) + "\nEND_GROUP"),
        )
        complete = enumerate_model(model, Query(QueryKind.ENUMERATE)).solutions
        state = MixedState(model)
        assert state.propagate()

        def visit(depth, state=state, model=model, complete=complete):
            before = state.domains.snapshot(), state.session.snapshot()
            checkpoint = state.checkpoint()
            for _ in range(3):
                state.rollback(checkpoint)
                assert state.domains.snapshot() == before[0]
                assert state.session.snapshot().facts == before[1].facts
                assert state.session.snapshot().derivations == before[1].derivations
                unresolved = [v for v in names if state.domains.size(v) > 1]
                if not unresolved:
                    break
                var = rng.choice(unresolved)
                value = rng.choice(state.domains.values(var))
                state.restrict(var, value)
                before_propagation = state.domains.snapshot()
                supported = [
                    s
                    for s in complete
                    if all(s.assignment[v] in before_propagation[v] for v in names)
                ]
                consistent = state.propagate()
                if not consistent:
                    assert not supported
                else:
                    assert all(
                        all(s.assignment[v] in state.domains.values(v) for v in names)
                        for s in supported
                    )
                    singleton = {
                        v: state.domains.values(v)[0]
                        for v in names
                        if state.domains.size(v) == 1
                    }
                    assert state.closed_facts() == reference_closure(model, singleton)
                    if depth:
                        visit(depth - 1)
            state.rollback(checkpoint)
            state.release(checkpoint)
            assert state.domains.snapshot() == before[0]
            assert state.session.snapshot().derivations == before[1].derivations

        visit(3)
