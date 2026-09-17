# Di Meola melody research fixture, version 1

Source: François Pachet and Pierre Roy, “Markov constraints: steerable generation
of Markov sequences,” *Constraints* 16, 148–172 (2011),
[DOI 10.1007/s10601-010-9101-4](https://doi.org/10.1007/s10601-010-9101-4).
Numeric transcription of Figure 1 (p. 157), Figures 2–3 (pp. 157–158), the four
solutions (p. 167), and Table 6 (p. 166). The supplied PDF's SHA-256 is recorded
in [corpus.json](corpus.json). Numeric notes were checked against rendered pages.
The PDF itself is not copied into this directory.

The article's p. 170 Open Access notice specifies Creative Commons Attribution
Noncommercial, permitting noncommercial use, distribution and reproduction with
author/source credit. No license version is stated in that notice. This numeric
transcription is attributed research material, excluded from Python source and
wheel distributions. That notice does not establish separate rights in any
external recording or book; neither is included.

## Transcription and boundaries

There are three training sequences, 48 + 48 + 9 = **105 notes**, over **15 pitches**.
C4 is numeric zero. Durations are omitted; there is no transposition. The ascending
and descending staircases consist of overlapping four-note windows of the scale
`4 6 7 9 11 12 15 16 18 19 21 23 24 27 28`, and its reverse. The third sequence is
`4 11 16 23 28 23 16 11 4`.

The construction description is a transcription cross-check, not a synthetic
replacement corpus. Sequence boundaries create no transitions. The generated
examples contain 17 notes anchored at numeric pitch 4 at each end. The paper's
occasional 16-note/E3 wording is not used to override its explicit numeric arrays.

Printed values and recomputed values are preserved separately. In particular,
Table 6's smoothing row and two entries in the smoothing solution's column do
not match the stated formulas under the documented training convention. **All
four printed solutions are nevertheless optimal under those formulas.** Details,
commands and interpretation are in the [melody guide](../../../docs/markov_melody_examples.md)
and [performance report](../../../docs/performance_melody_2026-09-16.md).
