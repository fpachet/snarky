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


def test_e3p09_preserves_idea_context_and_models_its_scholium() -> None:
    proposition = run_case(
        SYSTEMATIC_ROOT,
        "E3P09",
        "idees_adequates_et_inadequates",
    )
    names = run_case(
        SYSTEMATIC_ROOT,
        "E3P09",
        "scolie_volonte_appetit_desir",
    )
    direction = run_case(
        SYSTEMATIC_ROOT,
        "E3P09",
        "scolie_bien_suit_orientation",
    )
    no_converse = run_case(
        SYSTEMATIC_ROOT,
        "E3P09",
        "scolie_jugement_bon_sans_orientation",
    )

    assert proposition.proved
    assert proposition.proof_depths == (2, 2, 2, 3)
    assert "E3P03_idee_adequate_constitue_essence_ame" in proposition.rule_names
    assert "E3P03_idee_inadequate_constitue_essence_ame" in proposition.rule_names
    assert "E2P23_idee_affection_conscience_de_soi" in proposition.rule_names
    assert names.proved
    assert names.proof_depths == (1, 1, 2, 2, 2, 2)
    assert direction.proved
    assert direction.proof_depths == (1, 1, 1, 1)
    assert no_converse.proved


def test_e3p10_derives_both_exclusion_and_contrariety() -> None:
    exclusion = run_case(SYSTEMATIC_ROOT, "E3P10", "idee_excluant_corps")
    neutral = run_case(SYSTEMATIC_ROOT, "E3P10", "idee_non_excluante")

    assert exclusion.proved
    assert exclusion.proof_depths == (3, 4)
    assert exclusion.goals[0].status is Status.FAUX
    assert exclusion.rule_names == (
        "E3P05_destruction_implique_contrariete",
        "E2P09C_exclusion_objet_transmise_a_son_idee",
        "E2P11_E2P13_idee_de_corps_dans_ame",
        "E3P06_chose_singuliere_conatus",
        "E3P07_conatus_est_essence_actuelle",
        "E3P10D_effort_ame_affirme_existence_corps",
        "E3P10D_idee_excluant_corps_contraire_ame",
    )
    assert neutral.proved


def test_e3p11_covers_four_variations_and_joy_sadness_scholium() -> None:
    variations = run_case(
        SYSTEMATIC_ROOT,
        "E3P11",
        "quatre_variations_de_puissance",
    )
    affects = run_case(SYSTEMATIC_ROOT, "E3P11", "scolie_joie_tristesse")
    neutral = run_case(SYSTEMATIC_ROOT, "E3P11", "scolie_passage_neutre")

    assert variations.proved
    assert variations.proof_depths == (1, 1, 1, 1)
    assert variations.rule_names == (
        "E2P07_augmentation_corps_augmentation_ame",
        "E2P07_diminution_corps_diminution_ame",
        "E2P07_soutien_corps_soutien_ame",
        "E2P07_reduction_corps_reduction_ame",
    )
    assert affects.proved
    assert affects.proof_depths == (1, 2, 1, 2, 1, 2, 1, 2, 2, 2, 3)
    assert neutral.proved


def test_e3p12_to_e3p18_preserve_imagination_contexts() -> None:
    beneficial = run_case(SYSTEMATIC_ROOT, "E3P12", "augmentation_et_soutien")
    resemblance = run_case(
        SYSTEMATIC_ROOT,
        "E3P16",
        "ressemblances_joyeuse_et_triste",
    )
    temporal = run_case(
        SYSTEMATIC_ROOT,
        "E3P18",
        "scolie_existence_affirmee_dans_imagination",
    )

    assert beneficial.proved
    assert beneficial.proof_depths == (2, 2)
    assert beneficial.forbidden_violations == ()
    assert resemblance.proved
    assert resemblance.proof_depths == (4, 4)
    assert resemblance.forbidden_violations == ()
    assert temporal.proved
    assert temporal.proof_depths == (2,)
    assert temporal.forbidden_violations == ()


def test_e3p15_and_e3p17_keep_accident_and_conflict_explicit() -> None:
    accident = run_case(
        SYSTEMATIC_ROOT,
        "E3P15",
        "causes_accidentelles_trois_affects",
    )
    efficient = run_case(
        SYSTEMATIC_ROOT,
        "E3P15",
        "cause_reellement_efficiente",
    )
    fluctuation = run_case(SYSTEMATIC_ROOT, "E3P17", "amour_haine_simultanes")

    assert accident.proved
    assert accident.proof_depths == (2, 2, 2, 3, 3, 3, 3)
    assert efficient.proved
    assert fluctuation.proved
    assert fluctuation.proof_depths == (1, 1, 2, 2)


def test_e3p19_to_e3p22_reconstruct_affective_transmission() -> None:
    destruction = run_case(
        SYSTEMATIC_ROOT,
        "E3P19",
        "destruction_de_la_chose_aimee",
    )
    hated = run_case(
        SYSTEMATIC_ROOT,
        "E3P20",
        "destruction_de_la_chose_haie",
    )
    intensity = run_case(
        SYSTEMATIC_ROOT,
        "E3P21",
        "joies_partagees_et_intensite",
    )
    external_cause = run_case(
        SYSTEMATIC_ROOT,
        "E3P22",
        "amour_envers_cause_de_joie",
    )

    assert destruction.proved
    assert destruction.proof_depths == (1, 1, 2, 3)
    assert destruction.forbidden_violations == ()
    assert hated.proved
    assert hated.proof_depths == (1, 1, 2, 3)
    assert intensity.proved
    assert intensity.proof_depths == (1, 1, 3, 3, 4, 4, 4, 4, 5)
    assert intensity.forbidden_violations == ()
    assert external_cause.proved
    assert external_cause.proof_depths == (1, 4, 5, 6, 7)
    assert external_cause.forbidden_violations == ()


def test_spinolog_extensions_remain_outside_systematic_layer() -> None:
    proposition_20_bis = run_case(
        SYSTEMATIC_ROOT,
        "E3P20",
        "spinolog_20bis_non_importee",
    )
    proposition_21 = run_case(
        SYSTEMATIC_ROOT,
        "E3P21",
        "joies_partagees_et_intensite",
    )

    assert proposition_20_bis.proved
    assert proposition_20_bis.forbidden_violations == ()
    assert proposition_21.proved
    assert proposition_21.forbidden_violations == ()
    assert proposition_21.initial_fact_count == 17
    assert proposition_21.derived_fact_count > len(proposition_21.goals)
    assert proposition_21.total_fact_count == (
        proposition_21.initial_fact_count + proposition_21.derived_fact_count
    )
    assert proposition_21.derivation_count >= proposition_21.derived_fact_count
    assert "E3P21D_ordre_intensite_joie_transmis" in (
        proposition_21.activated_rule_names
    )


def test_e3p23_to_e3p26_invert_affects_without_flattening_contexts() -> None:
    contrary_affect = run_case(
        SYSTEMATIC_ROOT,
        "E3P23",
        "tristesses_chose_haie_produisent_joies",
    )
    external_cause = run_case(
        SYSTEMATIC_ROOT,
        "E3P24",
        "haine_envers_cause_de_joie",
    )
    loved_assertions = run_case(
        SYSTEMATIC_ROOT,
        "E3P25",
        "affirmer_et_nier_de_la_chose_aimee",
    )
    hated_assertions = run_case(
        SYSTEMATIC_ROOT,
        "E3P26",
        "affirmer_et_nier_de_la_chose_haie",
    )

    assert contrary_affect.proved
    assert contrary_affect.proof_depths == (1, 1, 3, 3, 4, 4, 4, 4, 5)
    assert external_cause.proved
    assert external_cause.proof_depths == (1, 2, 2, 3, 4)
    assert loved_assertions.proved
    assert loved_assertions.proof_depths == (4, 4, 6, 6, 6, 6)
    assert loved_assertions.forbidden_violations == ()
    assert hated_assertions.proved
    assert hated_assertions.proof_depths == (2, 2, 3, 3, 3, 3)
    assert hated_assertions.forbidden_violations == ()


def test_e3p24_and_e3p26_scholia_define_social_affects() -> None:
    envy = run_case(SYSTEMATIC_ROOT, "E3P24", "scolie_envie")
    estimates = run_case(SYSTEMATIC_ROOT, "E3P26", "scolie_estimes")

    assert envy.proved
    assert envy.proof_depths == (1,)
    assert estimates.proved
    assert estimates.proof_depths == (1, 1, 1, 1)


def test_e3p27_imitates_affects_only_through_relevant_similarity() -> None:
    imitation = run_case(
        SYSTEMATIC_ROOT,
        "E3P27",
        "imitation_de_trois_affects",
    )
    simple_trait = run_case(
        SYSTEMATIC_ROOT,
        "E3P27",
        "simple_trait_sans_similitude_corporelle",
    )

    assert imitation.proved
    assert imitation.proof_depths == (1, 2, 2, 2, 2, 3, 3)
    assert imitation.forbidden_violations == ()
    assert simple_trait.proved
    assert simple_trait.forbidden_violations == ()


def test_e3p28_to_e3p30_connect_conduct_social_affects_and_internal_cause() -> None:
    conduct = run_case(
        SYSTEMATIC_ROOT,
        "E3P28",
        "procurer_joie_et_ecarter_tristesse",
    )
    approval = run_case(
        SYSTEMATIC_ROOT,
        "E3P29",
        "approbation_et_aversion_des_hommes",
    )
    self_consideration = run_case(
        SYSTEMATIC_ROOT,
        "E3P30",
        "consideration_de_soi_par_affects_d_autrui",
    )
    no_glory = run_case(
        SYSTEMATIC_ROOT,
        "E3P30",
        "joie_interieure_sans_louange_non_gloire",
    )

    assert conduct.proved
    assert conduct.proof_depths == (1, 1, 1, 1, 1, 1, 1)
    assert approval.proved
    assert approval.proof_depths == (1, 2, 3, 4, 2, 3, 4)
    assert self_consideration.proved
    assert self_consideration.proof_depths == (1, 2, 3, 4, 1, 2, 3, 4)
    assert no_glory.proved
    assert no_glory.forbidden_violations == ()


def test_e3p31_and_e3p32_preserve_similarity_and_exclusive_possession() -> None:
    agreement = run_case(
        SYSTEMATIC_ROOT,
        "E3P31",
        "accord_amour_desir_haine",
    )
    exclusive = run_case(
        SYSTEMATIC_ROOT,
        "E3P32",
        "possession_exclusive_et_envie",
    )
    shareable = run_case(
        SYSTEMATIC_ROOT,
        "E3P32",
        "objet_non_exclusif",
    )

    assert agreement.proved
    assert agreement.proof_depths == (1, 2, 2, 2)
    assert exclusive.proved
    assert exclusive.proof_depths == (1, 1, 2, 3, 3, 4, 5, 6)
    assert exclusive.forbidden_violations == ()
    assert shareable.proved
    assert shareable.forbidden_violations == ()


def test_e3p33_requires_similarity_and_preserves_reciprocity_context() -> None:
    reciprocity = run_case(
        SYSTEMATIC_ROOT,
        "E3P33",
        "reciprocite_par_similitude",
    )
    no_similarity = run_case(
        SYSTEMATIC_ROOT,
        "E3P33",
        "amour_sans_similitude",
    )
    spinolog_dual = run_case(
        SYSTEMATIC_ROOT,
        "E3P33",
        "spinolog_33bis_non_importee",
    )

    assert reciprocity.proved
    assert reciprocity.proof_depths == (1, 1, 2, 3)
    assert reciprocity.forbidden_violations == ()
    assert no_similarity.proved
    assert no_similarity.forbidden_violations == ()
    assert spinolog_dual.proved
    assert spinolog_dual.forbidden_violations == ()


def test_e3p34_and_e3p35_preserve_intensity_and_jealousy_triangle() -> None:
    glory = run_case(
        SYSTEMATIC_ROOT,
        "E3P34",
        "deux_degres_d_affection_reciproque",
    )
    jealousy = run_case(
        SYSTEMATIC_ROOT,
        "E3P35",
        "triangle_de_jalousie",
    )
    weaker_link = run_case(
        SYSTEMATIC_ROOT,
        "E3P35",
        "lien_rival_moins_etroit",
    )

    assert glory.proved
    assert glory.proof_depths == (1, 2, 3, 5, 7, 7, 8)
    assert glory.forbidden_violations == ()
    assert jealousy.proved
    assert jealousy.proof_depths == (
        1,
        1,
        2,
        2,
        2,
        3,
        4,
        6,
        6,
        8,
        9,
        9,
        10,
        10,
    )
    assert jealousy.forbidden_violations == ()
    assert weaker_link.proved
    assert weaker_link.forbidden_violations == ()


def test_e3p36_desires_only_the_remembered_configuration() -> None:
    remembered = run_case(
        SYSTEMATIC_ROOT,
        "E3P36",
        "souvenir_avec_memes_circonstances",
    )
    other_circumstances = run_case(
        SYSTEMATIC_ROOT,
        "E3P36",
        "circonstances_non_associees",
    )

    assert remembered.proved
    assert remembered.proof_depths == (1, 2, 3, 5, 6, 7, 1, 1, 4, 8)
    assert remembered.forbidden_violations == ()
    assert other_circumstances.proved
    assert other_circumstances.forbidden_violations == ()


def test_e3p37_and_e3p38_transmit_qualitative_intensity() -> None:
    desire_order = run_case(
        SYSTEMATIC_ROOT,
        "E3P37",
        "ordre_deux_tristesses",
    )
    hate_after_love = run_case(
        SYSTEMATIC_ROOT,
        "E3P38",
        "haine_apres_amour_aboli",
    )
    love_not_abolished = run_case(
        SYSTEMATIC_ROOT,
        "E3P38",
        "amour_non_entierement_aboli",
    )

    assert desire_order.proved
    assert desire_order.proof_depths == (1, 1, 2)
    assert hate_after_love.proved
    assert hate_after_love.proof_depths == (1, 1, 2, 3, 4, 4, 4)
    assert love_not_abolished.proved
    assert love_not_abolished.forbidden_violations == ()


def test_e3p39_models_the_greater_evil_exception_explicitly() -> None:
    ordinary_conduct = run_case(
        SYSTEMATIC_ROOT,
        "E3P39",
        "haine_sans_peur_et_amour",
    )
    fear = run_case(
        SYSTEMATIC_ROOT,
        "E3P39",
        "peur_d_un_mal_plus_grand",
    )

    assert ordinary_conduct.proved
    assert ordinary_conduct.proof_depths == (1, 1, 2, 1, 1)
    assert ordinary_conduct.forbidden_violations == ()
    assert fear.proved
    assert fear.proof_depths == (1, 1, 1, 2, 3, 3)
    assert fear.forbidden_violations == ()


def test_e3p40_separates_reciprocal_hate_shame_and_revenge() -> None:
    reciprocal_hate = run_case(
        SYSTEMATIC_ROOT,
        "E3P40",
        "reciprocite_sans_cause",
    )
    shame = run_case(
        SYSTEMATIC_ROOT,
        "E3P40",
        "cause_juste_produit_honte",
    )
    revenge = run_case(
        SYSTEMATIC_ROOT,
        "E3P40",
        "corollaire_vengeance",
    )
    no_similarity = run_case(
        SYSTEMATIC_ROOT,
        "E3P40",
        "chose_non_semblable",
    )

    assert reciprocal_hate.proved
    assert reciprocal_hate.proof_depths == (1, 1, 2, 3, 4)
    assert reciprocal_hate.forbidden_violations == ()
    assert shame.proved
    assert shame.proof_depths == (1, 2)
    assert shame.forbidden_violations == ()
    assert revenge.proved
    assert revenge.proof_depths == (4, 5, 6, 6, 7)
    assert revenge.forbidden_violations == ()
    assert no_similarity.proved
    assert no_similarity.forbidden_violations == ()


def test_e3p41_separates_love_gratitude_glory_and_cruelty() -> None:
    reciprocity = run_case(
        SYSTEMATIC_ROOT,
        "E3P41",
        "reciprocite_sans_cause",
    )
    gratitude = run_case(
        SYSTEMATIC_ROOT,
        "E3P41",
        "gratitude_reciproque",
    )
    glory = run_case(
        SYSTEMATIC_ROOT,
        "E3P41",
        "juste_cause_produit_gloire",
    )
    cruelty = run_case(
        SYSTEMATIC_ROOT,
        "E3P41",
        "haine_prevalente_cruaute",
    )

    assert reciprocity.proved
    assert reciprocity.proof_depths == (1, 2, 3, 4, 5)
    assert reciprocity.forbidden_violations == ()
    assert gratitude.proved
    assert gratitude.proof_depths == (4, 5, 6, 6)
    assert gratitude.forbidden_violations == ()
    assert glory.proved
    assert glory.proof_depths == (1, 2)
    assert cruelty.proved
    assert cruelty.forbidden_violations == ()


def test_e3p42_requires_positive_ingratitude_to_derive_sadness() -> None:
    ingratitude = run_case(
        SYSTEMATIC_ROOT,
        "E3P42",
        "bienfait_par_amour_recu_ingratement",
    )
    no_ingratitude = run_case(
        SYSTEMATIC_ROOT,
        "E3P42",
        "bienfait_recu_sans_ingratitude",
    )

    assert ingratitude.proved
    assert ingratitude.proof_depths == (1, 2, 1, 2, 3)
    assert ingratitude.forbidden_violations == ()
    assert no_ingratitude.proved
    assert no_ingratitude.forbidden_violations == ()


def test_e3p43_distinguishes_added_hate_from_love_victory() -> None:
    increased_hate = run_case(
        SYSTEMATIC_ROOT,
        "E3P43",
        "haine_accrue_par_reciprocite",
    )
    love_wins = run_case(
        SYSTEMATIC_ROOT,
        "E3P43",
        "amour_plus_fort_extirpe_haine",
    )
    love_loses = run_case(
        SYSTEMATIC_ROOT,
        "E3P43",
        "amour_plus_faible_ne_suffit_pas",
    )

    assert increased_hate.proved
    assert increased_hate.proof_depths == (1, 1, 1, 1)
    assert increased_hate.forbidden_violations == ()
    assert love_wins.proved
    assert love_wins.proof_depths == (1, 2, 1, 2, 2, 3, 3)
    assert love_wins.forbidden_violations == ()
    assert love_loses.proved
    assert love_loses.forbidden_violations == ()


def test_e3p44_models_transition_without_erasing_affective_history() -> None:
    conversion = run_case(
        SYSTEMATIC_ROOT,
        "E3P44",
        "haine_vaincue_convertie_en_amour",
    )
    no_victory = run_case(
        SYSTEMATIC_ROOT,
        "E3P44",
        "haine_non_vaincue",
    )
    self_harm = run_case(
        SYSTEMATIC_ROOT,
        "E3P44",
        "scolie_refuse_auto_dommage",
    )

    assert conversion.proved
    assert conversion.proof_depths == (1, 2, 2, 3, 2, 3, 3)
    assert conversion.forbidden_violations == ()
    assert no_victory.proved
    assert no_victory.forbidden_violations == ()
    assert self_harm.proved
    assert self_harm.proof_depths == (2,)
    assert self_harm.forbidden_violations == ()


def test_e3p45_preserves_the_triangle_inside_imagination() -> None:
    triangle = run_case(SYSTEMATIC_ROOT, "E3P45", "triangle_de_haine")
    no_similarity = run_case(SYSTEMATIC_ROOT, "E3P45", "tiers_sans_similitude")

    assert triangle.proved
    assert triangle.proof_depths == (1, 2, 3, 4, 5)
    assert triangle.rule_origins[0] == "compilation"
    assert triangle.forbidden_violations == ()
    assert no_similarity.proved
    assert no_similarity.forbidden_violations == ()


def test_e3p46_generalizes_only_under_an_explicit_general_name() -> None:
    social_love = run_case(SYSTEMATIC_ROOT, "E3P46", "joie_sous_nom_de_classe")
    social_hate = run_case(
        SYSTEMATIC_ROOT,
        "E3P46",
        "tristesse_sous_nom_de_nation",
    )
    no_general_name = run_case(
        SYSTEMATIC_ROOT,
        "E3P46",
        "affect_sans_nom_general",
    )

    assert social_love.proved
    assert social_love.proof_depths == (1, 1, 2, 3)
    assert social_love.forbidden_violations == ()
    assert social_hate.proved
    assert social_hate.proof_depths == (1, 1, 2, 3)
    assert social_hate.forbidden_violations == ()
    assert no_general_name.proved
    assert no_general_name.forbidden_violations == ()


def test_e3p47_makes_the_extension_of_e3p27_explicit() -> None:
    mixed_affect = run_case(
        SYSTEMATIC_ROOT,
        "E3P47",
        "destruction_chose_haie_similaire",
    )
    no_similarity = run_case(
        SYSTEMATIC_ROOT,
        "E3P47",
        "destruction_chose_non_similaire",
    )
    memory = run_case(
        SYSTEMATIC_ROOT,
        "E3P47",
        "scolie_souvenir_du_mal_passe",
    )

    assert mixed_affect.proved
    assert mixed_affect.proof_depths == (1, 1, 2, 2, 3, 3)
    assert "interpretative" in mixed_affect.rule_origins
    assert mixed_affect.forbidden_violations == ()
    assert no_similarity.proved
    assert no_similarity.forbidden_violations == ()
    assert memory.proved
    assert memory.proof_depths == (1, 1, 2, 2, 2)


def test_e3p48_separates_reattribution_diminution_and_doubt() -> None:
    destroyed = run_case(
        SYSTEMATIC_ROOT,
        "E3P48",
        "reattribution_totale_amour_et_haine",
    )
    diminished = run_case(
        SYSTEMATIC_ROOT,
        "E3P48",
        "causes_partagees_diminuent",
    )
    insufficient = run_case(
        SYSTEMATIC_ROOT,
        "E3P48",
        "autre_cause_sans_retrait_ni_partage",
    )

    assert destroyed.proved
    assert destroyed.proof_depths == (1, 1, 1, 1)
    assert destroyed.forbidden_violations == ()
    assert diminished.proved
    assert diminished.proof_depths == (1, 1, 1, 1)
    assert diminished.forbidden_violations == ()
    assert insufficient.proved
    assert insufficient.forbidden_violations == ()


def test_e3p49_compares_free_and_necessary_causes_without_doubt() -> None:
    love = run_case(SYSTEMATIC_ROOT, "E3P49", "amour_libre_plus_grand")
    hate = run_case(SYSTEMATIC_ROOT, "E3P49", "haine_libre_plus_grande")
    unequal_motives = run_case(
        SYSTEMATIC_ROOT,
        "E3P49",
        "motifs_differents_non_comparables",
    )

    assert love.proved
    assert love.proof_depths == (1, 1, 2, 3)
    assert love.forbidden_violations == ()
    assert hate.proved
    assert hate.proof_depths == (1, 2, 3)
    assert hate.forbidden_violations == ()
    assert unequal_motives.proved
    assert unequal_motives.forbidden_violations == ()


def test_e3p50_requires_an_affective_association_for_an_omen() -> None:
    good_omen = run_case(SYSTEMATIC_ROOT, "E3P50", "bon_presage")
    bad_omen = run_case(SYSTEMATIC_ROOT, "E3P50", "mauvais_presage")
    neutral = run_case(
        SYSTEMATIC_ROOT,
        "E3P50",
        "chose_neutre_sans_association",
    )

    assert good_omen.proved
    assert good_omen.proof_depths == (1, 2, 3, 3, 3, 3)
    assert bad_omen.proved
    assert bad_omen.proof_depths == (1, 2, 3, 3, 3, 3)
    assert neutral.proved
    assert neutral.forbidden_violations == ()


def test_e3p51_makes_affective_variability_explicit() -> None:
    between_people = run_case(
        SYSTEMATIC_ROOT,
        "E3P51",
        "deux_hommes_meme_objet",
    )
    across_time = run_case(
        SYSTEMATIC_ROOT,
        "E3P51",
        "meme_homme_divers_temps",
    )
    unspecified_manners = run_case(
        SYSTEMATIC_ROOT,
        "E3P51",
        "manieres_non_distinguees",
    )

    assert between_people.proved
    assert between_people.proof_depths == (1, 1, 2)
    assert across_time.proved
    assert across_time.proof_depths == (1, 1, 2, 2)
    assert unspecified_manners.proved
    assert unspecified_manners.forbidden_violations == ()


def test_e3p52_requires_positive_absence_for_isolated_attention() -> None:
    comparison = run_case(
        SYSTEMATIC_ROOT,
        "E3P52",
        "objet_commun_et_objet_singulier",
    )
    no_positive_absence = run_case(
        SYSTEMATIC_ROOT,
        "E3P52",
        "singularite_sans_absence_positive",
    )
    common_trait = run_case(
        SYSTEMATIC_ROOT,
        "E3P52",
        "objet_n_ayant_que_trait_commun",
    )
    wonder = run_case(
        SYSTEMATIC_ROOT,
        "E3P52",
        "etonnement_consternation_veneration_horreur",
    )

    assert comparison.proved
    assert comparison.proof_depths == (1, 1, 1, 1, 2)
    assert no_positive_absence.proved
    assert no_positive_absence.forbidden_violations == ()
    assert common_trait.proved
    assert common_trait.proof_depths == (1, 1, 1, 2)
    assert wonder.proved
    assert wonder.proof_depths == (1, 2, 1, 1)


def test_e3p53_grounds_self_consideration_in_bodily_self_knowledge() -> None:
    self_joy = run_case(
        SYSTEMATIC_ROOT,
        "E3P53",
        "consideration_de_soi_et_puissance",
    )
    disconnected = run_case(
        SYSTEMATIC_ROOT,
        "E3P53",
        "consideration_sans_lien_corporel",
    )
    distinct = run_case(
        SYSTEMATIC_ROOT,
        "E3P53",
        "imagination_plus_distincte",
    )

    assert self_joy.proved
    assert self_joy.proof_depths == (1, 2, 2, 2, 3)
    assert disconnected.proved
    assert disconnected.forbidden_violations == ()
    assert distinct.proved
    assert distinct.proof_depths == (1,)


def test_e3p54_represents_only_with_explicit_content_qualification() -> None:
    powerful = run_case(SYSTEMATIC_ROOT, "E3P54", "contenu_posant_puissance")
    powerless = run_case(SYSTEMATIC_ROOT, "E3P54", "contenu_niant_puissance")
    neutral = run_case(
        SYSTEMATIC_ROOT,
        "E3P54",
        "contenu_sans_rapport_a_puissance",
    )

    assert powerful.proved
    assert powerful.proof_depths == (1, 2, 3, 3)
    assert powerless.proved
    assert powerless.proof_depths == (2, 2)
    assert powerless.forbidden_violations == ()
    assert neutral.proved
    assert neutral.forbidden_violations == ()


def test_e3p55_requires_similarity_for_envy_of_virtue() -> None:
    sadness = run_case(SYSTEMATIC_ROOT, "E3P55", "imagination_impuissance")
    peer = run_case(SYSTEMATIC_ROOT, "E3P55", "envie_envers_pair")
    dissimilar = run_case(SYSTEMATIC_ROOT, "E3P55", "vertu_sans_similitude")
    foreign = run_case(SYSTEMATIC_ROOT, "E3P55", "vertu_etrangere_veneree")

    assert sadness.proved
    assert sadness.proof_depths == (1, 2, 3, 3, 4)
    assert peer.proved
    assert peer.proof_depths == (1, 1, 1)
    assert dissimilar.proved
    assert dissimilar.forbidden_violations == ()
    assert foreign.proved
    assert foreign.proof_depths == (1, 1)


def test_e3p56_constructs_affective_species_without_domain_closure() -> None:
    distinct = run_case(
        SYSTEMATIC_ROOT,
        "E3P56",
        "objets_distincts_joies_distinctes",
    )
    same_nature = run_case(
        SYSTEMATIC_ROOT,
        "E3P56",
        "meme_nature_sans_difference",
    )
    derived = run_case(SYSTEMATIC_ROOT, "E3P56", "affect_derive_et_desir")
    governed = run_case(
        SYSTEMATIC_ROOT,
        "E3P56",
        "conduites_gouvernantes_non_passions",
    )

    assert distinct.proved
    assert distinct.proof_depths == (1, 1, 1, 1, 2)
    assert same_nature.proved
    assert same_nature.forbidden_violations == ()
    assert derived.proved
    assert derived.proof_depths == (1, 2, 3)
    assert governed.proved
    assert governed.proof_depths == (1, 1, 1, 1, 1, 1)


def test_e3p57_ties_affective_difference_to_explicit_essence_difference() -> None:
    desires = run_case(SYSTEMATIC_ROOT, "E3P57", "desirs_de_deux_individus")
    animals = run_case(SYSTEMATIC_ROOT, "E3P57", "cheval_et_homme")
    same_essence = run_case(
        SYSTEMATIC_ROOT,
        "E3P57",
        "essence_non_distinguee",
    )

    assert desires.proved
    assert desires.proof_depths == (1, 1, 2, 2)
    assert animals.proved
    assert animals.proof_depths == (1, 1, 2)
    assert same_essence.proved
    assert same_essence.forbidden_violations == ()


def test_e3p58_derives_active_joy_and_desire_only_from_adequate_ideas() -> None:
    joy = run_case(SYSTEMATIC_ROOT, "E3P58", "joie_issue_idee_adequate")
    desire = run_case(SYSTEMATIC_ROOT, "E3P58", "desir_issu_idee_adequate")
    inadequate = run_case(
        SYSTEMATIC_ROOT,
        "E3P58",
        "affect_issu_idee_inadequate",
    )

    assert joy.proved
    assert joy.proof_depths == (1, 2, 3, 4, 2, 5, 5)
    assert desire.proved
    assert desire.proof_depths == (1, 2, 2, 3, 3, 3)
    assert inadequate.proved
    assert inadequate.proof_depths == (1, 1, 2)
    assert inadequate.forbidden_violations == ()


def test_e3p59_closes_active_affects_and_preserves_scholium_branches() -> None:
    closure = run_case(SYSTEMATIC_ROOT, "E3P59", "joie_et_desir_actifs")
    sadness = run_case(SYSTEMATIC_ROOT, "E3P59", "tristesse_non_active")
    fortitude = run_case(SYSTEMATIC_ROOT, "E3P59", "fermete_et_generosite")
    satiety = run_case(SYSTEMATIC_ROOT, "E3P59", "degout_et_lassitude")

    assert closure.proved
    assert closure.proof_depths == (1, 2, 2, 1, 1, 2, 2)
    assert sadness.proved
    assert sadness.proof_depths == (1, 1)
    assert sadness.forbidden_violations == ()
    assert fortitude.proved
    assert fortitude.proof_depths == (1, 1, 1, 1)
    assert satiety.proved
    assert satiety.proof_depths == (1, 1, 2, 2)


def test_each_systematic_manifest_since_e3p04_has_passing_counter_cases() -> None:
    for proposition in range(4, 60):
        theorem_id = f"E3P{proposition:02d}"
        manifest = yaml.safe_load(
            (SYSTEMATIC_ROOT / "theorems" / f"{theorem_id}.yaml").read_text(
                encoding="utf-8"
            )
        )
        counter_cases = [
            case for case in manifest["cases"] if case.get("must_not_derive")
        ]

        assert counter_cases
        for counter_case in counter_cases:
            result = run_case(SYSTEMATIC_ROOT, theorem_id, counter_case["id"])
            assert result.proved
            assert result.forbidden_facts
            assert result.forbidden_violations == ()


def test_manifest_expected_depths_match_executable_provenance() -> None:
    for theorem_path in sorted((SYSTEMATIC_ROOT / "theorems").glob("E3P*.yaml")):
        manifest = yaml.safe_load(theorem_path.read_text(encoding="utf-8"))
        for case in manifest["cases"]:
            result = run_case(SYSTEMATIC_ROOT, theorem_path.stem, case["id"])
            assert result.proved
            if "proof_depths" in case["expected"]:
                assert result.proof_depths == tuple(case["expected"]["proof_depths"])


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


def test_systematic_manifests_load_only_current_proof_and_prior_theorems() -> None:
    for proposition in range(4, 60):
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
