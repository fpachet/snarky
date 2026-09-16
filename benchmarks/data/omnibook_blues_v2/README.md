# LSDB Omnibook Blues: two-family Boulez training added

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

Version 2 preserves every source-faithful and three-family sequence from version 1,
and adds `boulez_two_family_proposed`, its transformation map and position audit.

## Variants and proposed simplification

| Source family | Source-faithful | Three-family proposed | Boulez two-family proposed |
|---|---|---|---|
| Dominant seventh | `C7` | `C7` | `C7` |
| Minor triad | `Cm` | `Cm` | `Cm` |
| Major triad | `C` | `C7` | `C7` |
| Diminished triad | `Cdim` | `C-7b5` | `Cm` |
| Half-diminished seventh | `C-7b5` | `C-7b5` | `Cm` |

Roots stay fixed. Major-to-dominant and diminished-to-half-diminished add a
seventh. The Boulez reduction raises the diminished fifth and omits the
half-diminished seventh to retain the minor family. These are deliberate modeling
transformations, not source corrections. The user requested explicit maps for review. The map remains
**proposed**, not an authenticated reconstruction of historical preprocessing.
Source notes such as Visa's minor dominant-root chord are preserved.

The three-family variant has 31 changed half-bar positions in nine references:
C→C7 (24), F→F7 (2), A→A7 (2), Gbdim→Gb-7b5 (2), Ebdim→Eb-7b5 (1). The source segment inventory is
218 dominant, 77 minor, 15 major, three diminished and three half-diminished.

The two-family variant changes 34 of 528 half-bar positions across nine references:
C→C7 (24), F→F7 (2), A→A7 (2), Gbdim→Gbm (2), Ebdim→Ebm (1),
B-7b5→Bm (3). Every change is recorded in `boulez_changes`. Two-family training
is requested by the user; the mapping of diminished families to minor is explicit
and proposed for review, not an authenticated historical convention.

After notation normalization and transposition, Back Home Blues matches the
sequence printed in §2.1 of the paper. Blues for Alice matches after the proposed
major-to-dominant change in its first bar. This checks two examples, **not** the
identity of all 22 historical references. The old online corpus URL could not be
retrieved during this audit. See the [2011 paper](https://www.francoispachet.fr/wp-content/uploads/2021/01/pachet-09c.pdf).

## Training conventions

The first-order benchmark trains from all 12 transpositions of each reference
exactly once: 264 sequences, 6,336 symbols. This yields 60 source-faithful symbols
or 36 proposed paper-style symbols, and exactly 24 two-family Boulez symbols.
`Gb7` is the pitch-class equivalent of the paper's `F#7`; spelling is consistently flat-preferred.

Initial probabilities use the corpus symbol marginal, rather than only the first
symbol of each chorus. Conditional probabilities use within-chorus adjacent-pair
counts. The final chord does not connect to the next training sequence. Counts,
weights, comparisons and bounds use exact rational arithmetic. No smoothing,
terminal factor, or silent source correction is applied.

## Boulez training and generation

The chord reduction occurs **before counting** initial and transition frequencies.
Counts for merged chord symbols are pooled and probabilities recomputed from the
reduced corpus. This is different from filtering a larger trained alphabet.
All 12 transpositions are still used, with the same tune/take weights and boundaries.

Both training and generation now use the same 24-symbol alphabet: dominant seventh
and minor on all 12 roots. The 24 positions with all-different form a permutation
of those chords, with C7/F7/G7 anchors at positions 1/9/24.

The current benchmark runs ordinary and exotic controls on all three variants,
and the headline Boulez case on the two-family corpus. Earlier wider-alphabet and
intermediate generation-only Boulez experiments remain labeled historical records.
Their scores and timings are not comparisons on the same statistical model.

## Reproduction

From the Snarky checkout, with a fresh output directory:

```sh
.venv/bin/python -m benchmarks.blues_corpus \
  --lsdb-root ../lsdb --output /tmp/omnibook_blues_audit
```

Compare generated JSON and licence with this version 2 fixture. The importer
refuses to overwrite existing versioned output. LSDB source files are only read.

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
