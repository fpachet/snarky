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

The main model gives each note seven finite-domain variables:

- chord degree among `I`, `ii`, `IV`, `V`, `V7`, `vi`, and `vii°`;
- melodic role among chord tone, passing tone, upper/lower neighbor,
  suspension, and anticipation;
- root, first, or permitted second inversion;
- soprano, alto, tenor, and bass pitches.

One SATB voice is supplied by the caller. Declarative groups then generate
voicings, channel chord and inversion variables, propagate adjacent-event
support, produce choices, and interpret the result.

The current vocabulary includes:

- strict order, spacing, chord completeness, inversion bass, and doubling;
- soprano chord tones, passing tones, upper/lower neighbors, suspensions,
  and anticipations;
- functional progression and four cadence profiles;
- melodic bounds, overlap, forbidden parallels, and direct motion;
- leading-tone and dominant-seventh resolution;
- cadential `I64` resolutions;
- explicit harmonic rhythm and strong/weak metric facts.

In the note-by-note model, these are no longer opaque Python checks. Chord
completeness uses `NVALUE`; doubling uses correlated `COUNT`; motion,
overlap, parallels, direct outer-voice perfect intervals, tendency tones, and
cadential six-four resolution produce named `R-*` violation facts in
[`vertical_conformance.rules`](vertical_conformance.rules) and
[`voice_leading_conformance.rules`](voice_leading_conformance.rules).
`note_transition.rules` performs bidirectional support revision over the
transitions that have no violation.

Passing, neighbor, suspension, and anticipation shapes are recognized in
[`melodic_roles.rules`](melodic_roles.rules) from the local
previous–current–next contour and metric strength. The rules add admissible
values to a melodic-role CSP variable; they do not label the note after the
fact. Chord, role, inversion, and SATB support are then propagated jointly.
No Python callback decides the role.

Example:

```python
from harmonizer import harmonize_notes

solution = harmonize_notes((72, 69, 71, 72), max_solutions=1)[0]
assert solution.chords == (
    "degree_I",
    "degree_IV",
    "degree_V",
    "degree_I",
)
```

The generated lines are:

| Voice | MIDI pitches |
|---|---|
| soprano | `72 69 71 72` |
| alto | `64 65 62 64` |
| tenor | `55 60 50 55` |
| bass | `48 41 43 36` |

Chord values are not copied from Python: form, vertical support, and
transitions reduce their domains before the harmonic-plan step chooses among
the remaining alternatives. A `V7` resolution can still be requested as a
partial plan when testing that specific rule.

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

An optional harmonic plan can restrict those event variables with ordinary
`planned_chord` facts. It specifies no SATB notes or inversions. It is useful
as a test fixture or user constraint, but the extended example does not need
one:

```python
from snarky import ChoiceTraversal

extended = harmonize_notes(
    (67, 76, 69, 72, 72, 76, 65, 69, 67, 64, 69, 72, 74, 69, 71, 72),
    harmonic_rhythm=(0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 8),
    traversal=ChoiceTraversal.DEPTH_FIRST,
    max_solutions=1,
)[0]
```

Python emits the soprano, harmonic-event links, cadence name, finite domains,
and extensional tonal vocabulary. `derive_harmonic_plan` derives cadence and
functional restrictions; vertical and transition rules filter the chord
domains. The `harmonic_plan` step then chooses
`I–IV–I–IV–I–IV–ii–V–I`, after which `satb_realization` chooses inversions
and the 48 non-given pitches. A failure during realization can backtrack to a
harmonic choice. Depth-first traversal is used because this example
demonstrates one feasible realization rather than ranking a large best-first
frontier.

## Every soprano note receives a harmonic decision

By default, every soprano attack has its own chord and inversion variables.
For example, an ascending C-major scale is not preclassified as tonic with
passing notes:

```python
diatonic = harmonize_notes(
    (60, 62, 64, 65, 67, 69, 71, 72),
    traversal=ChoiceTraversal.DEPTH_FIRST,
    max_solutions=1,
)[0]

assert diatonic.chords == (
    "degree_I", "degree_V", "degree_I", "degree_IV",
    "degree_I", "degree_IV", "degree_V", "degree_I",
)
assert diatonic.melodic_roles == ("chord_tone",) * 8
```

The eight-bar generated example begins with this complete scale and follows it
with an eight-note cadential phrase. Thus D is harmonized normally in C major:
it receives the complete chord domain, the solver selects V, and all vertical,
transition, inversion, spacing, doubling, and voice-leading rules apply
exactly as at the other positions. A pitch is not intrinsically a non-chord
tone; that role is relative to the selected harmony.

## Metric-aware melodic roles

Every note has a `melodic_role` variable whose initial domain contains
`chord_tone`. Declarative contour and metric rules may add other candidates.
For example, a weak D between C and E admits `passing_tone`. A partial harmonic
plan can establish the local tonic context without stating the role:

```python
held = harmonize_notes(
    (72, 74, 76, 67, 65, 69, 71, 72),
    metric_strengths=(
        "strong", "weak", "strong", "strong",
        "strong", "strong", "strong", "strong",
    ),
    harmonic_plan=("I", "I", "vi", "I", "IV", "ii", "V", "I"),
    traversal=ChoiceTraversal.DEPTH_FIRST,
    max_solutions=1,
)[0]

assert held.melodic_roles[:3] == (
    "chord_tone",
    "passing_tone",
    "chord_tone",
)
assert held.chords[:3] == ("degree_I", "degree_I", "degree_vi")
```

The role channel enforces these meanings:

- chord tone: the soprano belongs to the current chord;
- passing or neighbor tone: a weak non-chord tone with the appropriate
  stepwise contour; the preceding chord and exact lower-voice voicing remain
  sounding through it, while the following structural note may receive a new
  harmony;
- suspension: a strong repeated pitch prepared in the previous chord,
  dissonant over the new harmony, then resolved downward by step while the
  lower voices sustain the resolution chord;
- anticipation: a weak non-chord tone over the sustained preceding harmony,
  held into a following chord that contains it.

Passing tones, neighbors, and anticipations leave a complete triad in the
three lower voices. They reuse the exact previous alto, tenor, and bass
pitches; the MuSES exporter consequently extends those notes instead of
writing repeated attacks. A suspension instead omits its resolution class
from the lower voices: the suspended pitch temporarily replaces that chord
member. The exact lower voicing is held through the resolution. All policies
are in rule premises and remain subject to the ordinary chord, inversion,
transition, spacing, doubling, and voice-leading propagation.

`metric_strengths` accepts one `strong` or `weak` value per note. The MuSES
adapter derives these facts from note onsets and the time signature.
`note_durations` accepts durations in quarter-note beats; MuSES supplies them
from the source notes.

Passing tones and neighbors must now be contextually short: at most one beat
and no longer than either adjacent note. Anticipations use the same brevity
test. Thus a weak, stepwise D may be a passing tone when short, but the same D
is harmonized as a chord tone when lengthened. Suspensions are deliberately
exempt because their identity depends on preparation, accent, and resolution,
not brevity.

The current metric hierarchy is deliberately binary; compound-meter accent
levels, appoggiaturas, escape tones, and ornaments over `V7` remain future
work.

The eight-bar generated demonstration harmonizes most soprano attacks,
including its opening D as a chord tone of V. It also contains a lower
neighbor, a 4–3 suspension, and an anticipation:

```sh
uv run python -m harmonizer.example_muses --roles
```

It supplies only two local chord anchors, for the suspension and anticipation,
and no melodic-role labels. Snarky derives all 18 role domains, infers the
remaining harmony, and selects the complete SATB realization. The passing-tone
and upper-neighbor paths remain covered by focused solver tests.

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

The manifest separates preparation, the sequential `harmonic_plan` and
`satb_realization` steps, common propagation, and interpretation. It is parsed
from [`note_harmonizer.program`](note_harmonizer.program), so the construction
order is part of the model rather than hidden solver configuration.

Preparation generates complete voicings, filters their vertical conformance,
applies the structural cadence restrictions, and classifies each remaining
ground transition once. This classification is value-invariant in the current
“case 1” model: rules and choices remove domain values but never add new
musical values. During search, each support query joins both a prepared legal
transition and the current neighboring `voicing_candidate`; a removed
candidate therefore cannot remain a support. This keeps transition revision
inside the branch fixed point without recomputing the rule catalogue in every
branch.

## Python boundary and Snarky limits

The note-by-note model keeps Python for finite model construction, not musical
policy:

- creating positions and CSP variables;
- enumerating the finite C-major pitch/chord vocabulary and choice weights;
- converting MuSES objects to facts and solutions back to objects;
- launching search and decoding its selected values.

Chord completeness, doubling, voice leading, melodic-role analysis, tendency
tones, cadence form, channeling, support revision, step-specific choices, and
contradictions are rules or constraints. Python supplies
`(problem cadence perfect)` and structural harmonic-event positions; rules
derive the corresponding initial, penultimate, final, and cadential
restrictions. The compact complete-voicing oracle remains intentionally
Python-backed as a differential reference.

No current core SATB rule required a new engine feature. A few formulations
are more verbose than their musical statement because Snarky currently has:

- no reusable rule macros or parameterized user-defined relations;
- no `ABS` arithmetic expression;
- no logical disjunction inside one premise block.

The rule base handles those cases with paired up/down rules and separate rules
for fifths and octaves. This is an abstraction limitation, not an
expressiveness blocker for finite SATB. More substantial future features need
new *musical facts*—key and spelling, metric strength, suspension preparation,
and modulation state—rather than hidden Python predicates.

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
uv run python -m harmonizer.example_muses --diatonic
uv run python -m harmonizer.example_muses --roles
uv run python -m harmonizer.example_muses --extended
```

Generated MIDI and MusicXML files are reproducible outputs under
`harmonizer/generated/`; they are not source inputs.

## Current limits

The model is restricted to C major and a focused tonal vocabulary. It does not
yet cover all seventh chords and inversions, passing or pedal six-four chords,
complete leading-tone exceptions, appoggiaturas, escape tones, modulation,
rests, a multi-level metric hierarchy, or lexicographic optimization.

The [specification](SPECIFICATION.md) and [project plan](PLAN.md) retain design
detail. Benchmark protocols and machine-readable measurements are in
[benchmarks](../benchmarks/README.md).
