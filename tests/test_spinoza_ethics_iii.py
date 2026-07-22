import json
from pathlib import Path

import pytest
import yaml

from snarky import Fact, ForwardEngine, Status, parse_term
from snarky.spinoza import load_historical_rules, run_case

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPINOZA_ROOT = PROJECT_ROOT / "spinoza"


@pytest.mark.parametrize(
    ("theorem_id", "case_id", "depth"),
    [
        ("E3P19", "destruction", 2),
        ("E3P19", "conservation", 2),
        ("E3P21", "joie", 2),
        ("E3P21", "tristesse", 2),
        ("E3P22", "amour", 3),
        ("E3P22", "haine", 3),
        ("E3P33", "reciprocite", 5),
    ],
)
def test_historical_cases_reach_the_presentation_results(
    theorem_id: str,
    case_id: str,
    depth: int,
) -> None:
    result = run_case(SPINOZA_ROOT, theorem_id, case_id)

    assert result.proved
    assert result.proof_depths == (depth,)


def test_p33_reproduces_and_exposes_the_historical_overstrength() -> None:
    rules = load_historical_rules(SPINOZA_ROOT)
    initial = (Fact(parse_term("(x0 aime y0)"), Status.VRAI),)
    goal = Fact(parse_term("(x0 s_efforce_que (y0 aime x0))"), Status.VRAI)

    result = ForwardEngine(rules).run(initial)

    assert goal in result.facts
    assert result.provenance.depth(goal) == 5
    manifest = yaml.safe_load(
        (SPINOZA_ROOT / "theorems" / "E3P33.yaml").read_text(encoding="utf-8")
    )
    assert "similitude" in manifest["known_divergences"][0]


def test_p33_runner_exposes_the_complete_minimal_rule_chain() -> None:
    result = run_case(SPINOZA_ROOT, "E3P33", "reciprocite")

    assert result.rule_names == (
        "P13_1_1_amour",
        "P12II_17II_effort_existence",
        "P12_29_effort_joie",
        "P29_1_effort_affecter_joie",
        "P13_2_2_effort_amour_reciproque",
    )


def test_rule_catalog_covers_every_executable_historical_rule() -> None:
    rules = load_historical_rules(SPINOZA_ROOT)
    catalog = yaml.safe_load(
        (SPINOZA_ROOT / "rules" / "rule_catalog.yaml").read_text(encoding="utf-8")
    )
    catalog_ids = {
        identifier for entry in catalog["rules"] for identifier in entry["ids"]
    }

    assert {rule.name for rule in rules} == catalog_ids
    assert {entry["origin"] for entry in catalog["rules"]} == {
        "historical_model",
        "historical_interpretation",
    }


def test_complete_source_catalog_and_theorem_scaffolding() -> None:
    corpus = json.loads(
        (SPINOZA_ROOT / "sources" / "passages.json").read_text(encoding="utf-8")
    )
    assert corpus["counts"] == {
        "preface": 1,
        "definition": 3,
        "postulate": 2,
        "proposition": 59,
        "definition_of_affect": 48,
        "general_definition_of_affect": 1,
    }
    propositions = [unit for unit in corpus["units"] if unit["type"] == "proposition"]
    assert all(unit["source_text"] for unit in propositions)
    assert all(
        any(section["type"] == "démonstration" for section in unit["sections"])
        for unit in propositions
    )
    theorem_files = sorted((SPINOZA_ROOT / "theorems").glob("E3P*.yaml"))
    assert len(theorem_files) == 59
    assert theorem_files[0].name == "E3P01.yaml"
    assert theorem_files[-1].name == "E3P59.yaml"
    graph = json.loads(
        (SPINOZA_ROOT / "reports" / "dependency_graph.json").read_text(encoding="utf-8")
    )
    assert len(graph["nodes"]) == 59
    assert all(edge["source"] != edge["target"] for edge in graph["edges"])


def test_plain_text_contains_every_imported_passage_without_omission() -> None:
    corpus = json.loads(
        (SPINOZA_ROOT / "sources" / "passages.json").read_text(encoding="utf-8")
    )
    full_text = (SPINOZA_ROOT / "sources" / "ethique_III_appuhn_1913.txt").read_text(
        encoding="utf-8"
    )

    for unit in corpus["units"]:
        assert unit["source_text"] in full_text, unit["id"]
        for section in unit.get("sections", []):
            assert section["text"] in full_text, (unit["id"], section["label"])
    assert full_text.count("\nPROPOSITION ") == 59
    assert full_text.count("\nDÉFINITION D’AFFECT ") == 48


def test_intentional_contexts_are_not_flattened() -> None:
    rules = load_historical_rules(SPINOZA_ROOT)
    imagined = Fact(parse_term("(x0 imagine (y0 est joyeux))"), Status.VRAI)
    result = ForwardEngine(rules).run((imagined,))

    assert Fact(parse_term("(y0 est joyeux)"), Status.VRAI) not in result.facts
    assert Fact(parse_term("(x0 est joyeux)"), Status.VRAI) not in result.facts
