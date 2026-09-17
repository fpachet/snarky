"""Small installed, corpus-independent examples of the declarative runtime.

Run ``python -m snarky.finite.examples`` for mixed scheduling and Markov MAP
with exactly representable negative-log2 costs.
"""

from __future__ import annotations

from importlib.resources import files
from random import Random

from ..factors import FactorDefinition
from ..facts import Fact
from ..parser import parse_rule_groups
from ..premises import FactPremise
from ..terms import Atom, Number, Term, Triple
from .constraints import AllDifferentConstraint, TableConstraint
from .factors import FactorObjective, IntegerFactor, TableFactor
from .markov import MarkovCosts, markov_model
from .model import FiniteModel, FiniteVariable, GuardedConstraint, Query, QueryKind
from .search import solve


def scheduling_model() -> FiniteModel:
    """Two jobs in distinct slots; late setup needs an earlier delivery slot."""
    setup, delivery = Atom("setup"), Atom("delivery")
    overtime = Fact(Triple(Atom("shift"), Atom("needs"), Atom("overtime")))
    rules = parse_rule_groups("""
        GROUP scheduling
            RULE late_setup
            WHEN
                (setup value 3)
            THEN
                ADD (shift needs overtime)
            END
        END_GROUP
    """)
    return FiniteModel(
        "scheduling",
        tuple(
            FiniteVariable(v, tuple(Number(i) for i in (1, 2, 3)))
            for v in (setup, delivery)
        ),
        (
            AllDifferentConstraint(Atom("separate_slots"), (setup, delivery)),
            GuardedConstraint(
                Atom("late_delivery_policy"),
                overtime,
                TableConstraint(
                    Atom("late_delivery_policy"), (delivery,), ((Number(2),),)
                ),
            ),
        ),
        rules=rules,
        objective=FactorObjective(
            (
                TableFactor("preferred_delivery", (delivery,), {(Number(2),): 5}),
                IntegerFactor(
                    FactorDefinition(
                        "overtime_cost", Atom("shift"), (FactPremise(overtime.entity),)
                    ),
                    -8,
                ),
            )
        ),
    )


def markov_probe_model(seed: int = 0) -> FiniteModel:
    """Uniform initial symbol and dyadic transition probabilities on four states."""
    rng = Random(seed)
    alphabet = tuple(Number(i) for i in range(4))
    costs: dict[tuple[Term, ...], int] = {}
    for left in alphabet:
        row = [1, 2, 3, 3]
        rng.shuffle(row)
        costs.update(
            {(left, right): cost for right, cost in zip(alphabet, row, strict=True)}
        )
    source = MarkovCosts(alphabet, 1, {(v,): 2 for v in alphabet}, costs)
    names = tuple(Atom(f"x{i}") for i in range(5))
    return markov_model(
        source,
        5,
        names=names,
        constraints=(
            AllDifferentConstraint(Atom("first_four_distinct"), names[:4]),
            TableConstraint(
                Atom("return_to_start"),
                (names[0], names[-1]),
                tuple((v, v) for v in alphabet),
            ),
        ),
    )


def model_source(name: str) -> str:
    """Read a packaged textual example from a wheel or a checkout."""
    if name not in {"rules", "four_queens", "linear", "scheduling", "probability"}:
        raise ValueError(f"unknown example {name!r}")
    return (
        files("snarky.finite")
        .joinpath("models", f"{name}.model")
        .read_text(encoding="utf-8")
    )


def main() -> None:
    for model, kind in (
        (scheduling_model(), QueryKind.MAXIMIZE),
        (markov_probe_model(), QueryKind.MINIMIZE),
    ):
        result = solve(model, Query(kind))
        assert result.incumbent is not None
        print(
            f"{model.name}: {result.status.value}; "
            f"objective={result.incumbent.objective_value}; "
            f"nodes={result.explored_nodes}; bound={result.objective_bound}"
        )
        print(dict(result.incumbent.assignment))


if __name__ == "__main__":
    main()
