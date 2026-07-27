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
  `SUM`, `LINEAR_SUM`, `LESS_EQUAL`, `LESS_THAN`, `NOT_EQUAL`, `ELEMENT`,
  `COUNT`, `GCC`, `TABLE`, and `LEX_LESS_EQUAL` constraints;
- reference, indexed, semi-naive, constraint-filtered, and adaptive
  instantiation strategies;
- compiled event handlers for simple rules and safe factorized
  multi-premise deltas;
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

For streamed positive conjunctions, the default strategy can compile an
added fact into the anchor of a factorized event join. If every comparison
was already bound at its textual position, indexed lookups retrieve the
remaining supports without materializing a Cartesian prefix. Unsupported
rules, focused conflict-resolution rules, and removal deltas automatically
fall back to the general engine. See the executable
[triangle-closure example](rulebases/small/triangle_closure/README.md).

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
    -> safe factorized event handlers
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

### Related work: Yves Caseau's LAURE and CLAIRE

Snarky's convergence of persistent constraint filtering, forward rules,
explicit choices, propagation, and reversible search has a direct historical
precedent in Yves Caseau's work and is not presented here as a new general
architecture. LAURE allowed rules, constraints, and methods to cooperate over
the same objects; rules could guide constraint resolution, and consequences
participated in backtracking. CLAIRE subsequently integrated sets, compiled
rules, and search as expressive algorithm-building primitives.

Primary references:

- Yves Caseau, [*Rule-aided constraint resolution in
  LAURE*](https://doi.org/10.1007/BFb0013534), PDK 1991, pp. 237–256;
- Yves Caseau, [*Constraint satisfaction with an object-oriented knowledge
  representation language*](https://doi.org/10.1007/BF00872107), *Applied
  Intelligence* 4(2), 1994, pp. 157–184;
- Yves Caseau, François-Xavier Josset, and François Laburthe,
  [*CLAIRE: combining sets, search and rules to better express
  algorithms*](https://doi.org/10.1017/S1471068401001363), *Theory and
  Practice of Logic Programming* 2(6), 2002, pp. 769–805.

The detailed [LORE → LAURE → CLAIRE comparison](docs/caseau_rules_constraints.md)
maps these precedents to Snarky's current fixed-point, `CHOICE`, checkpoint,
and rollback semantics and identifies where the present project may still
contribute.

## Research applications

| Project | Purpose |
|---|---|
| [Finite CSP](csp_solver/README.md) | Classical puzzles, sequencing, scheduling, coloring, and reproducible CSP benchmarks through declarative constraints, rules, and choices |
| [Sudoku](sudoku/README.md) | progressive, explainable human techniques followed by explicit search |
| [Four-part harmonizer](harmonizer/README.md) | SATB generation with tonal rules, hierarchical metre, declarative melodic roles, and MuSES integration |
| [Rulebase catalogue](rulebases/README.md) | executable pedagogical and historically motivated examples |
| [Spinoza](spinoza/README.md) | French-language formalization of Part III of the *Ethics* |

Spinoza intentionally remains in French because its corpus, formalization, and
reports are tied to French primary material. Publication-facing engine and
application documentation is in English.

The finite-CSP catalogue includes executable SEND + MORE = MONEY, Golomb
ruler, car-sequencing, balanced-curriculum, balanced graph-coloring,
N-queens, magic-square, Latin-square, and hybrid Sudoku models. These examples
exercise `ALL_DIFFERENT`, `SUM`, `LINEAR_SUM`, comparisons, `ELEMENT`,
`COUNT`, `GCC`, `TABLE`, and `LEX_LESS_EQUAL` in practical combinations. See
the [finite-CSP guide](csp_solver/README.md) for formulations and commands.

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

The classical-CSP benchmark validates and measures magic squares, Latin
squares, and constraints-only versus rules-plus-constraints Sudoku:

```sh
uv run python -m benchmarks.classical_csp --repeat 3
uv run python -m benchmarks.classical_csp \
  --magic-sizes 6 7 --only-magic --repeat 3 \
  --magic-dom-wdeg-only
```

It reports timing together with nodes, failures, depth, and propagation
counters. Recorded runs compare dependency scheduling, incremental domains,
dom/wdeg, learned-impact value ordering, propagation-guided ordering, and
lexicographic symmetry breaking. Start with the
[classical CSP results](benchmarks/results/classical_csp_learned_impact_2026-07-25.json)
and the
[magic-square search results](benchmarks/results/magic_square_learned_impact_2026-07-25.json);
the complete dated archive remains under
[`benchmarks/results/`](benchmarks/results/).

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
