from __future__ import annotations

from harmonizer.bach_rule_induction.rule_profiles import load_rule_base


def test_learned_profile_has_no_historical_rule_ids_or_inheritance() -> None:
    learned = load_rule_base("learned")

    assert learned.id == "S-LEARNED"
    assert learned.inherited_profiles == ()
    assert len(learned.rule_ids) == 7
    assert all(rule_id.startswith("R-LEARNED-") for rule_id in learned.rule_ids)
    assert set(learned.rule_ids) == set(learned.weight_by_rule)
    assert not any(
        path.name
        in {
            "harmonic_form.rules",
            "melodic_roles.rules",
            "vertical_conformance.rules",
            "voice_leading_conformance.rules",
            "note_generation.rules",
        }
        for path in learned.rule_files
    )


def test_historical_and_hybrid_profiles_preserve_provenance() -> None:
    historical = load_rule_base("historical")
    learned = load_rule_base("learned")
    hybrid = load_rule_base("hybrid")

    assert historical.id == "S-HISTORICAL"
    assert all(not rule_id.startswith("R-LEARNED-") for rule_id in historical.rule_ids)
    assert hybrid.id == "S-HYBRID"
    assert hybrid.inherited_profiles == ("historical", "learned")
    assert set(hybrid.rule_ids) == set(historical.rule_ids) | set(learned.rule_ids)
    assert set(hybrid.rule_files) == set(historical.rule_files) | set(
        learned.rule_files
    )
