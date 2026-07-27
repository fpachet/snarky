from __future__ import annotations

from pathlib import Path

import k3
import numpy as np
import run_k3_ablation as ablation
import run_k3_null_max_calibration as calibration


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


def test_contextual_vertical_signatures_are_candidate_dependent() -> None:
    data = _dataset().take(np.asarray([0]))
    data.tonic_pcs = np.asarray([0], dtype=np.int8)
    data.modes = np.asarray([0], dtype=np.int8)
    data.metric_levels = np.asarray([3], dtype=np.int8)

    signatures = k3.central_tonic_pcset_signatures(data)

    expected = sum(1 << pitch_class for pitch_class in {0, 2, 6, 9})
    assert signatures[0, 72 - data.candidate_min] == expected
    assert signatures[0, 71 - data.candidate_min] != expected


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


def test_rhythmic_gibbs_changes_one_attack_and_its_whole_hold() -> None:
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
    )

    assert np.array_equal(generated[1:3, 1], [62, 62])
    assert generated[3, 1] == 61
    assert np.array_equal(generated[:, 0], blocks[:, 0])


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


def test_clean_induction_source_has_no_rule_base_dependency() -> None:
    source = (Path(__file__).parent / "run_induction.py").read_text(encoding="utf-8")

    assert "rule_profiles" not in source
    assert "learned_generator" not in source
    assert "rule_bases" not in source
