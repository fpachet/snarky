# Blank 7×7 magic square with MRV

12 October 2026. Native MRV with middle-first values finds a first solution in
**1.61 seconds**, or **1.47 seconds with explicit symmetry constraints**.
These are medians of three runs including model and search setup. Every run
returns a validated solution. No transformer, learned constraint, reference
completion, or solution hint is used.

The model has 49 cells ranging over 1–49, one global all-different, and sixteen
sum constraints: seven rows, seven columns, and both main diagonals sum to 175.
It uses the compiled sum propagation from the preceding 6×6 optimization.
MRV chooses the smallest remaining domain with the existing row-major tie order.
Middle-first tries values in the declared order `25, 24, 26, 23, 27, …, 1, 49`.
Every original candidate remains available.

| Configuration | Finished | Median total seconds | Nodes | Revisions |
|---|---:|---:|---:|---:|
| MRV, ascending values (pilot) | 0/1 | >30 | — | — |
| MRV, middle-first | 3/3 | **1.606** | 2,589 | 47,884 |
| MRV, middle-first + symmetry | 3/3 | **1.471** | 2,114 | 42,239 |

Solve-only ranges are 1.579–1.636 seconds without symmetry and 1.459–1.501 seconds
with it. The single ascending pilot reaches the thirty-second time limit with
35,364 entered nodes; its full solve time remains unknown. The successful pilot
middle-first run takes 1.611 seconds. Those pilot runs are separate from the
three-repetition summaries. Repeated runs of the same blank square do not
constitute independent puzzle instances.

Symmetry uses the same five explicit inequalities as for 6×6, with top-left at
most 25: place the smallest corner top-left, the smaller adjacent corner top-right,
and allow complementing values with `50 - value`. It retains a representative
under rotation/reflection/complement, while excluding equivalent solutions.
It is an option for the blank first-solution task and cannot be transferred
blindly to clues. See the [6×6 optimization report](MAGIC6_OPTIMIZATION_REPORT.md)
for the formulation and orbit argument.

One returned solution without symmetry is:

```text
25  24  26  23  27  22  28
21  29  20  30  19  18  38
31  32  17  33  16  34  12
15  40  46  10  13   8  43
35   3  47  36  44   4   6
37  45   5   1   7  41  39
11   2  14  42  49  48   9
```

All returned squares pass the original model validator and a separate integer
check of range, distinctness, and all sixteen sums. Seven value-order/symmetry
tests pass, with sampled orbit coverage extended to size 7. Ruff passes. This
follow-up adds a `--size` option to the experimental runner; no additional core
solver changes are made.

Evidence lives in `generated/neural_attention/magic7_mrv_pilot/` and
`generated/neural_attention/magic7_mrv_repeats/`, including frozen settings/source
hashes and raw runs. The repeat set includes `summary.json`. Its source hashes
are checked unchanged after timing. Measurements use `PYTHONHASHSEED=0`, one
sequential process, no concurrent CPU tests, and three shuffled repetitions with
a ten-second limit per run after the pilot. Timing excludes validation and
interpreter imports.

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python \
  -m experiments.neural_attention.optimize_magic6 --size 7 \
  --orders middle --symmetry both --repeats 3 --limit 10 \
  --output generated/neural_attention/magic7_mrv_NEW
```

Use a fresh output directory; use `--symmetry none` for the unrestricted model.
