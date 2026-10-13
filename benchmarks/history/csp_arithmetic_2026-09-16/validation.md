# First CSP slice validation

The runtime/worker source hashes in `results.json` identify the measured source.
The following commands completed successfully on Python 3.13.11:

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:../vo_regular_bp .venv/bin/python scripts/check_redesign.py --durations=8
PYTHONPATH=src:. .venv/bin/python -m pytest -q tests/test_search_progress.py tests/test_arithmetic_supports.py tests/test_csp_diagnostics.py tests/test_finite_mixed.py
.venv/bin/ruff check .
.venv/bin/mypy src
```

- [Full non-Bach gate](regression.log): 991 passed, three skipped, 187.45 s.
- [Final focused set](focused.log): 33 passed, covering three tests added after full-suite collection (scope alias ordering, mixed-observer exception, truncated log).
- [Type check](mypy.log): 93 source files passed.
- A direct Python 3.12 diagnostic worker smoke proves Golomb 6 optimum 17 in eight nodes.
- The comparison records include independent Gecode checks, full normalized enumeration comparisons and unchanged search counters on all 47 mutually completed workloads.
- Controls preserve pure rule outputs, mixed facts, legacy CSP assignments and exact Boulez proof/sequence.

Bach research experiments are outside this gate.

Final packaging/documentation checks also passed:

```sh
.venv/bin/python scripts/check_markdown_links.py
PYTHONPATH=src .venv/bin/python -m snarky check --syntax-only --format .
.venv/bin/python -m build --no-isolation --outdir /tmp/snarky-csp-first-slice-dist
.venv/bin/python -m build --no-isolation --outdir /tmp/snarky-csp-first-slice-dist/csp csp_solver
.venv/bin/python scripts/check_distribution.py /tmp/snarky-csp-first-slice-dist
.venv/bin/python scripts/check_wheel_install.py /tmp/snarky-csp-first-slice-dist --companion /tmp/snarky-csp-first-slice-dist/csp/snarky_csp-0.1.0-py3-none-any.whl
```

The textual-source check covered 305 files. Isolated installations exercised
native optimization, mixed factors, Markov examples, exact inference and the
optional legacy companion.
