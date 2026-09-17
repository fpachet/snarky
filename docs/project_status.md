# Project status and validation map

This map separates compatibility promises from application and research work.
It describes the September 2026 review fixes; research results retain their
own dated protocols and promotion decisions.

| Track | Current boundary | Acceptance gate |
|---|---|---|
| [Core 0.1](core_0_1_baseline.md) | Frozen symbolic language and supported API; not a public release | Differential semantics, rollback/provenance, parser, and installed-package tests |
| [Finite CSP/optimization and mixed models](finite_model_contract.md) | Implemented experimental core namespace `snarky.finite` and `.model` language; independent solving plus coordinated positive rules and factors | Non-Bach manifest, exhaustive oracles, installed examples and paired performance evidence in [redesign progress](redesign_progress.md) |
| [Legacy fact-backed CSP](../csp_solver/README.md) | Optional installable companion; existing rule/choice interface and application catalogue, with an experimental Python API | Independent solution oracles, propagator support oracles, installed rule data |
| [Markov constraints](markov_constraints_application.md) | Exact first-order Blues optimization and fixed- and variable-order melody modes; Python API and research examples | Independent DP/exhaustive oracles, completed Boulez proof, mixed-constraint tests and archived performance evidence |
| [Sudoku](../sudoku/README.md) | Explainable reference techniques plus optional search | Reference puzzles and explanation replay |
| [Harmonizer](../harmonizer/README.md) | C-major SATB prototype with documented limits | Conformance checks and expensive integration examples |
| [Probabilistic extension](probabilistic_constraint_learning_spec.md) | Generic finite inference and optional regular-BP adapter implemented in `snarky.finite`; learning remains research | Partition/marginal/conditional-mass agreement and explicit arithmetic/capabilities; separate from frozen CHOICE semantics |

## Bach side project

The [Bach experiment](../harmonizer/bach_rule_induction/README.md) is a separate
side project, outside the main Snarky application and redesign portfolio. Its
learning experiments retain their own corpus, statistical and generation gates.
The generic SATB harmonizer remains an engine application and compatibility case.

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
The redesign CI gate uses `python scripts/check_redesign.py` to exclude three
Bach-dependent modules explicitly; those modules remain in the separate research
job. The optional regular-BP job checks its pinned dependency on both Python versions.
Research tests are explicitly selected in a separate CI job and need only
the optional NumPy extra in addition to development dependencies. These are
unit and fixture tests; they do not rerun training, evaluate sealed corpora,
or require the sibling historical DeepBach installation. Full research
reproduction follows the individual experiment protocols.

CI runs core/application checks on Python 3.12 and 3.13, verifies textual
sources, checks documentation links, builds the core and CSP distributions,
and exercises the installed console with and without the companion. See
[contribution instructions](../CONTRIBUTING.md) for the local packaging gate.

## Completed review actions

| Action | Result | Regression coverage |
|---|---|---|
| Propagation closure | Custom propagators reschedule on their own relevant changes; iterations remain bounded | Search observes closure, interacting filters, non-convergence |
| Saved explanations | Session and group results own isolated provenance copies | Mutation and repeated rollback preserve saved proofs |
| Minimum proof depths | Assumptions and shorter rule proofs update dependent depths reversibly | Assumption, shorter proof, descendant, and rollback cases |
| Numeric round trips | Exponent notation works in terms and arithmetic; non-finite numbers are rejected | Generated finite floats, signed zero, exponent limits, overflow errors |
| Installed CLI | Optional `snarky-csp` distribution includes required model data | Clean console invocation before/after installation, invalid constraints, four queens |
| Factor support collection | Ordered dictionary membership replaces quadratic list scans | Scores, scopes, witness counts, support order, and interleaved timing samples |
| Test infrastructure | Separate research job, Python 3.12/3.13 core matrix, expensive integration markers | Explicit test scopes documented above |

The executable [runtime tutorials](runtime_tutorial.md) demonstrate the
corrected boundaries. [Changelog](../CHANGELOG.md) entries describe the
user-facing behavior; [benchmark documentation](../benchmarks/README.md)
explains the measurement scope.

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
