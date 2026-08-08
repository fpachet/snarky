"""Focused tests for propagated reified-chord search."""

from __future__ import annotations

import json
from types import SimpleNamespace

import numpy as np
import run_full_snarky_score_floor_generation as generation

from snarky import ForwardEngine


def _candidate(time: int, index: int, pitches: generation.PitchBlock):
    return generation.ReifiedChordCandidate(
        time=time,
        index=index,
        pitches=pitches,
        signature=0,
        quality=0,
        root_degree=0,
        inversion_interval=0,
    )


def test_compiled_pair_support_matches_scalar_manual_filter() -> None:
    left = (
        _candidate(0, 0, (72, 67, 60, 48)),
        _candidate(0, 1, (71, 65, 62, 43)),
    )
    right = (
        _candidate(1, 0, (74, 69, 62, 50)),
        _candidate(1, 1, (72, 67, 64, 48)),
        _candidate(1, 2, (71, 67, 62, 55)),
    )

    compiled = generation.ReifiedChordSpace._pair_support(
        left,
        right,
        tonic_pc=2,
        strict_manual=True,
    )
    expected = np.asarray(
        [
            [
                not generation.ReifiedChordSpace.violates_pairwise_rules(
                    previous.pitches,
                    current.pitches,
                )
                and all(
                    abs(target - source) <= 7
                    for source, target in zip(
                        previous.pitches,
                        current.pitches,
                        strict=True,
                    )
                )
                and all(
                    source % 12 != 1 or target == source + 1
                    for source, target in zip(
                        previous.pitches,
                        current.pitches,
                        strict=True,
                    )
                )
                for current in right
            ]
            for previous in left
        ],
        dtype=bool,
    )

    np.testing.assert_array_equal(compiled, expected)


def test_official_manual_factors_are_loaded_and_additive() -> None:
    scorer = generation.OfficialManualTransitionScorer()
    previous = (71, 67, 64, 48)
    resolved = (72, 67, 64, 48)

    activations = scorer.activations(previous, resolved, tonic_pc=0)

    assert "manual_leading_tone_resolution" in activations
    assert scorer.energy(previous, resolved, tonic_pc=0) > 0


def test_reified_domain_never_admits_an_incomplete_or_ambiguous_chord() -> None:
    tonic_pc = 4
    voicings = generation.ReifiedChordSpace._voicings(
        soprano=71,
        tonic_pc=tonic_pc,
        voice_ranges={1: (55, 71), 2: (50, 68), 3: (36, 64)},
        allowed_signatures=generation._allowed_homorhythmic_signatures(
            frozenset((0, 1))
        ),
    )

    assert voicings
    for voicing in voicings:
        block = np.asarray((71, *voicing), dtype=np.int16)
        analysis = generation.v34_harmony.analyze_block(block, tonic_pc)
        assert len(set(int(pitch) % 12 for pitch in block)) == 3
        assert analysis["analysis_count"] == 1
        assert analysis["quality"] in {0, 1}


def test_boundary_factor_is_discriminative_and_excludes_target_piece(tmp_path) -> None:
    model_path = tmp_path / "boundary.json"
    model_path.write_text(
        json.dumps(
            {
                "status": "TRAIN_ONLY_FROZEN_COUNTS",
                "test_loaded": False,
                "validation_loaded": False,
                "alpha": 0.5,
                "records": [
                    {
                        "piece_id": "target",
                        "boundary": "opening",
                        "mode": "major",
                        "soprano_degree": 7,
                        "quality": 1,
                        "root_degree": 7,
                        "inversion_interval": 0,
                        "lower_intervals_from_soprano": [5, 8, 24],
                    },
                    *(
                        {
                            "piece_id": f"train-{index}",
                            "boundary": "opening",
                            "mode": "major",
                            "soprano_degree": 7,
                            "quality": 0,
                            "root_degree": 0,
                            "inversion_interval": 0,
                            "lower_intervals_from_soprano": [3, 7, 19],
                        }
                        for index in range(3)
                    ),
                ],
            }
        ),
        encoding="utf-8",
    )
    factor = generation.BoundaryChordFactor.load(
        model_path,
        excluded_piece_id="target",
    )
    tonic = generation.ReifiedChordCandidate(0, 0, (71, 68, 64, 52), 0, 0, 0, 0)
    dominant = generation.ReifiedChordCandidate(0, 1, (71, 66, 63, 47), 0, 1, 7, 0)

    energies = factor.energies(
        (tonic, dominant),
        boundary="opening",
        mode="major",
        soprano_degree=7,
    )

    assert len(factor.records) == 3
    assert energies[0] > energies[1]
    assert float(np.ptp(energies)) > 0


def test_arc_consistency_persists_rejections_and_singletons_as_facts() -> None:
    space = object.__new__(generation.ReifiedChordSpace)
    space.groups = (
        (0, ((0, 1, 1), (0, 1, 2), (0, 1, 3))),
        (1, ((1, 2, 1), (1, 2, 2), (1, 2, 3))),
    )
    space.time_to_position = {0: 0, 1: 1}
    space.domains = (
        (
            _candidate(0, 0, (72, 67, 60, 48)),
            _candidate(0, 1, (72, 69, 60, 45)),
        ),
        (
            _candidate(1, 0, (71, 67, 62, 43)),
            _candidate(1, 1, (71, 65, 59, 47)),
        ),
    )
    space.supports = (np.asarray(((True, False), (False, False))),)
    propagator = generation.ReifiedChordDomainPropagator(space)
    session = ForwardEngine(()).create_session(())

    propagator(session)

    rejected = generation._chord_indices(session, generation.REJECTED_CHORD)
    chosen = generation._chord_indices(session, generation.CHOSEN_CHORD)
    assert rejected == {0: {1}, 1: {1}}
    assert chosen == {0: {0}, 1: {0}}
    assert generation._assignments(session) == {
        (0, 1, 1): 67,
        (0, 1, 2): 60,
        (0, 1, 3): 48,
        (1, 2, 1): 67,
        (1, 2, 2): 62,
        (1, 2, 3): 43,
    }
    assert propagator.domain_removals == 2
    assert propagator.singleton_assignments == 2


def test_rejected_selected_value_produces_empty_domain() -> None:
    space = object.__new__(generation.ReifiedChordSpace)
    space.groups = ((0, ((0, 1, 1), (0, 1, 2), (0, 1, 3))),)
    space.time_to_position = {0: 0}
    space.domains = ((_candidate(0, 0, (72, 67, 60, 48)),),)
    space.supports = ()
    session = ForwardEngine(()).create_session(
        (
            generation._chord_fact(0, generation.CHOSEN_CHORD, 0),
            generation._chord_fact(0, generation.REJECTED_CHORD, 0),
        )
    )

    masks = space.masks(session)

    assert not np.any(masks[0])


def test_manual_step_bound_rejects_only_when_recovery_is_impossible() -> None:
    propagator = object.__new__(generation.OfficialManualBudgetPropagator)
    propagator.lattice = SimpleNamespace(
        size=5,
        attacks=np.ones((5, 4), dtype=bool),
        tonic_pc=0,
    )
    propagator.defaults = np.full((5, 4), 60, dtype=np.int16)
    propagator.controllers = {
        (time, voice): (time, time + 1, voice)
        for time in range(5)
        for voice in range(1, 4)
    }
    propagator.thresholds = {
        "parallel_fifth_rate": 1.0,
        "parallel_octave_rate": 1.0,
        "direct_fifth_rate": 1.0,
        "voice_crossing_rate": 1.0,
        "voice_overlap_rate": 1.0,
        "soprano_maximum_leap": 12.0,
        "alto_maximum_leap": 12.0,
        "tenor_maximum_leap": 12.0,
        "bass_maximum_leap": 16.0,
        "alto_longest_repeat_run": 6.0,
        "tenor_longest_repeat_run": 6.0,
        "bass_longest_repeat_run": 3.0,
        "alto_step_deficit": 0.34,
        "tenor_step_deficit": 0.38,
        "bass_step_deficit": 0.50,
    }
    propagator.profile = "bach_empirical"
    propagator.transition_scorer = generation.OfficialManualTransitionScorer()
    propagator.maximum_exceeded_budgets = 2
    propagator.group_budgets = {
        "contrapuntal": (
            frozenset(
                {
                    "parallel_fifth_rate",
                    "parallel_octave_rate",
                    "direct_fifth_rate",
                    "voice_crossing_rate",
                    "voice_overlap_rate",
                }
            ),
            2,
            "EMPIRICAL-GROUP-CONTRAPUNTAL",
        ),
        "leap": (
            frozenset(
                {
                    "soprano_maximum_leap",
                    "alto_maximum_leap",
                    "tenor_maximum_leap",
                    "bass_maximum_leap",
                }
            ),
            0,
            "EMPIRICAL-GROUP-LEAP",
        ),
        "repetition": (
            frozenset(
                {
                    "alto_longest_repeat_run",
                    "tenor_longest_repeat_run",
                    "bass_longest_repeat_run",
                }
            ),
            1,
            "EMPIRICAL-GROUP-REPETITION",
        ),
        "conjunct_motion": (
            frozenset(
                {
                    "alto_step_deficit",
                    "tenor_step_deficit",
                    "bass_step_deficit",
                }
            ),
            1,
            "EMPIRICAL-GROUP-CONJUNCT-MOTION",
        ),
    }
    recoverable = {
        (0, 1, 1): 60,
        (1, 2, 1): 64,
        (0, 1, 2): 55,
        (1, 2, 2): 59,
    }
    impossible = {
        **recoverable,
        (2, 3, 1): 67,
        (2, 3, 2): 62,
    }

    assert propagator.candidate_is_allowed(recoverable)
    assert not propagator.candidate_is_allowed(impossible)


def test_strict_suspension_is_rejected_when_third_chord_becomes_known() -> None:
    provider = object.__new__(generation.ReifiedChordChoiceProvider)
    space = object.__new__(generation.ReifiedChordSpace)
    space.groups = tuple(
        (
            time,
            (
                (time, time + 1, 1),
                (time, time + 1, 2),
                (time, time + 1, 3),
            ),
        )
        for time in range(3)
    )
    provider.space = space
    provider.defaults = np.asarray(
        (
            (64, 60, 55, 48),
            (64, 60, 55, 50),
            (64, 60, 55, 48),
        ),
        dtype=np.int16,
    )
    provider.manual_budget = SimpleNamespace(profile="pedagogical_strict")
    assignments = {
        segment: int(provider.defaults[time, voice])
        for time, segments in space.groups[:2]
        for segment in segments
        for voice in (segment[2],)
    }
    candidate = _candidate(2, 0, (64, 60, 55, 48))

    assert provider._violates_strict_window_rules(assignments, 2, candidate)
