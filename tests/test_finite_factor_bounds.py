"""Rule-factor bounds stay admissible across partial domains and alternative proofs."""

from dataclasses import replace
from itertools import product
from time import perf_counter

import pytest

from snarky import Atom, Fact, Number, Triple, Variable, parse_rule_groups
from snarky.factors import FactorDefinition
from snarky.finite import (
    FactorObjective,
    FiniteModel,
    IntegerFactor,
    Query,
    QueryKind,
    TableFactor,
    enumerate_model,
    solve,
)
from snarky.finite.closure import reference_closure
from snarky.finite.factor_bounds import compile_positive_factor_bound
from snarky.premises import FactPremise, NotExistsPremise
from tests.test_finite_scheduling import X, Y, variable


def model(weight):
    rules = parse_rule_groups("""
    GROUP positive
        RULE via_x
        WHEN
            (x value 1)
        THEN
            ADD (item eligible yes)
        END
        RULE via_y
        WHEN
            (y value 1)
        THEN
            ADD (item eligible yes)
        END
        RULE cycle_a
        WHEN
            (item eligible yes)
        THEN
            ADD (item selected yes)
        END
        RULE cycle_b
        WHEN
            (item selected yes)
        THEN
            ADD (item eligible yes)
        END
    END_GROUP
    """)
    factor = IntegerFactor(
        FactorDefinition(
            "preference",
            Variable("owner"),
            (
                FactPremise(Triple(Atom("item"), Atom("selected"), Atom("yes"))),
                FactPremise(
                    Triple(Variable("owner"), Atom("witness"), Variable("witness"))
                ),
            ),
        ),
        weight,
    )
    return FiniteModel(
        "bounds",
        (variable(X, [0, 1]), variable(Y, [0, 1])),
        context=tuple(
            Fact(Triple(Atom(owner), Atom("witness"), Atom(witness)))
            for owner, witness in (("a", "p"), ("a", "q"), ("b", "r"))
        ),
        rules=rules,
        objective=FactorObjective(
            (factor, TableFactor("operation", (X,), {(Number(1),): 3})), offset=7
        ),
    )


@pytest.mark.parametrize("weight", [-(10**25), -5, 0, 5, 10**25])
def test_bounds_enclose_all_completions_and_are_exact_on_singletons(weight):
    m = model(weight)
    bound = compile_positive_factor_bound(m)
    assert bound is not None
    subsets = (
        frozenset([Number(0)]),
        frozenset([Number(1)]),
        frozenset([Number(0), Number(1)]),
    )
    # Reversed/repeated order exercises caches across unrelated sibling branches.
    cases = list(product(subsets, repeat=2))
    for dx, dy in cases + cases[::-1]:
        domains = {X: dx, Y: dy}
        scores = []
        for x, y in product(dx, dy):
            assignment = {X: x, Y: y}
            scores.append(
                m.objective.evaluate(assignment, reference_closure(m, assignment))
            )
        low, high = bound(domains)
        assert low <= min(scores) <= max(scores) <= high
        if len(dx) == len(dy) == 1:
            assert low == high == scores[0]
    for kind in (QueryKind.MINIMIZE, QueryKind.MAXIMIZE):
        expected = enumerate_model(m, Query(kind)).incumbent
        for reverse in (False, True):
            actual = solve(
                m, Query(kind), reverse_values=reverse, value_policy="objective"
            ).incumbent
            assert actual.objective_value == expected.objective_value
            assert actual.contributions == m.objective.contributions(
                actual.assignment, actual.facts
            )


def test_incompatible_assignment_facts_remain_a_relaxation_not_a_proof():
    impossible = IntegerFactor(
        FactorDefinition(
            "impossible",
            Atom("scope"),
            (
                FactPremise(Triple(X, Atom("value"), Number(0))),
                FactPremise(Triple(X, Atom("value"), Number(1))),
            ),
        ),
        -5,
    )
    m = FiniteModel(
        "incompatible", (variable(X, [0, 1]),), objective=FactorObjective((impossible,))
    )
    bound = compile_positive_factor_bound(m)
    assert bound(m.domains) == (-5, 0)
    assert solve(m, Query(QueryKind.MINIMIZE)).incumbent.objective_value == 0


def test_fallback_deadline_and_interrupted_root_bound():
    m = model(5)
    assert compile_positive_factor_bound(m, budget=0) is None
    with pytest.raises(TimeoutError):
        compile_positive_factor_bound(m, deadline=perf_counter() - 1)
    unsupported = IntegerFactor(
        FactorDefinition(
            "absent",
            Atom("scope"),
            (NotExistsPremise((FactPremise(Triple(X, Atom("value"), Number(0))),)),),
        ),
        5,
    )
    m = replace(m, objective=FactorObjective((unsupported,)))
    assert compile_positive_factor_bound(m) is None
    assert (
        solve(m, Query(QueryKind.MINIMIZE)).incumbent.objective_value
        == enumerate_model(m, Query(QueryKind.MINIMIZE)).incumbent.objective_value
    )
    m = model(5)
    partial = solve(m, Query(QueryKind.MAXIMIZE, max_nodes=1))
    assert not partial.complete
    assert (
        partial.objective_bound
        >= enumerate_model(m, Query(QueryKind.MAXIMIZE)).incumbent.objective_value
    )


def test_workforce_wide_domains_prune_with_unchanged_scores():
    from benchmarks.workforce_scheduling import build_model

    m, _ = build_model(wide_starts=True)
    bound = compile_positive_factor_bound(m)
    assert bound is not None
    result = solve(
        m, Query(QueryKind.MINIMIZE, max_nodes=1000), value_policy="objective"
    )
    assert result.complete and result.incumbent.objective_value == 7
    assert result.pruned_branches > 0
    assert result.incumbent.derivations
