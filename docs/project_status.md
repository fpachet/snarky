# Project status and validation map

This map separates compatibility promises from application and research work.
It describes the September 2026 review fixes; research results retain their
own dated protocols and promotion decisions.

| Track | Current boundary | Acceptance gate |
|---|---|---|
| [Core 0.1](core_0_1_baseline.md) | Frozen symbolic language and supported API; not a public release | Differential semantics, rollback/provenance, parser, and installed-package tests |
| [CSP](../csp_solver/README.md) | Optional installable companion; experimental Python API | Independent solution oracles, propagator support oracles, installed rule data |
| [Sudoku](../sudoku/README.md) | Explainable reference techniques plus optional search | Reference puzzles and explanation replay |
| [Harmonizer](../harmonizer/README.md) | C-major SATB prototype with documented limits | Conformance checks and expensive integration examples |
| [Bach learning](../harmonizer/bach_rule_induction/README.md) | Multiple experimental tracks with separately versioned checkpoints | Unit tests plus each track's corpus, statistical, and generation protocol |
| [Probabilistic extension](probabilistic_constraint_learning_spec.md) | Research specification, separate from frozen CHOICE semantics | Exact toy oracles and backend conformance before promotion |

The Bach research README identifies the executable V19 and explanatory V20B
checkpoints for its K3 track and links subsequent decisions. Those labels are
track-specific, not a release or a claim that every later experimental model
has been promoted. The independent historical/manual base and induced-factor
experiments must retain their own provenance and acceptance decisions.

## Reproducible checks

```sh
uv sync --frozen --extra dev --extra research
uv run --frozen python -m snarky check --syntax-only --format .
uv run --frozen ruff check .
uv run --frozen mypy src
uv run --frozen pytest -m "not slow"
uv run --frozen pytest -m slow --durations=10
uv run --frozen pytest harmonizer/bach_rule_induction/experiments --durations=10
```

The default `pytest` invocation runs both configured core/application groups.
Research tests are explicitly selected in a separate CI job and need only
the optional NumPy extra in addition to development dependencies. These are
unit and fixture tests; they do not rerun training, evaluate sealed corpora,
or require the sibling historical DeepBach installation. Full research
reproduction follows the individual experiment protocols.

CI runs core/application checks on Python 3.12 and 3.13, verifies textual
sources, checks documentation links, builds the core and CSP distributions,
and exercises the installed console with and without the companion. See
[contribution instructions](../CONTRIBUTING.md) for the local packaging gate.

## Review-fix validation — 8 September 2026

Local validation used Python 3.13.11. The full configured run passed 671 tests
with three optional skips in 201 seconds. Two tests added afterward (the
runtime tutorial and shorter dependent proofs) passed in the focused follow-up;
the current core/application collection contains 676 tests. All 233 research
tests and the five original review reproductions passed as well.

Ruff, strict mypy (69 modules), Markdown links, and syntax/format validation
of 300 DSL files passed. Core and companion sdists rebuilt into wheels; isolated
checks covered core imports, inference, the actual console executable before
and after companion installation, malformed constraints, and four-queens
solving from packaged rule data. The new Python 3.12/3.13 CI matrix has been
configured; remote CI execution is separate from these local results.

The [factor support benchmark](../benchmarks/README.md) records the raw
interleaved measurements and exact logical-output checks. Its speedup applies
to the synthetic shared-scope evaluator workload, not all applications.

## Remaining work outside the review fixes

Publication still requires the decisions recorded in
[release guidance](../RELEASE.md). Broader musical coverage, exact
probabilistic inference, cache-lifetime experiments, and further module
decomposition remain separate work. A passing unit suite does not establish
a new statistical or musical research result.
