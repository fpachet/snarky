# Changelog

All notable user-facing changes to Snarky are recorded here. The project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html); compatibility
details are documented in [docs/versioning.md](docs/versioning.md).

## [Unreleased]

### Added

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
