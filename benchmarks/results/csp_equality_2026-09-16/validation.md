# Validation of the second CSP slice

The `results.json` source hashes and archives identify the exact measured runtime.

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:../vo_regular_bp .venv/bin/python scripts/check_redesign.py --durations=8
.venv/bin/ruff check .
.venv/bin/mypy src
```

- [Regression log](regression.log): 1,008 passed, three skipped, 185.93 s.
- [Ruff](ruff.log): passed.
- [Mypy](mypy.log): 93 source files passed.
- Primary comparisons and cache ablation validate original FlatZinc assignments,
  fixed original MiniZinc/Gecode models and complete enumeration sets.
- Rule, legacy, mixed, Markov and unseeded Boulez controls match the reference.
- Allocation comparisons retain identical search work and result/bound status.

Final source hashes still match the measured runtime. Additional checks passed:

```sh
.venv/bin/python scripts/check_markdown_links.py
PYTHONPATH=src .venv/bin/python -m snarky check --syntax-only --format .
.venv/bin/python -m build --no-isolation --outdir /tmp/snarky-csp-equality-dist
.venv/bin/python -m build --no-isolation --outdir /tmp/snarky-csp-equality-dist/csp csp_solver
.venv/bin/python scripts/check_distribution.py /tmp/snarky-csp-equality-dist
.venv/bin/python scripts/check_wheel_install.py /tmp/snarky-csp-equality-dist --companion /tmp/snarky-csp-equality-dist/csp/snarky_csp-0.1.0-py3-none-any.whl
PYTHONHASHSEED=0 /opt/homebrew/bin/python3.12 benchmarks/csp_diagnostics.py --model benchmarks/results/prune_comparison_2026-09-16/artifacts/extended--magic_sequence_40.fzn.json --diagnostic --nodes 100
```

- Textual-source validation: 305 files checked.
- [Wheel log](wheel.log): isolated core and optional companion checks passed.
- [Python 3.12 result](python312.json) and [progress](python312-progress.jsonl): magic sequence 40 completed in 62 nodes, independently evaluated against the original FlatZinc primitives. The full pytest gate ran on Python 3.13.
