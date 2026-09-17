# All-different optimization validation

The source archives and SHA-256 maps in `results.json` identify the exact runtimes.
Both use native NValue. No branching or consistency-strength change is intended.

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:../vo_regular_bp .venv/bin/python scripts/check_redesign.py --durations=8
.venv/bin/ruff check .
.venv/bin/mypy src
PYTHONPATH=src .venv/bin/python -m snarky check --syntax-only --format .
.venv/bin/python scripts/check_markdown_links.py
PYTHONHASHSEED=0 PYTHONPATH=src:. /opt/homebrew/bin/python3.12 benchmarks/csp_diagnostics.py --source . --model benchmarks/results/prune_alldiff_2026-09-16/artifacts/incremental_all_different--all_different_incremental_16.fzn.json --seconds 5
.venv/bin/python -m build --no-isolation --outdir /tmp/snarky-csp-alldiff-dist
.venv/bin/python -m build --no-isolation --outdir /tmp/snarky-csp-alldiff-dist/csp csp_solver
.venv/bin/python scripts/check_distribution.py /tmp/snarky-csp-alldiff-dist
.venv/bin/python scripts/check_wheel_install.py /tmp/snarky-csp-alldiff-dist --companion /tmp/snarky-csp-alldiff-dist/csp/snarky_csp-0.1.0-py3-none-any.whl
```

- [Full regression](regression.log): **1,089 passed, three skipped**, 224.19 s.
- [Ruff](ruff.log), [mypy](mypy.log) (94 source files),
  [text validation](syntax.log) (305 files): passed.
- Both distributions built; contents and [isolated core/companion checks](wheel.log)
  passed. [Markdown links](links.log) pass after documentation updates.
- [Python 3.12 Latin-16 smoke](python312.json) also passes: 150 nodes, zero
  failures, 2,817 revisions; its primitive assignments are checked by the worker.
  This is a compatibility check, not part of the paired Python 3.13 latency data.
- New all-different tests cover 1,400 exact-support problems across bitset and
  forced sparse paths, including 70 complete solution-set comparisons.
- Independent graph reachability checks cover 250 random graphs, plus deep
  chain/dense cases, matching-hint repair, nested failures and rollback.
- Sparse-chain dispatch is checked against exact Hall supports.
- Large candidate alphabets exercise the exact sparse fallback; huge numeric
  magnitudes on small explicit domains do not become giant bit indexes.
- Native-global queens models match independently enumerated chessboards at
  sizes one through five, including unsatisfiable sizes and projection uniqueness.

Latency measurements run sequentially after the test gate. CPU/allocation
instrumentation is separate from uninstrumented latency samples. Every returned
benchmark assignment is validated independently of propagation.

Final audit: all candidate source hashes/snapshots in the paired, ablation,
Prune, graph, control, CLAIRE and profile records match the committed runtime
and benchmark sources. The full Prune parity audit checks all 54 compiled inputs
and all 52 mutually completed workloads.
