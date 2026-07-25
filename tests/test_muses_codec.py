from collections.abc import Iterable

import pytest

from snarky import (
    Atom,
    Fact,
    ForwardEngine,
    Number,
    Triple,
    parse_term,
    render_term,
)
from snarky.integrations import (
    MusesTemporalCollectionCodec,
    MusesTemporalNoteCodec,
)
from snarky.integrations.muses import (
    MUSES_CONTAINS,
    MUSES_PITCH,
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
        self.end_beat = max(
            (end_beat, *(note.end_beat for note in self.temporals))
        )


def _codec() -> MusesTemporalCollectionCodec:
    note_codec = MusesTemporalNoteCodec(factory=FakeTemporalNote)
    return MusesTemporalCollectionCodec(
        note_codec=note_codec,
        factory=FakeTemporalCollection,
    )


def test_temporal_collection_round_trips_as_an_independent_snapshot() -> None:
    source = FakeTemporalCollection(
        name="Phrase été",
        temporals=(
            FakeTemporalNote(64, 1.0, 0.5, velocity=72, midi_channel=2),
            FakeTemporalNote(60, 0.0, 1.0, velocity=68, midi_channel=1),
        ),
        instrument="grand piano",
        program_change=4,
        melody_type="melody",
        end_beat=3.0,
    )
    codec = _codec()
    identity = Atom("phrase_1")

    facts = codec.encode(source, identity=identity)
    restored = codec.decode(identity, facts)

    assert all(
        parse_term(render_term(fact.entity)) == fact.entity
        for fact in facts
    )
    assert restored is not source
    assert restored.name == source.name
    assert restored.instrument == source.instrument
    assert restored.program_change == source.program_change
    assert restored.melody_type == source.melody_type
    assert restored.end_beat == source.end_beat
    assert [
        (
            note.pitch,
            note.start_beat,
            note.duration(),
            note.velocity,
            note.midi_channel,
        )
        for note in restored.temporals
    ] == [
        (60, 0.0, 1.0, 68, 1),
        (64, 1.0, 0.5, 72, 2),
    ]


def test_solution_facts_materialize_without_mutating_the_source() -> None:
    source = FakeTemporalCollection(
        temporals=(FakeTemporalNote(60, 0.0, 1.0),)
    )
    codec = _codec()
    identity = Atom("phrase")
    facts = codec.encode(source, identity=identity)
    note_identity = next(
        fact.entity.object
        for fact in facts
        if isinstance(fact.entity, Triple)
        and fact.entity.subject == identity
        and fact.entity.relation == MUSES_CONTAINS
    )
    assert isinstance(note_identity, Atom)
    old_pitch = Fact(Triple(note_identity, MUSES_PITCH, Number(60)))
    new_pitch = Fact(Triple(note_identity, MUSES_PITCH, Number(67)))
    session = ForwardEngine(()).create_session(facts)
    checkpoint = session.checkpoint()

    session.retract(old_pitch)
    session.assume(new_pitch)
    changed = codec.decode(identity, session.facts)

    assert changed.temporals[0].pitch == 67
    assert source.temporals[0].pitch == 60

    session.rollback(checkpoint)
    restored = codec.decode(identity, session.facts)
    session.release(checkpoint)

    assert restored.temporals[0].pitch == 60
    assert source.temporals[0].pitch == 60


def test_collection_codec_rejects_unsupported_temporal_objects() -> None:
    source = FakeTemporalCollection()
    source.temporals.append(object())

    with pytest.raises(TypeError, match="TemporalNote"):
        _codec().encode(source, identity=Atom("unsupported"))


def test_real_muses_objects_when_optional_dependency_is_available() -> None:
    temporals = pytest.importorskip("muses.base.temporals")
    source = temporals.TemporalCollection(
        name="real",
        temporals=(
            temporals.TemporalNote(60, 0.0, 1.0),
            temporals.TemporalNote(64, 1.0, 0.5),
        ),
        instrument="piano",
    )
    codec = MusesTemporalCollectionCodec()
    identity = Atom("real_phrase")

    restored = codec.decode(
        identity,
        codec.encode(source, identity=identity),
    )

    assert isinstance(restored, temporals.TemporalCollection)
    assert [note.pitch for note in restored.temporals] == [60, 64]
