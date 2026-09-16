"""Optional sibling-library agreement, using its public product-BP API."""

from dataclasses import replace
from fractions import Fraction
from itertools import product
from random import Random

import pytest

from snarky import Atom, Number
from snarky.finite import (
    FiniteModel,
    FiniteVariable,
    Measure,
    Query,
    QueryKind,
    ResultStatus,
    TableFactor,
    Termination,
    WeightTable,
    infer,
    negative_log2_measure,
)
from snarky.finite.constraints import (
    AllDifferentConstraint,
    SumConstraint,
    TableConstraint,
)
from snarky.finite.examples import markov_probe_model, scheduling_model
from tests.test_finite_inference import A, B, X, Y, rational_model

pytest.importorskip("vo_regular_bp")


@pytest.mark.parametrize("seed", range(6))
def test_markov_map_model_has_same_scores_mass_and_conditionals_in_all_backends(seed):
    costs = markov_probe_model(seed)
    model = replace(costs, measure=negative_log2_measure(costs.objective))
    expected = infer(model, backend="enumeration").inference
    actual = infer(model, backend="regular_bp").inference
    native = infer(model).inference
    assert actual.partition == pytest.approx(float(expected.partition), abs=1e-14)
    assert native.partition == expected.partition
    for row, mass in expected.rational_masses.items():
        assignment = dict(zip((v.name for v in model.variables), row, strict=True))
        assert mass == Fraction(2) ** -model.objective.evaluate(assignment)
        assert actual.mass(assignment) == pytest.approx(float(mass), abs=1e-14)
    first, last = model.variables[0].name, model.variables[-1].name
    assert actual.conditional(last, {first: Number(1)}) == {Number(1): pytest.approx(1)}


def test_public_bp_adapter_agrees_with_rational_reference_and_sampling():
    model = rational_model()
    for constraints in ((), (AllDifferentConstraint(Atom("distinct"), (X, Y)),)):
        conditioned = replace(model, constraints=constraints)
        expected = infer(conditioned, backend="enumeration").inference
        result = infer(conditioned, backend="regular_bp")
        assert result.status is ResultStatus.FEASIBLE
        assert result.arithmetic == "float64_log"
        actual = result.inference
        assert actual.certificate == "EXACT_REGULAR_BP"
        assert actual.partition == pytest.approx(float(expected.partition))
        for sequence in product((A, B), repeat=2):
            assignment = dict(zip((X, Y), sequence, strict=True))
            assert actual.mass(assignment) == pytest.approx(
                float(expected.mass(assignment))
            )
            assert actual.probability(assignment) == pytest.approx(
                float(expected.probability(assignment))
            )
        for variable in (X, Y):
            assert actual.marginals[variable] == pytest.approx(
                expected.marginals[variable]
            )
        assert actual.conditional(Y, {X: A}) == pytest.approx(
            expected.conditional(Y, {X: A})
        )
        samples = infer(
            conditioned,
            Query(QueryKind.SAMPLE_EXACT, sample_count=100, seed=2),
            backend="regular_bp",
        )
        assert len(samples.solutions) == 100
        assert all(expected.probability(s.assignment) > 0 for s in samples.solutions)


def test_random_windows_log_scores_marginals_and_expectations():
    rng = Random(4)
    variables = tuple(
        FiniteVariable(Atom(f"x{i}"), (Number(0), Number(1))) for i in range(5)
    )
    names = tuple(v.name for v in variables)
    for _ in range(12):
        weights = tuple(
            WeightTable(
                f"w{i}",
                names[i : i + 2],
                {
                    row: Fraction(rng.randrange(1, 5), 7)
                    for row in product((Number(0), Number(1)), repeat=2)
                },
            )
            for i in range(4)
        )
        scores = (
            TableFactor("initial", names[:1], {(Number(0),): 2}, default=-1),
            TableFactor("final", names[-2:], {(Number(1), Number(1)): -3}, default=1),
            TableFactor("constant", (), {(): -3}),
        )
        model = FiniteModel(
            "windows",
            variables,
            (SumConstraint(Atom("sum"), names[:3], 1),),
            measure=Measure(weights, scores),
        )
        expected = infer(model).inference
        actual = infer(model, backend="regular_bp").inference
        assert actual.log_partition == pytest.approx(expected.log_partition, abs=1e-12)
        for assignment in product((Number(0), Number(1)), repeat=5):
            evidence = dict(zip(names, assignment, strict=True))
            assert actual.mass(evidence) == pytest.approx(expected.mass(evidence))
        assert actual.factor_expectations == pytest.approx(expected.factor_expectations)
        for var in names:
            assert actual.marginals[var] == pytest.approx(expected.marginals[var])
        # Evidence may be non-prefix; both engines sum all compatible completions.
        assert actual.conditional(names[2], {names[4]: Number(1)}) == pytest.approx(
            expected.conditional(names[2], {names[4]: Number(1)})
        )


def test_bp_limits_and_capabilities_are_explicit():
    assert (
        infer(scheduling_model(), backend="regular_bp").status
        is ResultStatus.UNSUPPORTED
    )
    variables = tuple(FiniteVariable(Atom(f"x{i}"), (A, B)) for i in range(7))
    far = FiniteModel(
        "far",
        variables,
        (
            TableConstraint(
                Atom("ends"), (variables[0].name, variables[-1].name), ((A, A),)
            ),
        ),
    )
    assert infer(far, backend="regular_bp").status is ResultStatus.UNSUPPORTED
    for query in (
        Query(QueryKind.PARTITION, max_nodes=1),
        Query(QueryKind.SAMPLE_EXACT, time_limit_seconds=1e-12),
    ):
        result = infer(rational_model(), query, backend="regular_bp")
        assert result.status is ResultStatus.UNKNOWN
        assert result.inference is None and not result.solutions
        assert result.termination in (Termination.NODE_LIMIT, Termination.TIME_LIMIT)
    extreme = replace(
        rational_model(),
        measure=Measure(
            log_tables=(TableFactor("huge", (X,), {(A,): 1000}, default=1000),)
        ),
    )
    assert infer(extreme, backend="regular_bp").status is ResultStatus.UNSUPPORTED
    assert infer(extreme).status is ResultStatus.FEASIBLE


def test_empty_zero_and_constant_weights():
    for model, expected in (
        (FiniteModel("empty"), 1),
        (
            FiniteModel(
                "constant",
                measure=Measure((WeightTable("constant", (), {(): Fraction(3, 7)}),)),
            ),
            3 / 7,
        ),
    ):
        result = infer(model, backend="regular_bp")
        assert result.inference.partition == pytest.approx(expected)
        assert result.inference.probability({}) == pytest.approx(1)
    zero = replace(
        rational_model(), measure=Measure((WeightTable("zero", (), {(): 0}),))
    )
    assert infer(zero, backend="regular_bp").status is ResultStatus.ZERO_MASS
    empty_domain = FiniteModel("no_values", (FiniteVariable(X, ()),))
    assert infer(empty_domain, backend="regular_bp").status is ResultStatus.ZERO_MASS


def test_long_chain_partition_avoids_enumerating_configurations():
    variables = tuple(FiniteVariable(Atom(f"x{i}"), (A, B)) for i in range(120))
    model = FiniteModel(
        "long",
        variables,
        measure=Measure(
            tuple(
                WeightTable(
                    f"w{i}", (var.name,), {(A,): Fraction(1, 3), (B,): Fraction(2, 3)}
                )
                for i, var in enumerate(variables)
            )
        ),
    )
    result = infer(model, backend="regular_bp")
    assert result.explored_nodes == 120
    assert result.inference.log_partition == pytest.approx(0, abs=1e-12)
    assert result.inference.marginals[variables[-1].name] == pytest.approx(
        {A: 1 / 3, B: 2 / 3}
    )
    assert result.inference.mass({variables[0].name: A}) == pytest.approx(1 / 3)
