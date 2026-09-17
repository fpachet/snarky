# Compiled numeric masks: validation

Reference: `32842b55293602ee7396d8c2614f8a9f1827e649`. Candidate sources are
archived and hashed alongside each measurement; documentation was completed later.

- Full non-Bach gate: **1,106 passed, 3 skipped**, 206.70 seconds.
  Command: `PYTHONHASHSEED=0 PYTHONPATH=src:../vo_regular_bp .venv/bin/python scripts/check_redesign.py --durations=8`.
  This workspace includes two pre-existing Alice tests, not part of this commit.
  Seven new numeric tests exercise 650 signed/holey oracle models, restoration,
  direct masks, optimization, guard validation timing and exact fallback.
- Focused suite: 45 passed. Full output in `focused.log`.
- Mypy: 95 source files pass; Ruff passes; textual syntax: 305 files pass.
- Core and companion sdist/wheel builds, distribution-content checks and isolated
  installation/smoke checks pass. Exact output is in `wheel.log`.
- Python 3.12 FT06 smoke: optimum 55, 615 nodes, 68,529 revisions, proof complete.
  `python312_ft06.json` is a compatibility check, not part of the latency comparison.
- Paired Python and same-source on/off runs preserve completed search counters
  and normalized solutions. Independent Gecode checks validate assignments/optima.
- Full portfolio audit: all 54 FlatZinc hashes and the Prune binary are unchanged;
  all 52 completed Snarky workloads preserve counters, objectives and outputs.
  See `../prune_numeric_2026-09-17/audit.json`.
- Rule, legacy, mixed, Markov and Boulez controls preserve observations; allocation
  pairs preserve work at the fixed 30-node limit.
- Current source hashes match every candidate archive and the controls digest.

Correctness, lint and package jobs completed before latency collection. Separate
CPU/allocation instrumentation followed the latency runs. No full-suite rerun was
needed for subsequent documentation-only edits.
