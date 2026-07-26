# Generated harmony outputs

This directory is reserved for reproducible MIDI and MusicXML output. Generated
files are ignored by Git and excluded from Python distributions.

With the optional MuSES sibling project installed:

```sh
uv run python -m harmonizer.example_muses
uv run python -m harmonizer.example_muses --long
uv run python -m harmonizer.example_muses --diatonic
uv run python -m harmonizer.example_muses --roles
uv run python -m harmonizer.example_muses --extended
```

Use `--output-directory` to write elsewhere. The source inputs are the example
constructors and declarative rule modules, not files in this directory.
The eight-bar `--extended` example supplies only the soprano, harmonic rhythm,
and cadence; its harmonic plan is selected in Snarky's first program step.
The eight-bar `--diatonic` example gives every note its own harmonic decision.
Its first phrase traverses the complete ascending C-major scale and is
harmonized `I-V-I-IV-I-IV-V-I`; D is a normal chord tone of V and is subject
to the same vertical and transition rules as every other note.
The eight-bar `--roles` example obtains four metric levels from MuSES's
hierarchical-metre API and classifies contextually short durations. Its melody
covers every pitch class in C major. A weak D is selected as an escape tone
over I; an accented C is selected as an appoggiatura over V and resolves to B.
Policy facts expose the unchanged lower voices through `continues_voice_from`;
those voices are exported as sustained notes rather than repeated attacks.
The example supplies only those two local chord anchors, not a complete
harmonic plan or any role labels. Passing tones, neighbors, suspensions, and
anticipations are covered by focused tests.
