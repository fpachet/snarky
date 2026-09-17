# Changelog

All notable user-facing changes to Snarky are recorded here. The project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html); compatibility
details are documented in [docs/versioning.md](docs/versioning.md).

## [Unreleased]

### Fixed

- Custom deterministic propagators now requeue after their own relevant
  changes until the joint fixed point is reached, with bounded iteration.
- Saved session and group results retain isolated provenance across mutation
  and rollback. External assumptions shorten existing and dependent proof
  depths with reversible updates.
- Finite numbers round-trip through term rendering and parsing, including
  exponent notation in arithmetic. Non-finite numeric terms are rejected and
  arithmetic overflow retains the public evaluation-error family.
- The optional local `snarky-csp` distribution bundles required rule data and
  enables installed-console constraint validation. Isolated installation
  checks exercise the actual CLI with and without the companion.
- Factor explanation support deduplication uses ordered dictionary membership
  instead of quadratic list scans, preserving supports and witness counts.

### Validation and documentation

- Made CLAIRE binary-resolution tests cover both macOS and Linux, and removed
  three research tests' dependency on an untracked corpus cache.
- Replaced broken links to local research artifacts with explicit local paths
  and linked DeepBach references to the tracked source audit.
- Reorganized the main README around the rule engine, standalone finite
  CSP/optimization engine and mixed coordinator, with runnable quick starts and
  explicit distinctions between the core finite API and legacy CSP companion.
- Added current Prune average timings and a fresh CLAIRE comparison after numeric
  optimization, with archived evidence, explicit timeout exclusions and separate
  timing boundaries in the [comparison report](docs/performance_solver_averages_2026-09-17.md).
- Retained the ALICE-inspired magic-square benchmark, exact deduction certificates,
  small exhaustive regression tests and historical performance report at `104d903`.
  This is a modeling experiment; engine defaults are unchanged.
- Added a locked optional research dependency and a separate CI job covering
  the experiment tests; core CI now checks Python 3.12 and 3.13.
- Marked expensive harmonizer integrations, added executable runtime boundary
  tutorials, and consolidated the current status and validation map.
- Added an interleaved evaluator benchmark with raw samples and checks of
  scores, scopes, support ordering, and witness counts.

### Added

- Native and mixed all-different propagation compiles value IDs, repairs integer
  matchings, and retains exact support masks directly. Bounded compilation keeps
  the reference fallback; `alldifferent_masks=False` selects it explicitly.
  See the [compiled all-different report](docs/performance_csp_alldifferent_masks_2026-09-17.md).

- Native and mixed arithmetic propagation shares compiled integer contributions
  and filters candidate masks directly for inequalities and unary/binary equalities.
  Mask-checked extrema caches preserve rollback and exact supports; bounded
  compilation falls back to the existing kernels. `numeric_masks=False` selects
  the reference path. See the [numeric report](docs/performance_csp_numeric_2026-09-17.md).

- Native and mixed integer linear optimization now propagates strict incumbent
  cuts through the ordinary constraint queue, including after rollback.
  `objective_propagation=False` retains bound-check-only behavior for ablation.
  See the [objective-cut report](docs/performance_csp_objective_2026-09-17.md).

- Exact Régin filtering now uses compact bitset graphs for bounded value
  alphabets, retaining the exact sparse fallback. Native propagation avoids
  rebuilding unchanged domain masks. The
  [all-different report](docs/performance_csp_alldiff_2026-09-16.md) records paired
  performance, correctness oracles, and refreshed external comparisons.
- Native `NValueConstraint` in finite and legacy CSP execution, with literal or
  variable counts, constants, aliases, empty scopes, textual declarations and
  rollback support. Matching/cover bounds and a budgeted feasibility check replace
  the benchmark's Boolean decomposition by default; `--nvalue decomposed` retains
  it for ablation. See the [NValue report](docs/performance_csp_nvalue_2026-09-16.md).
- Shared exact SUM/weighted-equality filtering with signed normalization,
  bounded bitsets and a sparse fallback, plus reusable immutable native-domain
  projections that remain correct across rollback. The
  [second CSP report](docs/performance_csp_equality_2026-09-16.md) records paired
  measurements and a separate projection-cache ablation.
- Opt-in finite-search progress observations, flushed diagnostic records and
  archived before/after CSP profiles. Exact arithmetic fast paths avoid reachable
  sums for inequalities and binary channels; search builds its incident index
  in one pass. The [performance report](docs/performance_csp_arithmetic_2026-09-16.md)
  records gains, regressions and unchanged proof/search results.
- Exact variable-order Markov training, four scoring modes, forbidden patterns,
  rational contour objectives and fixed-prefix continuation; sparse suffix-state
  DP and compilation into ordinary CSP constraints/factors.
- Sparse product and integer chain bounds for large sparse transition models,
  with independent melody oracles and archived performance records.

- An opt-in `snarky.finite` runtime with standalone reversible domains, the full
  existing persistent constraint vocabulary, native integer optimization,
  coordinated positive rule closure and pure factor objectives.
- A `.model` language, shared Python/text model validation, installed examples,
  and `snarky run` with explicit query, proof, limit and explanation output.
- Fixed-order Markov costs, bounded-window completion bounds and optional
  objective-guided value order; generic finite probability inference and an
  optional public regular-BP adapter with declared arithmetic and capabilities.
- A non-Bach conformance manifest, complete rulebase references, exhaustive
  mixed/optimization oracles and reproducible performance baselines.

- A frozen Snarky Core 0.1 compatibility baseline separating the established
  symbolic language from experimental probabilistic learning and regular-BP
  work, without authorizing a public release tag.
- Explicit stable, advanced, integration, and experimental API categories.
- Differential and property-based coverage of mutable inference behavior.
- Isolated installation smoke testing for built wheels.
- English publication guides for architecture, semantics, benchmarks, CSP,
  Sudoku, and four-part harmonization.
- Contribution, security, citation, release, licensing-status, and
  third-party provenance guidance.
- Automated checks for local documentation links and distribution contents.
- Fact-derived persistent constraint templates with `ALL_DIFFERENT`, `SUM`,
  `GCC`, and allowed `TABLE` propagation.
- Persistent `LINEAR_SUM`, binary comparison, `ELEMENT`, and `COUNT`
  templates with generalized arc-consistency filtering.
- Executable cryptarithm, Golomb-ruler, car-sequencing, balanced-curriculum,
  and balanced-graph-coloring models covering the practical constraint
  vocabulary and rule/constraint interaction.
- Joint constraint/rule fixed points during reversible `CHOICE` search.
- Dependency-aware joint fixed-point scheduling and exact bitset filtering for
  bounded non-negative `SUM` constraints.
- Rollback-aware inference-event cursors, incremental finite-domain
  projections, compiled canonical CSP choice/classification lookup, and
  reusable `ALL_DIFFERENT` matchings.
- Parameterized magic-square and Latin-square models plus a classical CSP
  benchmark and a persistent-constraint/forward-rule Sudoku hybrid.
- Four-level metric profiles, appoggiatura and escape-tone analysis, and
  declarative accompaniment/voicing policies in the SATB harmonizer.
- A conservative factorized event handler for streamed positive
  multi-premise rules, plus an executable triangle-closure example and
  CLAIRE4 comparison.
- A comment-preserving `snarky format` command and a source-oriented
  `snarky check` validator for rules, persistent constraints, and programs.

### Changed

- Decomposed the forward engine, choice search, indexed instantiation, domain
  filtering, and parser into focused modules without changing their public
  behavior.
- Limited wildcard package imports to the stable core while retaining all
  historical explicit top-level imports for the 0.1 series.
- Improved parser, fact-index, query-memory, join, and constraint-propagation
  hot paths, with benchmark evidence recorded under `benchmarks/results`.
- Avoided materialized partial products for safe comparison-barrier rules by
  anchoring indexed joins directly on added facts; removals, `FOCUS`, unbound
  comparisons, and unsupported premises retain their previous paths.
- Reduced the source distribution to buildable package sources and
  publication metadata. External references, vendored corpora, Spinoza source
  text, generated music, and benchmark records are excluded.
- Made generated MIDI and MusicXML local reproducible outputs instead of
  tracked source files.
- Delegated hierarchical metre analysis in the optional MuSES harmonizer
  bridge to `muses.metric_positions`, removing its duplicate meter algorithm.

### Compatibility

- No historical explicit import has been removed.
- Future top-level alias removals will follow the deprecation schedule in
  [docs/api_stability.md](docs/api_stability.md).
- No public package or version tag is authorized until the project license and
  unresolved redistribution reviews in `THIRD_PARTY.md` are settled.

[Unreleased]: https://github.com/fpachet/snarky/compare/v0.1.0...HEAD
