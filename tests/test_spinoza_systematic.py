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
        "E1P36_donnee_effet_necessaire",
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
        "E1P36_donnee_effet_necessaire",
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


def test_manifest_counter_case_succeeds_when_forbidden_fact_is_absent(
    tmp_path: Path,
) -> None:
    root = tmp_path / "model"
    (root / "theorems").mkdir(parents=True)
    (root / "rules").mkdir()
    (root / "rules" / "empty.rules").write_text(
        "RULE inert\nWHEN\n    (x est x)\nTHEN\n    ADD (x est x)\nEND\n",
        encoding="utf-8",
    )
    (root / "theorems" / "TEST.yaml").write_text(
        """\
schema_version: 1
id: TEST
rule_files: [rules/empty.rules]
cases:
  - id: contre_exemple
    initial_facts:
      - "(signal est present)"
    goals: []
    must_not_derive:
      - "(cause0 detruit chose0)"
""",
        encoding="utf-8",
    )

    result = run_case(root, "TEST", "contre_exemple")

    assert result.proved
    assert result.forbidden_violations == ()

    violating_rules = parse_rules(
        """\
RULE derive_forbidden_fact
WHEN
    (signal est present)
THEN
    ADD (cause0 detruit chose0)
END
"""
    )
    violation = run_case(
        root,
        "TEST",
        "contre_exemple",
        rules=violating_rules,
    )

    assert not violation.proved
    assert violation.forbidden_violations == (
        Fact(parse_term("(cause0 detruit chose0)")),
    )


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


def test_e3p04_excludes_only_internal_destruction() -> None:
    internal = run_case(SYSTEMATIC_ROOT, "E3P04", "cause_interne")
    external = run_case(SYSTEMATIC_ROOT, "E3P04", "cause_exterieure_non_exclue")

    assert internal.proved
    assert internal.proof_depths == (2, 2)
    assert internal.rule_names == (
        "E3P04D_definition_affirme_non_negation",
        "E3P04D_non_negation_interdit_destruction",
    )
    assert all(goal.status is Status.FAUX for goal in internal.goals)
    assert external.proved
    assert external.forbidden_violations == ()


def test_e3p05_refutes_named_cohabitation_without_default_negation() -> None:
    contrary = run_case(
        SYSTEMATIC_ROOT,
        "E3P05",
        "destruction_mutuelle_incompatible",
    )
    harmless = run_case(SYSTEMATIC_ROOT, "E3P05", "simple_cohabitation")

    assert contrary.proved
    assert contrary.proof_depths == (3, 4, 4)
    assert "COMP_hypothese_refutee_par_fait_faux" in contrary.rule_names
    assert harmless.proved
    assert harmless.forbidden_violations == ()


def test_e3p06_derives_conatus_from_power_and_prior_theorems() -> None:
    conatus = run_case(SYSTEMATIC_ROOT, "E3P06", "chose_singuliere")
    incomplete = run_case(SYSTEMATIC_ROOT, "E3P06", "puissance_non_etablie")

    assert conatus.proved
    assert conatus.proof_depths == (3, 3, 3)
    assert "E1P25C_chose_singuliere_mode_determine" in conatus.rule_names
    assert "E1P34_mode_exprime_puissance" in conatus.rule_names
    assert "E3P04_cause_interne_non_destructrice" in conatus.rule_names
    assert "E3P05_destruction_implique_contrariete" in conatus.rule_names
    assert incomplete.proved


def test_e3p07_identifies_conatus_with_current_essence() -> None:
    identity = run_case(SYSTEMATIC_ROOT, "E3P07", "essence_actuelle_et_conatus")
    unlinked = run_case(SYSTEMATIC_ROOT, "E3P07", "effet_non_relier_a_essence")

    assert identity.proved
    assert identity.proof_depths == (3, 3)
    assert identity.rule_names == (
        "E1P36_donnee_effet_necessaire",
        "E1P29_effet_dans_limites_nature",
        "E3P06_chose_singuliere_conatus",
        "E3P07D_effort_identique_essence_actuelle",
    )
    assert unlinked.proved


def test_e3p08_uses_explicit_reductio_to_derive_indefinite_duration() -> None:
    indefinite = run_case(SYSTEMATIC_ROOT, "E3P08", "refutation_du_temps_fini")
    powerless = run_case(
        SYSTEMATIC_ROOT,
        "E3P08",
        "effort_sans_puissance_existence",
    )

    assert indefinite.proved
    assert indefinite.proof_depths == (4, 2)
    assert indefinite.rule_names == (
        "E3P06_chose_singuliere_conatus",
        "E3P08D_duree_finie_implique_autodestruction",
        "E3P04_cause_interne_non_destructrice",
        "COMP_hypothese_refutee_par_fait_faux",
        "E3P08D_refutation_duree_finie",
        "E3P08D_absence_destruction_exterieure_assure_continuation",
    )
    assert powerless.proved


def test_each_conatus_manifest_has_a_passing_counter_case() -> None:
    for proposition in range(4, 9):
        theorem_id = f"E3P{proposition:02d}"
        manifest = yaml.safe_load(
            (SYSTEMATIC_ROOT / "theorems" / f"{theorem_id}.yaml").read_text(
                encoding="utf-8"
            )
        )
        counter_cases = [
            case for case in manifest["cases"] if case.get("must_not_derive")
        ]

        assert len(counter_cases) == 1
        result = run_case(SYSTEMATIC_ROOT, theorem_id, counter_cases[0]["id"])
        assert result.proved
        assert result.forbidden_facts
        assert result.forbidden_violations == ()


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


def test_conatus_manifests_load_only_current_proof_and_prior_theorems() -> None:
    for proposition in range(4, 9):
        theorem_id = f"E3P{proposition:02d}"
        manifest = yaml.safe_load(
            (SYSTEMATIC_ROOT / "theorems" / f"{theorem_id}.yaml").read_text(
                encoding="utf-8"
            )
        )
        proof_files = [
            path for path in manifest["rule_files"] if path.startswith("rules/proofs/")
        ]
        validated_files = [
            path
            for path in manifest["rule_files"]
            if path.startswith("rules/validated/")
        ]

        assert proof_files == [f"rules/proofs/{theorem_id}.rules"]
        assert all(
            int(Path(path).stem.removeprefix("E3P")) < proposition
            for path in validated_files
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
        for path in (SYSTEMATIC_ROOT / "rules").rglob("*.rules")
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
