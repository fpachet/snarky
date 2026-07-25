# Four-part tonal harmonizer

The harmonizer is Snarky's main hybrid-generation case study. It combines
declarative tonal rules, finite-domain propagation, explicit choices,
contextual weights, reversible branches, and traceable contradictions.

It is a research prototype rather than a complete implementation of Pierre
Roy's 1998 profile.

## Two executable models

### Complete-voicing oracle

The compact oracle harmonizes a short C-major phrase by choosing one complete
SATB voicing per position. Python compiles vertically valid candidates; generic
Snarky rules handle domain reduction, singleton recognition, contradiction,
and solution detection.

Vertical constraints cover:

- the given soprano;
- strict SATB order and spacing;
- complete triads;
- the `2,1,1` pitch-class multiplicity.

Intensional transition rules remove a candidate when no compatible voicing
remains at the neighboring position. A pure registered predicate checks
melodic intervals, voice overlap, parallel perfect intervals, and direct
motion. Rules remain responsible for support, removal, fixed points, and
trace generation.

Run the oracle with:

```sh
uv run python -m harmonizer.solver
```

The extensional transition table remains available as a differential oracle.

### Note-by-note tonal model

The main model gives each harmonic event six finite-domain variables:

- chord degree among `I`, `ii`, `IV`, `V`, `V7`, `vi`, and `vii°`;
- root, first, or permitted second inversion;
- soprano, alto, tenor, and bass pitches.

One SATB voice is supplied by the caller. Declarative groups then generate
voicings, channel chord and inversion variables, propagate adjacent-event
support, produce choices, and interpret the result.

The current vocabulary includes:

- strict order, spacing, chord completeness, inversion bass, and doubling;
- functional progression and four cadence profiles;
- melodic bounds, overlap, forbidden parallels, and direct motion;
- leading-tone and dominant-seventh resolution;
- cadential `I64` resolutions;
- explicit harmonic rhythm.

Example:

```python
from harmonizer import harmonize_notes

solution = harmonize_notes((72, 69, 71, 72), max_solutions=1)[0]
assert solution.chords == (
    "degree_I",
    "degree_ii",
    "degree_V7",
    "degree_I",
)
```

The generated lines are:

| Voice | MIDI pitches |
|---|---|
| soprano | `72 69 71 72` |
| alto | `67 65 65 64` |
| tenor | `64 62 62 55` |
| bass | `48 50 43 48` |

The leading tone resolves upward and the seventh of `V7` resolves downward.
Chord values are not copied from Python: form, vertical support, and
transitions reduce their domains.

A supplied bass can produce a cadential six-four:

```python
six_four = harmonize_notes(
    (48, 43, 43, 48),
    given_voice="bass",
    max_solutions=1,
)[0]
assert six_four.inversions == ("root", "second", "root", "root")
```

## Cadence, rhythm, and weights

Cadence profiles are public parameters:

```python
plagal = harmonize_notes((69, 72), cadence="plagal")[0]
deceptive = harmonize_notes((71, 72), cadence="deceptive")[0]
half = harmonize_notes((72, 71), cadence="half")[0]
```

`harmonic_rhythm` maps input notes to harmonic events. Consecutive notes with
the same event number share chord and inversion variables:

```python
held = harmonize_notes(
    (72, 72, 71, 72),
    harmonic_rhythm=(0, 0, 1, 2),
)[0]
assert held.chords[0] == held.chords[1]
```

Static note, chord, and inversion weights become contextual when the preceding
choice is known. Best-first search returns deterministic high-scoring
realizations; reproducible weighted sampling is also available:

```python
from harmonizer import sample_harmonization

sample = sample_harmonization((71, 72), seed=7)
```

Weights order or sample feasible solutions. They never weaken hard
constraints and are not presented as a learned joint probability model.

## Explicit orchestration

`build_note_harmonizer_model()` returns a model with an inspectable
`RuleProgram`:

```python
from harmonizer import build_note_harmonizer_model

model = build_note_harmonizer_model()
print(model.program.manifest())
```

The manifest separates preparation, choice production, propagation, and
interpretation. This makes the exact generic CSP and musical groups part of
the reproducible model rather than hidden solver configuration.

## Optional MuSES pipeline

When the sibling MuSES project is installed, the public integration accepts a
monophonic `TemporalCollection` and returns one or more four-voice `Piece`
objects:

```python
from harmonizer import harmonize_temporal_collection
from muses.base.temporals import TemporalCollection, TemporalNote

soprano = TemporalCollection(
    name="given_soprano",
    temporals=(
        TemporalNote(72, 0.0, 2.0),
        TemporalNote(69, 2.0, 2.0),
        TemporalNote(71, 4.0, 2.0),
        TemporalNote(72, 6.0, 2.0),
    ),
    instrument="choir",
)
result = harmonize_temporal_collection(soprano, piece_name="generated_satb")[0]
piece = result.piece
```

The codec snapshots the source without mutating it, runs the same rule program,
reconstructs all four temporal collections, and preserves timing and playback
metadata.

With both repositories as siblings:

```sh
python -m pip install -e ../muses
uv run python -m harmonizer.example_muses
uv run python -m harmonizer.example_muses --long
```

Generated MIDI and MusicXML files are reproducible outputs under
`harmonizer/generated/`; they are not source inputs.

## Current limits

The model is restricted to C major and a focused tonal vocabulary. It does not
yet cover all seventh chords and inversions, passing or pedal six-four chords,
complete leading-tone exceptions, non-chord tones, modulation, rests, musical
meter in rule conditions, or lexicographic optimization.

The [specification](SPECIFICATION.md) and [project plan](PLAN.md) retain design
detail. Benchmark protocols and machine-readable measurements are in
[benchmarks](../benchmarks/README.md).
