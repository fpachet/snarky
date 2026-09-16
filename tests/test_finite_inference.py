"""Finite weighted inference checked against independent exact probability sums."""

import math
from dataclasses import replace
from fractions import Fraction
from itertools import product
from random import Random

import pytest

from snarky import Atom, Number, Triple
from snarky.factors import FactorDefinition, FactorGroup, FactorModel, factor
from snarky.finite import (
    FiniteModel,
    FiniteVariable,
    LinearObjective,
    Measure,
    Query,
    QueryKind,
    ResultStatus,
    TableFactor,
    Termination,
    WeightTable,
    enumerate_model,
    infer,
    solve,
)
from snarky.finite.constraints import AllDifferentConstraint
from snarky.finite.examples import scheduling_model
from snarky.premises import FactPremise

X, Y = Atom("x"), Atom("y")
A, B = Atom("a"), Atom("b")


def rational_model():
    return FiniteModel(
        "weighted",
        (FiniteVariable(X, (A, B)), FiniteVariable(Y, (A, B))),
        measure=Measure(
            (
                WeightTable(
                    "initial", (X,), {(A,): Fraction(1, 3), (B,): Fraction(2, 3)}
                ),
                WeightTable(
                    "transition",
                    (X, Y),
                    {
                        (A, A): Fraction(1, 4),
                        (A, B): Fraction(3, 4),
                        (B, A): Fraction(1, 2),
                        (B, B): Fraction(1, 2),
                    },
                ),
            )
        ),
    )


def test_exact_rational_joint_partition_marginals_and_conditionals():
    model = rational_model()
    expected = {
        (A, A): Fraction(1, 12),
        (A, B): Fraction(1, 4),
        (B, A): Fraction(1, 3),
        (B, B): Fraction(1, 3),
    }
    for backend in ("enumeration", "weighted_search"):
        result = infer(model, backend=backend)
        assert result.complete and result.status is ResultStatus.FEASIBLE
        assert result.arithmetic == "rational"
        distribution = result.inference
        assert distribution.partition == 1
        assert dict(distribution.rational_masses) == expected
        assert distribution.marginals[X] == {A: Fraction(1, 3), B: Fraction(2, 3)}
        assert distribution.marginals[Y] == {A: Fraction(5, 12), B: Fraction(7, 12)}
        assert distribution.conditional(Y, {X: A}) == {
            A: Fraction(1, 4),
            B: Fraction(3, 4),
        }
        assert distribution.mass({Y: A}) == Fraction(5, 12)
        assert distribution.probability({X: A, Y: B}) == Fraction(1, 4)
        assert distribution.probability({X: Atom("unknown")}) == 0
        with pytest.raises(ValueError, match="zero mass"):
            distribution.conditional(Y, {X: Atom("unknown")})
        with pytest.raises(ValueError, match="undeclared"):
            distribution.probability({Atom("bad"): A})
        with pytest.raises(TypeError):
            distribution.rational_masses[(A, A)] = 0


def test_hard_conditioning_changes_normalizer_without_changing_source():
    original = rational_model()
    conditioned = replace(
        original, constraints=(AllDifferentConstraint(Atom("different"), (X, Y)),)
    )
    distribution = solve(conditioned, Query(QueryKind.PARTITION)).inference
    assert distribution.partition == Fraction(7, 12)
    assert distribution.probability({X: A}) == Fraction(3, 7)
    assert distribution.probability({X: B}) == Fraction(4, 7)
    assert solve(original, Query(QueryKind.PARTITION)).inference.partition == 1


def test_integer_sampling_uses_completion_mass_not_local_choices():
    query = Query(QueryKind.SAMPLE_EXACT, sample_count=1200, seed=20)
    samples = solve(rational_model(), query)
    assert samples.arithmetic == "rational" and samples.complete
    assert len(samples.solutions) == 1200
    count = sum(s.assignment[Y] == A for s in samples.solutions)
    assert 440 < count < 560  # expected 500; deterministic seed, generous range
    again = solve(rational_model(), query)
    assert [s.assignment for s in samples.solutions] == [
        s.assignment for s in again.solutions
    ]
    # Very small rational masses do not become hard zero through underflow.
    tiny = replace(
        rational_model(),
        measure=Measure((WeightTable("tiny", (), {(): Fraction(1, 10**1000)}),)),
    )
    exact = solve(tiny, Query(QueryKind.PARTITION)).inference
    assert exact.partition == Fraction(4, 10**1000)
    assert exact.probability({X: A}) == Fraction(1, 2)


def test_log_scores_and_parameters_observe_mixed_closure_and_deduplicate():
    base = scheduling_model()
    overtime = FactPremise(Triple(Atom("shift"), Atom("needs"), Atom("overtime")))
    definition = FactorDefinition("late", Atom("shift"), (overtime,))
    model = replace(
        base,
        measure=Measure(
            factors=FactorModel(
                "preferences",
                (
                    FactorGroup(
                        "costs",
                        (
                            factor(
                                definition.name,
                                definition.scope,
                                definition.premises,
                                log_weight=-2,
                            ),
                        ),
                    ),
                ),
            )
        ),
    )
    reference = enumerate_model(model, Query(QueryKind.ENUMERATE))
    weights = {}
    for s in reference.solutions:
        row = tuple(s.assignment[v.name] for v in model.variables)
        weights[row] = math.exp(-2 if row[0] == Number(3) else 0)
    for backend in ("enumeration", "weighted_search"):
        result = infer(model, backend=backend)
        assert result.arithmetic == "float64_log"
        assert result.inference.partition == pytest.approx(sum(weights.values()))
        for row, weight in weights.items():
            assignment = dict(zip((v.name for v in model.variables), row, strict=True))
            assert result.inference.probability(assignment) == pytest.approx(
                weight / sum(weights.values())
            )
        assert result.inference.factor_expectations["late"] == pytest.approx(
            math.exp(-2) / sum(weights.values())
        )
    # An objective is unrelated to probabilities unless explicitly declared in Measure.
    changed = replace(model, objective=LinearObjective(((99999, Atom("delivery")),)))
    assert (
        infer(changed).inference.log_partition == infer(model).inference.log_partition
    )


def test_log_range_stability_parameter_revisions_and_float_sampling():
    variables = (FiniteVariable(X, (A, B)),)
    for offset in (-1000, 1000):
        model = FiniteModel(
            "extreme",
            variables,
            measure=Measure(
                log_tables=(
                    TableFactor("score", (X,), {(A,): offset, (B,): offset + 1}),
                )
            ),
        )
        distribution = infer(model).inference
        assert distribution.log_partition == pytest.approx(offset + math.log1p(math.e))
        assert distribution.probability({X: B}) == pytest.approx(math.e / (1 + math.e))
        assert distribution.factor_expectations["score"] == pytest.approx(
            offset + math.e / (1 + math.e)
        )
        sampled = solve(model, Query(QueryKind.SAMPLE_EXACT, sample_count=100, seed=10))
        assert len(sampled.solutions) == 100
        assert 60 < sum(s.assignment[X] == B for s in sampled.solutions) < 90
    huge = replace(
        model, measure=Measure(log_tables=(TableFactor("huge", (), {(): 10**1000}),))
    )
    assert infer(huge).status is ResultStatus.UNSUPPORTED


def test_limits_never_normalize_partial_mass_or_return_exact_samples():
    for backend in ("enumeration", "weighted_search"):
        for query in (
            Query(QueryKind.PARTITION, max_nodes=1),
            Query(QueryKind.SAMPLE_EXACT, max_nodes=1),
            Query(QueryKind.PARTITION, time_limit_seconds=1e-12),
        ):
            result = infer(rational_model(), query, backend=backend)
            assert result.status is ResultStatus.UNKNOWN
            assert result.inference is None and not result.solutions
            assert result.termination in (
                Termination.NODE_LIMIT,
                Termination.TIME_LIMIT,
            )
    assert (
        infer(rational_model(), backend="unavailable").status
        is ResultStatus.UNSUPPORTED
    )
    zero = replace(
        rational_model(), measure=Measure((WeightTable("zero", (), {(): 0}),))
    )
    result = infer(zero, Query(QueryKind.SAMPLE_EXACT))
    assert result.status is ResultStatus.ZERO_MASS and not result.solutions
    assert solve(zero).status is ResultStatus.FEASIBLE  # hard feasibility is distinct


def test_generated_rational_tables_match_explicit_fraction_sums():
    rng = Random(78)
    for _ in range(20):
        variables = tuple(FiniteVariable(Atom(f"v{i}"), (A, B)) for i in range(3))
        names = tuple(v.name for v in variables)
        entries = {
            row: Fraction(rng.randrange(5), 7) for row in product((A, B), repeat=3)
        }
        model = FiniteModel(
            "generated",
            variables,
            measure=Measure((WeightTable("joint", names, entries),)),
        )
        distribution = infer(model).inference
        total = sum(entries.values())
        assert distribution.partition == total
        for row, weight in entries.items():
            assert (
                distribution.probability(dict(zip(names, row, strict=True)))
                == weight / total
            )
