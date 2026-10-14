"""Emit the generated counterpart of the standalone native-batch sanitizer test."""

import argparse
from pathlib import Path

from snarky import Atom, Number
from snarky.finite.constraints import AllDifferentConstraint, SumConstraint
from snarky.finite.model import FiniteModel, FiniteVariable

from .model_batch import ModelSpec, source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    variables = tuple(
        FiniteVariable(Atom(f"x{i}"), tuple(map(Number, [0, 2, 3, 5])))
        for i in range(3)
    )
    names = tuple(v.name for v in variables)
    model = FiniteModel(
        "sanitizer",
        variables,
        (
            AllDifferentConstraint(Atom("distinct"), names),
            SumConstraint(Atom("sum"), names, 7),
        ),
    )
    driver = Path(__file__).with_suffix(".c").read_text()
    driver = "\n".join(
        line for line in driver.splitlines() if not line.startswith('#include "')
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(source(ModelSpec(model)) + "\n" + driver + "\n")


if __name__ == "__main__":
    main()
