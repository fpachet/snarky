# ALICE-inspired symbolic deductions on magic squares

This experiment asks whether explicitly combining constraints speeds up the
native Snarky solver on blank normal 4×4 and 5×5 magic squares. It implements
two bounded preprocessing methods in the benchmark, without changing the engine.
It does not implement ALICE's full control strategy or branch-local symbolic
reasoning.

The timings below are a frozen measurement of runtime `104d903`, before the
incumbent-cut and compiled numeric-mask changes. All recorded runtime hashes
match that commit, and the benchmark source still matches its recorded hash.
They are not measurements of the latest runtime. The experiment and its two
regression tests are now retained in the repository; no symbolic preprocessing
is enabled in the engine by this addition.

## Formulations

The baseline has integer cells in `1..n²`, one `ALL_DIFFERENT` over all cells,
and a sum constraint for each row, column and main diagonal. All sums have target
`n(n²+1)/2`. No symmetry breaking or clues are added. The task is to find the
first solution, not to enumerate all squares.

Two candidates retain every baseline constraint and add implied equalities:

- **Pair differences:** subtract each pair of original sum equations sharing
  at least one variable, normalize and deduplicate the results. This adds 32
  constraints of six variables for 4×4, and 46 of eight variables for 5×5.
- **Elimination:** compute exact rational reduced row echelon form of the sum
  equations in row-major variable order, normalize to primitive integer
  coefficients, and add the equations absent from the baseline. This adds six
  constraints in either size. Their scopes range from 4–8 variables for 4×4,
  and 9–14 for 5×5.

The pair-difference variant deliberately measures the cost of adding every
one-round overlapping difference. A strict policy requiring fewer variables than
the original sums would add none of these differences.

Every added equality carries an exact rational linear-combination certificate
over the original equations. Certificates are checked for every coefficient and
right-hand side. Since originals are retained, the complete solution set is
preserved algebraically; there is no need to enumerate every 4×4 or 5×5 square
to establish this property.

None of these methods removes a domain value at the root: all three variants
retain 256 cell/value possibilities for 4×4 and 625 for 5×5. This differs from
the previous 3×3 example, where combining equations can fix the centre.

## Protocol

- Same native runtime, row-major variable order, ascending declared values.
- Default `dom_wdeg` and a separate `mrv` control. Extra constraints alter degree
  and failure-weight information under `dom_wdeg`, so its search tree can change
  even without stronger propagation.
- Fixed `PYTHONHASHSEED=0`: process hash randomization can affect default search
  through propagation/failure ordering. These results describe this fixed seed.
- One warmup per combination, then five measured runs; rotate variant order.
- Ten-second solver limit per run. Timings include model construction, symbolic
  deductions, certificate checks, solver setup and search. Final solution
  validation is excluded. Interpreter startup and imports are excluded.
- Independently validate every returned square's range, distinctness, row sums,
  column sums and diagonal sums.
- Exhaustively compare all eight 3×3 solutions across the three formulations as
  a separate regression check; also check the simple sum-cancellation example.

Raw timings, preparation/search splits, search counters, returned squares,
certificates, source hashes, commit, dirty status and environment are recorded in
[the result file](../benchmarks/results/alice_magic_2026-09-17.json).

## Results

Median total time includes preprocessing. All five measured runs completed for every combination.

| Size | Policy | Formulation | Total time | Preparation | Nodes | Revisions |
|---|---|---|---:|---:|---:|---:|
| 4×4 | dom_wdeg | baseline | 26.70 ms | 0.28 ms | 26 | 560 |
| 4×4 | dom_wdeg | pair_differences | 56.71 ms | 6.79 ms | 28 | 1105 |
| 4×4 | dom_wdeg | elimination | 12.80 ms | 2.29 ms | 8 | 223 |
| 4×4 | mrv | baseline | 11.14 ms | 0.34 ms | 13 | 283 |
| 4×4 | mrv | pair_differences | 32.09 ms | 6.82 ms | 13 | 672 |
| 4×4 | mrv | elimination | 19.39 ms | 2.25 ms | 13 | 406 |
| 5×5 | dom_wdeg | baseline | 1678.95 ms | 0.56 ms | 1337 | 30709 |
| 5×5 | dom_wdeg | pair_differences | 2601.63 ms | 16.94 ms | 856 | 52401 |
| 5×5 | dom_wdeg | elimination | 2268.09 ms | 3.62 ms | 1394 | 39928 |
| 5×5 | mrv | baseline | 555.51 ms | 0.52 ms | 512 | 10584 |
| 5×5 | mrv | pair_differences | 1316.08 ms | 16.37 ms | 512 | 27484 |
| 5×5 | mrv | elimination | 964.26 ms | 3.70 ms | 512 | 15065 |

## Interpretation

The 4×4 improvement from elimination under default search is sensitive to the
search policy. With MRV, both candidates explore the same number of nodes as the
baseline and cost more per solve. On 5×5, both candidates are slower under both
tested policies. Pair differences can reduce default-policy nodes while still
increasing runtime because the extra propagation is expensive.

This does not support enabling blanket symbolic preprocessing for magic squares.
The worthwhile next experiment would be selective deductions after clues or
branch assignments simplify the equations, particularly deductions with smaller
scopes. That would be a different experiment, and is not measured here.

These are first-solution measurements on two blank instances, not results for
partially filled puzzles, exhaustive enumeration, other elimination orders or
ALICE as a complete solver. Millisecond timings for 4×4 are especially sensitive
to system load; portable search counters are reported alongside elapsed time.

## Reproduction

```sh
PYTHONHASHSEED=0 .venv/bin/python -m benchmarks.alice_magic \
  --repeats 5 --warmups 1 --limit 10 \
  --output benchmarks/results/alice_magic_NEW_LABEL.json
.venv/bin/pytest tests/test_alice_magic_benchmark.py
```

This command measures the checked-out runtime; use a new output label to preserve
the historical record. To reproduce the recorded runtime, run the benchmark with
`src/` from commit `104d903` on `PYTHONPATH`.

The implementation is in [benchmarks/alice_magic.py](../benchmarks/alice_magic.py).
