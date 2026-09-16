"""Frozen complete-result guards, independent of optimized matching internals."""

import json
from pathlib import Path

import pytest

from rulebases.runner import run_scenario
from scripts.capture_rulebase_reference import observation
from scripts.check_redesign import selected_tests
from snarky import (
    IndexedInstantiationStrategy,
    NaiveInstantiationStrategy,
    SemiNaiveInstantiationStrategy,
)

REFERENCE = json.loads(
    (Path(__file__).parent / "fixtures/redesign_rulebase_reference.json").read_text()
)


@pytest.mark.parametrize("scenario", REFERENCE["observations"])
@pytest.mark.parametrize("strategy", (
    NaiveInstantiationStrategy,
    IndexedInstantiationStrategy,
    SemiNaiveInstantiationStrategy,
))
def test_rulebases_preserve_complete_reference_observations(scenario, strategy):
    actual = run_scenario(scenario, strategy=strategy()).result
    assert observation(actual) == REFERENCE["observations"][scenario]


def test_non_bach_manifest_includes_generic_and_new_tests():
    selected = selected_tests()
    assert "tests/test_redesign_conformance.py" in selected
    assert "tests/test_factor_dsl.py" in selected
    assert "tests/test_persistent_constraint_oracles.py" in selected
    assert "tests/test_learned_rule_generator.py" not in selected
    assert "tests/test_official_manual_rulebase.py" not in selected
