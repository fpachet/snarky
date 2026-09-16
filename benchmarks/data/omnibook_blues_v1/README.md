# LSDB Omnibook Blues: two explicit corpus variants

This compact research fixture derives from the user's selected LSDB references:
`data/reference/omnibook_blues/references.json`, SHA-256
`49bb1a041968ccb03fb7fb27086f70ea6e7925c873e51d8bfb6070a73e1542ac`.
The inputs already are normalized to C. No second transposition is applied.

[corpus.json](corpus.json) retains 22 first complete choruses, including alternate
takes, each with weight one and 24 half-bar symbols. Identical progressions retain
their tune/take multiplicity. It records original XML hashes, source bar ranges,
source notes, and a complete position-level transformation list.

The importer checked all 22 XML hashes, 12-bar/4-4 dimensions, complete contiguous
bar coverage, exact half-bar alignment, and the transposition of roots, basses,
pitch-class sets and displayed symbols. There are no slash-bass or degree-altered
chords in this selection; future inputs containing them are rejected for explicit
handling rather than silently simplified. LSDB's independent source XML audit is
documented in its reference-set README.

## Variants and proposed simplification

| Source family | Source-faithful variant | Proposed paper-style variant |
|---|---|---|
| Dominant seventh | `C7` | `C7` |
| Minor triad | `Cm` | `Cm` |
| Major triad | `C` | `C7` |
| Diminished triad | `Cdim` | `C-7b5` |
| Half-diminished seventh | `C-7b5` | `C-7b5` |

Roots stay fixed. Major-to-dominant and diminished-to-half-diminished add a
seventh; they are deliberate modeling transformations, not source corrections.
The user requested both variants with an explicit map for review. The map remains
**proposed**, not an authenticated reconstruction of historical preprocessing.
Source notes such as Visa's minor dominant-root chord are preserved.

There are 31 changed half-bar positions in nine references: C→C7 (24), F→F7 (2),
A→A7 (2), Gbdim→Gb-7b5 (2), Ebdim→Eb-7b5 (1). The source segment inventory is
218 dominant, 77 minor, 15 major, three diminished and three half-diminished.

After notation normalization and transposition, Back Home Blues matches the
sequence printed in §2.1 of the paper. Blues for Alice matches after the proposed
major-to-dominant change in its first bar. This checks two examples, **not** the
identity of all 22 historical references. The old online corpus URL could not be
retrieved during this audit. See the [2011 paper](https://www.francoispachet.fr/wp-content/uploads/2021/01/pachet-09c.pdf).

## Training conventions

The first-order benchmark trains from all 12 transpositions of each reference
exactly once: 264 sequences, 6,336 symbols. This yields 60 source-faithful symbols
or 36 proposed paper-style symbols. `Gb7` is the pitch-class equivalent of the
paper's `F#7`; spelling is consistently flat-preferred.

Initial probabilities use the corpus symbol marginal, rather than only the first
symbol of each chorus. Conditional probabilities use within-chorus adjacent-pair
counts. The final chord does not connect to the next training sequence. Counts,
weights, comparisons and bounds use exact rational arithmetic. No smoothing,
terminal factor, or silent source correction is applied.

## Reproduction

From the Snarky checkout, with a fresh output directory:

```sh
.venv/bin/python -m benchmarks.blues_corpus \
  --lsdb-root ../lsdb --output /tmp/omnibook_blues_audit
```

Compare generated JSON and licence with this fixture. The importer refuses to
overwrite existing versioned output. LSDB source files are only read.

## Attribution and distribution

MusicXML provided by Inria (Ken Déguernel, Emmanuel Vincent) and STMS Lab,
Ircam/CNRS/UPMC (Ken Déguernel, Gérard Assayag); original copyrights Atlantic
Music Corp. Derived via the user's LSDB extraction and selection. Original
source attribution and CC BY-NC-SA 2.0 UK terms are in [LICENCE.txt](LICENCE.txt).

Required publication citation: Ken Déguernel, Emmanuel Vincent and Gérard Assayag,
*Using Multidimensional Sequences for Improvisation in the OMax Paradigm*,
Proceedings of SMC 2016. Changes here: half-bar encoding, canonical chord tokens,
the separately labeled simplification map, and provenance/audit metadata. This
research dataset is excluded from both Python distributions. The dataset's terms
do not become the licence of the solver source code.
