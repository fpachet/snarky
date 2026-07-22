import json
from pathlib import Path

import pytest
import yaml

from snarky import parse_rules
from snarky.spinoza import run_case
from snarky.terms import Term, Triple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPINOZA_ROOT = PROJECT_ROOT / "spinoza"
SYSTEMATIC_ROOT = SPINOZA_ROOT / "systematic"
ALL_AFFECT_DEFINITIONS = tuple(f"E3DA{index:02d}" for index in range(1, 49))


@pytest.mark.parametrize("definition_id", ALL_AFFECT_DEFINITIONS)
def test_affect_definitions_prove_their_cases(definition_id: str) -> None:
    manifest = yaml.safe_load(
        (SYSTEMATIC_ROOT / "definitions" / f"{definition_id}.yaml").read_text(
            encoding="utf-8"
        )
    )

    for case in manifest["cases"]:
        result = run_case(SYSTEMATIC_ROOT, definition_id, case["id"])

        assert result.proved, (definition_id, case["id"])
        assert result.proof_depths == tuple(case["expected"].get("proof_depths", []))
        assert result.forbidden_violations == ()
        assert set(result.rule_origins) <= {"textual_definition"}


@pytest.mark.parametrize("definition_id", ALL_AFFECT_DEFINITIONS)
def test_definition_manifest_excludes_its_validated_summary(
    definition_id: str,
) -> None:
    manifest = yaml.safe_load(
        (SYSTEMATIC_ROOT / "definitions" / f"{definition_id}.yaml").read_text(
            encoding="utf-8"
        )
    )
    loaded_rules = parse_rules(
        "\n".join(
            (SYSTEMATIC_ROOT / relative_path).read_text(encoding="utf-8")
            for relative_path in manifest["rule_files"]
        )
    )

    assert manifest["rule_files"] == [f"rules/definitions/{definition_id}.rules"]
    assert set(manifest["forbidden_rules"]).isdisjoint(
        rule.name for rule in loaded_rules
    )
    assert manifest["allowed_rule_origins"] == ["textual_definition"]
    assert any(case.get("must_not_derive") for case in manifest["cases"])


def test_all_affect_definitions_are_linked_to_imported_source() -> None:
    corpus = json.loads(
        (SPINOZA_ROOT / "sources" / "passages.json").read_text(encoding="utf-8")
    )
    source_units = {unit["id"]: unit for unit in corpus["units"]}

    for definition_id in ALL_AFFECT_DEFINITIONS:
        manifest = yaml.safe_load(
            (SYSTEMATIC_ROOT / "definitions" / f"{definition_id}.yaml").read_text(
                encoding="utf-8"
            )
        )

        assert manifest["source_unit"] == definition_id
        assert source_units[definition_id]["type"] == "definition_of_affect"
        assert source_units[definition_id]["source_text"]


def test_general_affect_definition_proves_all_cases() -> None:
    manifest = yaml.safe_load(
        (SYSTEMATIC_ROOT / "definitions" / "E3DA-GENERAL.yaml").read_text(
            encoding="utf-8"
        )
    )

    for case in manifest["cases"]:
        result = run_case(SYSTEMATIC_ROOT, "E3DA-GENERAL", case["id"])

        assert result.proved, case["id"]
        assert result.proof_depths == tuple(case["expected"].get("proof_depths", []))
        assert result.forbidden_violations == ()


def test_definition_scaffolding_is_complete() -> None:
    manifests = sorted((SYSTEMATIC_ROOT / "definitions").glob("E3DA*.yaml"))
    identifiers = {path.stem for path in manifests}

    assert len(manifests) == 49
    assert identifiers == {*ALL_AFFECT_DEFINITIONS, "E3DA-GENERAL"}


def test_every_affect_definition_declares_canonical_dependencies() -> None:
    dependency_map = yaml.safe_load(
        (SYSTEMATIC_ROOT / "definitions" / "dependencies.yaml").read_text(
            encoding="utf-8"
        )
    )["definitions"]

    assert set(dependency_map) == {*ALL_AFFECT_DEFINITIONS, "E3DA-GENERAL"}
    assert all(dependencies for dependencies in dependency_map.values())
    for dependencies in dependency_map.values():
        for reference in dependencies:
            if reference.startswith("E3P"):
                proposition_id = reference[:5]
                assert (
                    SYSTEMATIC_ROOT / "theorems" / f"{proposition_id}.yaml"
                ).is_file(), reference


def _relations(term: Term) -> set[str]:
    if not isinstance(term, Triple):
        return set()
    return {
        term.relation.name,
        *_relations(term.subject),
        *_relations(term.object),
    }


def test_affect_definition_relations_are_declared_in_ontology() -> None:
    ontology = yaml.safe_load(
        (SYSTEMATIC_ROOT / "ontology" / "concepts.yaml").read_text(encoding="utf-8")
    )
    declared = {
        concept
        for concepts in ontology.values()
        if isinstance(concepts, list)
        for concept in concepts
        if isinstance(concept, str)
    }
    rules = (
        rule
        for path in (SYSTEMATIC_ROOT / "rules" / "definitions").glob("E3DA*.rules")
        for rule in parse_rules(path.read_text(encoding="utf-8"))
    )
    used = {
        relation
        for rule in rules
        for term in (
            *(premise.entity for premise in rule.premises),
            *(action.entity for action in rule.actions),
        )
        for relation in _relations(term)
    }

    assert used <= declared
