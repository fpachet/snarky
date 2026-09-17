"""NValue crosses text, legacy propagation, mixed rules and factor boundaries."""

from dataclasses import replace

import pytest

from snarky import Atom, Fact, Number, Triple, parse_rule_groups
from snarky.finite import (
    FactorObjective,
    FiniteModel,
    FiniteVariable,
    GuardedConstraint,
    Measure,
    NValueConstraint,
    Query,
    QueryKind,
    TableFactor,
    enumerate_model,
    infer,
    parse_model_document,
    solve,
)
from snarky.finite.bounds import ChainBound, NoObjectiveCompletion
from snarky.finite.mixed import MixedState
from snarky.finite.search import search


def test_legacy_removal_explanations_and_domains_restore_after_rollback():
    from csp_solver import CandidateRemovalExplanation, PersistentConstraintPropagator
    from csp_solver.solver import CANDIDATE
    from snarky import ForwardEngine
    from tests.test_persistent_constraints import _domain_facts

    problem, x, y = map(Atom, ("rollback_nvalue", "x", "y"))
    session = ForwardEngine(()).create_session(
        _domain_facts(problem, {x: (1, 2), y: (1, 2)})
    )
    constraint = NValueConstraint(Atom("one_color"), (x, y), 1)
    propagator = PersistentConstraintPropagator(problem, (constraint,))
    propagator(session)
    before = set(session.facts)
    for chosen in (1, 2, 1):
        checkpoint = session.checkpoint()
        removed = Number(3 - chosen)
        session.retract(Fact(Triple(x, CANDIDATE, removed)), label="decision")
        propagator(session)
        assert Fact(Triple(y, CANDIDATE, removed)) not in session.facts
        assert propagator.removal_explanations(session) == (
            CandidateRemovalExplanation(y, removed, constraint.name),
        )
        session.rollback(checkpoint)
        session.release(checkpoint)
        propagator(session)
        assert set(session.facts) == before
        assert propagator.removal_explanations(session) == ()


def test_variable_count_optimization_and_exact_measure_match_enumeration():
    x, y, k = map(Atom, ("x", "y", "k"))
    model = FiniteModel(
        "count",
        tuple(FiniteVariable(v, (Number(1), Number(2))) for v in (x, y, k)),
        (NValueConstraint(Atom("n"), (x, y, k), k),),
        objective=FactorObjective(
            (TableFactor("cost", (k,), {(Number(1),): 3, (Number(2),): -5}),)
        ),
        measure=Measure(),
    )
    for kind in (QueryKind.MINIMIZE, QueryKind.MAXIMIZE):
        expected = enumerate_model(model, Query(kind))
        for bounding in ("local", "chain"):
            result = solve(model, Query(kind), bounding=bounding)
            assert result.complete
            assert (
                result.incumbent.objective_value == expected.incumbent.objective_value
            )
    measured = replace(model, objective=None)
    expected = infer(measured, backend="enumeration")
    result = infer(measured, backend="weighted_search")
    assert result.inference.partition == expected.inference.partition
    assert result.inference.marginals == expected.inference.marginals


def test_model_text_count_variable_constants_empty_scope_and_formatting():
    from snarky.formatting import format_source

    source = """MODEL colors
VARIABLE x DOMAIN SEQ[red blue]
VARIABLE k DOMAIN SEQ[1 2]
CONSTRAINT colors
KIND NVALUE
SCOPE SEQ[x x]
TARGET k
CONSTANTS SEQ[red]
END_CONSTRAINT
CONSTRAINT empty
KIND NVALUE
SCOPE SEQ[]
TARGET 0
END_CONSTRAINT
END_MODEL
"""
    model = parse_model_document(source).model
    assert parse_model_document(format_source(source)).model == model
    result = solve(model, Query(QueryKind.ENUMERATE))
    assert result.complete
    assert {
        (s.assignment[Atom("x")], s.assignment[Atom("k")]) for s in result.solutions
    } == {(Atom("red"), Number(1)), (Atom("blue"), Number(2))}


def test_fact_templates_and_legacy_session_propagation():
    from csp_solver import (
        FiniteCSP,
        instantiate_constraint_templates,
        parse_constraint_templates,
        solve_finite_csp,
    )
    from csp_solver.solver import (
        CANDIDATE,
        CSP_PROBLEM,
        CSP_VARIABLE,
        KIND,
        VARIABLE,
        assignment_from_solution,
    )

    problem, x, y, k = map(Atom, ("p", "x", "y", "k"))
    facts = [Fact(Triple(problem, KIND, CSP_PROBLEM))]
    for var, values in ((x, (1, 2)), (y, (2,)), (k, (1,))):
        facts.extend(
            [
                Fact(Triple(problem, VARIABLE, var)),
                Fact(Triple(var, KIND, CSP_VARIABLE)),
            ]
        )
        facts.extend(Fact(Triple(var, CANDIDATE, Number(value))) for value in values)
    facts.extend(Fact(Triple(problem, Atom("scoped"), v)) for v in (x, y))
    template = parse_constraint_templates("""CONSTRAINT colors
KIND NVALUE
SCOPE $v
FROM
(p scoped $v)
END_SCOPE
TARGET k
END
""")
    constraints = instantiate_constraint_templates(template, facts)
    assert constraints == (NValueConstraint(Atom("colors"), (x, y), k),)
    result = solve_finite_csp(
        FiniteCSP(problem, tuple(facts), {}, constraints=constraints)
    )
    assert len(result.solutions) == 1
    assignment = assignment_from_solution(result.solutions[0], problem)
    assert assignment[x] == assignment[y] == Number(2)


def test_guarded_mixed_nvalue_matches_oracle_and_restores_after_observer_failure():
    x, y = map(Atom, ("x", "y"))
    (group,) = parse_rule_groups("""GROUP switch
RULE chosen
WHEN
(x value 1)
THEN
ADD (switch mode single)
END
END_GROUP""")
    model = FiniteModel(
        "mixed",
        tuple(FiniteVariable(v, (Number(1), Number(2))) for v in (x, y)),
        (
            GuardedConstraint(
                Atom("guard"),
                Fact(Triple(Atom("switch"), Atom("mode"), Atom("single"))),
                NValueConstraint(Atom("n"), (x, y), 1),
            ),
        ),
        rules=(group,),
    )
    query = Query(QueryKind.ENUMERATE)

    def project(result):
        return {
            (tuple(s.assignment[v] for v in (x, y)), s.facts) for s in result.solutions
        }

    assert project(solve(model, query)) == project(enumerate_model(model, query))
    state = MixedState(model)
    before = state.domains.snapshot()
    facts = tuple(state.session.facts)

    def interrupt(event):
        if event.event == "finished":
            raise RuntimeError("interrupted")

    with pytest.raises(RuntimeError):
        search(state, query, on_progress=interrupt)
    assert state.domains.snapshot() == before and tuple(state.session.facts) == facts


@pytest.mark.parametrize("count", [0, 1])
def test_zero_arity_nvalue_in_objective_bounds_and_exact_inference(count):
    x = Atom("x")
    model = FiniteModel(
        "constant",
        (FiniteVariable(x, (Number(1), Number(2))),),
        (NValueConstraint(Atom("n"), (), count),),
        objective=FactorObjective(
            (TableFactor("cost", (x,), {(Number(1),): 3, (Number(2),): 5}),)
        ),
        measure=Measure(),
    )
    bound = ChainBound(model, 1, cache_limit=100)
    if count:
        with pytest.raises(NoObjectiveCompletion):
            bound(model.domains)
    else:
        assert bound(model.domains) == (3, 5)
    result = solve(model, Query(QueryKind.MINIMIZE), bounding="chain")
    assert result.complete and (result.incumbent is None) == bool(count)
    query = Query(QueryKind.PARTITION)
    result = infer(replace(model, objective=None), query, backend="weighted_search")
    assert result.complete
    pytest.importorskip("vo_regular_bp")
    regular = infer(replace(model, objective=None), query, backend="regular_bp")
    assert regular.status == result.status
    if not count:
        assert regular.inference.partition == result.inference.partition
