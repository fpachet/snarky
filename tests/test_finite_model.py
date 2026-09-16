"""Independent contracts for the new declarative finite-model surface."""

from dataclasses import replace
from itertools import product

import pytest

from snarky import (
    Atom,
    Fact,
    Number,
    Triple,
    Variable,
    parse_rule_groups,
)
from snarky.finite import (
    FactConstraint,
    FiniteModel,
    FiniteVariable,
    LinearObjective,
    PredicateConstraint,
    Query,
    QueryKind,
    ResultStatus,
    Termination,
    enumerate_model,
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
from snarky.finite.predicates import accepts

X, Y, Z = (Atom(name) for name in ("x", "y", "z"))


def test_exact_linear_optimum_matches_arithmetic_enumeration():
    model = FiniteModel(
        "allocation",
        tuple(
            FiniteVariable(var, tuple(Number(n) for n in (1, 2, 3))) for var in (X, Y)
        ),
        (AllDifferentConstraint(Atom("different"), (X, Y)),),
        objective=LinearObjective(((3, X), (-2, Y)), 7),
    )
    expected = [7 + 3 * x - 2 * y for x, y in product((1, 2, 3), repeat=2) if x != y]
    for kind, value in (
        (QueryKind.MINIMIZE, min(expected)),
        (QueryKind.MAXIMIZE, max(expected)),
    ):
        result = enumerate_model(model, Query(kind))
        assert result.status is ResultStatus.OPTIMAL
        assert result.complete
        assert result.incumbent.objective_value == value
        assert result.objective_bound == value
    enumerated = enumerate_model(model, Query(QueryKind.ENUMERATE))
    assert len(enumerated.solutions) == 6
    assert enumerated.complete
    with pytest.raises(TypeError):
        enumerated.solutions[0].assignment[X] = Number(9)


def test_all_builtin_predicates_have_direct_complete_semantics():
    assignment = {X: Number(1), Y: Number(2), Z: Number(2)}
    constraints = (
        AllDifferentConstraint(Atom("ad"), (X, Y)),
        SumConstraint(Atom("sum"), (X, Y, Z), 5),
        LinearSumConstraint(
            Atom("linear"), ((-2, X), (3, Y)), ConstraintOperator.LESS_EQUAL, 4
        ),
        BinaryComparisonConstraint(
            Atom("lt"), X, Y, BinaryComparisonOperator.LESS_THAN
        ),
        ElementConstraint(Atom("element"), X, (Y,), Z),
        CountConstraint(
            Atom("count"), (X, Y, Z), Number(2), ConstraintOperator.EQUAL, 2
        ),
        GlobalCardinalityConstraint(Atom("gcc"), (X, Y, Z), ((Number(2), 2, 2),)),
        TableConstraint(Atom("table"), (X, Y), ((Number(1), Number(2)),)),
        LexLessEqualConstraint(Atom("lex"), (X, Y), (Y, Z)),
    )
    assert all(accepts(c, assignment) for c in constraints)
    invalid = (
        (1, 1, 2),
        (1, 1, 1),
        (1, 3, 2),
        (2, 1, 1),
        (2, 2, 2),
        (1, 1, 2),
        (1, 1, 2),
        (2, 1, 2),
        (3, 2, 1),
    )
    for constraint, values in zip(constraints, invalid, strict=True):
        assignment = dict(zip((X, Y, Z), map(Number, values), strict=True))
        assert not accepts(constraint, assignment)


def test_mixed_model_closure_is_independent_of_rule_order():
    (rules,) = parse_rule_groups("""
        GROUP classify
          RULE selected
          WHEN
            ($job value 2)
          THEN
            ADD ($job selected yes)
          END
          RULE report
          WHEN
            ($job selected yes)
          THEN
            ADD ($job report ready)
          END
        END_GROUP
    """)
    required = Fact(Triple(X, Atom("report"), Atom("ready")))
    model = FiniteModel(
        "mixed",
        (FiniteVariable(X, (Number(1), Number(2))),),
        (FactConstraint(Atom("require_report"), required=(required,)),),
        rules=(rules,),
        objective=LinearObjective(((1, X),)),
    )
    first = enumerate_model(model, Query(QueryKind.MINIMIZE))
    second = enumerate_model(
        replace(model, rules=(replace(rules, rules=rules.rules[::-1]),)),
        Query(QueryKind.MINIMIZE),
    )
    assert first.status is ResultStatus.OPTIMAL
    assert first.incumbent.objective_value == 2
    assert first.solutions == second.solutions
    assert required in first.incumbent.facts


@pytest.mark.parametrize(
    "body",
    (
        "RULE bad\nWHEN\n(x value $v)\nTHEN\nREMOVE (x value $v)\nEND",
        "RULE bad\nWHEN\n(x value $v)\nTHEN\nFRESH $new\nADD ($new kind thing)\nEND",
        "RULE bad\nWHEN\n(x value $v)\nNOT EXISTS (x blocked yes)\n"
        "THEN\nADD (x ok yes)\nEND",
        "RULE bad\nWHEN\n(x value $v)\nTHEN\nADD (x nested (x nested $v))\nEND",
        "RULE bad\nWHEN\n(x value $v)\nTHEN\nADD (x value 99)\nEND",
    ),
)
def test_unsupported_scoreable_rules_are_rejected_without_changing_core_parser(body):
    groups = parse_rule_groups(f"GROUP unsupported\n{body}\nEND_GROUP")
    # All remain valid operational Core programs.
    with pytest.raises(ValueError):
        FiniteModel("unsafe", (FiniteVariable(X, (Number(1),)),), rules=groups)


def test_rule_only_models_have_one_empty_assignment_and_a_closure():
    groups = parse_rule_groups("""
        GROUP derive
          RULE copy
          WHEN
            ($item kind thing)
          THEN
            ADD ($item visible yes)
          END
        END_GROUP
    """)
    model = FiniteModel(
        "rules", context=(Fact(Triple(X, Atom("kind"), Atom("thing"))),), rules=groups
    )
    result = enumerate_model(model, Query(QueryKind.ENUMERATE))
    assert result.complete and len(result.solutions) == 1
    assert result.incumbent.assignment == {}
    assert Fact(Triple(X, Atom("visible"), Atom("yes"))) in result.incumbent.facts


def test_limits_preserve_incumbents_and_never_claim_an_unproved_optimum():
    model = FiniteModel(
        "limited",
        (FiniteVariable(X, (Number(3), Number(2), Number(1))),),
        objective=LinearObjective(((1, X),)),
    )
    limited = enumerate_model(model, Query(QueryKind.MINIMIZE, max_nodes=2))
    assert limited.status is ResultStatus.FEASIBLE
    assert limited.termination is Termination.NODE_LIMIT
    assert limited.incumbent.objective_value == 2
    assert limited.objective_bound is None
    impossible = replace(
        model, constraints=(TableConstraint(Atom("only_one"), (X,), ((Number(1),),)),)
    )
    unknown = enumerate_model(impossible, Query(max_nodes=2))
    assert unknown.status is ResultStatus.UNKNOWN and not unknown.solutions
    assert enumerate_model(impossible).incumbent.assignment[X] == Number(1)
    assert (
        enumerate_model(model, Query(QueryKind.ENUMERATE, max_solutions=2)).complete
        is False
    )


def test_empty_domains_and_zero_variables_are_distinct():
    assert (
        enumerate_model(FiniteModel("empty_domain", (FiniteVariable(X, ()),))).status
        is ResultStatus.INFEASIBLE
    )
    empty = enumerate_model(
        FiniteModel("constant", objective=LinearObjective(offset=8)),
        Query(QueryKind.MINIMIZE),
    )
    assert empty.status is ResultStatus.OPTIMAL and empty.incumbent.objective_value == 8


def test_objective_bounds_signed_coefficients_and_large_exact_integers():
    objective = LinearObjective(((3, X), (-1, X), (-7, Y)), 10**100)
    domains = {
        X: frozenset((Number(-4), Number(8))),
        Y: frozenset((Number(-3), Number(9))),
    }
    scores = [
        objective.evaluate({X: x, Y: y}) for x, y in product(domains[X], domains[Y])
    ]
    assert objective.bounds(domains) == (min(scores), max(scores))
    assert type(objective.evaluate({X: Number(1), Y: Number(2)})) is int


def test_extension_predicate_observes_only_declared_assignment_scope():
    observed = []

    def valid(assignment, facts):
        observed.append(tuple(assignment))
        assert type(facts) is frozenset
        with pytest.raises(TypeError):
            assignment[X] = Number(8)
        return assignment[X] == Number(2)

    model = FiniteModel(
        "extension",
        (FiniteVariable(X, (Number(1), Number(2))), FiniteVariable(Y, (Number(0),))),
        (PredicateConstraint(Atom("custom"), (X,), valid),),
    )
    result = enumerate_model(model)
    assert result.incumbent.assignment[X] == Number(2)
    assert observed == [(X,), (X,)]


def test_model_validation_and_unsupported_queries_fail_explicitly():
    with pytest.raises(TypeError, match="Snarky terms"):
        FiniteVariable(X, (None,))
    with pytest.raises(ValueError, match="ground"):
        FiniteVariable(X, (Variable("unbound"),))
    with pytest.raises(ValueError, match="duplicate"):
        FiniteModel("duplicate", (FiniteVariable(X, ()), FiniteVariable(X, ())))
    with pytest.raises(ValueError, match="undeclared"):
        FiniteModel("missing", objective=LinearObjective(((1, X),)))
    with pytest.raises(TypeError, match="integer"):
        FiniteModel(
            "float",
            (FiniteVariable(X, (Number(1.2),)),),
            objective=LinearObjective(((1, X),)),
        )
    with pytest.raises(ValueError, match="value facts"):
        FiniteModel(
            "spoof",
            (FiniteVariable(X, (Number(1),)),),
            context=(Fact(Triple(X, Atom("value"), Number(2))),),
        )
    probability = enumerate_model(
        FiniteModel("probability"), Query(QueryKind.SAMPLE_EXACT)
    )
    assert probability.status is ResultStatus.FEASIBLE
    assert probability.inference.partition == 1
    assert dict(probability.incumbent.assignment) == {}
