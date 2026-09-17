# Objective propagation validation

- [Full workspace regression](regression.log): **1,099 passed, 3 skipped**, 225.88 s.
  This includes two pre-existing Alice benchmark tests from concurrent workspace
  work. The objective-cut change adds eight tests; Alice implementation/results
  are outside this change.
- [Focused tests](focused.log): objective cuts, progress, mixed fixed points and
  admissible bounds pass.
- [Ruff](ruff.log), [mypy](mypy.log), [textual source validation](syntax.log) pass.
- [Distribution and isolated installation checks](wheel.log) pass for core and
  companion packages.

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:../vo_regular_bp .venv/bin/python scripts/check_redesign.py --durations=8
.venv/bin/ruff check .
.venv/bin/mypy src
PYTHONPATH=src .venv/bin/python -m snarky check --syntax-only --format .
.venv/bin/python -m build --no-isolation --outdir /tmp/snarky-objective-dist
.venv/bin/python -m build --no-isolation --outdir /tmp/snarky-objective-dist/csp csp_solver
.venv/bin/python scripts/check_distribution.py /tmp/snarky-objective-dist
.venv/bin/python scripts/check_wheel_install.py /tmp/snarky-objective-dist --companion /tmp/snarky-objective-dist/csp/snarky_csp-0.1.0-py3-none-any.whl
```

Correctness and package jobs finish before performance measurements. Each latency
worker is run sequentially. Profile instrumentation is separate from latency data.

[Markdown links](links.log) pass after documentation updates. The separate
[audit](cut_effects.json) records cut-specific counters without making latency
claims. Candidate runtime/source hashes are checked against the final files.

[Python 3.12 smoke](python312.json): FT06 proves optimum 55 with objective
propagation enabled, 615 nodes and 68,529 revisions. This compatibility check is
separate from the Python 3.13 paired latency records.
