"""Check the cross-solver witness bridge and matched symmetry restrictions."""

import subprocess

import pytest

from .magic_solver_comparison import (
    MINIZINC,
    external_trial,
    model_text,
    snarky_trial,
    validate_square,
)


@pytest.mark.parametrize("symmetry", [False, True])
def test_native_witness_mapping_with_reordered_variables(symmetry):
    row = snarky_trial(
        3,
        dict(
            policy="dom_wdeg", order="random", tie="random", seed=1, symmetry=symmetry
        ),
        2,
    )
    assert row["solved"]
    assert len(row["squares"]) == 1


@pytest.mark.parametrize(
    "solver,free_search", [("gecode", False), ("chuffed", False), ("chuffed", True)]
)
@pytest.mark.parametrize("symmetry", [False, True])
def test_installed_solver_witness_and_statistics(
    tmp_path, solver, symmetry, free_search
):
    if not MINIZINC.exists():
        pytest.skip("MiniZincIDE not installed")
    base = tmp_path / "magic"
    base.with_suffix(".mzn").write_text(model_text(3, symmetry, "first_fail"))
    subprocess.run(
        [
            str(MINIZINC),
            "--solver",
            solver,
            "--compile",
            "--output-fzn-to-file",
            str(base.with_suffix(".fzn")),
            "--output-ozn-to-file",
            str(base.with_suffix(".ozn")),
            str(base.with_suffix(".mzn")),
        ],
        check=True,
        capture_output=True,
        timeout=10,
    )
    row = external_trial(solver, base, 2, 3, symmetry, free_search=free_search)
    assert row["solved"]
    assert len(row["squares"]) == 1
    assert row["statistics"]["nodes"] >= 1
    assert not row["statuses"]


def test_validator_checks_diagonals_and_symmetry():
    valid = [2, 9, 4, 7, 5, 3, 6, 1, 8]
    assert validate_square(3, valid, True)
    with pytest.raises(AssertionError):
        validate_square(3, [4, 9, 2, 3, 5, 7, 8, 1, 6], True)
    # Semi-magic: rows and columns total 15, diagonals total 12 and 24.
    with pytest.raises(AssertionError):
        validate_square(3, [1, 5, 9, 6, 7, 2, 8, 3, 4], False)
