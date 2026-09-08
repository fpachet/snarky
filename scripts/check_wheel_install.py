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
"""

CSP_SMOKE_TEST = """
from csp_solver.four_queens import solve_four_queens
from snarky import ChoiceSearchStatus
result = solve_four_queens()
assert result.status is ChoiceSearchStatus.SOLVED
assert len(result.solutions) == 2
print("isolated companion rules and solving: ok")
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


def check_wheel(wheel: Path, companion: Path | None = None) -> None:
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
    arguments = parser.parse_args()
    check_wheel(find_wheel(arguments.path), arguments.companion)


if __name__ == "__main__":
    main()
