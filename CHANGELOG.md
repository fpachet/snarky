# Changelog

All notable user-facing changes to Snarky are recorded here. The project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html); compatibility
details are documented in [docs/versioning.md](docs/versioning.md).

## [Unreleased]

### Added

- Explicit stable, advanced, integration, and experimental API categories.
- Differential and property-based coverage of mutable inference behavior.
- Isolated installation smoke testing for built wheels.

### Changed

- Decomposed the forward engine, choice search, indexed instantiation, domain
  filtering, and parser into focused modules without changing their public
  behavior.
- Limited wildcard package imports to the stable core while retaining all
  historical explicit top-level imports for the 0.1 series.
- Improved parser, fact-index, query-memory, join, and constraint-propagation
  hot paths, with benchmark evidence recorded under `benchmarks/results`.

### Compatibility

- No historical explicit import has been removed.
- Future top-level alias removals will follow the deprecation schedule in
  [docs/api_stability.md](docs/api_stability.md).

[Unreleased]: https://github.com/fpachet/snarky/compare/v0.1.0...HEAD

