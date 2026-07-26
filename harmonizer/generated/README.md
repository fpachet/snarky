# Generated harmony outputs

This directory is reserved for reproducible MIDI and MusicXML output. Generated
files are ignored by Git and excluded from Python distributions.

With the optional MuSES sibling project installed:

```sh
uv run python -m harmonizer.example_muses
uv run python -m harmonizer.example_muses --long
uv run python -m harmonizer.example_muses --diatonic
uv run python -m harmonizer.example_muses --extended
```

Use `--output-directory` to write elsewhere. The source inputs are the example
constructors and declarative rule modules, not files in this directory.
The eight-bar `--extended` example supplies only the soprano, harmonic rhythm,
and cadence; its harmonic plan is selected in Snarky's first program step.
The `--diatonic` example gives every note its own harmonic decision. Its
opening `C-D-E` is harmonized `I-V-I`; D is a normal chord tone of V and is
subject to the same vertical and transition rules as every other note.
