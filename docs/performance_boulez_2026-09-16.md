# Boulez Blues optimization — 2026-09-16

Unseeded search now regenerates the **exact sequence printed in Table 5** and
proves it optimal for the documented two-family LSDB corpus. All three measured
runs agree on the exact rational optimum and sequence. This completes the
first-order Boulez milestone for this corpus; it does not establish identity with
the paper's historical training preprocessing or implement variable-order modes.

## Paired result and ablation

Each configuration has one discarded warmup and three fresh-process samples.
Runs alternate configuration order, use the same machine, Python 3.13.11,
`PYTHONHASHSEED=0`, five-second search limit, MRV and objective value ordering.
Finish/limit times include native preparation and search. First-solution and
target timestamps are relative to controller start (after native state preparation).
Training and model construction are recorded separately; Python startup/imports are excluded. Background and thermal
state were not controlled. These are observed medians, not confidence intervals.

| Configuration | First solution | Reach published score | Finish / limit | Nodes | Best log score | Outcome |
|---|---:|---:|---:|---:|---:|---|
| Reference `e5e25cf`, chain | 0.214 s | Not reached | 5.006 s | 6455–6684 | -63.195230 | Time limit; feasible |
| New controller, chain ablation | 0.216 s | Not reached | 5.006 s | 5786–5810 | -63.195230 | Time limit; feasible |
| Assignment bound, unseeded | 0.182 s | 0.272 s | 1.732 s | 209 | -46.921592 | Proved optimal |
| Assignment bound, published seed | 0.001 s | 0.001 s | 1.527 s | 145 | -46.921592 | Proved optimal |

The ablation retains the new candidate pruning but disables the assignment bound.
It still reaches neither the published score nor a proof within five seconds.
The assignment relaxation is therefore the decisive change in this experiment.
A speedup ratio against the reference proof time cannot be given: the reference
did not complete its proof. Seeded timings include seed validation, but not discovery
of the supplied sequence; they are not unseeded generation measurements.

## Sequence and exact result

Each pair is one bar; each line is four bars:

```text
C7 Fm | Bb7 Ebm | Ab7 Db7 | Dbm Cm
F7 Bbm | Eb7 Abm | Gm Gbm | B7 Gb7
Bm E7 | Am D7 | Em A7 | Dm G7
```

All 24 seventh/minor chords occur once. C7/F7/G7 occupy positions 1/9/24.
The corpus is reduced before counting, augmented through all 12 transpositions,
with the source tune/take multiplicity and sequence boundaries retained.
The exact objective is

```text
55914539936246868146107748625/13344832588479756870916478934403139802829834682368
```

Its displayed natural log is **−46.921591738232166**. The paper reports −46.74
under its historical model. Search returns `optimal`, `exhausted`, and an objective
bound equal to the incumbent. Comparisons and pruning use exact rational arithmetic;
floating logs appear only in reports. Optimality does not imply uniqueness.

## What changed

1. Automatic bounds recognize a hard whole-alphabet permutation with fixed distinct
   endpoints and unary/adjacent-pair product factors. For each possible transition,
   take its largest weight over compatible positions. Every feasible sequence then
   induces a matching from all chords except the end to all chords except the start.
   The maximum-product matching bounds every feasible path, while allowing disconnected
   cycles and relaxing positional correlations. Constants and the initial factor
   are included exactly once. A multiplicative Hungarian algorithm uses exact rational
   operations. Recognition is capped at 64 symbols and the existing edge-volume budget.
2. Objective value ordering skips candidates whose bound cannot improve the incumbent.
3. Complete warm starts are propagated, checked and rescored before acceptance.
   No caller-supplied score or derived facts are trusted; branch state is restored.
   `bounding="chain"` provides the former relaxation as an explicit ablation.

No all-different algorithm, generic table propagator or rule matcher was rewritten.
Profiling the old five-second run attributed about 2.36 seconds to chain bounds
and 2.31 seconds to propagation (including 1.31 seconds in all-different filtering).
This suggested improving search pruning before optimizing individual propagator loops.
The profile is instrumented and must not be used as a latency benchmark.

## Traced allocation diagnostic

| Configuration | Peak traced Python allocation | Search result | Nodes |
|---|---:|---|---:|
| Reference `e5e25cf`, chain | 1,916,734 bytes | feasible | 1748 |
| Assignment bound, unseeded | 3,142,426 bytes | optimal | 209 |

These are separate allocation-instrumented runs, not the timing samples and not
process RSS. Training/model construction are excluded. The reference retains its
five-second limit; the candidate has a 60-second diagnostic limit and finishes its
proof. Their explored work differs, so the peaks are an explicit memory tradeoff,
not a fixed-work memory speedup claim.

## Rule/CSP/mixed controls

All 21 controls retain identical independently checked outputs and work counts.
They use the existing collector and workloads, one warmup and three samples per
checkout; checkout order alternates between workloads. This is a regression check,
not a claim of broad engine acceleration.

| Control | Reference median | Candidate median | Candidate/reference |
|---|---:|---:|---:|
| rules/small/triangle_closure:indexed | 0.001231 s | 0.001021 s | 0.829 |
| rules/small/triangle_closure:semi-naive | 0.000968 s | 0.001119 s | 1.156 |
| rules/thesis/hanoi:indexed | 0.040462 s | 0.039972 s | 0.988 |
| rules/thesis/hanoi:semi-naive | 0.042946 s | 0.040182 s | 0.936 |
| rules/thesis/monkey_bananas/neopus_mea:indexed | 0.021337 s | 0.021451 s | 1.005 |
| rules/thesis/monkey_bananas/neopus_mea:semi-naive | 0.019411 s | 0.019603 s | 1.010 |
| joins/25x8/cold | 0.038427 s | 0.037684 s | 0.981 |
| joins/25x8/streamed | 0.114203 s | 0.112837 s | 0.988 |
| joins/100x8/cold | 0.157306 s | 0.157290 s | 1.000 |
| joins/100x8/streamed | 0.475243 s | 0.471849 s | 0.993 |
| classical/magic5 | 0.075825 s | 0.073579 s | 0.970 |
| classical/sudoku_pure | 0.083834 s | 0.091792 s | 1.095 |
| classical/sudoku_mixed | 0.445399 s | 0.462387 s | 1.038 |
| magic3 | 0.001996 s | 0.001790 s | 0.897 |
| magic4 | 0.213281 s | 0.211802 s | 0.993 |
| latin5 | 0.002605 s | 0.002367 s | 0.909 |
| latin7 | 0.013116 s | 0.013316 s | 1.015 |
| mixed_magic3 | 0.002261 s | 0.002283 s | 1.010 |
| markov25x4 | 0.015868 s | 0.015585 s | 0.982 |
| markov33x8 | 0.143699 s | 0.142934 s | 0.995 |
| markov129x8 | 2.648221 s | 2.618130 s | 0.989 |

Cases over 5 ms range from about 0.936× to 1.095× reference time. A roughly 1 ms
rule case is 1.156×, an absolute difference of about 0.15 ms; the rule implementation
is unchanged. These few samples do not distinguish such small differences from
run-to-run noise. No general speedup is claimed.

## Validation and reproducibility

- Full non-Bach suite: 883 passed, three optional integrations skipped (224.97 s).
- Final focused suite: 100 tests, including exhaustive assignment/permutation oracles,
  mixed-rule warm starts, rollback, invalid seeds, timeouts, zero weights and near ties.
  The 64-symbol preparation guard was added after the broad run and checked by this
  focused rerun. The focused suite also passes on Python 3.12.
- Ruff, mypy (91 modules), distribution contents and installed-wheel smoke tests on
  Python 3.12/3.13 pass. The installed test exercises the new bound and warm start.
- Bounds are checked against all feasible residual permutations in small generated
  problems; the exact matching kernel is checked against exhaustive assignments.
  Large-instance optimality is established by completed branch-and-bound, not by
  enumerating all 24! sequences independently.

- [Raw paired measurements](../benchmarks/results/boulez_optimization_2026-09-16.json)
- [Reference sources](../benchmarks/results/boulez_optimization_2026-09-16.reference.tar.gz)
- [Candidate sources](../benchmarks/results/boulez_optimization_2026-09-16.candidate.tar.gz)
- [Pre-optimization profile](../benchmarks/results/boulez_profile_2026-09-16.txt)
- [Validation record](../tests/fixtures/boulez_optimization_validation_2026-09-16.json)
- [Collector and reproduction command](../benchmarks/README.md#boulez-assignment-bound-comparison)
- [Corpus and proposed reduction map](../benchmarks/data/omnibook_blues_v2/README.md)
- [Earlier five-second baseline](performance_blues_2026-09-16.md)

The source archives include dirty/new runtime and collector files; their hashes were
checked before and after collection. The result embeds the witness and external
Sudoku fixture needed to recreate the archived workloads. An initial collection
stopped because the reference checkout lacked that Sudoku input; the reported
collection was restarted from scratch after restoring it, with no engine changes.

Variable-order modes were subsequently implemented in the
[melody follow-up](markov_melody_examples.md). Generic incremental table filtering
and further global constraint optimizations remain separate follow-up work.

For a portable summary of all Blues results, sequences, local probabilities and
LaTeX tables, see the [Villani research handoff](research/blues_villani_2026-09-16/README.md).
