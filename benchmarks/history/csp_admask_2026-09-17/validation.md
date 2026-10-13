# Compiled all-different validation

Reference runtime: `a291ce789d2cbc3f17024329a276a8caba80f567`.
Candidate runtime/worker sources are archived and hashed in the measurement records.

- Full non-Bach gate: **1,113 passed, 3 skipped**, 228.95 seconds.
  Command: `PYTHONHASHSEED=0 PYTHONPATH=src:../vo_regular_bp .venv/bin/python scripts/check_redesign.py --durations=8`.
- Focused checks: 121 tests pass (new mask oracles, existing bitset all-different,
  numeric masks and Prune importer); output in `focused.log`.
- Seven new tests compare supported values against exhaustive enumeration,
  reference kernels and restored domains, including sparse traversal and guards.
- Ruff passes; mypy passes for 96 source files.
- Textual syntax, core and companion sdist/wheel builds, distribution contents,
  isolated imports, model solving and installed-console checks pass (`wheel.log`).
- Python 3.12 queens-50 smoke returns a solution with 52 nodes and 6,867 revisions
  (`python312_queens50.json`). This is a compatibility check, not a latency sample.
- Correctness/package checks finish before repeated timing runs. CPU and memory
  instrumentation are collected separately after latency runs.

The regression gate includes rule, mixed-model, factor, optimization and Markov
coverage. The reference set-based kernel remains unchanged. Subsequent report-only
edits do not require another full regression run.

The full portfolio audit preserves all 54 FlatZinc hashes and all 52 completed
Snarky outputs, objectives and counters against the preceding run. Rule, legacy,
mixed, Markov and Boulez controls retain their checked observations. All five
allocation pairs preserve work at the 30-node limit. The Prune/CLAIRE binaries
and CLAIRE templates match the preceding records. Runtime/worker source hashes
and control digests match the current implementation after collection.
