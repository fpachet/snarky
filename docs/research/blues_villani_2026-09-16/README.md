# Blues generation evidence for Markov-constraints---Villani

Prepared 16 September 2026 from Snarky commit `ccb346abfc163367371b36359e142c8db7046c70` and the archived
experiment sources. This is a portable research handoff: the files below are local
to this directory, and the detailed reports are linked to a fixed repository revision.
No new benchmark was run for this handoff. The manuscript has not been changed.

## Main finding

Unseeded branch-and-bound regenerates the **exact Boulez Blues printed in Table 5
of Pachet and Roy (2011)** and proves it optimal for our explicitly reconstructed
two-family corpus. Median preparation-plus-search time is **1.732 s**, with **209
nodes**; the optimal incumbent is reached at **0.272 s** on the controller's clock.
The exact rational score has natural logarithm **−46.921591738232166**, versus
**−46.74** reported in 2011 under the historical model. Optimality is certified for
our model, not inferred from similarity to the paper. Uniqueness is not claimed.

## Files to use in the new paper

- [Draft LaTeX subsection](draft_subsection.tex): a suggested factual results paragraph, ready for editorial integration.
- [Results table](results_table.tex) and [machine-readable table](results.csv).
- [Chord grids](chord_grids.tex): 12-bar, two-chords-per-bar layouts for all seven cases.
- [Complete sequences and exact scores](sequences.json).
- [Every local probability](local_factors.csv): exact fractions and display decimals, including the initial marginal.
- [Evidence manifest](manifest.json): source identity and SHA-256 hashes.
- [Corpus licence and required attribution](CORPUS_LICENCE.txt).

From the paper root, the LaTeX files can be included with
`\input{research/snarky_blues_2026-09-16/results_table}` and similarly for the
draft subsection or chord grids. They are independent fragments using ordinary
LaTeX tables; no existing paper source is automatically modified.

## Experimental model and corpus

Each generated sequence contains **24 half-bar chords** (12 bars, 4/4). All three
tasks require C7, F7 and G7 at positions **1, 9 and 24**, respectively:

- Ordinary: the three anchors.
- Exotic: anchors and **exactly one Gb7**, enharmonic to the paper's F-sharp seventh.
- Boulez: anchors and **all-different over the 24 dominant-seventh/minor chords**,
  hence exactly one occurrence of each chord.

There are 22 LSDB-selected first complete Blues choruses, already normalized to C,
including alternate takes with unit weight. Repeated sequences retain their
multiplicity. The 528 half-bars are augmented through all 12 transpositions, giving
264 sequences and 6,336 training symbols. Boundaries never create transitions.

The first-order objective is `P(x1) * product(P(xi | x(i-1)), i=2..24)`.
`P(x1)` is the corpus symbol marginal, not the frequency of chorus starts.
Transition denominators count occurrences with an outgoing transition. Unsupported
transitions are forbidden. There is no smoothing or terminal factor. Products,
bounds and comparisons use exact rational arithmetic; only reported logs are floats.

| Source family | Source-faithful | Three-family proposed | Two-family proposed |
|---|---|---|---|
| Dominant seventh | Seventh | Seventh | Seventh |
| Minor | Minor | Minor | Minor |
| Major | Major | Seventh | Seventh |
| Diminished | Diminished | Half-diminished | Minor |
| Half-diminished | Half-diminished | Half-diminished | Minor |

Roots are preserved. The corresponding augmented alphabets have 60, 36 and 24
symbols. The two-family reduction is applied **before counting**, changing 34 of
528 positions across nine references. It is an explicit proposed reduction,
requested for this reconstruction, not an authenticated historical preprocessing
map. Two source examples match the paper as described in the corpus audit; identity
of the complete historical set of 22 references has not been established.

## Results

| Corpus | Control | Natural-log score | Native median | Nodes | Proof |
|---|---|---:|---:|---:|---|
| Source-faithful | ordinary | -20.536927 | 0.965 s | 22 | Optimal |
| Source-faithful | exotic | -28.051704 | 1.802 s | 22 | Optimal |
| Three-family proposed | ordinary | -20.428036 | 0.650 s | 22 | Optimal |
| Three-family proposed | exotic | -28.191003 | 1.200 s | 22 | Optimal |
| Two-family proposed | ordinary | -20.428036 | 0.586 s | 22 | Optimal |
| Two-family proposed | exotic | -28.213666 | 1.131 s | 22 | Optimal |
| Two-family proposed | boulez | -46.921592 | 1.732 s | 209 | Optimal |

Ordinary/exotic measurements come from the earlier count-aware baseline; Boulez
comes from the later assignment-bound follow-up. Preserve these experiment
identities when quoting the table. All ordinary/exotic optima equal an independent
exact dynamic program (with a count state for exotic). The ordinary/exotic DP
measurements are single evaluations, recorded separately in `results.csv`; they
are not three-run medians. The Boulez proof is completed exact branch-and-bound,
validated by exhaustive bound tests on small instances, not independent enumeration
of all 24! permutations.

## Boulez sequence

```text
C7 Fm  | Bb7 Ebm | Ab7 Db7 | Dbm Cm
F7 Bbm | Eb7 Abm | Gm Gbm  | B7 Gb7
Bm E7  | Am D7   | Em A7   | Dm G7
```

Exact product:
`55914539936246868146107748625/13344832588479756870916478934403139802829834682368`.

## Search improvement and performance protocol

| Configuration | First solution | Reach optimal score | Finish/limit | Nodes | Outcome |
|---|---:|---:|---:|---:|---|
| Reference chain bound | 0.214 s | Not reached | 5.006 s | 6455–6684 | Feasible, −63.195230; timeout |
| New controller, chain ablation | 0.216 s | Not reached | 5.006 s | 5786–5810 | Feasible, −63.195230; timeout |
| Assignment bound, unseeded | 0.182 s | 0.272 s | 1.732 s | 209 | Optimal, −46.921592 |
| Assignment bound, published seed | 0.001 s | 0.001 s | 1.527 s | 145 | Optimal, −46.921592 |

The assignment bound relaxes the Hamiltonian path into a maximum-product matching,
allowing disconnected cycles and relaxing positional correlations. Every feasible
path induces an admissible matching, so the bound is safe. The matching kernel uses
exact rational arithmetic. Candidate-bound pruning and validated warm starts are
additional controller improvements. No general rule-matcher or all-different
rewrite is needed for this result.

The paired Boulez study uses one discarded warmup and three fresh-process samples
per configuration, alternating order, Python 3.13.11, macOS 15.7.7 arm64,
`PYTHONHASHSEED=0`, MRV, objective value ordering and a five-second search limit.
Hardware model, thermal state and background activity were not controlled or fully
recorded. Preparation-plus-search excludes training, model construction, imports
and startup. Incumbent timestamps start after native state preparation and must
not be subtracted from the finish times as though they shared the same origin.
The archived JSON records training and construction separately.

The seeded result excludes discovery of the supplied sequence. No proof-time
speedup ratio over the timed-out reference is defined. Separate allocation probes
report 1,916,734 bytes for the timed-out reference and 3,142,426 bytes for the
completed assignment-bound run; these are Python allocation peaks, not process
RSS, and represent different explored work. Twenty-one rule/CSP/mixed controls
retain the same checked outputs and work counts. A later single control run still
proves the same Boulez sequence in 209 nodes and 1.714 s; it is not a new median.

## Relationship to the 2011 paper

| Paper example | Reported log score | Present comparison |
|---|---:|---|
| Table 2, C-only training | −21.45 | Not reproduced by these all-key measurements |
| Table 3, augmented ordinary Blues | −20.55 | Same repeated-tonic sequence pattern; current scores depend on corpus variant |
| Table 4, exactly one F-sharp seventh | −34.5 | Same control, different optimized sequence and reconstructed-model score |
| Table 5, Boulez Blues | −46.74 | Exact chord sequence recovered and proved optimal; current two-family score −46.921592 |

Differences in probabilities are not evidence of a better solver: the trained
models differ. Do not recompute exact scores from rounded probabilities printed
in the paper. The 2011 timing figure concerns melody generation, not a directly
comparable Boulez benchmark; no modern-versus-Backtalk speed ratio is established.
For fixed-order chains, anchors alone preserve dynamic-programming tractability;
a small occurrence counter handles the exotic example. Global distinctness is
what makes Boulez a useful search benchmark. Optimization is not exact sampling.

## Source reports and reproducibility

- [Corpus audit and transformation map](https://github.com/fpachet/snarky/blob/ccb346abfc163367371b36359e142c8db7046c70/benchmarks/data/omnibook_blues_v2/README.md)
- [Ordinary/exotic baseline](https://github.com/fpachet/snarky/blob/ccb346abfc163367371b36359e142c8db7046c70/docs/performance_blues_2026-09-16.md)
- [Completed Boulez proof and ablation](https://github.com/fpachet/snarky/blob/ccb346abfc163367371b36359e142c8db7046c70/docs/performance_boulez_2026-09-16.md)
- [Published-paper review](https://github.com/fpachet/snarky/blob/ccb346abfc163367371b36359e142c8db7046c70/docs/markov_paper_review.md)
- [Related variable-order melody results](https://github.com/fpachet/snarky/blob/ccb346abfc163367371b36359e142c8db7046c70/docs/markov_melody_examples.md)

The baseline report retains a historical unproved Boulez row; the later proved
result above supersedes that row for the same two-family problem. Wider-alphabet
and generation-only Boulez experiments are superseded models and are deliberately
excluded from the headline table.

`evidence/` contains the corpus, original raw records, validation record and the
exact source snapshots for the earlier baseline and paired Boulez experiment.
Snapshots are authoritative where the original measurements record a dirty tree.
To rerun on an extracted source snapshot, create a Python 3.13 environment with the
project's declared dependencies, then run from its root:

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. python -m benchmarks.blues_markov \
  --repeat 3 --seconds 5 --output /tmp/blues-new.json
```

For the paired reference/candidate ablation, the candidate archive contains the
collector. Extract both archives separately, restore the Sudoku fixture embedded
in the paired JSON at its recorded path, then use the command documented in the
[collector guide](https://github.com/fpachet/snarky/blob/ccb346abfc163367371b36359e142c8db7046c70/benchmarks/README.md#boulez-assignment-bound-comparison).
The current runtime may give different timings; retain the archived measurements
as historical records and generate new output paths for new experiments.

Validation at the Boulez milestone: 883 non-Bach tests passed, three optional
integrations skipped; 100 focused tests passed on Python 3.12 and 3.13, including
exhaustive small assignment/permutation oracles, near ties, zero weights, rollback,
timeouts and invalid seeds. The subsequent melody milestone passed a broader
920-test gate; its new features do not retroactively change the Blues measurements.

## Handoff verification

All seven result rows were checked against the original exact objectives and
proof bounds. All 168 local factors multiply to their recorded exact sequence
scores. LaTeX fragments compile together in a standard article wrapper, with no
undefined citations or overfull boxes. This verifies the draft fragments, not
their final layout in the target journal style. The manifest hashes every
included file. No source probabilities or performance measurements were fitted
to the historical paper.

## Attribution

Pachet, François, and Pierre Roy. 2011. “Markov constraints: steerable generation
of Markov sequences.” Constraints 16: 148–172. DOI: 10.1007/s10601-010-9101-4.
The existing paper bibliography key is `DBLP:journals/constraints/PachetR11`.

The corpus licence also requests citation of Ken Déguernel, Emmanuel Vincent and
Gérard Assayag, “Using Multidimensional Sequences for Improvisation in the OMax
Paradigm,” Proceedings of the 13th Sound and Music Computing Conference, 2016.
MusicXML attribution: Inria and STMS Lab/Ircam/CNRS/UPMC; original copyrights
Atlantic Music Corp. The derived corpus carries CC BY-NC-SA 2.0 UK terms; see the
included licence. This does not license the Snarky solver code, whose project
licence status is separately recorded in its repository.
