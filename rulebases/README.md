# Rulebase catalogue

This directory contains executable Snarky rulebases. It separates short
teaching examples, historically motivated reformulations, constraint
examples, and full project models.

```text
rulebases/
├── small/          # focused language and inference examples
├── thesis/         # examples reconstructed from historical research
├── constraints/    # binary, arithmetic, and global constraints
└── projects/       # links to the larger application rulebases
```

Most runnable cases contain:

- a README describing the problem and its research purpose;
- `rules.rules` in Snarky's textual DSL;
- `initial_facts.yaml`;
- `expected_facts.yaml` as a minimal oracle;
- `scenario.yaml` defining group execution order.

[`catalog.yaml`](catalog.yaml) records provenance, feature coverage, and
execution metadata. Historical attribution does not imply exact
source-compatibility with the original systems.

Run one entry from the repository root:

```sh
uv run python -m rulebases.runner \
  rulebases/small/fibonacci_explicit/scenario.yaml
```

Directory shorthand is also accepted:

```sh
uv run python -m rulebases.runner thesis/tomorrow_date
```

The catalogue is included in differential tests and in the cross-rulebase
benchmark. External source corpora remain under `third_party/`; their
provenance and redistribution status are documented in
[`../THIRD_PARTY.md`](../THIRD_PARTY.md).

Spinoza is intentionally maintained as a separate French-language research
corpus under [`../spinoza`](../spinoza/README.md).
