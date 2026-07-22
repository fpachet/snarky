import json
from pathlib import Path

import pytest
import yaml

from snarky.parser import parse_rules
from snarky.spinoza import run_case

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SYSTEMATIC_ROOT = PROJECT_ROOT / "spinoza" / "systematic"
SOURCE_PATH = PROJECT_ROOT / "spinoza" / "sources" / "passages.json"
EXPLANATION_IDS = (
    "E3DA01-EXP",
    "E3DA03-EXP",
    "E3DA04-EXP",
    "E3DA06-EXP",
    "E3DA07-EXP",
    "E3DA10-EXP",
    "E3DA11-EXP",
    "E3DA13-EXP",
    "E3DA15-EXP",
    "E3DA18-EXP",
    "E3DA20-EXP",
    "E3DA22-EXP",
    "E3DA23-EXP",
    "E3DA24-EXP",
    "E3DA26-EXP",
    "E3DA27-EXP",
    "E3DA28-EXP",
    "E3DA29-EXP",
    "E3DA31-EXP",
    "E3DA32-EXP",
    "E3DA33-EXP",
    "E3DA38-EXP",
    "E3DA41-EXP",
    "E3DA42-EXP",
    "E3DA44-EXP",
    "E3DA48-EXP",
    "E3DA-GENERAL-EXP",
)


@pytest.mark.parametrize("explanation_id", EXPLANATION_IDS)
def test_affect_explanations_prove_positive_and_negative_cases(
    explanation_id: str,
) -> None:
    manifest = yaml.safe_load(
        (SYSTEMATIC_ROOT / "explanations" / f"{explanation_id}.yaml").read_text(
            encoding="utf-8"
        )
    )

    assert manifest["id"] == explanation_id
    assert manifest["allowed_rule_origins"] == ["textual_explanation"]
    assert manifest["rule_files"] == [f"rules/explanations/{explanation_id}.rules"]
    assert any(case.get("must_not_derive") for case in manifest["cases"])
    for case in manifest["cases"]:
        result = run_case(SYSTEMATIC_ROOT, explanation_id, case["id"])
        assert result.proved, (explanation_id, case["id"])
        assert list(result.proof_depths) == case.get("expected", {}).get(
            "proof_depths", list(result.proof_depths)
        )


def test_explanation_layer_matches_every_imported_explanation_section() -> None:
    corpus = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    source_ids = {
        f"{unit['id']}-EXP"
        for unit in corpus["units"]
        if any(
            "explication" in (section.get("label") or section.get("type") or "").lower()
            for section in unit.get("sections", [])
        )
    }
    manifest_paths = sorted((SYSTEMATIC_ROOT / "explanations").glob("*.yaml"))

    assert source_ids == set(EXPLANATION_IDS)
    assert {path.stem for path in manifest_paths} == source_ids
    assert len(manifest_paths) == 27


def test_explanation_rules_are_catalogued_and_have_stable_prefixes() -> None:
    catalog = yaml.safe_load(
        (SYSTEMATIC_ROOT / "rules" / "catalog.yaml").read_text(encoding="utf-8")
    )
    catalog_ids = {rule_id for entry in catalog["rules"] for rule_id in entry["ids"]}
    rule_paths = sorted((SYSTEMATIC_ROOT / "rules" / "explanations").glob("*.rules"))
    rules = [
        rule
        for path in rule_paths
        for rule in parse_rules(path.read_text(encoding="utf-8"))
    ]

    assert len(rule_paths) == 27
    assert len(rules) == 44
    assert all(rule.name in catalog_ids for rule in rules)
    assert all("_EXP_" in rule.name for rule in rules)
