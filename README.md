# Snarky

Snarky is a typed symbolic inference engine for Python, inspired by
Jean-Louis Laurière's SNARK and Jean-Luc Dormoy's BOOJUM. It combines
production rules, recursive terms, finite-domain propagation, explicit
weighted choices, and reversible search in one explainable runtime.

The opt-in `snarky.finite` API also provides standalone CSP solving, integer
branch-and-bound, pure factor objectives and supported probability queries.
Its [finite model language](docs/finite_language.md) combines positive rules,
constraints and factors in one declarative model, with explicit query semantics.
The [performance ledger](docs/performance_baseline.md) preserves measurements
for comparing future changes. The Bach experiment is a separate side project,
outside Snarky's main application and redesign portfolio.
The [Markov melody examples](docs/markov_melody_examples.md) reproduce the four
2011 scoring modes, forbidden patterns, contour control and continuation using
exact objectives and the ordinary CSP engine.
The [Blues research handoff](docs/research/blues_villani_2026-09-16/README.md)
collects ordinary, exotic and Boulez results, performance evidence and LaTeX tables.

Snarky is a research prototype: its core inference and finite-domain
constraint semantics are extensively tested. Adaptive strategy selection,
selected search policies, and the pre-1.0 `csp_solver` public API remain
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
python -m snarky check --syntax-only --format .
pytest
ruff check .
mypy src
```

To use persistent constraints through the installed console outside the
checkout, install the optional CSP companion after the core:

```sh
python -m pip install ./csp_solver
snarky check csp_solver/magic_square.constraints
```

The companion bundles its rule and constraint data. Reinstall it after
editing its sources; `python -m snarky` from the checkout uses the current
sources directly.

Choose the test scope explicitly:

| Scope | Command |
|---|---|
| Complete core/application suite | `pytest` |
| Non-Bach redesign conformance | `python scripts/check_redesign.py` |
| Shorter feedback loop | `pytest -m "not slow"` |
| Expensive harmonizer integrations | `pytest -m slow --durations=10` |
| Research unit and fixture tests | `pytest harmonizer/bach_rule_induction/experiments` |

Research tests additionally require `python -m pip install -e ".[dev,research]"`.
They run separately in CI. For a locked environment, use
`uv sync --frozen --extra dev --extra research` and prefix commands with
`uv run --frozen`. See the [validation map](docs/project_status.md) for details.

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

Relation variables make it possible to express the same kind of reasoning
once for every relation having a given property. This second rulebase keeps
the immediate `parent_of` relation intact, promotes it to `ancestor_of`, and
declares only `ancestor_of` to be transitive:

```python
from snarky import Fact, ForwardEngine, parse_rules, parse_term

rules = parse_rules(
    """
    RULE parent_implies_ancestor
    WHEN
        ($x parent_of $y)
    THEN
        ADD ($x ancestor_of $y)
    END

    RULE transitive_relation
    WHEN
        ($relation is_transitive TRUE)
        ($x $relation $y)
        ($y $relation $z)
        $x != $z
    THEN
        ADD ($x $relation $z)
    END
    """
)
facts = (
    Fact(parse_term("(ancestor_of is_transitive TRUE)")),
    Fact(parse_term("(alice parent_of bob)")),
    Fact(parse_term("(bob parent_of clara)")),
    Fact(parse_term("(clara parent_of david)")),
)
result = ForwardEngine(rules).run(facts)

assert Fact(parse_term("(alice ancestor_of david)")) in result.facts
```

The variable `$relation` occurs in relation position in
`($x $relation $y)`: it denotes a relation rather than an individual term,
which makes `transitive_relation` an order-2 rule. Newly inferred
`ancestor_of` facts can activate the rule again, so the engine computes the
complete transitive closure. The same rule can serve any other relation
declared with `($relation is_transitive TRUE)`.

The default engine uses semi-naive instantiation. A separate exhaustive
strategy remains the executable semantic reference and a useful diagnostic
oracle.

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
| [Markov constraints](docs/markov_constraints_application.md) | Ordinary, exotic and Boulez Blues; four melody scoring modes, forbidden patterns, contour control and continuation, with exact optimization and measured performance |
| [Sudoku](sudoku/README.md) | progressive, explainable human techniques followed by explicit search |
| [Four-part harmonizer](harmonizer/README.md) | SATB generation with tonal rules, hierarchical metre, declarative melodic roles, and MuSES integration |
| [Rulebase catalogue](rulebases/README.md) | executable pedagogical and historically motivated examples |
| [Spinoza](spinoza/README.md) | French-language formalization of Part III of the *Ethics* |

The [Bach experiment](harmonizer/bach_rule_induction/README.md) is a separate
side project with its own corpus, learning protocols and acceptance criteria.
The generic four-part harmonizer remains an engine application and compatibility
case study.

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
- [Language validation and formatting](docs/language_tooling.md)
- [Semantics](docs/semantics.md)
- [Runtime boundary tutorials](docs/runtime_tutorial.md)
- [Learned-factor language plan](docs/learned_factor_language_plan.md)
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

The [Prune comparison](docs/performance_prune_2026-09-16.md) adds a shared-model
pure CSP/optimization portfolio with independent Gecode validation, recorded
timeouts, and explicit coverage and solver-capability differences.

Correctness tests compare optimized strategies with the executable reference
implementation across mutation, negation, search, propagation, and
application scenarios.
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

The [current status map](docs/project_status.md) distinguishes frozen Core 0.1,
application prototypes, tested research code, and proposed probabilistic APIs.

The September 2026 review fixes are implemented:

- custom propagators reach a complete fixed point before search proceeds;
- saved results preserve their explanations across rollback, and assumptions
  update dependent minimum proof depths reversibly;
- finite numeric terms round-trip through exponent-aware parsing;
- the optional CSP companion supports installed-console constraint validation;
- factor explanations preserve witness order without quadratic support scans.

The [recorded benchmark](benchmarks/results/factor_supports_review_2026-09-08.json)
reduced the 4,000-witness shared-scope evaluator median from 1.467 s to
0.00937 s. This result is specific to that synthetic workload. The
[validation record](docs/project_status.md#review-fix-validation--8-september-2026)
documents local tests and distinguishes them from remote CI execution.
The [runtime tutorials](docs/runtime_tutorial.md) provide executable examples
of propagation, saved proofs, and factor/choice boundaries.

The consolidation through parser decomposition and API stabilization is
complete. Work still required before a public tagged release is tracked in
[docs/consolidation_plan.md](docs/consolidation_plan.md), especially explicit
licensing and third-party redistribution decisions.

Feature proposals such as reflective meta-rules, full ATMS support, and
parallel choice search remain research directions rather than current API
commitments.
