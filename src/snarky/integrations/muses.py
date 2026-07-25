"""Snapshot codecs for the optional MuSES temporal object model."""

from __future__ import annotations

from base64 import urlsafe_b64decode, urlsafe_b64encode
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from importlib import import_module
from typing import Protocol, cast, runtime_checkable

from ..facts import Fact
from ..terms import Atom, Number, Status, Term, Triple

MUSES_TYPE = Atom("muses_type")
MUSES_TEMPORAL_NOTE = Atom("muses_temporal_note")
MUSES_TEMPORAL_COLLECTION = Atom("muses_temporal_collection")
MUSES_NAME = Atom("muses_name")
MUSES_INSTRUMENT = Atom("muses_instrument")
MUSES_PROGRAM_CHANGE = Atom("muses_program_change")
MUSES_MELODY_TYPE = Atom("muses_melody_type")
MUSES_END_BEAT = Atom("muses_end_beat")
MUSES_CONTAINS = Atom("muses_contains")
MUSES_INDEX = Atom("muses_index")
MUSES_PITCH = Atom("muses_pitch")
MUSES_START_BEAT = Atom("muses_start_beat")
MUSES_DURATION = Atom("muses_duration")
MUSES_VELOCITY = Atom("muses_velocity")
MUSES_MIDI_CHANNEL = Atom("muses_midi_channel")

_TEXT_PREFIX = "muses_text_"


@runtime_checkable
class TemporalNoteLike(Protocol):
    """Structural subset of ``muses.base.temporals.TemporalNote``."""

    pitch: int
    start_beat: int | float
    end_beat: int | float
    velocity: int
    midi_channel: int

    def duration(self) -> int | float: ...


class TemporalCollectionLike(Protocol):
    """Structural subset of ``TemporalCollection`` used by the codec."""

    name: str
    temporals: Sequence[object]
    instrument: str
    program_change: int
    melody_type: str
    end_beat: int | float


class _TemporalNoteFactory(Protocol):
    def __call__(
        self,
        pitch: int,
        start_time: int | float,
        duration: int | float,
        velocity: int = 60,
        midi_channel: int = 0,
    ) -> TemporalNoteLike: ...


class _TemporalCollectionFactory(Protocol):
    def __call__(
        self,
        name: str = "",
        temporals: Iterable[TemporalNoteLike] | None = None,
        *,
        instrument: str = "",
        program_change: int = 0,
        melody_type: str = "",
        end_beat: int | float = 0.0,
    ) -> TemporalCollectionLike: ...


@dataclass(frozen=True, slots=True)
class MusesTemporalNoteCodec:
    """Encode and reconstruct one mutable MuSES ``TemporalNote`` snapshot."""

    factory: _TemporalNoteFactory | None = field(
        default=None,
        repr=False,
    )

    def encode(
        self,
        value: TemporalNoteLike,
        *,
        identity: Atom,
    ) -> tuple[Fact, ...]:
        _require_note(value)
        return (
            _fact(identity, MUSES_TYPE, MUSES_TEMPORAL_NOTE),
            _fact(identity, MUSES_PITCH, _integer(value.pitch, "pitch")),
            _fact(
                identity,
                MUSES_START_BEAT,
                _numeric(value.start_beat, "start_beat"),
            ),
            _fact(
                identity,
                MUSES_DURATION,
                _numeric(value.duration(), "duration"),
            ),
            _fact(
                identity,
                MUSES_VELOCITY,
                _integer(value.velocity, "velocity"),
            ),
            _fact(
                identity,
                MUSES_MIDI_CHANNEL,
                _integer(value.midi_channel, "midi_channel"),
            ),
        )

    def decode(
        self,
        identity: Atom,
        facts: Iterable[Fact],
    ) -> TemporalNoteLike:
        snapshot = tuple(facts)
        _require_type(snapshot, identity, MUSES_TEMPORAL_NOTE)
        factory = self.factory or _load_muses_factories()[0]
        return factory(
            _required_integer(snapshot, identity, MUSES_PITCH),
            _required_number(snapshot, identity, MUSES_START_BEAT),
            _required_number(snapshot, identity, MUSES_DURATION),
            velocity=_required_integer(
                snapshot,
                identity,
                MUSES_VELOCITY,
            ),
            midi_channel=_required_integer(
                snapshot,
                identity,
                MUSES_MIDI_CHANNEL,
            ),
        )


@dataclass(frozen=True, slots=True)
class MusesTemporalCollectionCodec:
    """Encode and reconstruct a note-only MuSES temporal collection."""

    note_codec: MusesTemporalNoteCodec = field(
        default_factory=MusesTemporalNoteCodec
    )
    factory: _TemporalCollectionFactory | None = field(
        default=None,
        repr=False,
    )

    def encode(
        self,
        value: TemporalCollectionLike,
        *,
        identity: Atom,
    ) -> tuple[Fact, ...]:
        facts = [
            _fact(identity, MUSES_TYPE, MUSES_TEMPORAL_COLLECTION),
            _fact(identity, MUSES_NAME, _text(value.name)),
            _fact(identity, MUSES_INSTRUMENT, _text(value.instrument)),
            _fact(
                identity,
                MUSES_PROGRAM_CHANGE,
                _integer(value.program_change, "program_change"),
            ),
            _fact(
                identity,
                MUSES_MELODY_TYPE,
                _text(value.melody_type),
            ),
            _fact(
                identity,
                MUSES_END_BEAT,
                _numeric(value.end_beat, "end_beat"),
            ),
        ]
        for index, temporal in enumerate(value.temporals):
            note = _require_note(temporal)
            note_identity = _note_identity(identity, index)
            facts.extend(
                (
                    _fact(identity, MUSES_CONTAINS, note_identity),
                    _fact(note_identity, MUSES_INDEX, Number(index)),
                    *self.note_codec.encode(
                        note,
                        identity=note_identity,
                    ),
                )
            )
        return tuple(facts)

    def decode(
        self,
        identity: Atom,
        facts: Iterable[Fact],
    ) -> TemporalCollectionLike:
        snapshot = tuple(facts)
        _require_type(snapshot, identity, MUSES_TEMPORAL_COLLECTION)
        indexed_notes: list[tuple[int, TemporalNoteLike]] = []
        indexes: set[int] = set()
        for note_identity in _values(snapshot, identity, MUSES_CONTAINS):
            if not isinstance(note_identity, Atom):
                raise TypeError("MuSES collection members must be Atom identities")
            index = _required_integer(
                snapshot,
                note_identity,
                MUSES_INDEX,
            )
            if index in indexes:
                raise ValueError(f"duplicate MuSES temporal index {index}")
            indexes.add(index)
            indexed_notes.append(
                (
                    index,
                    self.note_codec.decode(note_identity, snapshot),
                )
            )
        indexed_notes.sort(key=lambda item: item[0])
        factory = self.factory or _load_muses_factories()[1]
        return factory(
            name=_required_text(snapshot, identity, MUSES_NAME),
            temporals=tuple(note for _, note in indexed_notes),
            instrument=_required_text(
                snapshot,
                identity,
                MUSES_INSTRUMENT,
            ),
            program_change=_required_integer(
                snapshot,
                identity,
                MUSES_PROGRAM_CHANGE,
            ),
            melody_type=_required_text(
                snapshot,
                identity,
                MUSES_MELODY_TYPE,
            ),
            end_beat=_required_number(
                snapshot,
                identity,
                MUSES_END_BEAT,
            ),
        )


def _load_muses_factories(
) -> tuple[_TemporalNoteFactory, _TemporalCollectionFactory]:
    try:
        module = import_module("muses.base.temporals")
    except ModuleNotFoundError as error:
        raise ModuleNotFoundError(
            "MuSES is required only when decoding without explicit "
            "factories; install the optional sibling project first"
        ) from error
    return (
        cast(_TemporalNoteFactory, module.TemporalNote),
        cast(
            _TemporalCollectionFactory,
            module.TemporalCollection,
        ),
    )


def _fact(subject: Atom, relation: Atom, object_: Term) -> Fact:
    return Fact(Triple(subject, relation, object_))


def _require_note(value: object) -> TemporalNoteLike:
    if not isinstance(value, TemporalNoteLike):
        raise TypeError(
            "the first MuSES codec supports TemporalNote objects only"
        )
    return value


def _integer(value: object, field_name: str) -> Number:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"MuSES {field_name} must be an integer")
    return Number(value)


def _numeric(value: object, field_name: str) -> Number:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"MuSES {field_name} must be numeric")
    return Number(value)


def _text(value: object) -> Atom:
    if not isinstance(value, str):
        raise TypeError("MuSES textual metadata must be strings")
    return Atom(f"{_TEXT_PREFIX}{_encode_token(value)}")


def _decode_text(value: Term) -> str:
    if not isinstance(value, Atom) or not value.name.startswith(_TEXT_PREFIX):
        raise TypeError("invalid encoded MuSES text")
    payload = value.name[len(_TEXT_PREFIX) :]
    return _decode_token(payload)


def _note_identity(collection: Atom, index: int) -> Atom:
    return Atom(f"muses_note_{_encode_token(collection.name)}_{index}")


def _encode_token(value: str) -> str:
    return urlsafe_b64encode(value.encode("utf-8")).decode("ascii").rstrip("=")


def _decode_token(value: str) -> str:
    padding = "=" * (-len(value) % 4)
    return urlsafe_b64decode(f"{value}{padding}".encode("ascii")).decode(
        "utf-8"
    )


def _values(
    facts: Iterable[Fact],
    subject: Atom,
    relation: Atom,
) -> tuple[Term, ...]:
    values: list[Term] = []
    for fact in facts:
        entity = fact.entity
        if (
            fact.status == Status.VRAI
            and isinstance(entity, Triple)
            and entity.subject == subject
            and entity.relation == relation
        ):
            values.append(entity.object)
    return tuple(dict.fromkeys(values))


def _required_value(
    facts: Iterable[Fact],
    subject: Atom,
    relation: Atom,
) -> Term:
    values = _values(facts, subject, relation)
    if len(values) != 1:
        raise ValueError(
            f"expected one {relation.name} value for {subject.name}, "
            f"found {len(values)}"
        )
    return values[0]


def _required_number(
    facts: Iterable[Fact],
    subject: Atom,
    relation: Atom,
) -> int | float:
    value = _required_value(facts, subject, relation)
    if not isinstance(value, Number):
        raise TypeError(f"{relation.name} must contain a Number")
    return value.value


def _required_integer(
    facts: Iterable[Fact],
    subject: Atom,
    relation: Atom,
) -> int:
    value = _required_number(facts, subject, relation)
    if isinstance(value, float) and not value.is_integer():
        raise TypeError(f"{relation.name} must contain an integer")
    return int(value)


def _required_text(
    facts: Iterable[Fact],
    subject: Atom,
    relation: Atom,
) -> str:
    return _decode_text(_required_value(facts, subject, relation))


def _require_type(
    facts: Iterable[Fact],
    identity: Atom,
    expected: Atom,
) -> None:
    actual = _required_value(facts, identity, MUSES_TYPE)
    if actual != expected:
        raise ValueError(
            f"{identity.name} has type {actual!r}, expected {expected.name}"
        )
