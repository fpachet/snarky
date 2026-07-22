from pathlib import Path

import yaml

from snarky import Fact, ForwardEngine, Status, parse_rules, parse_term
from snarky.serialization import load_facts
from snarky.spinoza import load_historical_rules, run_case

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPINOZA_ROOT = PROJECT_ROOT / "spinoza"
SYSTEMATIC_ROOT = SPINOZA_ROOT / "systematic"


def test_e3p01_derives_activity_and_passivity_through_definitions() -> None:
    adequate = run_case(SYSTEMATIC_ROOT, "E3P01", "idee_adequate")
    inadequate = run_case(SYSTEMATIC_ROOT, "E3P01", "idee_inadequate")

    assert adequate.proved
    assert adequate.proof_depths == (3, 3)
    assert adequate.rule_names == (
        "E1P36_idee_donnee_effet_necessaire",
        "E2P11C_idee_adequate_cause_adequate",
        "E3D2_activite_par_cause_adequate",
    )
    assert adequate.rule_origins == (
        "external_textual",
        "external_textual",
        "textual",
    )
    assert inadequate.proved
    assert inadequate.proof_depths == (3, 3)
    assert inadequate.rule_names == (
        "E1P36_idee_donnee_effet_necessaire",
        "E2P11C_idee_inadequate_cause_partielle",
        "E3D2_passivite_par_cause_partielle",
    )


def test_e3p01_fails_without_the_explicit_external_bridge() -> None:
    definition_rules = parse_rules(
        (SYSTEMATIC_ROOT / "rules" / "definitions.rules").read_text(encoding="utf-8")
    )

    result = run_case(
        SYSTEMATIC_ROOT,
        "E3P01",
        "idee_adequate",
        rules=definition_rules,
    )

    assert not result.proved
    assert result.proof_depths == (None, None)
    assert result.rule_names == ()


def test_definitions_e3d1_and_e3d3_are_executable_ontological_rules() -> None:
    rules = parse_rules(
        (SYSTEMATIC_ROOT / "rules" / "definitions.rules").read_text(encoding="utf-8")
    )
    initial = tuple(
        Fact(parse_term(entity))
        for entity in (
            "(effet0 est_percu_clairement_par cause0)",
            "(effet0 est_percu_distinctement_par cause0)",
            "(affection0 affecte corps0)",
            "(affection0 modifie_puissance_agir_de corps0)",
            "(idee0 est_idee_de affection0)",
        )
    )

    result = ForwardEngine(rules).run(initial)

    assert Fact(parse_term("(cause0 est_cause_adequate_de effet0)")) in result.facts
    assert (
        Fact(parse_term("(affection0 est_affection_corporelle_de corps0)"))
        in result.facts
    )
    assert (
        Fact(parse_term("(idee0 est_composante_ideelle_de affection0)")) in result.facts
    )


def test_e3p02_represents_impossibility_with_explicit_false_statuses() -> None:
    result = run_case(SYSTEMATIC_ROOT, "E3P02", "independance_des_attributs")

    assert result.proved
    assert result.proof_depths == (1, 1)
    assert result.rule_names == ("E2P06_independance_causale_des_attributs",)
    assert result.rule_origins == ("external_textual",)
    assert all(goal.status is Status.FAUX for goal in result.goals)


def test_e3p03_reuses_only_the_validated_e3p01_fragment() -> None:
    action = run_case(SYSTEMATIC_ROOT, "E3P03", "origine_action")
    passion = run_case(SYSTEMATIC_ROOT, "E3P03", "origine_passion")

    assert action.proved
    assert action.proof_depths == (1, 2)
    assert action.rule_names == (
        "E3P01_idee_adequate_implique_action",
        "COMP_action_origine_adequate",
    )
    assert action.rule_origins == ("textual_theorem", "compilation")
    assert passion.proved
    assert passion.proof_depths == (1, 2)
    assert passion.rule_names == (
        "E3P01_idee_inadequate_implique_passion",
        "COMP_passion_origine_inadequate",
    )


def test_systematic_manifests_do_not_load_the_historical_model() -> None:
    historical_names = {rule.name for rule in load_historical_rules(SPINOZA_ROOT)}
    for theorem_path in sorted((SYSTEMATIC_ROOT / "theorems").glob("E3P*.yaml")):
        manifest = yaml.safe_load(theorem_path.read_text(encoding="utf-8"))
        assert all(
            not relative_path.startswith("../")
            for relative_path in manifest["rule_files"]
        )
        systematic_rules = parse_rules(
            "\n".join(
                (SYSTEMATIC_ROOT / relative_path).read_text(encoding="utf-8")
                for relative_path in manifest["rule_files"]
            )
        )
        assert historical_names.isdisjoint(rule.name for rule in systematic_rules)
        assert set(manifest["forbidden_rules"]).isdisjoint(
            rule.name for rule in systematic_rules
        )


def test_rule_catalog_covers_the_systematic_rule_files() -> None:
    catalog = yaml.safe_load(
        (SYSTEMATIC_ROOT / "rules" / "catalog.yaml").read_text(encoding="utf-8")
    )
    catalog_names = {
        rule_name for entry in catalog["rules"] for rule_name in entry["ids"]
    }
    executable_names = {
        rule.name
        for path in (SYSTEMATIC_ROOT / "rules").glob("*.rules")
        for rule in parse_rules(path.read_text(encoding="utf-8"))
    }

    assert catalog_names == executable_names


def test_systematic_postulates_are_explicit_ground_facts() -> None:
    facts = load_facts(SYSTEMATIC_ROOT / "facts" / "postulates.yaml")

    assert len(facts) == 5
    assert (
        Fact(
            parse_term("(corps_humain conserve traces_des_objets)"),
            Status.VRAI,
        )
        in facts
    )
