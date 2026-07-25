# Snarky

Snarky is a typed symbolic inference engine for Python, inspired by
Jean-Louis Laurière's SNARK and Jean-Luc Dormoy's BOOJUM. It combines
production rules, recursive terms, finite-domain propagation, explicit
weighted choices, and reversible search in one explainable runtime.

Snarky is a research prototype: its core semantics and compatibility boundary
are tested, while adaptive propagation and some search policies remain
experimental.

## Why Snarky?

The name acknowledges the historical SNARK language and nods to Snarky Puppy.
The latter also suggests the project's central idea: a fusion of symbolic
rules, constraint filtering, search, and musical applications.

Snarky is not a source-compatible reimplementation of SNARK or BOOJUM.
Historical behavior is identified where sources support it; reconstructed
behavior and modern extensions are documented separately.

## Capabilities

- immutable atoms, numbers, variables, triples, propositions, sequences, and
  sets;
- recursive terms and variables in every triple position;
- forward chaining with deterministic ordering, refraction, and provenance;
- mutable working memory with reversible `ADD` and `REMOVE` actions;
- correlated `EXISTS`, `NOT EXISTS`, `COUNT`, `UNIQUE`, and collection
  premises;
- named rule groups, persistent sessions, checkpoints, and explicit programs;
- finite choices, contextual weights, depth- or breadth-first traversal, and
  backtracking;
- premise-local finite-domain filtering plus persistent `ALL_DIFFERENT`,
  `SUM`, `GCC`, `TABLE`, and `LEX_LESS_EQUAL` constraints;
- reference, indexed, semi-naive, constraint-filtered, and adaptive
  instantiation strategies;
- strict type checking and differential tests across execution strategies.

The required runtime is Python 3.12 or newer. PyYAML is the only mandatory
third-party dependency.

## Install from source

```sh
git clone https://github.com/fpachet/snarky.git
cd snarky
python -m pip install -e .
```

For development:

```sh
python -m pip install -e ".[dev]"
pytest
ruff check .
mypy src
```

The project has not yet declared a redistribution license. See
[publication status](LICENSE_STATUS.md) before copying or redistributing it.

## Quick start

The stable Python API can define rules directly:

```python
from snarky import Atom, Fact, ForwardEngine, Rule, Triple, Variable, add, when

x = Variable("x")
y = Variable("y")
z = Variable("z")

grandparent = Rule(
    name="grandparent",
    premises=(
        when(Triple(x, Atom("parent_of"), y)),
        when(Triple(y, Atom("parent_of"), z)),
    ),
    actions=(add(Triple(x, Atom("grandparent_of"), z)),),
)

facts = (
    Fact(Triple(Atom("alice"), Atom("parent_of"), Atom("bob"))),
    Fact(Triple(Atom("bob"), Atom("parent_of"), Atom("clara"))),
)
result = ForwardEngine((grandparent,)).run(facts)

assert Fact(
    Triple(Atom("alice"), Atom("grandparent_of"), Atom("clara"))
) in result.facts
```

The same ideas can be written in the textual rule language:

```python
from snarky import Fact, ForwardEngine, parse_rules, parse_term

rules = parse_rules(
    """
    RULE grandparent
    WHEN
        ($x parent_of $y)
        ($y parent_of $z)
    THEN
        ADD ($x grandparent_of $z)
    END
    """
)
facts = (
    Fact(parse_term("(alice parent_of bob)")),
    Fact(parse_term("(bob parent_of clara)")),
)
result = ForwardEngine(rules).run(facts)
```

The default engine uses semi-naive instantiation. The naive strategy remains
the executable semantic reference and a useful diagnostic oracle.

## Execution model

Snarky keeps inference and search separate:

1. a forward engine evaluates eligible rule activations to a deterministic
   fixed point;
2. an inference session retains facts, refraction, indexes, and provenance;
3. checkpoints make mutations and propagation state reversible;
4. choice search selects explicit alternatives and restores the session when
   a branch fails.

Constraint filtering narrows finite variable domains before exact matching:

```text
candidate facts
    -> premise tables and variable domains
    -> propagation to a fixed point
    -> active Compact-Table rows
    -> semi-naive joins containing new facts
    -> exact matcher validation
```

This preserves one semantic reference while allowing optimized strategies to
avoid irrelevant matches.

Choice search can additionally host persistent constraints over fact-encoded
domains:

```text
persistent constraint closure
    -> forward-rule closure
    -> repeat to a joint fixed point
    -> explicit CHOICE
    -> reversible propagation or backtracking
```

Fact-derived `.constraints` templates keep global scopes independent of
problem size. See [persistent constraints](docs/persistent_constraints.md)
and the [Caseau historical comparison](docs/caseau_rules_constraints.md).

## Research applications

| Project | Purpose |
|---|---|
| [Finite CSP](csp_solver/README.md) | N-queens, magic squares, and Sudoku through generic declarative choices and propagation |
| [Sudoku](sudoku/README.md) | progressive, explainable human techniques followed by explicit search |
| [Four-part harmonizer](harmonizer/README.md) | SATB generation with tonal rules, contextual weights, and MuSES integration |
| [Rulebase catalogue](rulebases/README.md) | executable pedagogical and historically motivated examples |
| [Spinoza](spinoza/README.md) | French-language formalization of Part III of the *Ethics* |

Spinoza intentionally remains in French because its corpus, formalization, and
reports are tied to French primary material. Publication-facing engine and
application documentation is in English.

## Documentation

- [Documentation map](docs/README.md)
- [Textual syntax](docs/syntax.md)
- [Semantics](docs/semantics.md)
- [Finite-CSP solver optimization plan](docs/solver_optimization_plan.md)
- [API stability](docs/api_stability.md)
- [Versioning and compatibility](docs/versioning.md)
- [Strategy lifecycle](docs/strategy_lifecycle.md)
- [Benchmarks](benchmarks/README.md)
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)

The stable API is exported from `snarky`. Advanced and experimental components
should be imported from their defining modules. All historical explicit root
imports remain compatible during the 0.1 series.

## Reproducibility and performance

Correctness tests compare optimized strategies with the naive reference across
mutation, negation, search, propagation, and application scenarios.
Microbenchmarks are separate from tests and write machine-readable results
under `benchmarks/results/`.

Run the cross-rulebase benchmark:

```sh
uv run python -m benchmarks.rulebase_suite --repeat 7
```

See [benchmarks/README.md](benchmarks/README.md) for protocols, interpretation,
and the historical result files. Performance figures are environment-specific;
logical equivalence is always checked before a change is accepted.

## Project status

The consolidation through parser decomposition and API stabilization is
complete. Work still required before a public tagged release is tracked in
[docs/consolidation_plan.md](docs/consolidation_plan.md), especially explicit
licensing and third-party redistribution decisions.

Feature proposals such as reflective meta-rules, full ATMS support, and
parallel choice search remain research directions rather than current API
commitments.
