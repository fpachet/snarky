"""Independent exhaustive checks for the experimental native residual kernels."""

import ctypes as ct
import json
import shutil
import subprocess
import sys
from itertools import product
from pathlib import Path
from random import Random

import pytest

from snarky import Atom, Number
from snarky.finite.constraints import (
    AllDifferentConstraint,
    ConstraintOperator,
    LinearSumConstraint,
)
from snarky.finite.model import FiniteModel, FiniteVariable, Query
from snarky.finite.propagation import NativeState
from snarky.finite.search import search

from .magic_residual_enumeration import Compiler, Kernel, Residual
from .magic_residual_evaluation import HybridState
from .magic_residual_jit import generate
from .magic_residual_study import product_bound


@pytest.fixture(scope="module")
def kernel(tmp_path_factory):
    if shutil.which("cc") is None:
        pytest.skip("native residual experiments require a C compiler")
    return Kernel.build(tmp_path_factory.mktemp("residual") / "enum.so")[0]


@pytest.mark.parametrize("mode", [0, 1, 2, 3, 4])
def test_native_modes_match_exhaustive_signed_sum_oracle(kernel, mode):
    rng = Random(141026)
    for _ in range(120):
        domains = tuple(
            tuple(rng.sample(range(7), rng.randrange(1, 5)))
            for _ in range(rng.randrange(1, 6))
        )
        rows = tuple(
            (
                rng.randrange(3),
                tuple(
                    (i, rng.choice((-3, -1, 1, 2)))
                    for i in rng.sample(
                        range(len(domains)), rng.randrange(len(domains) + 1)
                    )
                ),
                rng.randrange(-10, 18),
            )
            for _ in range(3)
        )
        valid = []
        for values in product(*domains):
            if len(set(values)) != len(values):
                continue
            if all(
                (
                    sum(c * values[i] for i, c in terms) == target
                    if op == 0
                    else sum(c * values[i] for i, c in terms) <= target
                    if op == 1
                    else sum(c * values[i] for i, c in terms) >= target
                )
                for op, terms, target in rows
            ):
                valid.append(values)
        run = kernel.prepare(Residual(tuple(range(len(domains))), domains, rows))
        result = run(mode, count_all=True, limit=1000000)
        assert result["status"] == bool(valid)
        assert result["solutions"] == len(valid)
        assert (
            result["witness"] is None
            if not valid
            else tuple(result["witness"]) in valid
        )
        first = run(mode, count_all=False)
        assert first["status"] == bool(valid)
        assert first["solutions"] == bool(valid)
        if valid and mode == 3:
            assert first["witness"] == list(valid[0])


def test_extraction_fixed_values_signed_coefficients_and_domain_order(kernel):
    variables = tuple(
        FiniteVariable(Atom(f"x{i}"), tuple(map(Number, d)))
        for i, d in enumerate(((4, 1, 2), (1, 2, 3), (4, 3, 2)))
    )
    names = tuple(v.name for v in variables)
    model = FiniteModel(
        "test",
        variables,
        (
            AllDifferentConstraint(Atom("d"), names),
            LinearSumConstraint(
                Atom("s"),
                ((2, names[0]), (-1, names[1]), (1, names[2])),
                ConstraintOperator.EQUAL,
                9,
            ),
        ),
    )
    compiler = Compiler(model)
    for masks in ((1, 7, 7), (7, 2, 7), (7, 7, 7), (1, 1, 1)):
        domains = [
            [int(v.value) for j, v in enumerate(var.domain) if mask & (1 << j)]
            for var, mask in zip(variables, masks, strict=True)
        ]
        valid = [
            r
            for r in product(*domains)
            if len(set(r)) == 3 and 2 * r[0] - r[1] + r[2] == 9
        ]
        result = kernel.prepare(compiler.extract(masks))(2, count_all=True)
        assert result["status"] == bool(valid)
        assert result["solutions"] == len(valid)


def test_limits_are_incomplete_and_empty_residual_is_checked(kernel):
    residual = Residual((0, 1), ((1, 2), (1, 2)), ())
    result = kernel.prepare(residual)(0, limit=0)
    assert result["status"] == 2 and not result["witness"]
    assert kernel.prepare(Residual((), (), ()))(0)["solutions"] == 1
    assert kernel.prepare(Residual((), (), ((0, (), 1),)))(0)["status"] == 0
    assert product_bound([100000000, 0]) == 0
    assert product_bound([2, 3], 6) == 6
    assert product_bound([2, 3], 5) is None


@pytest.mark.parametrize("mode", [2, 3, 4])
@pytest.mark.parametrize("limit", [0, 10, 100000])
def test_hybrid_first_solution_and_failure_match_exhaustive_oracle(kernel, limit, mode):
    rng = Random(151026)
    for _ in range(60):
        variables = tuple(
            FiniteVariable(
                Atom(f"x{i}"),
                tuple(map(Number, rng.sample(range(7), rng.randrange(1, 5)))),
            )
            for i in range(4)
        )
        names = tuple(v.name for v in variables)
        coefficients = [rng.choice((-2, -1, 1, 2)) for _ in variables]
        target = rng.randrange(-10, 20)
        model = FiniteModel(
            "oracle",
            variables,
            (
                AllDifferentConstraint(Atom("distinct"), names),
                LinearSumConstraint(
                    Atom("sum"),
                    tuple(zip(coefficients, names, strict=True)),
                    ConstraintOperator.EQUAL,
                    target,
                ),
            ),
        )
        rows = [
            r
            for r in product(*(v.domain for v in variables))
            if len(set(r)) == 4
            and sum(c * v.value for c, v in zip(coefficients, r, strict=True)) == target
        ]
        hybrid = HybridState(model, "middle", kernel, 24, mode, limit)
        actual = search(hybrid, Query())
        reference = search(NativeState(model), Query())
        assert bool(actual.solutions) == bool(reference.solutions) == bool(rows)
        assert actual.termination == reference.termination
        if rows:
            assert tuple(actual.solutions[0].assignment[v] for v in names) in rows
        assert hybrid.native.domains.snapshot() == model.domains


@pytest.mark.parametrize("case", [0, 1, 2])
def test_generated_unrolled_program_matches_native_kernel(kernel, tmp_path, case):
    cases = (
        (Residual((), (), ((0, (), 1),)), 100),
        (
            Residual(
                (0, 1, 2),
                ((3, 0, 1), (2, 0, 4), (1, 3, 4)),
                ((0, ((0, 2), (1, -1), (2, 1)), 5), (1, ((0, -3), (2, 2)), 4)),
            ),
            100000,
        ),
        (Residual((0, 1), ((1, 2), (1, 2)), ()), 0),
    )
    residual, limit = cases[case]
    source, library = tmp_path / "case.c", tmp_path / "case.so"
    source.write_text(generate(residual))
    subprocess.run(
        ["cc", "-O3", "-shared", "-fPIC", str(source), "-o", str(library)], check=True
    )
    lib = ct.CDLL(str(library))
    lib.specialized.argtypes = [
        ct.c_uint64,
        ct.POINTER(ct.c_int),
        ct.POINTER(ct.c_uint64),
    ]
    lib.specialized.restype = ct.c_int
    first = (ct.c_int * len(residual.domains))()
    counts = (ct.c_uint64 * 3)()
    expected = kernel.prepare(residual)(2, limit)
    assert lib.specialized(limit, first, counts) == expected["status"]
    assert list(counts) == [expected[k] for k in ("visits", "leaves", "solutions")]
    if expected["witness"] is not None:
        assert list(first) == expected["witness"]


@pytest.mark.parametrize("mode", [3, 4])
def test_forced_values_holes_signed_division_and_word_boundaries(kernel, mode):
    domains = ((4095, 64, 0), (63, 65, 4094))
    cases = (
        (((0, ((0, -2), (1, 1)), -65),), 1),
        (((0, ((0, 1), (1, 2)), 128),), 0),  # Required value in a hole.
        (((0, ((0, 1),), 64), (0, ((0, 1),), 0)), 0),
        (((0, ((0, 1), (1, 1)), 8189),), 1),
    )
    for rows, count in cases:
        result = kernel.prepare(Residual((0, 1), domains, rows))(mode, count_all=True)
        assert result["solutions"] == count
        assert result["status"] == bool(count)
    duplicate = Residual((0, 1), ((64, 65), (64, 65)), ((0, ((1, 1),), 64),))
    assert kernel.prepare(duplicate)(mode, count_all=True)["solutions"] == 1


def test_array_and_bitset_variants_preserve_sorted_search_and_budgets(kernel):
    rng = Random(161026)
    for _ in range(120):
        domains = tuple(
            tuple(sorted(rng.sample(range(130), rng.randrange(1, 8)))) for _ in range(5)
        )
        rows = (
            (
                0,
                tuple((i, rng.choice((-2, -1, 0, 1, 2))) for i in range(5)),
                rng.randrange(-100, 300),
            ),
        )
        run = kernel.prepare(Residual(tuple(range(5)), domains, rows))
        for limit in (0, 1, 10, 1000):
            assert run(3, limit) == run(4, limit)


def test_persistent_cache_and_source_invalidation(tmp_path):
    if shutil.which("cc") is None:
        pytest.skip("native residual experiments require a C compiler")
    cache = tmp_path / "cache"
    output = tmp_path / "first.so"
    first, cold = Kernel.build(output, cache_dir=cache)
    second, warm = Kernel.build(tmp_path / "second.so", cache_dir=cache)
    assert first is second
    assert not cold["cache_hit"] and cold["compile_seconds"] > 0
    assert warm["cache_hit"] and warm["loaded_reused"]
    assert warm["compile_seconds"] == 0
    program = (
        "import json; from experiments.neural_attention.magic_residual_enumeration "
        "import Kernel; _, report = Kernel.build("
        + repr(str(tmp_path / "third.so"))
        + ", cache_dir="
        + repr(str(cache))
        + "); print(json.dumps(report))"
    )
    other = json.loads(
        subprocess.check_output([sys.executable, "-c", program], text=True)
    )
    assert other["cache_hit"] and not other["loaded_reused"]
    assert other["compile_seconds"] == 0
    source = tmp_path / "changed.c"
    source.write_bytes(
        Path(__file__).with_name("residual_enum.c").read_bytes()
        + b"\n/* source invalidation test */\n"
    )
    _, changed = Kernel.build(tmp_path / "changed.so", cache_dir=cache, source=source)
    assert not changed["cache_hit"] and changed["cache_key"] != cold["cache_key"]
