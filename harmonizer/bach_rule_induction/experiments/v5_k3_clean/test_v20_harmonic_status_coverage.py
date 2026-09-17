from __future__ import annotations

from audit_v20_harmonic_status_coverage import (
    analyze_pitch_classes,
    triad_plus_one_analyses,
)


def test_named_triad_exposes_degree_quality_and_inversion() -> None:
    root = analyze_pitch_classes(
        (60, 64, 67, 72),
        bass_pitch=60,
        tonic_pc=60 % 12,
    )
    first_inversion = analyze_pitch_classes(
        (64, 67, 72, 76),
        bass_pitch=64,
        tonic_pc=60 % 12,
    )

    assert len(root) == 1
    assert root[0].root_degree == 0
    assert root[0].quality == "major_triad"
    assert root[0].inversion == 0
    assert first_inversion[0].inversion == 1


def test_dominant_seventh_exposes_third_inversion() -> None:
    analyses = analyze_pitch_classes(
        (65, 67, 71, 74),
        bass_pitch=65,
        tonic_pc=0,
    )

    assert len(analyses) == 1
    assert analyses[0].root_degree == 7
    assert analyses[0].quality == "dominant_seventh"
    assert analyses[0].inversion == 3


def test_symmetric_diminished_seventh_preserves_ambiguity() -> None:
    analyses = analyze_pitch_classes(
        (59, 62, 65, 68),
        bass_pitch=59,
        tonic_pc=11,
    )

    assert len(analyses) == 4
    assert {analysis.root_degree for analysis in analyses} == {0, 3, 6, 9}


def test_triad_plus_one_identifies_foreign_pitch_class() -> None:
    analyses = triad_plus_one_analyses(
        (60, 62, 64, 67),
        bass_pitch=60,
        tonic_pc=0,
    )

    assert len(analyses) == 1
    foreign_pc, status = analyses[0]
    assert foreign_pc == 2
    assert status.quality == "major_triad"
    assert status.root_degree == 0
