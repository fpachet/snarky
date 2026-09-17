from rulebases.projects.runtime_boundaries import (
    preferences_example,
    propagation_example,
    snapshot_example,
)
from snarky import Atom, Fact


def test_runtime_tutorial_examples() -> None:
    assert propagation_example() == (Fact(Atom("a")),)
    assert snapshot_example() == (1, 0)
    assert preferences_example() == ("accepted", 2.0)
