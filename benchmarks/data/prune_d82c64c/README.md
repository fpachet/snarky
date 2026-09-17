# Prune benchmark snapshot

Imported from [ynosound-dev/prune](https://github.com/ynosound-dev/prune), revision
`d82c64c29e823513845e56a54e22e21606c0698c`. Copyright 2026 Pierre Roy.
The upstream project offers MIT OR Apache-2.0; both license files are retained.
[PROVENANCE.json](PROVENANCE.json) hashes every imported file. The models,
parameters, solver library and manifests are unmodified. Cargo.lock is retained
for rebuilding the corresponding Rust binary; Rust sources are not vendored.

The seven manifests define 54 instances and 59 instance/mode workloads. The
requested CSPLib 20-instance suite and reserved 11-instance validation suite are
absent from this revision. Their definitions must be obtained before claiming
coverage of the requested 85 instances; reserved parameters must not be invented
or used for heuristic tuning.

The local collector applies one recorded syntax-only compatibility correction
in temporary copies of `dominating_queens_nvalue.mzn` for MiniZinc 2.9.7:
`array[square in squares]` becomes `array[squares]` in the dominators declaration.
Both solvers receive the same compiled result. The original remains here.

Both large-domain chains are fully solved by MiniZinc during compilation;
the resulting solver inputs contain no variables or constraints. These cases
cannot establish solver support for billion-value domains.

The original `minizinc/prune.msc` records an upstream relative executable path.
The collector generates a separate configuration with the supplied binary path.
See the [comparison report](../../../docs/performance_prune_2026-09-16.md) for
protocol, results, limitations, and reproduction commands.
