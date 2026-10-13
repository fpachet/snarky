# Native NValue validation

The source hashes and archives in `results.json` identify the measured runtime.
Both sides of this ablation use that runtime, with explicit distinct encodings.

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:../vo_regular_bp .venv/bin/python scripts/check_redesign.py --durations=8
.venv/bin/ruff check .
.venv/bin/mypy src
PYTHONPATH=src .venv/bin/python -m snarky check --syntax-only --format .
.venv/bin/python scripts/check_markdown_links.py
.venv/bin/python -m build --no-isolation --outdir /tmp/snarky-csp-nvalue-dist
.venv/bin/python -m build --no-isolation --outdir /tmp/snarky-csp-nvalue-dist/csp csp_solver
.venv/bin/python scripts/check_distribution.py /tmp/snarky-csp-nvalue-dist
.venv/bin/python scripts/check_wheel_install.py /tmp/snarky-csp-nvalue-dist --companion /tmp/snarky-csp-nvalue-dist/csp/snarky_csp-0.1.0-py3-none-any.whl
```

- [Full regression log](regression.log): 1,075 passed, three skipped, 227.97 seconds.
- [Ruff](ruff.log), [mypy](mypy.log) (94 source files), and
  [text validation](syntax.log) (305 files): passed.
- Both distributions built and passed contents checks.
- [Isolated installation](wheel.log): core NValue optimization, rule/mixed/Markov
  examples and optional legacy companion checks passed.
- New independent oracles cover 1,000 deterministic filtering cases with normal
  and zero cover budgets, including 200 complete solution-set comparisons;
  matching and cover helpers have separate brute-force oracles.
- Both bridge encodings match the original distinct-count predicate on small
  Cartesian products, including constants, empty scopes and count aliases.
- Native and legacy rollback, legacy removal explanations, guarded mixed rules,
  observer exceptions, objectives and inference are tested.
- A successful at-most cover is never treated as an exact-count proof; budget
  exhaustion is unknown. Complete assignments use an independent evaluator.
- [Python 3.12 worker](python312.json) and [progress](python312-progress.jsonl):
  Dominating Queens 8 solved in 79 nodes and 80 revisions, with a separately
  evaluated original FlatZinc assignment. The full test gate used Python 3.13.
- Fresh full Prune comparison: 52/59 Snarky, 59/59 Prune; every measured repetition
  is retained and original MiniZinc/Gecode checks pass. Rule, legacy, mixed, Markov
  and unseeded Boulez control outputs and search observations match `e296d09`.
