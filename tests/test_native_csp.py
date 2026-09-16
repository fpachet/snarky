"""Native domains, support filtering, and search checked against independent oracles."""

from dataclasses import replace
from itertools import product
from random import Random

import pytest

from csp_solver.magic_square import magic_square_facts
from csp_solver.native import native_model
from csp_solver.persistent_constraints import TableConstraint as LegacyTable
from snarky import Atom, Fact, ForwardEngine, Number, Status, Triple
from snarky.finite import (
    FiniteModel,
    FiniteVariable,
    LinearObjective,
    Query,
    QueryKind,
    ResultStatus,
    Termination,
    enumerate_model,
    solve,
)
from snarky.finite.constraints import (
    AllDifferentConstraint,
    BinaryComparisonConstraint,
    BinaryComparisonOperator,
    ConstraintOperator,
    CountConstraint,
    ElementConstraint,
    GlobalCardinalityConstraint,
    LexLessEqualConstraint,
    LinearSumConstraint,
    SumConstraint,
    TableConstraint,
)
from snarky.finite.domains import FiniteDomains
from snarky.finite.predicates import accepts
from snarky.finite.propagation import NativeState
from snarky.finite.search import search

X, Y, Z = (Atom(name) for name in ("x", "y", "z"))


def variables(names=(X, Y, Z), values=(0, 1, 2)):
    return tuple(FiniteVariable(var, tuple(map(Number, values))) for var in names)


def test_nested_domain_checkpoints_restore_reasons_and_reject_stale_handles():
    domains = FiniteDomains(variables())
    initial = domains.snapshot()
    root = domains.checkpoint()
    domains.retain(X, {Number(0), Number(1)}, Atom("outer"))
    outer = domains.snapshot()
    inner = domains.checkpoint()
    domains.retain(X, {Number(1)}, Atom("inner"))
    domains.retain(Y, set(), Atom("failure"))
    assert domains.empty
    domains.rollback(inner)
    assert domains.snapshot() == outer and not domains.empty
    assert [removal.cause for removal in domains.removals] == [Atom("outer")]
    domains.rollback(root)
    assert domains.snapshot() == initial and domains.removals == ()
    with pytest.raises(ValueError, match="abandoned"):
        domains.rollback(inner)
    with pytest.raises(ValueError, match="foreign"):
        FiniteDomains(variables()).rollback(root)
    domains.release(root)
    with pytest.raises(ValueError, match="released"):
        domains.rollback(root)


def test_bitset_table_supports_match_exhaustive_rows_after_sibling_rollbacks():
    allowed = ((Number(0), Number(1)), (Number(1), Number(2)), (Number(2), Number(0)))
    model = FiniteModel(
        "table", variables((X, Y)), (TableConstraint(Atom("allowed"), (X, Y), allowed),)
    )
    state = NativeState(model)
    assert state.propagate()
    checkpoint = state.checkpoint()
    for left in (2, 0, 1, 2):
        state.restrict(X, Number(left))
        assert state.propagate()
        expected = {row[1] for row in allowed if row[0] == Number(left)}
        assert set(state.domains.values(Y)) == expected
        state.rollback(checkpoint)
    state.release(checkpoint)


def test_checkpoint_before_first_propagation_requeues_all_constraints():
    model = FiniteModel(
        "root", variables((X, Y), (1, 2)), (SumConstraint(Atom("sum"), (X, Y), 2),)
    )
    state = NativeState(model)
    checkpoint = state.checkpoint()
    assert state.propagate() and state.domains.complete
    state.rollback(checkpoint)
    assert state.domains.size(X) == 2
    assert state.propagate() and state.domains.complete


def test_native_csp_does_not_create_an_inference_session(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("pure CSP must not create an inference session")

    monkeypatch.setattr(ForwardEngine, "create_session", forbidden)
    model = FiniteModel(
        "native", variables(), (AllDifferentConstraint(Atom("different"), (X, Y, Z)),)
    )
    result = solve(model, Query(QueryKind.ENUMERATE))
    assert result.complete and len(result.solutions) == 6
    assert LegacyTable is TableConstraint


def test_generated_native_solution_sets_and_optima_match_enumeration():
    rng = Random(250916)
    for case in range(30):
        allowed = tuple(
            row
            for row in product(map(Number, range(3)), repeat=2)
            if rng.random() < 0.5
        ) or ((Number(0), Number(0)),)
        model = FiniteModel(
            f"case{case}",
            variables(),
            (
                TableConstraint(Atom("table"), (X, Y), allowed),
                LinearSumConstraint(
                    Atom("bound"),
                    ((2, X), (-1, Y), (3, Z)),
                    ConstraintOperator.LESS_EQUAL,
                    rng.randrange(-1, 8),
                ),
            ),
            objective=LinearObjective(((rng.randrange(-3, 4), X), (-2, Y), (1, Z)), -5),
        )
        expected = enumerate_model(model, Query(QueryKind.ENUMERATE))
        actual = solve(model, Query(QueryKind.ENUMERATE))

        def project(result):
            return {
                tuple(s.assignment[var] for var in (X, Y, Z)) for s in result.solutions
            }

        assert project(actual) == project(expected)
        for kind in (QueryKind.MINIMIZE, QueryKind.MAXIMIZE):
            oracle = enumerate_model(model, Query(kind))
            for order in ((X, Y, Z), (Z, Y, X)):
                result = solve(
                    model,
                    Query(kind),
                    variable_order=order,
                    reverse_values=case % 2 == 0,
                )
                assert result.status == oracle.status
                assert result.objective_bound == oracle.objective_bound
                if oracle.incumbent:
                    assert (
                        result.incumbent.objective_value
                        == oracle.incumbent.objective_value
                    )


def test_native_limits_keep_global_bound_and_improving_incumbents():
    model = FiniteModel(
        "budget", variables((X,), (3, 2, 1)), objective=LinearObjective(((1, X),))
    )
    result = solve(model, Query(QueryKind.MINIMIZE, max_nodes=3))
    assert result.status is ResultStatus.FEASIBLE
    assert result.termination is Termination.NODE_LIMIT
    assert result.incumbent.objective_value == 2
    assert result.incumbent_values == (3, 2)
    assert result.objective_bound == 1
    unknown = solve(model, Query(QueryKind.MINIMIZE, max_nodes=1))
    assert unknown.status is ResultStatus.UNKNOWN
    assert not unknown.solutions and unknown.objective_bound == 1
    final = solve(model, Query(QueryKind.MINIMIZE))
    assert final.status is ResultStatus.OPTIMAL and final.objective_bound == 1


def test_search_restores_caller_state_on_early_solution_or_limit():
    state = NativeState(
        FiniteModel(
            "restore", variables(), (AllDifferentConstraint(Atom("ad"), (X, Y, Z)),)
        )
    )
    before = state.domains.snapshot()
    for query in (Query(), Query(QueryKind.ENUMERATE, max_nodes=2)):
        search(state, query)
        assert state.domains.snapshot() == before
        assert state.domains.removals == ()


def test_adapter_solves_existing_magic_square_model_and_preserves_all_solutions():
    model = native_model(magic_square_facts(3))
    result = solve(model, Query(QueryKind.ENUMERATE))
    assert result.complete and len(result.solutions) == 8
    for solution in result.solutions:
        grid = [
            [solution.assignment[Atom(f"cell_{r}_{c}")].value for c in range(1, 4)]
            for r in range(1, 4)
        ]
        assert sorted(value for row in grid for value in row) == list(range(1, 10))
        assert all(sum(row) == 15 for row in grid)
        assert all(sum(grid[r][c] for r in range(3)) == 15 for c in range(3))
        assert sum(grid[i][i] for i in range(3)) == 15
        assert sum(grid[i][2 - i] for i in range(3)) == 15


def test_branch_pruning_counts_propagation_fixed_objective_variables():
    model = FiniteModel(
        "fixed",
        variables((X, Y), (1, 2, 3)),
        (
            TableConstraint(
                Atom("channel"),
                (X, Y),
                (
                    (Number(1), Number(3)),
                    (Number(2), Number(1)),
                ),
            ),
        ),
        objective=LinearObjective(((1, X), (4, Y))),
    )
    result = solve(model, Query(QueryKind.MINIMIZE))
    assert result.status is ResultStatus.OPTIMAL
    assert result.incumbent.objective_value == 6
    assert result.incumbent.assignment[Y] == Number(1)
    empty = solve(
        replace(model, variables=(FiniteVariable(X, ()), model.variables[1])),
        Query(QueryKind.MINIMIZE),
    )
    assert empty.status is ResultStatus.INFEASIBLE


def test_iterative_search_handles_more_variables_than_python_recursion_limit():
    model = FiniteModel(
        "deep",
        variables(
            tuple(Atom(f"var_{index}") for index in range(1100)),
            (0, 1),
        ),
    )
    result = solve(model)
    assert result.status is ResultStatus.FEASIBLE
    assert len(result.incumbent.assignment) == 1100


def test_legacy_adapter_respects_fact_status():
    legacy = magic_square_facts(3)
    false_candidate = Fact(
        Triple(Atom("cell_1_1"), Atom("candidate"), Number(99)),
        Status.FAUX,
    )
    model = native_model(replace(legacy, facts=(*legacy.facts, false_candidate)))
    assert Number(99) not in model.domains[Atom("cell_1_1")]
    assert false_candidate in model.context


W = Atom("w")


@pytest.mark.parametrize(
    "constraint",
    (
        AllDifferentConstraint(Atom("ad"), (X, Y, Z)),
        SumConstraint(Atom("sum"), (X, Y, Z), 6),
        LinearSumConstraint(
            Atom("linear"), ((2, X), (-3, Y), (1, Z)), ConstraintOperator.EQUAL, 0
        ),
        BinaryComparisonConstraint(
            Atom("less"), X, Y, BinaryComparisonOperator.LESS_THAN
        ),
        BinaryComparisonConstraint(
            Atom("le"), X, Y, BinaryComparisonOperator.LESS_EQUAL
        ),
        BinaryComparisonConstraint(
            Atom("ne"), X, Y, BinaryComparisonOperator.NOT_EQUAL
        ),
        ElementConstraint(Atom("element"), X, (Y, Z), W),
        CountConstraint(
            Atom("count"), (X, Y, Z), Number(2), ConstraintOperator.EQUAL, 2
        ),
        GlobalCardinalityConstraint(Atom("gcc"), (X, Y, Z), ((Number(1), 1, 2),)),
        TableConstraint(
            Atom("table"),
            (X, Y),
            (
                (Number(1), Number(2)),
                (Number(2), Number(3)),
                (Number(3), Number(1)),
            ),
        ),
        LexLessEqualConstraint(Atom("lex"), (X, Y), (Z, W)),
        LexLessEqualConstraint(Atom("alias"), (X, Y), (Y, Z)),
    ),
)
def test_every_native_constraint_preserves_exhaustive_support_and_rollback(constraint):
    rng = Random(918)
    for _ in range(30):
        choices = tuple(
            FiniteVariable(
                var,
                tuple(Number(value) for value in (1, 2, 3) if rng.random() < 0.7)
                or (Number(1),),
            )
            for var in constraint.variables
        )
        model = FiniteModel("oracle", choices, (constraint,))
        assignments = [
            dict(zip(constraint.variables, values, strict=True))
            for values in product(*(var.domain for var in choices))
        ]
        expected = [
            assignment for assignment in assignments if accepts(constraint, assignment)
        ]
        state = NativeState(model)
        consistent = state.propagate()
        if expected:
            assert consistent
            for var in constraint.variables:
                supported = {assignment[var] for assignment in expected}
                actual = set(state.domains.values(var))
                assert supported <= actual
                if constraint.name != Atom("alias"):
                    assert actual == supported
        elif constraint.name != Atom("alias"):
            assert not consistent
        if not consistent:
            continue
        before = state.domains.snapshot()
        reasons = state.domains.removals
        checkpoint = state.checkpoint()
        var = constraint.variables[0]
        for value in state.domains.values(var):
            state.restrict(var, value)
            state.propagate()
            state.rollback(checkpoint)
            assert state.domains.snapshot() == before
            assert state.domains.removals == reasons
        state.release(checkpoint)
