from __future__ import annotations

from pathlib import Path

import aggregate_v6_multiseed_control as v6_multiseed
import apply_v6_control_delta as v6_control_apply
import export_v5_16_factor_catalogue as factor_export
import export_v5_16_factor_program as factor_program_export
import fit_joint_pseudolikelihood as joint_pl
import fit_v7_residual_factors as v7_fit
import k3
import local_tonality
import numpy as np
import pytest
import refit_v6_generative_weights as v6_refit
import run_exact_factor_reinduction as exact_reinduction
import run_k3_ablation as ablation
import run_k3_null_max_calibration as calibration
import run_rhythmic_gibbs as rhythmic
import run_v6_factor_controllability as v6_control
import run_v6_residual_feature_diagnostic as v6_residual
import snarky_choice_bridge


def _dataset() -> k3.K3Dataset:
    return k3.K3Dataset(
        piece_ids=np.asarray(["p1", "p2"]),
        offsets=np.asarray([[0, 1, 2], [0, 1, 2]], dtype=np.float32),
        voice_indices=np.asarray([0, 1], dtype=np.int8),
        blocks=np.asarray(
            [
                [[67, 64, 55, 48], [69, 66, 57, 50], [71, 67, 59, 52]],
                [[72, 64, 55, 48], [72, 65, 57, 50], [74, 67, 59, 52]],
            ],
            dtype=np.int16,
        ),
        attacks=np.ones((2, 3, 4), dtype=bool),
        candidate_min=60,
        candidate_max=72,
    )


def test_model_version_ignores_k3_namespace_prefix() -> None:
    assert rhythmic._model_version("K3-V19-UNANIMOUS-FULL-1") == "V19"
    assert rhythmic._model_version("V5.7-K3-CONTEXTUAL") == "V5.7"


def test_catalogue_is_numeric_and_has_no_historical_rule_names() -> None:
    labels = " ".join(feature.label.lower() for feature in k3.feature_catalogue())

    assert "parallel" not in labels
    assert "direct" not in labels
    assert "overlap" not in labels
    assert "leading" not in labels
    assert "v-1" not in labels
    assert "all_voices" in labels


def test_preserved_pair_feature_uses_previous_and_central_blocks() -> None:
    data = _dataset().take(np.asarray([0]))
    feature = k3.FeatureSpec(
        "pair_abs_class_preserved_same_sign",
        target_voice=0,
        other_voice=3,
        value=7,
        complexity=4,
    )

    mask = k3.feature_mask(data, feature)

    # Previous soprano/bass interval is 7 mod 12. Candidate 69 over bass 50
    # preserves class 7 while both voices move upward.
    assert mask[0, 69 - data.candidate_min]
    assert not mask[0, 68 - data.candidate_min]


def test_counterfactual_pitch_propagates_into_a_following_hold() -> None:
    data = _dataset().take(np.asarray([0]))
    data.attacks[0, 2, 0] = False
    feature = k3.FeatureSpec(
        "abs_class_to_next",
        target_voice=0,
        value=0,
    )

    mask = k3.feature_mask(data, feature)

    assert mask.all()


def test_universal_step_feature_applies_to_every_voice() -> None:
    data = _dataset()
    feature = k3.FeatureSpec(
        "any_voice_adjacent_step_gt",
        target_voice=-1,
        value=2,
    )

    mask = k3.feature_mask(data, feature)

    assert mask[0, 72 - data.candidate_min]
    assert mask[1, 60 - data.candidate_min]


def test_adjacent_step_sizes_propagate_holds() -> None:
    data = _dataset().take(np.asarray([0]))
    data.attacks[0, 2, 0] = False
    sizes = k3.adjacent_step_sizes(data)

    candidate = 70
    expected = abs(candidate - data.blocks[0, 0, 0])
    assert sizes[0, candidate - data.candidate_min] == expected


def test_contextual_features_distinguish_key_and_attacked_repetition() -> None:
    data = _dataset()
    data.tonic_pcs = np.asarray([0, 2], dtype=np.int8)
    data.modes = np.asarray([0, 1], dtype=np.int8)
    data.metric_levels = np.asarray([3, 0], dtype=np.int8)

    relative = k3.feature_mask(
        data,
        k3.FeatureSpec("tonic_relative_class_mode", -1, value=9, second_value=0),
    )
    repeated = k3.feature_mask(
        data,
        k3.FeatureSpec("attacked_repeat_from_previous", -1),
    )
    bass_repeated = k3.feature_mask(
        data,
        k3.FeatureSpec("attacked_repeat_from_previous", 3),
    )

    assert relative[0, 69 - data.candidate_min]
    assert not relative[1, 71 - data.candidate_min]
    assert repeated[0, 67 - data.candidate_min]
    assert repeated[1, 64 - data.candidate_min]
    assert not bass_repeated.any()


def test_voice_tonal_baseline_has_one_distribution_per_voice_and_mode() -> None:
    data = _dataset()
    data.tonic_pcs = np.asarray([0, 2], dtype=np.int8)
    data.modes = np.asarray([0, 1], dtype=np.int8)
    data.metric_levels = np.asarray([3, 0], dtype=np.int8)

    logits = k3.learn_voice_tonal_logits(data)
    scores = k3.contextual_base_scores(
        data,
        k3.learn_register_logits(data),
        logits,
    )

    assert logits.shape == (4, 2, 12)
    assert scores.shape == (data.size, data.candidate_pitches.size)


def test_rare_tonal_features_encode_local_licences() -> None:
    data = _dataset().take(np.asarray([0]))
    data.tonic_pcs = np.asarray([0], dtype=np.int8)
    data.modes = np.asarray([0], dtype=np.int8)
    data.metric_levels = np.asarray([1], dtype=np.int8)
    rare_a = 1 << 9

    generic = k3.feature_mask(
        data,
        k3.FeatureSpec(
            "rare_tonal_class",
            0,
            value=rare_a,
            second_value=0,
        ),
    )
    passing = k3.feature_mask(
        data,
        k3.FeatureSpec(
            "rare_tonal_immediate_passing",
            0,
            value=rare_a,
            second_value=0,
        ),
    )
    weak = k3.feature_mask(
        data,
        k3.FeatureSpec(
            "rare_tonal_weak_metric",
            0,
            value=rare_a,
            second_value=0,
        ),
    )

    candidate = 69
    index = candidate - data.candidate_min
    assert generic[0, index]
    assert passing[0, index]
    assert weak[0, index]
    assert not generic[0, 68 - data.candidate_min]


def test_rare_tonal_catalogue_can_exclude_the_fixed_soprano() -> None:
    data = _dataset()
    data.tonic_pcs = np.asarray([0, 2], dtype=np.int8)
    data.modes = np.asarray([0, 1], dtype=np.int8)
    data.metric_levels = np.asarray([3, 0], dtype=np.int8)

    features = k3.rare_tonal_feature_catalogue(
        data,
        0.1,
        voices=(1, 2, 3),
    )

    assert features
    assert {feature.target_voice for feature in features} == {1, 2, 3}
    assert all(feature.kind.startswith("rare_tonal_") for feature in features)


def test_interval_context_catalogue_is_class_neutral() -> None:
    features = k3.interval_context_feature_catalogue()

    assert len(features) == 96
    assert {feature.value for feature in features} == set(range(12))
    assert all(feature.target_voice == -1 for feature in features)


def test_directed_metric_context_catalogue_is_complete_and_neutral() -> None:
    features = k3.directed_metric_context_feature_catalogue()
    kinds = {feature.kind for feature in features}

    assert len(features) == 610
    assert kinds == {
        "any_pair_central_abs_class_target_passing_metric",
        "central_pair_abs_class_metric",
        "bass_abs_step_from_previous_gt_metric",
        "bass_tonic_transition_metric",
    }
    pair_features = [
        feature
        for feature in features
        if feature.kind == "central_pair_abs_class_metric"
    ]
    assert len(pair_features) == 288
    assert {feature.value for feature in pair_features} == set(range(12))


def test_directed_metric_trajectory_catalogue_is_complete_and_neutral() -> None:
    features = k3.directed_metric_trajectory_feature_catalogue()

    assert len(features) == 2016
    assert len({feature.key for feature in features}) == 2016
    assert {feature.value for feature in features} == set(range(12))
    assert {feature.second_value for feature in features} == {0, 1}
    assert {feature.target_voice for feature in features} == set(range(4))


def test_directed_pair_and_bass_metric_contexts_activate_locally() -> None:
    data = _dataset().take(np.asarray([0]))
    data.metric_levels = np.asarray([3], dtype=np.int8)
    pair = k3.FeatureSpec(
        "central_pair_abs_class_metric",
        0,
        1,
        value=3,
        second_value=1,
        complexity=3,
    )
    bass_motion = k3.FeatureSpec(
        "bass_abs_step_from_previous_gt_metric",
        3,
        value=4,
        second_value=1,
        complexity=3,
    )

    pair_mask = k3.feature_mask(data, pair)
    bass_mask = k3.feature_mask(data, bass_motion)

    assert pair_mask[0, 69 - data.candidate_min]
    assert not pair_mask[0, 68 - data.candidate_min]
    assert not bass_mask[0].any()


def test_directed_pair_trajectory_detects_other_voice_step_resolution() -> None:
    data = _dataset().take(np.asarray([0]))
    data.metric_levels = np.asarray([3], dtype=np.int8)
    data.blocks[0, 1, 1] = 68
    data.blocks[0, 2, 1] = 67
    data.attacks[0, 2, 1] = True
    resolved = k3.FeatureSpec(
        "central_pair_abs_class_metric_other_step_resolved",
        0,
        1,
        value=1,
        second_value=1,
        complexity=4,
    )
    held_and_resolved = k3.FeatureSpec(
        "central_pair_abs_class_metric_other_held_step_resolved",
        0,
        1,
        value=1,
        second_value=1,
        complexity=5,
    )

    resolved_mask = k3.feature_mask(data, resolved)
    held_mask = k3.feature_mask(data, held_and_resolved)

    assert resolved_mask[0, 69 - data.candidate_min]
    assert not held_mask[0, 69 - data.candidate_min]
    data.attacks[0, 1, 1] = False
    held_mask = k3.feature_mask(data, held_and_resolved)
    assert held_mask[0, 69 - data.candidate_min]


def test_interval_context_distinguishes_passing_and_neighbor_motion() -> None:
    data = _dataset().take(np.asarray([0]))
    passing = k3.feature_mask(
        data,
        k3.FeatureSpec(
            "any_pair_central_abs_class_target_passing",
            -1,
            value=3,
            complexity=4,
        ),
    )
    neighbor = k3.feature_mask(
        data,
        k3.FeatureSpec(
            "any_pair_central_abs_class_target_neighbor",
            -1,
            value=3,
            complexity=4,
        ),
    )

    assert passing[0, 69 - data.candidate_min]
    assert not passing[0, 68 - data.candidate_min]
    assert not neighbor[0, 69 - data.candidate_min]
    data.blocks[0, 2, 0] = data.blocks[0, 0, 0]
    neighbor = k3.feature_mask(
        data,
        k3.FeatureSpec(
            "any_pair_central_abs_class_target_neighbor",
            -1,
            value=3,
            complexity=4,
        ),
    )
    assert neighbor[0, 69 - data.candidate_min]


def test_interval_context_detects_held_other_voice_resolution() -> None:
    data = _dataset().take(np.asarray([0]))
    data.blocks[0, 1, 1] = data.blocks[0, 0, 1]
    data.blocks[0, 2, 1] = data.blocks[0, 1, 1] + 1
    data.attacks[0, 1, 1] = False
    feature = k3.FeatureSpec(
        "any_pair_central_abs_class_other_held_step_resolved",
        -1,
        value=5,
        complexity=4,
    )

    mask = k3.feature_mask(data, feature)

    assert mask[0, 69 - data.candidate_min]
    assert not mask[0, 70 - data.candidate_min]


def test_v10_grammar_extends_v6_without_mutating_it() -> None:
    grammar_path = (
        Path(__file__).resolve().parents[2]
        / "factor_bases/k3_v6_induced/grammar_v10_interval_context.yaml"
    )
    grammar = exact_reinduction._load_grammar(grammar_path)
    kinds = {
        kind
        for family in grammar["families"]
        for kind in family["feature_kinds"]
    }

    assert grammar["id"] == "K3-V10-INTERVAL-CONTEXT-GRAMMAR-1"
    assert grammar["extensions"]["interval_context_licenses"]
    assert "any_voice_adjacent_step_gt" in kinds
    assert "any_pair_central_abs_class_target_passing" in kinds


def test_v13_grammar_adds_only_neutral_directed_metric_relations() -> None:
    grammar_path = (
        Path(__file__).resolve().parents[2]
        / "factor_bases/k3_v6_induced/grammar_v13_directed_metric_context.yaml"
    )
    grammar = exact_reinduction._load_grammar(grammar_path)
    kinds = {
        kind
        for family in grammar["families"]
        for kind in family["feature_kinds"]
    }

    assert grammar["id"] == "K3-V13-DIRECTED-METRIC-CONTEXT-GRAMMAR-1"
    assert grammar["extensions"]["directed_metric_context_licenses"]
    assert "central_pair_abs_class_metric" in kinds
    assert "bass_tonic_transition_metric" in kinds


def test_v14_grammar_adds_full_directed_metric_trajectory_relations() -> None:
    grammar_path = (
        Path(__file__).resolve().parents[2]
        / "factor_bases/k3_v6_induced/grammar_v14_directed_metric_trajectory.yaml"
    )
    grammar = exact_reinduction._load_grammar(grammar_path)
    kinds = {
        kind
        for family in grammar["families"]
        for kind in family["feature_kinds"]
    }

    assert grammar["id"] == "K3-V14-DIRECTED-METRIC-TRAJECTORY-GRAMMAR-1"
    assert grammar["extensions"]["directed_metric_trajectory_licenses"]
    assert "central_pair_abs_class_metric_other_step_resolved" in kinds
    assert "central_pair_abs_class_metric_target_passing" in kinds


def test_v11_grammar_adds_train_defined_tonal_licences() -> None:
    grammar_path = (
        Path(__file__).resolve().parents[2]
        / "factor_bases/k3_v6_induced/grammar_v11_tonal_licenses.yaml"
    )
    grammar = exact_reinduction._load_grammar(grammar_path)
    kinds = {
        kind
        for family in grammar["families"]
        for kind in family["feature_kinds"]
    }

    assert grammar["id"] == "K3-V11-TONAL-LICENSE-GRAMMAR-1"
    assert grammar["extensions"]["interval_context_licenses"]
    assert grammar["extensions"]["rare_tonal_threshold"] == 0.02
    assert "rare_tonal_class" in kinds
    assert "rare_tonal_immediate_passing" in kinds


def test_rare_tonal_vertical_feature_uses_candidate_pcset() -> None:
    data = _dataset().take(np.asarray([0]))
    data.tonic_pcs = np.asarray([0], dtype=np.int8)
    data.modes = np.asarray([0], dtype=np.int8)
    data.metric_levels = np.asarray([1], dtype=np.int8)
    major_triad = sum(1 << pitch_class for pitch_class in {0, 4, 7})
    feature = k3.FeatureSpec(
        "rare_tonal_bass_pcset",
        0,
        value=1 << 9,
        second_value=major_triad,
    )

    mask = k3.feature_mask(data, feature)

    assert mask[0, 69 - data.candidate_min]
    assert not mask[0, 68 - data.candidate_min]


def test_contextual_vertical_signatures_are_candidate_dependent() -> None:
    data = _dataset().take(np.asarray([0]))
    data.tonic_pcs = np.asarray([0], dtype=np.int8)
    data.modes = np.asarray([0], dtype=np.int8)
    data.metric_levels = np.asarray([3], dtype=np.int8)

    signatures = k3.central_tonic_pcset_signatures(data)

    expected = sum(1 << pitch_class for pitch_class in {0, 2, 6, 9})
    assert signatures[0, 72 - data.candidate_min] == expected
    assert signatures[0, 71 - data.candidate_min] != expected


def test_following_signature_propagates_a_central_hold() -> None:
    data = _dataset().take(np.asarray([0]))
    data.attacks[0, 2, 0] = False
    central = k3.central_bass_pcset_signatures(data)
    following = k3.bass_pcset_signatures(data, position=2)

    candidate = 69
    index = candidate - data.candidate_min
    expected_central = sum(1 << pitch_class for pitch_class in {0, 4, 7})
    expected_following = sum(1 << pitch_class for pitch_class in {0, 3, 5, 7})

    assert central[0, index] == expected_central
    assert following[0, index] == expected_following


def test_explicit_metric_and_transition_features_are_candidate_dependent() -> None:
    data = _dataset().take(np.asarray([0]))
    data.tonic_pcs = np.asarray([0], dtype=np.int8)
    data.modes = np.asarray([0], dtype=np.int8)
    data.metric_levels = np.asarray([3], dtype=np.int8)
    data.attacks[0, 2, 0] = False
    central = sum(1 << pitch_class for pitch_class in {0, 4, 7})
    following = sum(1 << pitch_class for pitch_class in {0, 3, 5, 7})

    metric = k3.feature_mask(
        data,
        k3.FeatureSpec(
            "central_bass_pcset_metric",
            -1,
            value=central,
            second_value=1,
        ),
    )
    transition = k3.feature_mask(
        data,
        k3.FeatureSpec(
            "bass_pcset_transition",
            -1,
            value=central,
            second_value=following,
        ),
    )
    semitone_on_strong_block = k3.feature_mask(
        data,
        k3.FeatureSpec(
            "any_pair_central_abs_class_metric",
            -1,
            value=1,
            second_value=1,
        ),
    )
    triadic_on_strong_block = k3.feature_mask(
        data,
        k3.FeatureSpec(
            "central_triadic_metric",
            -1,
            value=1,
            second_value=1,
        ),
    )

    assert metric[0, 69 - data.candidate_min]
    assert transition[0, 69 - data.candidate_min]
    assert semitone_on_strong_block[0, 67 - data.candidate_min]
    assert triadic_on_strong_block[0, 69 - data.candidate_min]


def test_context_survives_dataset_round_trip(tmp_path: Path) -> None:
    data = _dataset()
    data.tonic_pcs = np.asarray([0, 2], dtype=np.int8)
    data.modes = np.asarray([0, 1], dtype=np.int8)
    data.metric_levels = np.asarray([3, 0], dtype=np.int8)
    path = tmp_path / "context.npz"

    k3.save_k3_dataset(path, data)
    loaded = k3.load_k3_dataset(path)

    assert np.array_equal(loaded.tonic_pcs, data.tonic_pcs)
    assert np.array_equal(loaded.modes, data.modes)
    assert np.array_equal(loaded.metric_levels, data.metric_levels)


def test_local_tonality_collapses_simultaneous_voice_decisions() -> None:
    data = _dataset()
    data.piece_ids[:] = "p1"
    data.offsets[:] = np.asarray([0, 1, 2], dtype=np.float32)
    data.tonic_pcs = np.asarray([0, 0], dtype=np.int8)
    data.modes = np.asarray([0, 0], dtype=np.int8)
    data.metric_levels = np.asarray([3, 3], dtype=np.int8)

    sequences = local_tonality.state_sequences(data)

    assert len(sequences) == 1
    assert sequences[0].offsets.size == 1
    assert sequences[0].histograms.sum() == 16


def test_local_tonality_posterior_is_normalized() -> None:
    sequence = local_tonality.LocalTonalSequence(
        piece_id="p1",
        offsets=np.asarray([1.0, 2.0]),
        histograms=np.asarray(
            [
                [4, 0, 0, 0, 4, 0, 0, 4, 0, 0, 0, 0],
                [4, 0, 0, 0, 4, 0, 0, 4, 0, 0, 0, 0],
            ],
            dtype=np.float64,
        ),
        global_tonic=0,
        mode=0,
    )
    profiles = np.full((2, 12), 0.01)
    profiles[:, [0, 4, 7]] = np.asarray([0.3, 0.2, 0.4])
    profiles /= profiles.sum(axis=1, keepdims=True)

    inference = local_tonality.infer_sequence(
        sequence,
        profiles,
        stay_probability=0.9,
        global_start_probability=0.8,
    )

    assert np.allclose(inference.posterior.sum(axis=1), 1.0)
    assert np.isfinite(inference.log_evidence)
    assert np.array_equal(inference.map_tonics, [0, 0])


def test_ablation_removes_exactly_one_rule_column() -> None:
    matrix = np.arange(2 * 3 * 4).reshape(2, 3, 4)

    reduced = ablation.remove_column(matrix, 1)

    assert reduced.shape == (2, 3, 3)
    assert np.array_equal(reduced, matrix[:, :, [0, 2, 3]])


def test_null_index_permutations_preserve_group_histograms() -> None:
    data = _dataset()
    data.piece_ids[:] = "p1"
    data.voice_indices[:] = 0

    shuffled = calibration.shuffled_choice_indices(data, replicates=3, seed=9)

    assert shuffled.shape == (3, data.size)
    original = data.chosen_indices
    for replicate in shuffled:
        for piece in np.unique(data.piece_ids):
            for voice in range(4):
                rows = (data.piece_ids == piece) & (data.voice_indices == voice)
                assert sorted(replicate[rows]) == sorted(original[rows])


def test_null_shuffle_preserves_piece_voice_pitch_histograms() -> None:
    data = _dataset()
    shuffled = k3.shuffle_choices_within_piece_and_voice(data, seed=7)

    for piece in np.unique(data.piece_ids):
        for voice in range(4):
            original_rows = (data.piece_ids == piece) & (data.voice_indices == voice)
            shuffled_rows = (shuffled.piece_ids == piece) & (
                shuffled.voice_indices == voice
            )
            assert sorted(data.chosen_pitches[original_rows]) == sorted(
                shuffled.chosen_pitches[shuffled_rows]
            )


def test_residual_sign_distinguishes_avoidance_and_preference() -> None:
    data = _dataset()
    probs = np.full((data.size, data.candidate_pitches.size), 1 / 13)
    avoided = np.zeros_like(probs, dtype=bool)
    preferred = np.zeros_like(probs, dtype=bool)
    avoided[:, :4] = True
    preferred[np.arange(data.size), data.chosen_indices] = True

    avoided_stat = k3.residual_statistic(data, probs, avoided, 1, 0.0)
    preferred_stat = k3.residual_statistic(data, probs, preferred, 1, 0.0)

    assert avoided_stat is not None and avoided_stat.gradient < 0
    assert preferred_stat is not None and preferred_stat.gradient > 0


def test_joint_pseudolikelihood_gradient_includes_the_factor_sum() -> None:
    data = _dataset()
    features = (
        k3.FeatureSpec("abs_class_from_previous", 0, value=2),
        k3.FeatureSpec("central_pair_abs_class", 0, other_voice=3, value=7),
    )
    matrix = k3.feature_matrix(data, features)
    weights = np.asarray([0.37, -0.21], dtype=np.float64)
    register = np.zeros((4, data.candidate_pitches.size), dtype=np.float64)

    _, analytic = k3.conditional_nll_gradient(
        data,
        register,
        matrix,
        weights,
    )
    numerical = np.empty_like(weights)
    epsilon = 1e-6
    for index in range(weights.size):
        upper = weights.copy()
        lower = weights.copy()
        upper[index] += epsilon
        lower[index] -= epsilon
        numerical[index] = (
            k3.conditional_nll(data, register, matrix, upper)
            - k3.conditional_nll(data, register, matrix, lower)
        ) / (2.0 * epsilon)

    assert np.allclose(analytic, numerical, atol=1e-7)


def test_joint_pseudolikelihood_combines_unique_base_and_residual_factors() -> None:
    base_feature = k3.FeatureSpec("abs_class_from_previous", 3, value=2)
    residual_feature = k3.FeatureSpec("abs_class_from_previous", 3, value=3)
    structure = {
        "model": {
            "rules": [{"feature": base_feature.to_dict(), "weight": 0.5}],
            "factors": [],
        }
    }
    residual = {
        "selected": [
            {
                "feature": base_feature.to_dict(),
                "description": "duplicate",
                "family": "bass_motion",
                "bach_rate": 0.2,
                "gibbs_rate": 0.1,
                "gradient": 0.1,
                "z_score": 3.0,
                "seed_sign_agreement": True,
            },
            {
                "feature": residual_feature.to_dict(),
                "description": "new",
                "family": "bass_motion",
                "bach_rate": 0.1,
                "gibbs_rate": 0.2,
                "gradient": -0.1,
                "z_score": -3.0,
                "seed_sign_agreement": True,
            },
        ]
    }

    records = joint_pl._combined_records(structure, residual)

    assert [record["feature"].key for record in records] == [
        base_feature.key,
        residual_feature.key,
    ]
    assert [record["origin"] for record in records] == [
        "v6_structure",
        "v6_iteration3_residual",
    ]


def test_gibbs_sampler_is_deterministic_and_preserves_fixed_cells() -> None:
    blocks = np.asarray(
        [
            [72, 64, 55, 48],
            [74, 65, 57, 50],
            [76, 67, 59, 52],
            [74, 65, 57, 50],
        ],
        dtype=np.int16,
    )
    fixed = np.zeros_like(blocks, dtype=bool)
    fixed[:, 0] = True
    logits = np.zeros((4, 13), dtype=np.float64)
    kwargs = {
        "candidate_min": 60,
        "candidate_max": 72,
        "register_logits": logits,
        "features": (),
        "weights": np.asarray([], dtype=np.float64),
        "sweeps": 3,
        "seed": 7,
    }

    first = k3.gibbs_sample(blocks, fixed, **kwargs)
    second = k3.gibbs_sample(blocks, fixed, **kwargs)

    assert np.array_equal(first, second)
    assert np.array_equal(first[:, 0], blocks[:, 0])


def test_attack_segments_cover_holds_until_the_next_attack() -> None:
    attacks = np.ones((5, 4), dtype=bool)
    attacks[2, 1] = False
    attacks[3, 1] = False

    voice_one = [segment for segment in k3.attack_segments(attacks) if segment[2] == 1]

    assert voice_one == [(0, 1, 1), (1, 4, 1), (4, 5, 1)]


def test_attack_segments_preserve_a_leading_hold_as_boundary_segment() -> None:
    attacks = np.ones((5, 4), dtype=bool)
    attacks[0, 0] = False
    attacks[1, 0] = False

    soprano = [segment for segment in k3.attack_segments(attacks) if segment[2] == 0]

    assert soprano == [(0, 2, 0), (2, 3, 0), (3, 4, 0), (4, 5, 0)]


def test_validated_attack_segments_reject_an_unrepresented_internal_attack() -> None:
    attacks = np.ones((5, 4), dtype=bool)
    attacks[2, 0] = False
    blocks = np.full((5, 4), 60, dtype=np.int16)
    blocks[2, 0] = 62

    with pytest.raises(
        ValueError,
        match=r"voice 0 held span \[1, 3\) changes pitch",
    ):
        k3.validated_attack_segments(blocks, attacks)


def test_colored_segment_groups_have_disjoint_factor_scopes() -> None:
    attacks = np.ones((9, 4), dtype=bool)
    segments = k3.attack_segments(attacks)
    groups = k3.independent_segment_groups(segments, attacks.shape[0])

    assert sorted(segment for group in groups for segment in group) == sorted(segments)
    assert any(len(group) > 1 for group in groups)
    for group in groups:
        scopes = [
            set(k3.segment_energy_times(segment, attacks.shape[0]))
            for segment in group
        ]
        for left in range(len(scopes)):
            for right in range(left + 1, len(scopes)):
                assert scopes[left].isdisjoint(scopes[right])


def test_trust_region_preserves_direction_and_bounds_the_largest_step() -> None:
    proposed = np.asarray([0.5, -1.0, 2.0])

    scale = v6_control_apply.trust_region_scale(proposed, 1.0, 0.2)

    assert scale == pytest.approx(0.1)
    assert scale * proposed == pytest.approx([0.05, -0.1, 0.2])


def test_minimum_norm_delta_projects_diagnostic_residuals() -> None:
    jacobian = np.asarray([[1.0, 0.0, 1.0], [0.0, 1.0, 1.0]])
    residual = np.asarray([0.2, -0.1])

    delta, projected = v6_control._minimum_norm_delta(
        jacobian,
        residual,
        ridge=0.0,
        diagnostic_scales=np.ones(2),
    )

    assert projected == pytest.approx(residual)
    assert jacobian @ delta == pytest.approx(residual)


def test_controllability_chain_cache_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "chains.npz"
    chain_ids = ["piece-a#replica=0", "piece-b#replica=0"]
    states = {
        chain_ids[0]: np.arange(20, dtype=np.int16).reshape(5, 4),
        chain_ids[1]: np.arange(24, dtype=np.int16).reshape(6, 4),
    }

    v6_control._write_chain_cache(
        path,
        chain_ids=chain_ids,
        states=states,
        source_model=tmp_path / "model.json",
        weights=np.asarray([0.5, -0.25]),
        candidate_min=36,
        candidate_max=84,
        seed=7613,
    )
    restored, metadata = v6_control._load_chain_cache(path)

    assert list(restored) == chain_ids
    assert all(np.array_equal(restored[key], states[key]) for key in chain_ids)
    assert metadata["schema_version"] == 1
    assert metadata["candidate_min"] == 36
    assert metadata["candidate_max"] == 84
    assert metadata["chains"] == 2


def test_convergence_summary_monitors_gradient_moments() -> None:
    diagnostics = np.tile(np.asarray([[0.0], [1.0]]), (8, 1))
    counts = np.tile(np.asarray([[1.0, 0.0], [0.0, 1.0]]), (8, 1))

    moments = v6_control._convergence_moments(diagnostics, counts)
    ess_q05, drift_q95 = v6_control._convergence_summary(
        diagnostics,
        counts,
        window=4,
    )

    assert moments.shape == (16, 5)
    assert ess_q05 >= 4
    assert drift_q95 == pytest.approx(0.0)


def test_lag1_ess_penalizes_persistent_samples() -> None:
    alternating = np.tile(np.asarray([0.0, 1.0]), 10)[:, None]
    persistent = np.repeat(np.asarray([0.0, 1.0]), 10)[:, None]

    assert (
        v6_control._lag1_effective_sample_sizes(alternating)[0]
        > v6_control._lag1_effective_sample_sizes(persistent)[0]
    )


def test_multiseed_ridge_selects_first_stable_direction() -> None:
    jacobians = np.asarray(
        [
            [[1.0, 0.1], [0.1, 0.03]],
            [[1.0, -0.1], [-0.1, 0.03]],
        ]
    )
    residuals = np.asarray([[0.2, 0.01], [0.2, -0.01]])
    scales = np.ones_like(residuals)

    ridge, delta, records = v6_multiseed.select_stable_ridge(
        jacobians,
        residuals,
        scales,
        (1e-5, 1.0, 10.0),
        minimum_cosine=0.8,
        max_abs_step=0.2,
    )

    assert ridge in {1.0, 10.0}
    selected = next(record for record in records if record["ridge"] == ridge)
    assert selected["passes_stability_gate"]
    assert np.max(np.abs(delta)) <= 0.2


def test_residual_feature_selection_requires_seed_sign_agreement() -> None:
    features = (
        k3.FeatureSpec("abs_class_from_previous", 3, value=2),
        k3.FeatureSpec("abs_class_from_previous", 3, value=3),
    )
    records = [
        {
            "bach_rate": 0.3,
            "gibbs_rate": 0.2,
            "gradient": 0.1,
            "z_score": 4.0,
            "selection_score": 0.2,
            "seed_sign_agreement": True,
        },
        {
            "bach_rate": 0.1,
            "gibbs_rate": 0.2,
            "gradient": -0.1,
            "z_score": -5.0,
            "selection_score": 0.3,
            "seed_sign_agreement": False,
        },
    ]

    selected = v6_residual._select_robust(
        records,
        features,
        per_family=2,
        minimum_rate=0.003,
        minimum_abs_z=2.0,
    )

    assert selected == [0]


def test_v7_chooses_one_factor_per_sign_and_family() -> None:
    records = [
        {
            "family": family,
            "gradient": sign,
            "selection_score": score,
        }
        for family in ("bass_motion", "vertical_context", "sonority_transition")
        for sign, score in ((1.0, 2.0), (-1.0, 3.0), (1.0, 1.0))
    ]

    selected = v7_fit._choose_two_per_family(records)

    assert len(selected) == 6
    for family in ("bass_motion", "vertical_context", "sonority_transition"):
        local = [record for record in selected if record["family"] == family]
        assert sorted(np.sign(record["gradient"]) for record in local) == [-1.0, 1.0]


@pytest.mark.parametrize("update_schedule", ("sequential", "colored"))
def test_rhythmic_gibbs_changes_one_attack_and_its_whole_hold(
    update_schedule: str,
) -> None:
    blocks = np.asarray(
        [
            [62, 60, 60, 60],
            [62, 60, 60, 60],
            [62, 60, 60, 60],
            [62, 61, 60, 60],
            [62, 61, 60, 60],
        ],
        dtype=np.int16,
    )
    attacks = np.ones_like(blocks, dtype=bool)
    attacks[2, 1] = False
    fixed = np.ones_like(blocks, dtype=bool)
    fixed[1:3, 1] = False
    logits = np.zeros((4, 3), dtype=np.float64)
    logits[1] = (-100.0, -100.0, 0.0)

    generated = k3.rhythmic_gibbs_sample(
        blocks,
        attacks,
        fixed,
        candidate_min=60,
        candidate_max=62,
        register_logits=logits,
        features=(),
        weights=np.asarray([], dtype=np.float64),
        sweeps=1,
        seed=3,
        update_schedule=update_schedule,
    )

    assert np.array_equal(generated[1:3, 1], [62, 62])
    assert generated[3, 1] == 61
    assert np.array_equal(generated[:, 0], blocks[:, 0])


def test_rhythmic_gibbs_removes_hard_constraint_candidates() -> None:
    blocks = np.asarray(
        [
            [60, 55, 52, 48],
            [60, 55, 52, 48],
            [60, 55, 52, 48],
        ],
        dtype=np.int16,
    )
    attacks = np.ones_like(blocks, dtype=bool)
    fixed = np.ones_like(blocks, dtype=bool)
    fixed[1, 0] = False
    logits = np.full((4, 15), -100.0, dtype=np.float64)
    logits[0, 12:15] = (0.0, 100.0, 0.0)

    generated = k3.rhythmic_gibbs_sample(
        blocks,
        attacks,
        fixed,
        candidate_min=48,
        candidate_max=62,
        register_logits=logits,
        features=(),
        weights=np.asarray([], dtype=np.float64),
        constraint_features=(
            k3.FeatureSpec(
                "abs_class_from_previous",
                0,
                value=1,
            ),
        ),
        sweeps=1,
        seed=3,
    )

    assert generated[1, 0] != 61


def test_vectorized_segment_energies_match_scalar_worlds() -> None:
    blocks = np.asarray(
        [
            [67, 64, 55, 48],
            [69, 65, 57, 50],
            [71, 67, 59, 52],
            [72, 69, 60, 53],
            [74, 71, 62, 55],
        ],
        dtype=np.int16,
    )
    attacks = np.ones_like(blocks, dtype=bool)
    candidates = np.arange(60, 73, dtype=np.int16)
    register_logits = np.zeros((4, candidates.size), dtype=np.float64)
    tonal_logits = np.zeros((4, 2, 12), dtype=np.float64)
    metric_levels = np.asarray([3, 1, 2, 1, 3], dtype=np.int8)
    features = (
        k3.FeatureSpec("abs_step_from_previous_gt", 0, value=2),
        k3.FeatureSpec(
            "rare_tonal_incoming_step",
            0,
            value=1 << 11,
            second_value=0,
        ),
    )
    weights = np.asarray([-0.7, 0.4])
    affected = range(1, 4)
    vectorized = k3._candidate_state_energies(
        blocks,
        attacks,
        affected,
        2,
        3,
        0,
        candidates,
        candidate_min=60,
        candidate_max=72,
        register_logits=register_logits,
        features=features,
        weights=weights,
        tonal_logits=tonal_logits,
        tonic_pc=0,
        mode=0,
        metric_levels=metric_levels,
    )
    scalar = []
    original = blocks[2, 0]
    for candidate in candidates:
        blocks[2, 0] = candidate
        scalar.append(
            k3._state_energy(
                blocks,
                attacks,
                affected,
                candidate_min=60,
                candidate_max=72,
                register_logits=register_logits,
                features=features,
                weights=weights,
                tonal_logits=tonal_logits,
                tonic_pc=0,
                mode=0,
                metric_levels=metric_levels,
            )
        )
    blocks[2, 0] = original

    assert np.allclose(vectorized, scalar)


def test_compiled_segment_energies_exactly_match_legacy_worlds() -> None:
    blocks = np.asarray(
        [
            [67, 64, 55, 48],
            [69, 65, 57, 50],
            [71, 67, 59, 52],
            [72, 69, 60, 53],
            [74, 71, 62, 55],
        ],
        dtype=np.int16,
    )
    attacks = np.ones_like(blocks, dtype=bool)
    attacks[2, 1] = False
    candidates = np.arange(48, 75, dtype=np.int16)
    register_logits = np.arange(4 * candidates.size, dtype=np.float64).reshape(
        4,
        -1,
    )
    register_logits /= 100
    tonal_logits = np.arange(4 * 2 * 12, dtype=np.float64).reshape(4, 2, 12)
    tonal_logits /= 200
    metric_levels = np.asarray([3, 1, 2, 1, 3], dtype=np.int8)
    features = (
        k3.FeatureSpec("any_voice_adjacent_step_gt", -1, value=2),
        k3.FeatureSpec("central_bass_pcset", -1, value=145),
        k3.FeatureSpec("attacked_repeat_from_previous", 1),
        k3.FeatureSpec("any_pair_central_abs_class", -1, value=2),
    )
    weights = np.asarray([-0.7, 1.2, -0.3, 0.4])
    kwargs = {
        "candidate_min": 48,
        "candidate_max": 74,
        "register_logits": register_logits,
        "features": features,
        "weights": weights,
        "tonal_logits": tonal_logits,
        "tonic_pc": 11,
        "mode": 0,
        "metric_levels": metric_levels,
    }

    compiled = k3._candidate_state_energies(
        blocks,
        attacks,
        range(1, 4),
        1,
        3,
        1,
        candidates,
        **kwargs,
    )
    legacy = k3._candidate_state_energies_legacy(
        blocks,
        attacks,
        range(1, 4),
        1,
        3,
        1,
        candidates,
        **kwargs,
    )
    component_kwargs = {key: value for key, value in kwargs.items() if key != "weights"}
    base_scores, factor_totals = k3.candidate_segment_components(
        blocks,
        attacks,
        range(1, 4),
        1,
        3,
        1,
        candidates,
        **component_kwargs,
    )

    assert np.array_equal(compiled, legacy)
    assert np.array_equal(
        base_scores + factor_totals @ weights,
        compiled,
    )


def test_joint_segment_components_match_scalar_worlds() -> None:
    blocks = np.asarray(
        [
            [67, 64, 55, 48],
            [69, 65, 57, 50],
            [71, 67, 59, 52],
            [72, 69, 60, 53],
        ],
        dtype=np.int16,
    )
    attacks = np.ones_like(blocks, dtype=bool)
    register_logits = np.arange(4 * 27, dtype=np.float64).reshape(4, 27) / 100
    metric_levels = np.asarray([3, 1, 2, 3], dtype=np.int8)
    features = (
        k3.FeatureSpec("any_voice_adjacent_step_gt", -1, value=2),
        k3.FeatureSpec("central_bass_pcset", -1, value=145),
        k3.FeatureSpec("any_pair_central_abs_class", -1, value=2),
    )
    weights = np.asarray([-0.7, 1.2, 0.4])
    segments = ((1, 2, 1), (1, 2, 3))
    candidate_sets = (
        np.asarray([64, 65, 66], dtype=np.int16),
        np.asarray([48, 49], dtype=np.int16),
    )
    kwargs = {
        "candidate_min": 48,
        "candidate_max": 74,
        "register_logits": register_logits,
        "features": features,
        "tonic_pc": 0,
        "mode": 0,
        "metric_levels": metric_levels,
    }

    combinations, base_scores, factor_totals = k3.joint_segment_components(
        blocks,
        attacks,
        range(1, 3),
        segments,
        candidate_sets,
        **kwargs,
    )
    expected = []
    for combination in combinations:
        world = blocks.copy()
        for (start, end, voice), pitch in zip(
            segments,
            combination,
            strict=True,
        ):
            world[start:end, voice] = pitch
        expected.append(
            k3._state_energy(
                world,
                attacks,
                range(1, 3),
                weights=weights,
                **kwargs,
            )
        )

    assert np.allclose(base_scores + factor_totals @ weights, expected)


def test_selected_candidate_feature_path_matches_full_masks() -> None:
    data = _dataset()
    data.tonic_pcs = np.asarray([0, 2], dtype=np.int8)
    data.modes = np.asarray([0, 1], dtype=np.int8)
    data.metric_levels = np.asarray([3, 0], dtype=np.int8)
    features = (
        k3.FeatureSpec("any_voice_adjacent_step_gt", -1, value=2),
        k3.FeatureSpec("any_pair_central_abs_class", -1, value=2),
        k3.FeatureSpec("central_bass_pcset", -1, value=145),
        k3.FeatureSpec("attacked_repeat_from_previous", -1),
        k3.FeatureSpec("tonic_relative_class_mode", -1, value=9, second_value=0),
        k3.FeatureSpec(
            "pair_abs_class_preserved_same_sign",
            target_voice=0,
            other_voice=3,
            value=7,
        ),
    )
    rows = np.arange(data.size)

    for feature in features:
        expected = k3.feature_mask(data, feature)[rows, data.chosen_indices]
        assert np.array_equal(k3.chosen_feature_values(data, feature), expected)


def test_compiled_gibbs_exactly_matches_legacy_seeded_trajectory() -> None:
    blocks = np.asarray(
        [
            [67, 64, 55, 48],
            [69, 65, 57, 50],
            [71, 67, 59, 52],
            [72, 69, 60, 53],
            [74, 71, 62, 55],
        ],
        dtype=np.int16,
    )
    attacks = np.ones_like(blocks, dtype=bool)
    attacks[2, 1] = False
    blocks[2, 1] = blocks[1, 1]
    fixed = np.zeros_like(blocks, dtype=bool)
    fixed[:, 0] = True
    fixed[0, :] = True
    fixed[-1, :] = True
    candidate_min = 48
    candidate_max = 74
    kwargs = {
        "candidate_min": candidate_min,
        "candidate_max": candidate_max,
        "register_logits": np.zeros((4, candidate_max - candidate_min + 1)),
        "features": (
            k3.FeatureSpec("any_voice_adjacent_step_gt", -1, value=2),
            k3.FeatureSpec("any_pair_central_abs_class", -1, value=2),
        ),
        "weights": np.asarray([-0.7, 0.4]),
        "sweeps": 3,
        "seed": 4709,
    }

    compiled = k3.rhythmic_gibbs_sample(
        blocks,
        attacks,
        fixed,
        energy_backend="compiled",
        **kwargs,
    )
    legacy = k3.rhythmic_gibbs_sample(
        blocks,
        attacks,
        fixed,
        energy_backend="legacy",
        **kwargs,
    )

    assert np.array_equal(compiled, legacy)


def test_joint_energy_counts_one_shared_sonority_potential_per_block() -> None:
    blocks = np.asarray(
        [
            [67, 64, 55, 48],
            [69, 66, 57, 50],
            [71, 67, 59, 52],
        ],
        dtype=np.int16,
    )
    attacks = np.ones_like(blocks, dtype=bool)
    major_triad = sum(1 << pitch_class for pitch_class in {0, 4, 7})
    dataset = k3._decision_dataset(
        blocks,
        attacks,
        [1],
        36,
        81,
    )

    assert dataset is not None
    assert dataset.size == 4
    assert k3.shared_potential_rows(dataset).sum() == 1

    energy = k3._state_energy(
        blocks,
        attacks,
        [1],
        candidate_min=36,
        candidate_max=81,
        register_logits=np.zeros((4, 46), dtype=np.float64),
        features=(k3.FeatureSpec("central_bass_pcset", -1, value=major_triad),),
        weights=np.asarray([2.0]),
    )

    assert energy == 2.0


def test_v6_refit_uses_factor_grounding_semantics() -> None:
    data = _dataset()
    data.piece_ids[:] = "p1"
    data.offsets[:] = np.asarray([0, 1, 2], dtype=np.float32)

    shared = v6_refit._grounding_rows(
        data,
        k3.FeatureSpec("central_bass_pcset", -1, value=145),
    )
    bass = v6_refit._grounding_rows(
        data,
        k3.FeatureSpec("attacked_repeat_from_previous", 3),
    )
    decision = v6_refit._grounding_rows(
        data,
        k3.FeatureSpec("any_voice_adjacent_step_gt", -1, value=2),
    )

    assert shared.sum() == 1
    assert not bass.any()
    assert decision.all()


def test_v6_refit_cannot_add_or_remove_factor_structure() -> None:
    source = (Path(__file__).parent / "refit_v6_generative_weights.py").read_text(
        encoding="utf-8"
    )

    assert "feature_catalogue(" not in source
    assert "rare_tonal_feature_catalogue(" not in source
    assert '"new_factor_count": 0' in source
    assert '"factor_structure_changed": False' in source


def test_factor_export_merges_additive_weights_and_preserves_sources() -> None:
    feature = k3.FeatureSpec(
        "abs_class_from_previous",
        target_voice=3,
        value=1,
    )
    model = {
        "base_rule_count": 1,
        "calibration_rule_count": 0,
        "v5_14_rule_count": 0,
        "rules": [
            {"feature": feature.to_dict(), "weight": -0.4},
            {"feature": feature.to_dict(), "weight": -0.2},
        ],
    }

    (merged,) = factor_export.merge_rules(model)

    assert np.isclose(merged["log_weight"], -0.6)
    assert len(merged["sources"]) == 2
    assert factor_export.factor_grounding(feature) == "once_per_target_voice_attack"


def test_factor_export_marks_shared_sonorities_once_per_vertical_block() -> None:
    feature = k3.FeatureSpec(
        "central_bass_pcset_metric",
        target_voice=-1,
        value=145,
        second_value=1,
    )

    assert factor_export.factor_grounding(feature) == "once_per_vertical_block"
    assert factor_export.factor_scope(feature)["voices"] == [
        "soprano",
        "alto",
        "tenor",
        "bass",
    ]


def test_v5_16_factor_program_round_trips_all_weights() -> None:
    catalogue = {
        "counts": {"canonical_factors_after_merge": 2},
        "factors": [
            {
                "id": "F-ONE",
                "parameter": {"log_weight": -0.5},
            },
            {
                "id": "F-TWO",
                "parameter": {"log_weight": 1.25},
            },
        ],
    }

    text = factor_program_export.render_factor_program(catalogue)
    (group,) = factor_program_export.parse_factor_groups(text)

    assert [factor.name for factor in group.factors] == ["F-ONE", "F-TWO"]
    assert [factor.parameter.log_weight for factor in group.factors] == [
        -0.5,
        1.25,
    ]


def test_snarky_choice_bridge_preserves_v5_16_conditionals() -> None:
    data = _dataset()
    data.tonic_pcs = np.asarray([0, 2], dtype=np.int8)
    data.modes = np.asarray([0, 1], dtype=np.int8)
    data.metric_levels = np.asarray([3, 0], dtype=np.int8)
    program = snarky_choice_bridge.load_choice_program()

    compiled = program.evaluate(data)
    source = snarky_choice_bridge.source_model_evaluation(data)

    assert len(program.factors) == 41
    assert np.all(compiled.positive_weights > 0)
    assert np.allclose(compiled.probabilities.sum(axis=1), 1.0)
    assert np.allclose(compiled.local_scores, source.local_scores)
    assert np.allclose(compiled.positive_weights, source.positive_weights)
    assert np.allclose(compiled.probabilities, source.probabilities)


def test_snarky_choice_bridge_explains_each_candidate_by_factor_id() -> None:
    data = _dataset().take(np.asarray([0]))
    data.tonic_pcs = np.asarray([0], dtype=np.int8)
    data.modes = np.asarray([0], dtype=np.int8)
    data.metric_levels = np.asarray([3], dtype=np.int8)
    program = snarky_choice_bridge.load_choice_program()

    (alternatives,) = program.explanations(data)

    assert len(alternatives) == data.candidate_pitches.size
    assert {item["pitch"] for item in alternatives} == set(data.candidate_pitches)
    assert np.isclose(sum(item["probability"] for item in alternatives), 1.0)
    assert all(
        activation["factor_id"].startswith("F-K3-V5.16-")
        for alternative in alternatives
        for activation in alternative["active_factors"]
    )


def test_snarky_factor_model_matches_the_v5_16_activation_sum() -> None:
    data = _dataset()
    data.tonic_pcs = np.asarray([0, 2], dtype=np.int8)
    data.modes = np.asarray([0, 1], dtype=np.int8)
    data.metric_levels = np.asarray([3, 0], dtype=np.int8)
    program = snarky_choice_bridge.load_choice_program()
    evaluation = program.evaluate(data)

    expected = np.tensordot(
        evaluation.activations,
        program.weights,
        axes=([2], [0]),
    )
    actual = program.snarky_factor_scores(data, evaluation)

    assert np.allclose(actual, expected)
    assert program.snarky_factor_model().groups[0].name == "k3_v5_16_reference"


def test_clean_induction_source_has_no_rule_base_dependency() -> None:
    source = (Path(__file__).parent / "run_induction.py").read_text(encoding="utf-8")

    assert "rule_profiles" not in source
    assert "learned_generator" not in source
    assert "rule_bases" not in source


def test_vertical_status_extension_adds_only_two_named_triadic_factors() -> None:
    data = _dataset()
    data.tonic_pcs = np.asarray([0, 2], dtype=np.int8)
    data.modes = np.asarray([0, 1], dtype=np.int8)
    data.metric_levels = np.asarray([3, 0], dtype=np.int8)

    baseline = k3.contextual_feature_catalogue(data)
    extended = k3.contextual_feature_catalogue(
        data,
        vertical_status_features=True,
    )
    added = {feature.key: feature for feature in extended}
    for feature in baseline:
        added.pop(feature.key)

    assert {feature.kind for feature in added.values()} == {
        "central_triadic_metric"
    }
    assert {feature.second_value for feature in added.values()} == {0, 1}
    assert all(feature.complexity == 2 for feature in added.values())


def test_named_harmonic_statuses_distinguish_quality_degree_and_inversion() -> None:
    data = k3.K3Dataset(
        piece_ids=np.asarray(["p"]),
        offsets=np.asarray([[0, 1, 2]], dtype=np.float32),
        voice_indices=np.asarray([0], dtype=np.int8),
        blocks=np.asarray(
            [[[72, 64, 55, 48], [72, 64, 55, 48], [72, 64, 55, 48]]],
            dtype=np.int16,
        ),
        attacks=np.ones((1, 3, 4), dtype=bool),
        candidate_min=60,
        candidate_max=72,
        tonic_pcs=np.asarray([0], dtype=np.int8),
        modes=np.asarray([0], dtype=np.int8),
        metric_levels=np.asarray([3], dtype=np.int8),
    )
    major = k3.feature_mask(
        data,
        k3.FeatureSpec("central_named_chord_quality", -1, value=0),
    )
    dominant_seventh = k3.feature_mask(
        data,
        k3.FeatureSpec("central_named_chord_quality", -1, value=4),
    )
    tonic_root = k3.feature_mask(
        data,
        k3.FeatureSpec("central_named_chord_root_degree", -1, value=0),
    )
    root_position = k3.feature_mask(
        data,
        k3.FeatureSpec("central_named_chord_inversion", -1, value=0),
    )
    strong_dominant_seventh = k3.feature_mask(
        data,
        k3.FeatureSpec(
            "central_named_chord_quality_metric",
            -1,
            value=4,
            second_value=1,
        ),
    )
    tonic_dominant_seventh = k3.feature_mask(
        data,
        k3.FeatureSpec(
            "central_named_chord_degree_quality",
            -1,
            value=0,
            second_value=4,
        ),
    )

    assert major[0, 72 - data.candidate_min]
    assert not major[0, 70 - data.candidate_min]
    assert dominant_seventh[0, 70 - data.candidate_min]
    assert tonic_root[0, 70 - data.candidate_min]
    assert root_position[0, 70 - data.candidate_min]
    assert strong_dominant_seventh[0, 70 - data.candidate_min]
    assert tonic_dominant_seventh[0, 70 - data.candidate_min]


def test_named_harmonic_status_extension_adds_only_low_order_named_factors() -> None:
    data = _dataset()
    data.tonic_pcs = np.asarray([0, 0], dtype=np.int8)
    data.modes = np.asarray([0, 0], dtype=np.int8)
    data.metric_levels = np.asarray([1, 3], dtype=np.int8)

    baseline = k3.contextual_feature_catalogue(data)
    extended = k3.contextual_feature_catalogue(
        data,
        named_harmonic_status_features=True,
    )
    baseline_keys = {feature.key for feature in baseline}
    added = [feature for feature in extended if feature.key not in baseline_keys]

    assert len(added) == 226
    assert {feature.kind for feature in added} == k3.NAMED_CHORD_STATUS_KINDS
    assert max(feature.complexity for feature in added) == 2


def test_named_harmonic_baseline_deviation_encoding_is_not_collinear() -> None:
    features = k3.named_harmonic_status_feature_catalogue(
        metric_encoding="baseline_plus_strong_deviation",
    )
    metric_features = [
        feature
        for feature in features
        if feature.kind
        in {
            "central_named_chord_quality_metric",
            "central_named_chord_root_degree_metric",
        }
    ]

    assert len(features) == 204
    assert len(metric_features) == 22
    assert {feature.second_value for feature in metric_features} == {1}


def test_named_root_transition_uses_chord_roots_not_bass_notes() -> None:
    data = k3.K3Dataset(
        piece_ids=np.asarray(["p"]),
        offsets=np.asarray([[0, 1, 2]], dtype=np.float32),
        voice_indices=np.asarray([0], dtype=np.int8),
        blocks=np.asarray(
            [
                [
                    [76, 67, 60, 52],  # C major in first inversion.
                    [74, 67, 59, 55],  # G major in root position.
                    [72, 64, 55, 48],
                ]
            ],
            dtype=np.int16,
        ),
        attacks=np.ones((1, 3, 4), dtype=bool),
        candidate_min=72,
        candidate_max=76,
        tonic_pcs=np.asarray([0], dtype=np.int8),
        modes=np.asarray([0], dtype=np.int8),
        metric_levels=np.asarray([3], dtype=np.int8),
    )
    tonic_to_dominant = k3.feature_mask(
        data,
        k3.FeatureSpec(
            "central_named_root_transition_mode",
            -1,
            value=0 * 12 + 7,
            second_value=0,
            complexity=4,
        ),
    )
    bass_mimic = k3.feature_mask(
        data,
        k3.FeatureSpec(
            "central_named_root_transition_mode",
            -1,
            value=4 * 12 + 7,
            second_value=0,
            complexity=4,
        ),
    )

    assert tonic_to_dominant[0, 74 - data.candidate_min]
    assert not bass_mimic[0, 74 - data.candidate_min]


def test_named_root_transition_catalogue_is_symmetric_and_low_order() -> None:
    features = k3.named_harmonic_transition_feature_catalogue()

    assert len(features) == 2 * 12 * 12
    assert {feature.kind for feature in features} == {
        "central_named_root_transition_mode"
    }
    assert {feature.second_value for feature in features} == {0, 1}
    assert {feature.complexity for feature in features} == {4}


def test_named_root_motion_shares_one_parameter_across_departure_degrees() -> None:
    data = k3.K3Dataset(
        piece_ids=np.asarray(["c_to_g", "d_to_a"]),
        offsets=np.asarray([[0, 1, 2], [0, 1, 2]], dtype=np.float32),
        voice_indices=np.asarray([0, 0], dtype=np.int8),
        blocks=np.asarray(
            [
                [
                    [76, 67, 60, 52],
                    [74, 67, 59, 55],
                    [72, 64, 55, 48],
                ],
                [
                    [78, 69, 62, 54],
                    [76, 69, 61, 57],
                    [74, 66, 57, 50],
                ],
            ],
            dtype=np.int16,
        ),
        attacks=np.ones((2, 3, 4), dtype=bool),
        candidate_min=74,
        candidate_max=78,
        tonic_pcs=np.asarray([0, 0], dtype=np.int8),
        modes=np.asarray([0, 0], dtype=np.int8),
        metric_levels=np.asarray([3, 3], dtype=np.int8),
    )
    ascending_fifth = k3.feature_mask(
        data,
        k3.FeatureSpec(
            "central_named_root_motion_mode",
            -1,
            value=7,
            second_value=0,
            complexity=3,
        ),
    )

    assert ascending_fifth[0, 74 - data.candidate_min]
    assert ascending_fifth[1, 76 - data.candidate_min]


def test_named_root_motion_catalogue_has_only_24_shared_parameters() -> None:
    features = k3.named_harmonic_root_motion_feature_catalogue()

    assert len(features) == 24
    assert {feature.second_value for feature in features} == {0, 1}
    assert {feature.value for feature in features} == set(range(12))
    assert {feature.complexity for feature in features} == {3}


def test_bass_tonal_strong_mode_status_tracks_candidate_bass() -> None:
    data = k3.K3Dataset(
        piece_ids=np.asarray(["p"]),
        offsets=np.asarray([[0, 1, 2]], dtype=np.float32),
        voice_indices=np.asarray([3], dtype=np.int8),
        blocks=np.asarray(
            [[[72, 64, 55, 48], [72, 64, 55, 48], [72, 64, 55, 48]]],
            dtype=np.int16,
        ),
        attacks=np.ones((1, 3, 4), dtype=bool),
        candidate_min=48,
        candidate_max=50,
        tonic_pcs=np.asarray([0], dtype=np.int8),
        modes=np.asarray([0], dtype=np.int8),
        metric_levels=np.asarray([3], dtype=np.int8),
    )
    tonic = k3.feature_mask(
        data,
        k3.FeatureSpec(
            "central_bass_tonal_strong_mode",
            -1,
            value=0,
            second_value=0,
            complexity=2,
        ),
    )

    assert tonic[0, 0]
    assert not tonic[0, 1]
    data.metric_levels[:] = 1
    assert not k3.feature_mask(
        data,
        k3.FeatureSpec(
            "central_bass_tonal_strong_mode",
            -1,
            value=0,
            second_value=0,
            complexity=2,
        ),
    ).any()


def test_unique_chord_family_inversion_excludes_ambiguous_analyses() -> None:
    data = k3.K3Dataset(
        piece_ids=np.asarray(["major", "augmented"]),
        offsets=np.asarray([[0, 1, 2], [0, 1, 2]], dtype=np.float32),
        voice_indices=np.asarray([0, 0], dtype=np.int8),
        blocks=np.asarray(
            [
                [
                    [72, 64, 55, 48],
                    [72, 64, 55, 48],
                    [72, 64, 55, 48],
                ],
                [
                    [72, 68, 64, 48],
                    [72, 68, 64, 48],
                    [72, 68, 64, 48],
                ],
            ],
            dtype=np.int16,
        ),
        attacks=np.ones((2, 3, 4), dtype=bool),
        candidate_min=72,
        candidate_max=72,
        tonic_pcs=np.asarray([0, 0], dtype=np.int8),
        modes=np.asarray([0, 0], dtype=np.int8),
        metric_levels=np.asarray([3, 3], dtype=np.int8),
    )
    consonant_root_position = k3.feature_mask(
        data,
        k3.FeatureSpec(
            "central_unique_chord_family_inversion_strong",
            -1,
            value=0,
            complexity=3,
        ),
    )

    assert consonant_root_position[0, 0]
    assert not consonant_root_position[1, 0]


def test_v23_catalogues_have_only_38_shared_status_parameters() -> None:
    bass = k3.bass_tonal_strong_mode_feature_catalogue()
    chords = k3.unique_chord_family_inversion_strong_feature_catalogue()

    assert len(bass) == 24
    assert len(chords) == 14
    assert {feature.value for feature in chords} == {
        0,
        1,
        2,
        4,
        5,
        6,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
    }


def _residual_sonority_dataset(
    central: list[int],
    *,
    previous: list[int] | None = None,
    following: list[int] | None = None,
    metric_level: int = 3,
) -> k3.K3Dataset:
    previous = central if previous is None else previous
    following = central if following is None else following
    return k3.K3Dataset(
        piece_ids=np.asarray(["p"]),
        offsets=np.asarray([[0, 1, 2]], dtype=np.float32),
        voice_indices=np.asarray([2], dtype=np.int8),
        blocks=np.asarray([[previous, central, following]], dtype=np.int16),
        attacks=np.ones((1, 3, 4), dtype=bool),
        candidate_min=central[2],
        candidate_max=central[2],
        tonic_pcs=np.asarray([0], dtype=np.int8),
        modes=np.asarray([0], dtype=np.int8),
        metric_levels=np.asarray([metric_level], dtype=np.int8),
    )


def test_v24_residual_status_leaves_strict_unique_chords_to_v23() -> None:
    major = _residual_sonority_dataset([76, 67, 60, 48])
    augmented = _residual_sonority_dataset([76, 68, 60, 48])

    assert k3.central_residual_strong_sonority_statuses(major)[0, 0] == -1
    assert k3.central_residual_strong_sonority_statuses(augmented)[0, 0] == 0


def test_v24_residual_status_recognizes_incomplete_consonant_triad() -> None:
    data = _residual_sonority_dataset([76, 64, 60, 48])

    assert k3.central_residual_strong_sonority_statuses(data)[0, 0] == 1


def test_v24_residual_status_licenses_passing_foreign_tone() -> None:
    data = _residual_sonority_dataset(
        [76, 67, 62, 48],
        previous=[76, 67, 60, 48],
        following=[76, 67, 64, 48],
    )

    assert k3.central_residual_strong_sonority_statuses(data)[0, 0] == 3


def test_v24_residual_status_distinguishes_suspension_and_appoggiatura() -> None:
    suspension = _residual_sonority_dataset(
        [76, 67, 62, 48],
        previous=[76, 67, 62, 48],
        following=[76, 67, 60, 48],
    )
    appoggiatura = _residual_sonority_dataset(
        [76, 67, 62, 48],
        previous=[76, 67, 65, 48],
        following=[76, 67, 60, 48],
    )

    assert k3.central_residual_strong_sonority_statuses(
        suspension
    )[0, 0] == 4
    assert k3.central_residual_strong_sonority_statuses(
        appoggiatura
    )[0, 0] == 5


def test_v24_residual_catalogue_is_one_exhaustive_eight_cell_group() -> None:
    data = _residual_sonority_dataset(
        [76, 67, 62, 48],
        previous=[76, 67, 60, 48],
        following=[76, 67, 65, 48],
    )
    features = k3.residual_strong_sonority_feature_catalogue()
    activations = k3.feature_matrix(data, features)

    assert len(features) == 8
    assert activations[0, 0].sum() == 1
    assert activations[0, 0, 6]


def test_v25_weak_status_leaves_strict_unique_chords_as_reference() -> None:
    major = _residual_sonority_dataset(
        [76, 67, 60, 48],
        metric_level=1,
    )
    augmented = _residual_sonority_dataset(
        [76, 68, 60, 48],
        metric_level=1,
    )

    assert k3.central_residual_weak_sonority_statuses(major)[0, 0] == -1
    assert k3.central_residual_weak_sonority_statuses(augmented)[0, 0] == 0


def test_v25_weak_status_separates_passing_and_neighbor() -> None:
    passing = _residual_sonority_dataset(
        [76, 67, 62, 48],
        previous=[76, 67, 60, 48],
        following=[76, 67, 64, 48],
        metric_level=1,
    )
    neighbor = _residual_sonority_dataset(
        [76, 67, 62, 48],
        previous=[76, 67, 60, 48],
        following=[76, 67, 60, 48],
        metric_level=1,
    )

    assert k3.central_residual_weak_sonority_statuses(passing)[0, 0] == 3
    assert k3.central_residual_weak_sonority_statuses(neighbor)[0, 0] == 4


def test_v25_weak_status_separates_suspension_and_appoggiatura() -> None:
    suspension = _residual_sonority_dataset(
        [76, 67, 62, 48],
        previous=[76, 67, 62, 48],
        following=[76, 67, 60, 48],
        metric_level=1,
    )
    appoggiatura = _residual_sonority_dataset(
        [76, 67, 62, 48],
        previous=[76, 67, 65, 48],
        following=[76, 67, 60, 48],
        metric_level=1,
    )

    assert k3.central_residual_weak_sonority_statuses(suspension)[0, 0] == 5
    assert k3.central_residual_weak_sonority_statuses(appoggiatura)[0, 0] == 6


def test_v25_weak_catalogue_is_one_exhaustive_nine_cell_group() -> None:
    data = _residual_sonority_dataset(
        [76, 67, 62, 48],
        previous=[76, 67, 60, 48],
        following=[76, 67, 65, 48],
        metric_level=1,
    )
    features = k3.residual_weak_sonority_feature_catalogue()
    activations = k3.feature_matrix(data, features)

    assert len(features) == 9
    assert activations[0, 0].sum() == 1
    assert activations[0, 0, 7]
