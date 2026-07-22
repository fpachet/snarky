# External rule-base corpora

This directory contains unmodified, source-language test corpora selected for
the Boojum reconstruction. They are reference inputs, not native Boojum tests.
Each corpus needs an explicit adapter, and comparisons are valid only for the
intersection between its source semantics and the semantics documented for this
project.

See `manifest.yaml` for exact revisions, archive checksums, selected paths, and
license status. In particular, ChaseBench and rbench did not expose a license in
the downloaded repository snapshot. Review their redistribution terms before
publishing a repository that contains those two directories.

## Imported selections

- `n3-w3c`: W3C N3 grammar and reasoning tests, excluding the large legacy
  `N3Tests/01etc` directory.
- `rif-1.22`: W3C RIF Core, BLD, and PRD test-suite archives.
- `clips-6.4.2`: official CLIPS examples and feature tests.
- `chasebench`: the small correctness and deep-chain scenarios only. LUBM,
  Ontology-256, STB-128, and the large medical datasets are intentionally not
  vendored.
- `rbench`: XSB and Souffle rule programs plus the transitive-closure,
  same-generation, and Join1 data selected from the OpenRuleBench-derived
  rbench repository.
- `souffle`: semantic, evaluation, provenance, scheduler, and syntax tests.
- `eye`: a compact selection of N3 reasoning cases relevant to recursive terms,
  reification, meta-interpretation, paths, and ordinary forward inference.

Run `scripts/fetch_test_rulebases.sh` in a clean checkout to reproduce the
selection. The script deliberately refuses to overwrite an existing corpus.
