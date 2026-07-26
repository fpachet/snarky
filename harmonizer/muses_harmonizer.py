"""End-to-end MuSES to tonal Snarky SATB harmonization.

The current executable profile chooses six diatonic triads or V7, their
supported inversions, and four SATB notes per position. Snarky rules enforce
vertical voicing, doubling, tendency-tone resolution, harmonic rhythm and the
selected cadence before the solution is reconstructed as a MuSES Piece.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from importlib import import_module
from typing import Protocol, cast

from snarky import Atom, ChoiceTraversal, Fact, Number, Status, Term, Triple
from snarky.integrations import (
    MusesTemporalCollectionCodec,
    MusesTemporalNoteCodec,
    TemporalCollectionLike,
    TemporalNoteLike,
)
from snarky.integrations.muses import (
    MUSES_CONTAINS,
    MUSES_INDEX,
)

from .note_solver import (
    VOICE_NAMES,
    Cadence,
    HarmonicPlanDegree,
    HarmonicPlanProfile,
    MetricStrength,
    NoteHarmonization,
    SATBVoice,
    _note_harmonization,
    build_note_harmonizer_model,
    solve_note_harmonizer,
)

DEFAULT_SOURCE_IDENTITY = Atom("muses_given_line")


class TemporalNoteFactory(Protocol):
    def __call__(
        self,
        pitch: int,
        start_time: int | float,
        duration: int | float,
        velocity: int = 60,
        midi_channel: int = 0,
    ) -> TemporalNoteLike: ...


class TemporalCollectionFactory(Protocol):
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


class PieceLike(Protocol):
    name: str
    title: str
    composer: str
    melodies: list[TemporalCollectionLike]
    ticks_per_beat: int
    time_signature: str
    key_signature: str
    tempo: int

    def save_midi(self, file_name: object) -> str: ...


class PieceFactory(Protocol):
    def __call__(
        self,
        name: str = "unnamed",
        title: str = "unknown",
        composer: str = "unknown",
        melodies: Sequence[TemporalCollectionLike] | None = None,
        ticks_per_beat: int = 480,
        time_signature: str = "4/4",
        key_signature: str = "C",
        tempo: int = 500_000,
    ) -> PieceLike: ...


@dataclass(frozen=True, slots=True)
class MusesFactories:
    """Constructors used to materialize the optional MuSES result."""

    note: TemporalNoteFactory
    collection: TemporalCollectionFactory
    piece: PieceFactory


@dataclass(frozen=True, slots=True)
class MusesHarmonization:
    """One four-voice MuSES piece and its complete symbolic result."""

    piece: PieceLike
    symbolic: NoteHarmonization
    given_voice: SATBVoice
    source_facts: tuple[Fact, ...]
    voice_facts: tuple[tuple[Fact, ...], ...]


def harmonize_temporal_collection(
    line: TemporalCollectionLike,
    *,
    given_voice: SATBVoice = "soprano",
    cadence: Cadence = "perfect",
    harmonic_rhythm: tuple[int, ...] | None = None,
    harmonic_plan: tuple[HarmonicPlanDegree | None, ...] | None = None,
    harmonic_plan_profile: HarmonicPlanProfile | None = None,
    metric_strengths: tuple[MetricStrength, ...] | None = None,
    max_solutions: int = 1,
    traversal: ChoiceTraversal = ChoiceTraversal.BEST_FIRST,
    seed: int = 0,
    identity: Atom = DEFAULT_SOURCE_IDENTITY,
    codec: MusesTemporalCollectionCodec | None = None,
    factories: MusesFactories | None = None,
    piece_name: str | None = None,
    title: str | None = None,
    composer: str = "Snarky",
    ticks_per_beat: int = 480,
    time_signature: str = "4/4",
    key_signature: str = "C",
    tempo: int = 500_000,
) -> tuple[MusesHarmonization, ...]:
    """Harmonize one MuSES monophonic line as any SATB voice.

    The current musical profile is the executable C-major core documented by
    :mod:`harmonizer`: diatonic triads, dominant seventh, inversions, SATB
    ranges and spacing, tendency-tone resolution, functional transitions,
    cadence profile and explicit harmonic rhythm.
    """

    if key_signature != "C":
        raise ValueError("the current harmonizer profile supports C major only")
    constructors = factories or _load_muses_factories()
    temporal_codec = codec or MusesTemporalCollectionCodec(
        note_codec=MusesTemporalNoteCodec(factory=constructors.note),
        factory=constructors.collection,
    )
    source_facts = temporal_codec.encode(line, identity=identity)
    source = temporal_codec.decode(identity, source_facts)
    notes = _validated_notes(source)
    source_notes = _ordered_note_identities(source_facts, identity)
    if len(source_notes) != len(notes):
        raise ValueError("MuSES fact snapshot and collection length disagree")

    pitches = tuple(note.pitch for note in notes)
    metric = (
        _metric_strengths(notes, time_signature)
        if metric_strengths is None
        else metric_strengths
    )
    model = build_note_harmonizer_model(
        pitches,
        given_voice=given_voice,
        cadence=cadence,
        harmonic_rhythm=harmonic_rhythm,
        harmonic_plan=harmonic_plan,
        harmonic_plan_profile=harmonic_plan_profile,
        metric_strengths=metric,
        note_durations=tuple(note.duration() for note in notes),
        source_facts=source_facts,
        source_notes=source_notes,
    )
    search = solve_note_harmonizer(
        model,
        max_solutions=max_solutions,
        traversal=traversal,
        seed=seed,
    )
    symbolic = tuple(
        _note_harmonization(model, search, index)
        for index in range(len(search.solutions))
    )
    return tuple(
        _materialize_solution(
            source,
            notes,
            solution,
            given_voice=given_voice,
            codec=temporal_codec,
            factories=constructors,
            source_facts=source_facts,
            piece_name=piece_name,
            title=title,
            composer=composer,
            ticks_per_beat=ticks_per_beat,
            time_signature=time_signature,
            key_signature=key_signature,
            tempo=tempo,
        )
        for solution in symbolic
    )


def _materialize_solution(
    source: TemporalCollectionLike,
    source_notes: tuple[TemporalNoteLike, ...],
    solution: NoteHarmonization,
    *,
    given_voice: SATBVoice,
    codec: MusesTemporalCollectionCodec,
    factories: MusesFactories,
    source_facts: tuple[Fact, ...],
    piece_name: str | None,
    title: str | None,
    composer: str,
    ticks_per_beat: int,
    time_signature: str,
    key_signature: str,
    tempo: int,
) -> MusesHarmonization:
    collections: list[TemporalCollectionLike] = []
    voice_fact_sets: list[tuple[Fact, ...]] = []
    for voice_index, voice in enumerate(VOICE_NAMES):
        voice_name = cast(SATBVoice, voice.name)
        notes = _materialize_voice_notes(
            source_notes,
            solution,
            voice_index=voice_index,
            voice_name=voice_name,
            given_voice=given_voice,
            factory=factories.note,
        )
        collection = factories.collection(
            name=voice_name,
            temporals=notes,
            instrument=source.instrument,
            program_change=source.program_change,
            melody_type=_melody_type(voice_name),
            end_beat=source.end_beat,
        )
        voice_identity = Atom(f"harmonized_{voice_name}")
        voice_facts = codec.encode(collection, identity=voice_identity)
        collections.append(codec.decode(voice_identity, voice_facts))
        voice_fact_sets.append(voice_facts)

    name = piece_name or f"{source.name or 'phrase'}_satb"
    piece = factories.piece(
        name=name,
        title=title or name,
        composer=composer,
        melodies=tuple(collections),
        ticks_per_beat=ticks_per_beat,
        time_signature=time_signature,
        key_signature=key_signature,
        tempo=tempo,
    )
    return MusesHarmonization(
        piece,
        solution,
        given_voice,
        source_facts,
        tuple(voice_fact_sets),
    )


def _materialize_voice_notes(
    source_notes: tuple[TemporalNoteLike, ...],
    solution: NoteHarmonization,
    *,
    voice_index: int,
    voice_name: SATBVoice,
    given_voice: SATBVoice,
    factory: TemporalNoteFactory,
) -> tuple[TemporalNoteLike, ...]:
    """Preserve soprano attacks and merge sustained accompaniment spans."""

    continuation_sources = {
        continuation.position: continuation.previous_position
        for continuation in solution.voice_continuations
        if continuation.voice == voice_name
    }
    specifications: list[tuple[int, float, float, int, int]] = []
    for index, (source_note, voicing) in enumerate(
        zip(source_notes, solution.voicings, strict=True)
    ):
        pitch = voicing[voice_index]
        start = float(source_note.start_beat)
        end = float(source_note.end_beat)
        channel = source_note.midi_channel if voice_name == given_voice else voice_index
        continuation_source = continuation_sources.get(index)
        if continuation_source is not None:
            if continuation_source != index - 1:
                raise ValueError("voice continuation must reference the previous note")
            if not specifications or specifications[-1][0] != pitch:
                raise ValueError("a continued voice must preserve its pitch")
            if not math.isclose(specifications[-1][2], start):
                raise ValueError("a continued voice must join contiguous notes")
            previous = specifications[-1]
            specifications[-1] = (
                previous[0],
                previous[1],
                end,
                previous[3],
                previous[4],
            )
            continue
        specifications.append((pitch, start, end, source_note.velocity, channel))

    return tuple(
        factory(
            pitch,
            start,
            end - start,
            velocity=velocity,
            midi_channel=channel,
        )
        for pitch, start, end, velocity, channel in specifications
    )


def _validated_notes(
    collection: TemporalCollectionLike,
) -> tuple[TemporalNoteLike, ...]:
    notes: list[TemporalNoteLike] = []
    for temporal in collection.temporals:
        if not isinstance(temporal, TemporalNoteLike):
            raise TypeError("the harmonizer accepts TemporalNote objects only")
        if temporal.duration() <= 0:
            raise ValueError("the given line contains a non-positive duration")
        notes.append(temporal)
    if len(notes) < 2:
        raise ValueError("the harmonizer needs at least two TemporalNote objects")
    for previous, current in zip(notes[:-1], notes[1:], strict=True):
        if current.start_beat < previous.end_beat:
            raise ValueError("the given SATB line must be monophonic")
    return tuple(notes)


def _metric_strengths(
    notes: tuple[TemporalNoteLike, ...],
    time_signature: str,
) -> tuple[MetricStrength, ...]:
    """Translate note onsets into strong/weak facts for simple meters."""

    try:
        numerator_text, denominator_text = time_signature.split("/", maxsplit=1)
        numerator = int(numerator_text)
        denominator = int(denominator_text)
    except (AttributeError, ValueError) as error:
        raise ValueError(
            "time_signature must have the form numerator/denominator"
        ) from error
    if numerator <= 0 or denominator <= 0:
        raise ValueError("time_signature values must be positive")
    measure_quarters = numerator * 4 / denominator
    if measure_quarters <= 0:
        raise ValueError("time_signature must define a positive measure")
    secondary_accent = measure_quarters / 2
    strengths: list[MetricStrength] = []
    for note in notes:
        offset = float(note.start_beat) % measure_quarters
        strong = math.isclose(offset, 0.0) or math.isclose(
            offset,
            secondary_accent,
        )
        strengths.append("strong" if strong else "weak")
    return tuple(strengths)


def _ordered_note_identities(
    facts: tuple[Fact, ...],
    collection: Atom,
) -> tuple[Atom, ...]:
    indexed: list[tuple[int, Atom]] = []
    for value in _values(facts, collection, MUSES_CONTAINS):
        if not isinstance(value, Atom):
            raise TypeError("MuSES collection members must be Atom identities")
        index = _required_integer(facts, value, MUSES_INDEX)
        indexed.append((index, value))
    indexed.sort(key=lambda item: item[0])
    expected = list(range(len(indexed)))
    if [index for index, _ in indexed] != expected:
        raise ValueError("MuSES temporal indexes must be contiguous from zero")
    return tuple(identity for _, identity in indexed)


def _values(
    facts: tuple[Fact, ...],
    subject: Atom,
    relation: Atom,
) -> tuple[Term, ...]:
    output: list[Term] = []
    for fact in facts:
        entity = fact.entity
        if (
            fact.status == Status.VRAI
            and isinstance(entity, Triple)
            and entity.subject == subject
            and entity.relation == relation
        ):
            output.append(entity.object)
    return tuple(dict.fromkeys(output))


def _required_integer(
    facts: tuple[Fact, ...],
    subject: Atom,
    relation: Atom,
) -> int:
    values = _values(facts, subject, relation)
    if len(values) != 1 or not isinstance(values[0], Number):
        raise ValueError(f"expected one numeric {relation.name} for {subject.name}")
    value = values[0].value
    if isinstance(value, float) and not value.is_integer():
        raise TypeError(f"{relation.name} must contain an integer")
    return int(value)


def _melody_type(voice: SATBVoice) -> str:
    if voice == "soprano":
        return "melody"
    if voice == "bass":
        return "bass"
    return "harmony"


def _load_muses_factories() -> MusesFactories:
    try:
        module = import_module("muses.base.temporals")
    except ModuleNotFoundError as error:
        raise ModuleNotFoundError(
            "MuSES is required for harmonize_temporal_collection; install "
            "the sibling project first"
        ) from error
    return MusesFactories(
        cast(TemporalNoteFactory, module.TemporalNote),
        cast(TemporalCollectionFactory, module.TemporalCollection),
        cast(PieceFactory, module.Piece),
    )
