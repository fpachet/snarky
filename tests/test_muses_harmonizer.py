from collections.abc import Iterable, Sequence
from dataclasses import replace
from pathlib import Path

import pytest

from harmonizer import (
    MusesFactories,
    VoiceContinuation,
    harmonize_notes,
    harmonize_temporal_collection,
)
from harmonizer.muses_harmonizer import _materialize_voice_notes, _metric_levels
from snarky import ChoiceTraversal
from snarky.integrations import (
    MusesTemporalCollectionCodec,
    MusesTemporalNoteCodec,
)


class FakeTemporalNote:
    def __init__(
        self,
        pitch: int,
        start_time: int | float,
        duration: int | float,
        velocity: int = 60,
        midi_channel: int = 0,
    ) -> None:
        self.pitch = pitch
        self.start_beat = start_time
        self.end_beat = start_time + duration
        self.velocity = velocity
        self.midi_channel = midi_channel

    def duration(self) -> int | float:
        return self.end_beat - self.start_beat


class FakeTemporalCollection:
    def __init__(
        self,
        name: str = "",
        temporals: Iterable[FakeTemporalNote] | None = None,
        *,
        instrument: str = "",
        program_change: int = 0,
        melody_type: str = "",
        end_beat: int | float = 0.0,
    ) -> None:
        self.name = name
        self.temporals = sorted(
            list(temporals or ()),
            key=lambda note: note.start_beat,
        )
        self.instrument = instrument
        self.program_change = program_change
        self.melody_type = melody_type
        self.end_beat = max((end_beat, *(note.end_beat for note in self.temporals)))


class FakePiece:
    def __init__(
        self,
        name: str = "unnamed",
        title: str = "unknown",
        composer: str = "unknown",
        melodies: Sequence[FakeTemporalCollection] | None = None,
        ticks_per_beat: int = 480,
        time_signature: str = "4/4",
        key_signature: str = "C",
        tempo: int = 500_000,
    ) -> None:
        self.name = name
        self.title = title
        self.composer = composer
        self.melodies = list(melodies or ())
        self.ticks_per_beat = ticks_per_beat
        self.time_signature = time_signature
        self.key_signature = key_signature
        self.tempo = tempo


class FakeMetricPosition:
    def __init__(self, accent_level: int) -> None:
        self.accent_level = accent_level


def _integration() -> tuple[
    MusesFactories,
    MusesTemporalCollectionCodec,
]:
    factories = MusesFactories(
        FakeTemporalNote,
        FakeTemporalCollection,
        FakePiece,
    )
    codec = MusesTemporalCollectionCodec(
        note_codec=MusesTemporalNoteCodec(factory=FakeTemporalNote),
        factory=FakeTemporalCollection,
    )
    return factories, codec


@pytest.mark.parametrize(
    ("voice", "line", "voice_index"),
    (
        ("soprano", (71, 72), 0),
        ("alto", (62, 64), 1),
        ("tenor", (50, 52), 2),
        ("bass", (43, 48), 3),
    ),
)
def test_note_harmonizer_accepts_any_given_satb_voice(
    voice: str,
    line: tuple[int, int],
    voice_index: int,
) -> None:
    solution = harmonize_notes(
        line,
        given_voice=voice,  # type: ignore[arg-type]
        max_solutions=1,
    )[0]

    assert tuple(voicing[voice_index] for voicing in solution.voicings) == line


def test_muses_line_becomes_a_four_voice_piece_through_rules() -> None:
    factories, codec = _integration()
    source = FakeTemporalCollection(
        name="subject",
        temporals=(
            FakeTemporalNote(71, 0.0, 0.5, velocity=72, midi_channel=9),
            FakeTemporalNote(72, 1.0, 1.5, velocity=68, midi_channel=9),
        ),
        instrument="choir",
        program_change=52,
        melody_type="melody",
        end_beat=3.0,
    )

    result = harmonize_temporal_collection(
        source,
        given_voice="soprano",
        metric_levels=(3, 1),
        factories=factories,
        codec=codec,
        piece_name="generated_satb",
        title="Generated SATB",
    )[0]

    assert isinstance(result.piece, FakePiece)
    assert result.piece.name == "generated_satb"
    assert result.piece.title == "Generated SATB"
    assert result.piece.composer == "Snarky"
    assert [voice.name for voice in result.piece.melodies] == [
        "soprano",
        "alto",
        "tenor",
        "bass",
    ]
    assert [note.pitch for note in result.piece.melodies[0].temporals] == [71, 72]
    assert [
        [note.pitch for note in voice.temporals] for voice in result.piece.melodies
    ] == [
        [voicing[index] for voicing in result.symbolic.voicings] for index in range(4)
    ]
    for voice in result.piece.melodies:
        assert [note.start_beat for note in voice.temporals] == [0.0, 1.0]
        assert [note.duration() for note in voice.temporals] == [0.5, 1.5]
        assert voice.instrument == "choir"
        assert voice.program_change == 52
        assert voice.end_beat == 3.0
    assert [note.midi_channel for note in result.piece.melodies[0].temporals] == [9, 9]
    assert source.temporals[0].pitch == 71
    assert len(result.voice_facts) == 4
    assert all(result.voice_facts)
    assert result.symbolic.inference_events
    assert result.symbolic.metric_strengths == ("strong", "weak")
    assert result.symbolic.metric_levels == (3, 1)
    assert result.symbolic.note_durations == (0.5, 1.5)
    assert any(
        event.rule_group == "import_muses_given_voice"
        for event in result.symbolic.inference_events
    )
    assert any(
        event.rule_group == "generate_candidate_voicings"
        for event in result.symbolic.inference_events
    )


def test_muses_metric_translation_preserves_four_hierarchical_levels() -> None:
    notes = tuple(
        FakeTemporalNote(72, start, 0.25)
        for start in (0.0, 0.5, 1.0, 2.0)
    )
    calls: list[tuple[tuple[FakeTemporalNote, ...], str]] = []

    def metric_positions(
        received_notes: Iterable[FakeTemporalNote],
        time_signature: str,
    ) -> tuple[FakeMetricPosition, ...]:
        note_tuple = tuple(received_notes)
        calls.append((note_tuple, time_signature))
        return tuple(
            FakeMetricPosition(level)
            for level in (3, 0, 1, 2)
        )

    assert _metric_levels(
        notes,
        "4/4",
        metric_positions_function=metric_positions,
    ) == (3, 0, 1, 2)
    assert calls == [(notes, "4/4")]


def test_muses_metric_translation_validates_the_external_projection() -> None:
    notes = tuple(FakeTemporalNote(72, start, 0.25) for start in (0.0, 1.0))

    def wrong_count(
        received_notes: Iterable[FakeTemporalNote],
        time_signature: str,
    ) -> tuple[FakeMetricPosition, ...]:
        del received_notes, time_signature
        return (FakeMetricPosition(3),)

    def invalid_level(
        received_notes: Iterable[FakeTemporalNote],
        time_signature: str,
    ) -> tuple[FakeMetricPosition, ...]:
        del received_notes, time_signature
        return (FakeMetricPosition(3), FakeMetricPosition(4))

    with pytest.raises(ValueError, match="note count"):
        _metric_levels(
            notes,
            "4/4",
            metric_positions_function=wrong_count,
        )
    with pytest.raises(ValueError, match="integers from 0 to 3"):
        _metric_levels(
            notes,
            "4/4",
            metric_positions_function=invalid_level,
        )


def test_real_muses_metric_projection_when_optional_dependency_is_available() -> None:
    pytest.importorskip("muses")
    notes = tuple(
        FakeTemporalNote(72, start, 0.25)
        for start in (0.0, 0.5, 1.0, 2.0)
    )

    assert _metric_levels(notes, "4/4") == (3, 0, 1, 2)


def test_muses_bass_line_is_preserved_in_the_bass_output() -> None:
    factories, codec = _integration()
    source = FakeTemporalCollection(
        name="bass_subject",
        temporals=(
            FakeTemporalNote(43, 0.0, 1.0),
            FakeTemporalNote(48, 1.0, 1.0),
        ),
    )

    result = harmonize_temporal_collection(
        source,
        given_voice="bass",
        metric_levels=(3, 1),
        factories=factories,
        codec=codec,
    )[0]

    assert [note.pitch for note in result.piece.melodies[3].temporals] == [43, 48]


def test_passing_tone_extends_the_sounding_lower_voice_notes() -> None:
    factories, codec = _integration()
    starts = (0.0, 1.0, 2.0, 4.0, 6.0, 8.0)
    durations = (1.0, 1.0, 2.0, 2.0, 2.0, 2.0)
    source = FakeTemporalCollection(
        name="passing_subject",
        temporals=tuple(
            FakeTemporalNote(pitch, start, duration)
            for pitch, start, duration in zip(
                (72, 74, 76, 74, 71, 72),
                starts,
                durations,
                strict=True,
            )
        ),
        end_beat=10.0,
    )

    result = harmonize_temporal_collection(
        source,
        harmonic_plan=("I", "I", "vi", "ii", "V", "I"),
        metric_levels=(3, 1, 2, 3, 2, 3),
        traversal=ChoiceTraversal.DEPTH_FIRST,
        factories=factories,
        codec=codec,
    )[0]

    assert result.symbolic.melodic_roles[1] == "passing_tone"
    assert result.symbolic.voice_continuations == (
        VoiceContinuation(position=1, voice="alto", previous_position=0),
        VoiceContinuation(position=1, voice="tenor", previous_position=0),
        VoiceContinuation(position=1, voice="bass", previous_position=0),
    )
    assert len(result.piece.melodies[0].temporals) == 6
    for lower_voice in result.piece.melodies[1:]:
        assert len(lower_voice.temporals) == 5
        assert lower_voice.temporals[0].duration() == 2.0


def test_materializer_obeys_continuation_facts_not_melodic_role_names() -> None:
    factories, codec = _integration()
    source = FakeTemporalCollection(
        name="passing_subject",
        temporals=tuple(
            FakeTemporalNote(pitch, start, duration)
            for pitch, start, duration in zip(
                (72, 74, 76, 74, 71, 72),
                (0.0, 1.0, 2.0, 4.0, 6.0, 8.0),
                (1.0, 1.0, 2.0, 2.0, 2.0, 2.0),
                strict=True,
            )
        ),
        end_beat=10.0,
    )
    result = harmonize_temporal_collection(
        source,
        harmonic_plan=("I", "I", "vi", "ii", "V", "I"),
        metric_levels=(3, 1, 2, 3, 2, 3),
        traversal=ChoiceTraversal.DEPTH_FIRST,
        factories=factories,
        codec=codec,
    )[0]

    relabeled = replace(
        result.symbolic,
        melodic_roles=("chord_tone",) * len(source.temporals),
    )
    sustained = _materialize_voice_notes(
        tuple(source.temporals),
        relabeled,
        voice_index=1,
        voice_name="alto",
        given_voice="soprano",
        factory=factories.note,
    )
    rearticulated = _materialize_voice_notes(
        tuple(source.temporals),
        replace(relabeled, voice_continuations=()),
        voice_index=1,
        voice_name="alto",
        given_voice="soprano",
        factory=factories.note,
    )

    assert len(sustained) == 5
    assert sustained[0].duration() == 2.0
    assert len(rearticulated) == 6
    assert [note.duration() for note in rearticulated[:2]] == [1.0, 1.0]


def test_muses_harmonizer_rejects_polyphonic_or_unsupported_input() -> None:
    factories, codec = _integration()
    overlapping = FakeTemporalCollection(
        temporals=(
            FakeTemporalNote(67, 0.0, 2.0),
            FakeTemporalNote(72, 1.0, 1.0),
        )
    )

    with pytest.raises(ValueError, match="monophonic"):
        harmonize_temporal_collection(
            overlapping,
            factories=factories,
            codec=codec,
        )
    with pytest.raises(ValueError, match="C major"):
        harmonize_temporal_collection(
            FakeTemporalCollection(
                temporals=(
                    FakeTemporalNote(67, 0.0, 1.0),
                    FakeTemporalNote(72, 1.0, 1.0),
                )
            ),
            key_signature="G",
            factories=factories,
            codec=codec,
        )


def test_real_muses_piece_and_exports_when_optional_dependency_is_available(
    tmp_path: Path,
) -> None:
    temporals = pytest.importorskip("muses.base.temporals")
    muses_io = pytest.importorskip("muses.io")
    source = temporals.TemporalCollection(
        name="real_subject",
        temporals=(
            temporals.TemporalNote(71, 0.0, 1.0),
            temporals.TemporalNote(72, 1.0, 1.0),
        ),
        instrument="choir",
    )

    result = harmonize_temporal_collection(source)[0]

    assert isinstance(result.piece, temporals.Piece)
    assert all(
        isinstance(voice, temporals.TemporalCollection)
        for voice in result.piece.melodies
    )
    assert len(result.piece.melodies) == 4
    midi_path = tmp_path / "harmonized.mid"
    musicxml_path = tmp_path / "harmonized.musicxml"
    result.piece.save_midi(midi_path)
    muses_io.write_musicxml(result.piece, musicxml_path)

    assert midi_path.stat().st_size > 0
    assert "<score-partwise" in musicxml_path.read_text()
