# Generated harmony outputs

This directory is reserved for reproducible MIDI and MusicXML output. Generated
files are ignored by Git and excluded from Python distributions.

With the optional MuSES sibling project installed:

```sh
uv run python -m harmonizer.example_muses
uv run python -m harmonizer.example_muses --long
```

Use `--output-directory` to write elsewhere. The source inputs are the example
constructors and declarative rule modules, not files in this directory.
