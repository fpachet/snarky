from __future__ import annotations

import pytest

from harmonizer.note_solver import (
    VOICING_CANDIDATE,
    _harmonic_vocabulary_facts,
    _vertical_conformance_groups,
    _voice_leading_conformance_groups,
)
from snarky import Atom, Fact, FiniteSequence, InferenceSession, Number, Triple

LEFT = Atom("left")
RIGHT = Atom("right")
SUCCESSOR = Atom("successor")
VIOLATES = Atom("violates")
STATE = Atom("state")
LEGAL = Atom("legal")


def _voicing(
    chord: str,
    inversion: str,
    pitches: tuple[int, int, int, int],
) -> FiniteSequence:
    return FiniteSequence(
        (
            Atom(chord),
            Atom(inversion),
            *(Number(pitch) for pitch in pitches),
        )
    )


def _transition(
    source_chord: str,
    source_inversion: str,
    source: tuple[int, int, int, int],
    target_chord: str,
    target_inversion: str,
    target: tuple[int, int, int, int],
) -> tuple[InferenceSession, FiniteSequence]:
    source_voicing = _voicing(source_chord, source_inversion, source)
    target_voicing = _voicing(target_chord, target_inversion, target)
    transition = FiniteSequence((LEFT, source_voicing, RIGHT, target_voicing))
    session = InferenceSession(
        (
            *_harmonic_vocabulary_facts(),
            Fact(Triple(LEFT, SUCCESSOR, RIGHT)),
            Fact(Triple(LEFT, VOICING_CANDIDATE, source_voicing)),
            Fact(Triple(RIGHT, VOICING_CANDIDATE, target_voicing)),
        )
    )
    for group in _voice_leading_conformance_groups():
        session.run_group(group)
    return session, transition


def _violation_names(
    session: InferenceSession,
    transition: FiniteSequence,
) -> set[str]:
    return {
        entity.object.name
        for fact in session.facts
        if isinstance((entity := fact.entity), Triple)
        and entity.subject == transition
        and entity.relation == VIOLATES
        and isinstance(entity.object, Atom)
    }


@pytest.mark.parametrize(
    ("target_soprano", "expected"),
    ((84, False), (85, True)),
)
def test_R_MELODY_001_octave_boundary(
    target_soprano: int,
    expected: bool,
) -> None:
    session, transition = _transition(
        "degree_I",
        "root",
        (72, 64, 55, 48),
        "degree_I",
        "root",
        (target_soprano, 64, 55, 48),
    )

    assert ("R-MELODY-001" in _violation_names(session, transition)) is expected


def test_R_MELODY_002_rejects_a_tritone() -> None:
    session, transition = _transition(
        "degree_I",
        "root",
        (72, 64, 55, 48),
        "degree_I",
        "root",
        (78, 64, 55, 48),
    )

    assert "R-MELODY-002" in _violation_names(session, transition)


def test_R_OVERLAP_001_rejects_voice_overlap() -> None:
    session, transition = _transition(
        "degree_I",
        "root",
        (72, 64, 55, 48),
        "degree_I",
        "root",
        (76, 73, 55, 48),
    )

    assert "R-OVERLAP-001" in _violation_names(session, transition)


def test_R_PARALLEL_002_rejects_parallel_fifths() -> None:
    session, transition = _transition(
        "degree_I",
        "root",
        (72, 65, 55, 48),
        "degree_I",
        "root",
        (74, 67, 55, 48),
    )

    assert "R-PARALLEL-002" in _violation_names(session, transition)


@pytest.mark.parametrize(
    ("source_soprano", "expected"),
    ((71, True), (72, False)),
)
def test_R_DIRECT_002_distinguishes_leap_from_step(
    source_soprano: int,
    expected: bool,
) -> None:
    session, transition = _transition(
        "degree_I",
        "root",
        (source_soprano, 64, 57, 53),
        "degree_I",
        "root",
        (74, 67, 59, 55),
    )

    assert ("R-DIRECT-002" in _violation_names(session, transition)) is expected


@pytest.mark.parametrize(
    ("target_soprano", "expected"),
    ((72, False), (74, True)),
)
def test_R_LEADING_001_requires_resolution_up(
    target_soprano: int,
    expected: bool,
) -> None:
    session, transition = _transition(
        "degree_V",
        "root",
        (71, 67, 62, 43),
        "degree_I",
        "root",
        (target_soprano, 64, 60, 48),
    )

    assert ("R-LEADING-001" in _violation_names(session, transition)) is expected


def test_R_LEADING_002_allows_the_documented_deceptive_inner_exception() -> None:
    session, transition = _transition(
        "degree_V",
        "root",
        (67, 59, 55, 43),
        "degree_vi",
        "root",
        (72, 57, 52, 45),
    )

    assert "R-LEADING-001" not in _violation_names(session, transition)


@pytest.mark.parametrize(
    ("target_alto", "expected"),
    ((64, False), (67, True)),
)
def test_R_SEVENTH_001_requires_F_to_resolve_down(
    target_alto: int,
    expected: bool,
) -> None:
    session, transition = _transition(
        "degree_V7",
        "root",
        (71, 65, 62, 43),
        "degree_I",
        "root",
        (72, target_alto, 60, 48),
    )

    assert ("R-SEVENTH-001" in _violation_names(session, transition)) is expected


def test_cadential_six_four_has_a_positive_and_negative_fixture() -> None:
    good, good_transition = _transition(
        "degree_I",
        "second",
        (72, 67, 64, 43),
        "degree_V",
        "root",
        (71, 67, 62, 43),
    )
    bad, bad_transition = _transition(
        "degree_I",
        "second",
        (72, 67, 64, 43),
        "degree_V",
        "root",
        (72, 67, 62, 43),
    )

    assert not {
        name
        for name in _violation_names(good, good_transition)
        if name.startswith("R-CAD64-")
    }
    assert Fact(Triple(good_transition, STATE, LEGAL)) in good.facts
    assert "R-CAD64-005" in _violation_names(bad, bad_transition)


@pytest.mark.parametrize(
    ("chord", "inversion", "pitches", "retained", "rule_name"),
    (
        ("degree_I", "root", (76, 64, 55, 48), True, None),
        (
            "degree_I",
            "root",
            (76, 67, 64, 48),
            False,
            "R_DOUBLING_004_005_root_third_exception_is_soprano_alto_only",
        ),
        (
            "degree_I",
            "first",
            (76, 72, 67, 40),
            False,
            "R_DOUBLING_007_selected_first_inversion_bass_is_unique",
        ),
        ("degree_I", "second", (72, 67, 64, 43), True, None),
        (
            "degree_I",
            "second",
            (72, 64, 60, 43),
            False,
            "R_CAD64_001_double_the_cadential_bass",
        ),
        (
            "degree_V",
            "first",
            (74, 71, 67, 47),
            False,
            "R_DOUBLING_002_never_double_the_leading_tone",
        ),
    ),
)
def test_vertical_doubling_rules_are_declarative(
    chord: str,
    inversion: str,
    pitches: tuple[int, int, int, int],
    retained: bool,
    rule_name: str | None,
) -> None:
    position = Atom("position")
    voicing = _voicing(chord, inversion, pitches)
    candidate = Fact(Triple(position, VOICING_CANDIDATE, voicing))
    session = InferenceSession((*_harmonic_vocabulary_facts(), candidate))
    for group in _vertical_conformance_groups():
        session.run_group(group)

    assert (candidate in session.facts) is retained
    if rule_name is not None:
        assert any(event.rule_name == rule_name for event in session.events)
