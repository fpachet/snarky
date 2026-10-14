"""Differential and exhaustive checks for native/model-specialized fixpoints."""

from itertools import product
from random import Random
from shutil import which

import pytest

from snarky import Atom, Number
from snarky.finite.constraints import (
    AllDifferentConstraint,
    ConstraintOperator,
    LinearSumConstraint,
)
from snarky.finite.model import FiniteModel, FiniteVariable
from snarky.finite.propagation import NativeState

from .model_batch import BatchContext, BatchKernel, ModelSpec, PythonEpisode


@pytest.fixture(scope="module")
def generic(tmp_path_factory):
    if which("cc") is None:
        pytest.skip("native batching experiment requires cc")
    return BatchKernel.build_model(
        tmp_path_factory.mktemp("batch_generic") / "generic.so"
    )[0]


def build(tmp_path, model, generic):
    spec = ModelSpec(model)
    special, _ = BatchKernel.build_model(tmp_path / f"{spec.key}.so", spec)
    return (
        spec,
        BatchContext(spec, generic, audit=True),
        BatchContext(spec, special, audit=True),
    )


def check(spec, generic, special, masks, reference):
    a, b, p = generic.run(masks), special.run(masks), reference.run(masks)
    assert a == b
    assert all(a[k] == p[k] for k in p), (a, p)
    native = NativeState(spec.model)
    for variable, mask in zip(spec.model.variables, masks, strict=True):
        native.domains.retain_mask(variable.name, mask, Atom("capture"))
    assert native.propagate() == a["consistent"]
    if a["consistent"]:
        assert tuple(native.domains._masks) == a["masks"]
    return a


@pytest.mark.parametrize("seed", [141026, 151026, 161026])
def test_random_fixpoints_holes_unsat_and_restored_domains(tmp_path, generic, seed):
    rng = Random(seed)
    for trial in range(5):
        shift = 10**80 if trial % 2 else 0
        variables = tuple(
            FiniteVariable(
                Atom(f"x{i}"),
                tuple(Number(shift + v) for v in rng.sample(range(-3, 8), 4)),
            )
            for i in range(rng.randrange(2, 7))
        )
        names = [v.name for v in variables]
        constraints = [AllDifferentConstraint(Atom("a"), tuple(names))]
        for j in range(3):
            scope = rng.sample(range(len(names)), rng.randrange(1, len(names) + 1))
            coefficients = [rng.choice([-3, -1, 1, 2]) for _ in scope]
            target = sum(
                c * variables[i].domain[0].value
                for i, c in zip(scope, coefficients, strict=True)
            ) + rng.randrange(-5, 6)
            constraints.append(
                LinearSumConstraint(
                    Atom(f"s{j}"),
                    tuple(
                        (c, names[i]) for i, c in zip(scope, coefficients, strict=True)
                    ),
                    rng.choice(list(ConstraintOperator)),
                    target,
                )
            )
        spec, g, s = build(
            tmp_path, FiniteModel("random", variables, tuple(constraints)), generic
        )
        reference = PythonEpisode(spec)
        for _ in range(18):
            masks = tuple(rng.randrange(1 << 4) for _ in variables)
            for current in (masks, spec.full, masks):
                check(spec, g, s, current, reference)


def test_exhaustive_small_model_preserves_every_solution(tmp_path, generic):
    variables = tuple(
        FiniteVariable(Atom(f"x{i}"), tuple(map(Number, [-2, 0, 1, 3])))
        for i in range(3)
    )
    names = tuple(v.name for v in variables)
    model = FiniteModel(
        "oracle",
        variables,
        (
            AllDifferentConstraint(Atom("a"), names),
            LinearSumConstraint(
                Atom("s"),
                ((2, names[0]), (-1, names[1]), (1, names[2])),
                ConstraintOperator.EQUAL,
                1,
            ),
        ),
    )
    spec, g, s = build(tmp_path, model, generic)
    reference = PythonEpisode(spec)
    for masks in product(range(1, 16), repeat=3):
        result = check(spec, g, s, masks, reference)
        for selected in product(
            *[[j for j in range(4) if mask & (1 << j)] for mask in masks]
        ):
            values = [variables[i].domain[j].value for i, j in enumerate(selected)]
            if len(set(values)) == 3 and 2 * values[0] - values[1] + values[2] == 1:
                assert result["consistent"]
                assert all(
                    result["masks"][i] & (1 << j) for i, j in enumerate(selected)
                )


def test_large_word_boundaries_and_warm_reconciliation(tmp_path, generic):
    variables = tuple(
        FiniteVariable(Atom(f"x{i}"), tuple(map(Number, range(130)))) for i in range(4)
    )
    names = tuple(v.name for v in variables)
    model = FiniteModel(
        "words",
        variables,
        (
            AllDifferentConstraint(Atom("a"), names),
            LinearSumConstraint(
                Atom("s"), tuple((1, v) for v in names), ConstraintOperator.EQUAL, 256
            ),
        ),
    )
    spec, g, s = build(tmp_path, model, generic)
    reference = PythonEpisode(spec)
    cases = [
        spec.full,
        tuple(
            sum(1 << p for p in ps)
            for ps in [(0, 63, 64), (1, 64, 127), (2, 65, 128), (3, 66, 129)]
        ),
    ]
    for masks in cases * 3:
        expected = reference.run(masks)
        a = g.run(masks, reset=False)
        b = s.run(masks, reset=False)
        assert a == b
        assert a["consistent"] == expected["consistent"]
        if a["consistent"]:
            assert a["masks"] == expected["masks"]


def test_mismatched_library_invalid_input_and_interruption_are_rejected(
    tmp_path, generic
):
    variables = (FiniteVariable(Atom("x"), (Number(0), Number(1))),)
    c = LinearSumConstraint(Atom("s"), ((1, Atom("x")),), ConstraintOperator.EQUAL, 0)
    spec, g, s = build(tmp_path, FiniteModel("x", variables, (c,)), generic)
    other = ModelSpec(
        FiniteModel(
            "y", variables, (LinearSumConstraint(Atom("s"), c.terms, c.operator, 1),)
        )
    )
    with pytest.raises(ValueError, match="another model"):
        BatchContext(other, s.kernel)
    with pytest.raises(ValueError, match="alphabet"):
        g.run((4,))
    with pytest.raises(RuntimeError, match="interrupted"):
        g.run(spec.full, max_revisions=1)
    g.log_capacity = 0
    with pytest.raises(RuntimeError, match="interrupted"):
        g.run(spec.full)
    g.log_capacity = sum(spec.lengths)
    assert g.run(spec.full)["masks"] == (1,)
    with pytest.raises(ValueError):
        ModelSpec(
            FiniteModel(
                "symbols",
                (FiniteVariable(Atom("x"), (Atom("a"),)),),
                (AllDifferentConstraint(Atom("a"), (Atom("x"),)),),
            )
        )


def test_search_adapter_enumeration_causes_and_rollback(tmp_path, generic):
    from dataclasses import replace
    from time import perf_counter

    from snarky.finite.model import Query, QueryKind
    from snarky.finite.search import search

    from .model_batch import BatchNative

    variables = tuple(
        FiniteVariable(Atom(f"x{i}"), tuple(map(Number, range(4)))) for i in range(3)
    )
    names = tuple(v.name for v in variables)
    model = FiniteModel(
        "search",
        variables,
        (
            AllDifferentConstraint(Atom("different"), names),
            LinearSumConstraint(
                Atom("sum"), tuple((1, v) for v in names), ConstraintOperator.EQUAL, 4
            ),
        ),
    )
    spec, g, s = build(tmp_path, model, generic)
    states = [BatchNative(model, spec, k) for k in (g.kernel, s.kernel)]
    for state in states:
        point = state.checkpoint()
        state.restrict(names[0], Number(0))
        expected = PythonEpisode(spec).run(tuple(state.domains._masks))
        assert state.propagate() == expected["consistent"]
        assert tuple(state.domains._masks) == expected["masks"]
        assert [
            (spec.names.index(r.variable), r.cause) for r in state.domains.removals[1:]
        ] == [(v, model.constraints[c].name) for c, v, _ in expected["log"]]
        state.rollback(point)
        assert state.domains.snapshot() == model.domains
        assert not state.domains.removals
        with pytest.raises(TimeoutError):
            state.propagate(deadline=perf_counter() - 1)
        state.rollback(point)
        state.release(point)
    a, b = (
        search(state, Query(kind=QueryKind.ENUMERATE, max_solutions=None))
        for state in states
    )
    assert replace(a, elapsed_seconds=0) == replace(b, elapsed_seconds=0)
    observed = {tuple(s.assignment[v].value for v in names) for s in a.solutions}
    expected = {
        values
        for values in product(range(4), repeat=3)
        if len(set(values)) == 3 and sum(values) == 4
    }
    assert observed == expected
