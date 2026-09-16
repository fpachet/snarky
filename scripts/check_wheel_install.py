"""Smoke-test a built Snarky wheel in an isolated virtual environment."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

SMOKE_TEST = """
from snarky import Fact, ForwardEngine, parse_rules, parse_term

rules = parse_rules(
    '''
    RULE smoke
    WHEN
        seed
    THEN
        ADD installed
    END
    '''
)
result = ForwardEngine(rules).run((Fact(parse_term("seed")),))
assert Fact(parse_term("installed")) in result.facts
print("isolated wheel import and inference: ok")

from snarky import Atom, Number
from snarky.finite import (
    FiniteModel, FiniteVariable, LinearObjective, Query, QueryKind, ResultStatus, solve,
)
from snarky.finite.constraints import AllDifferentConstraint
x, y = Atom("x"), Atom("y")
model = FiniteModel(
    "installed_native",
    tuple(FiniteVariable(var, (Number(1), Number(2))) for var in (x, y)),
    (AllDifferentConstraint(Atom("different"), (x, y)),),
    objective=LinearObjective(((1, x), (-2, y))),
)
result = solve(model, Query(QueryKind.MINIMIZE))
assert result.status is ResultStatus.OPTIMAL
assert result.incumbent.objective_value == -3
print("isolated native CSP optimization without companion: ok")

from snarky.finite.examples import scheduling_model, markov_probe_model
mixed = solve(scheduling_model(), Query(QueryKind.MAXIMIZE))
assert mixed.status is ResultStatus.OPTIMAL and mixed.incumbent.objective_value == 5
markov = solve(markov_probe_model(), Query(QueryKind.MINIMIZE))
assert markov.status is ResultStatus.OPTIMAL and markov.incumbent.objective_value == 9
assert sum(c.value for c in markov.incumbent.contributions) == 9
print("isolated mixed factor and Markov examples: ok")

from dataclasses import replace
from fractions import Fraction
from snarky.finite import negative_log2_measure
cost_model = markov_probe_model()
probability_model = replace(
    cost_model, measure=negative_log2_measure(cost_model.objective)
)
partition = solve(probability_model, Query(QueryKind.PARTITION))
assert partition.arithmetic == "rational"
assert isinstance(partition.inference.partition, Fraction)
sample = solve(probability_model, Query(QueryKind.SAMPLE_EXACT, seed=1))
assert sample.inference.probability(sample.incumbent.assignment) > 0
print("isolated rational partition and exact sampling: ok")

from snarky.finite import parse_model_document
from snarky.finite.examples import model_source
for name, query, expected_count in (
    ("rules", "closure", 1), ("four_queens", "all", 2),
    ("linear", "optimum", 1), ("scheduling", "optimum", 1),
    ("probability", "draw", 5),
):
    document = parse_model_document(model_source(name))
    assert len(document.execute(query).solutions) == expected_count
print("isolated packaged MODEL examples: ok")
"""

CSP_SMOKE_TEST = """
from csp_solver.four_queens import solve_four_queens
from snarky import ChoiceSearchStatus
result = solve_four_queens()
assert result.status is ChoiceSearchStatus.SOLVED
assert len(result.solutions) == 2
print("isolated companion rules and solving: ok")
from csp_solver.magic_square import magic_square_facts
from csp_solver.native import native_model
from snarky.finite import Query, QueryKind, solve
native = solve(native_model(magic_square_facts(3)), Query(QueryKind.ENUMERATE))
assert native.complete and len(native.solutions) == 8
print("isolated companion-to-native adapter: ok")
"""

REGULAR_SMOKE_TEST = """
from dataclasses import replace
from math import isclose
from snarky.finite import infer, negative_log2_measure
from snarky.finite.examples import markov_probe_model
costs = markov_probe_model()
model = replace(costs, measure=negative_log2_measure(costs.objective))
generic = infer(model).inference
regular = infer(model, backend="regular_bp").inference
assert regular.certificate == "EXACT_REGULAR_BP"
assert isclose(float(generic.partition), regular.partition, rel_tol=1e-12)
print("isolated optional regular-BP agreement: ok")
"""


def check_cli(python: Path, root: Path, *, companion: bool) -> None:
    """Exercise the installed executable without checkout import paths."""

    command = python.parent / ("snarky.exe" if sys.platform == "win32" else "snarky")
    environment = {
        key: value for key, value in os.environ.items()
        if key not in {"PYTHONPATH", "PYTHONHOME"}
    }
    rules = root / "example.rules"
    rules.write_text(
        "GROUP smoke\nRULE infer\nWHEN\nseed\nTHEN\nADD result\nEND\nEND_GROUP\n",
        encoding="utf-8",
    )
    program = root / "example.program"
    program.write_text("PROGRAM demo\nPREPARE smoke\nEND_PROGRAM\n", encoding="utf-8")
    constraint = root / "example.constraints"
    constraint.write_text(
        "CONSTRAINT distinct\nKIND ALL_DIFFERENT\nSCOPE $variable\nFROM\n"
        "($variable kind cell)\nEND_SCOPE\nEND\n", encoding="utf-8",
    )
    subprocess.run(
        [str(command), "check", "--syntax-only", str(rules), str(program)],
        cwd=root, env=environment, check=True,
    )
    model = root / "example.model"
    model.write_text(
        "MODEL smoke\nVARIABLE x DOMAIN SEQ[1 2]\n"
        "OBJECTIVE LINEAR\nTERMS SEQ[SEQ[1 x]]\nEND_OBJECTIVE\n"
        "QUERY best MINIMIZE\nEND_QUERY\nEND_MODEL\n", encoding="utf-8",
    )
    subprocess.run(
        [str(command), "check", "--syntax-only", str(model)],
        cwd=root, env=environment, check=True,
    )
    model_run = subprocess.run(
        [str(command), "run", str(model), "--query", "best"],
        cwd=root, env=environment, capture_output=True, text=True, check=True,
    )
    import json

    assert json.loads(model_run.stdout)["objective_bound"] == 1
    checked = subprocess.run(
        [str(command), "check", "--syntax-only", str(constraint)],
        cwd=root, env=environment, capture_output=True, text=True,
    )
    assert checked.returncode == (0 if companion else 1), (
        checked.stdout + checked.stderr
    )
    if not companion:
        assert "pip install ./csp_solver" in checked.stdout + checked.stderr
    if companion:
        constraint.write_text("CONSTRAINT invalid\nKIND UNKNOWN\n", encoding="utf-8")
        invalid = subprocess.run(
            [str(command), "check", str(constraint)], cwd=root,
            env=environment, capture_output=True, text=True,
        )
        assert invalid.returncode == 1, invalid.stdout + invalid.stderr
    print(f"isolated console validation (companion={companion}): ok")


def find_wheel(path: Path) -> Path:
    """Resolve one Snarky wheel from a wheel path or distribution directory."""
    if path.is_file():
        if path.suffix != ".whl":
            raise ValueError(f"not a wheel: {path}")
        return path.resolve()

    wheels = sorted(path.glob("snarky-*.whl"))
    if len(wheels) != 1:
        raise ValueError(f"expected one Snarky wheel in {path}, found {len(wheels)}")
    return wheels[0].resolve()


def environment_python(environment: Path) -> Path:
    """Return the Python executable created by venv on this platform."""
    directory = "Scripts" if sys.platform == "win32" else "bin"
    executable = "python.exe" if sys.platform == "win32" else "python"
    return environment / directory / executable


def check_wheel(
    wheel: Path, companion: Path | None = None, regular: Path | None = None
) -> None:
    """Install and exercise a wheel without importing the source checkout."""
    with tempfile.TemporaryDirectory(prefix="snarky-wheel-") as temporary:
        root = Path(temporary)
        environment = root / "venv"
        venv.EnvBuilder(with_pip=True).create(environment)
        python = environment_python(environment)

        subprocess.run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-deps",
                str(wheel),
            ],
            cwd=root,
            check=True,
        )
        subprocess.run([str(python), "-I", "-c", SMOKE_TEST], cwd=root, check=True)
        check_cli(python, root, companion=False)
        if regular is not None:
            subprocess.run(
                [str(python), "-m", "pip", "install", "--no-deps",
                 "--disable-pip-version-check", str(regular.resolve())],
                cwd=root, check=True,
            )
            subprocess.run(
                [str(python), "-I", "-c", REGULAR_SMOKE_TEST], cwd=root, check=True,
            )
        if companion is not None:
            subprocess.run(
                [str(python), "-m", "pip", "install", "--no-deps",
                 "--disable-pip-version-check", str(companion.resolve())],
                cwd=root, check=True,
            )
            check_cli(python, root, companion=True)
            subprocess.run(
                [str(python), "-I", "-c", CSP_SMOKE_TEST], cwd=root, check=True
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("dist"),
        help="wheel file or directory containing exactly one Snarky wheel",
    )
    parser.add_argument("--companion", type=Path, help="optional snarky-csp wheel")
    parser.add_argument("--regular", type=Path, help="optional vo-regular-bp wheel")
    arguments = parser.parse_args()
    check_wheel(find_wheel(arguments.path), arguments.companion, arguments.regular)


if __name__ == "__main__":
    main()
