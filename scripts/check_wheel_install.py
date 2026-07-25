"""Smoke-test a built Snarky wheel in an isolated virtual environment."""

from __future__ import annotations

import argparse
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


def check_wheel(wheel: Path) -> None:
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("dist"),
        help="wheel file or directory containing exactly one Snarky wheel",
    )
    wheel = find_wheel(parser.parse_args().path)
    check_wheel(wheel)


if __name__ == "__main__":
    main()
