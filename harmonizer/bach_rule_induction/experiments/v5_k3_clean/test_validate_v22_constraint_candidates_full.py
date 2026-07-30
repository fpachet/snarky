from __future__ import annotations

import k3
import validate_v22_constraint_candidates_full as full


def test_constraint_families_remain_separate_from_soft_rule_groups() -> None:
    assert (
        full.constraint_family(
            k3.FeatureSpec(
                "pair_abs_class_preserved_same_sign",
                0,
                1,
                7,
            )
        )
        == "parallel_preserved_interval"
    )
    assert (
        full.constraint_family(
            k3.FeatureSpec(
                "central_named_chord_degree_quality",
                -1,
                value=0,
                second_value=3,
            )
        )
        == "named_harmonic_exclusion"
    )
