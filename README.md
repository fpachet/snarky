# Snarky

Snarky is a Python system for **symbolic reasoning, constraint solving and
optimization**, inspired by Jean-Louis Laurière's SNARK and Jean-Luc Dormoy's
BOOJUM. It provides two primary execution engines and a coordinator that lets
them cooperate:

| Component | What it does | Entry point |
|---|---|---|
| **Rule engine** | Derives facts with incremental forward chaining, mutable working memory, provenance and reversible sessions | `ForwardEngine` and the operational Core rule language |
| **Finite CSP and optimization engine** | Propagates finite domains, searches for solutions, and minimizes or maximizes explicit objectives | `snarky.finite.solve` and the declarative `.model` language |
| **Mixed coordinator** | Exchanges singleton assignments and derived facts, activates guarded constraints, and coordinates fixed points and rollback | Selected automatically by native `solve` when a finite model includes rules |

Both engines work independently. Pure CSP models use direct domain storage and
propagators without creating an inference session. Mixed models share symbolic
terms and model definitions; the coordinator connects the engines during search.
Factors supply explicit objective scores or probability measures rather than
forming a third solver. See [how the engines cooperate](#execution-model).

Both engines ship in the core Python package. The optional `csp_solver` companion
retains the older fact-backed CSP interface and application catalogue. The
operational Core API has a frozen compatibility contract; `snarky.finite`,
`.model`, and the companion API remain tested, pre-1.0 experimental surfaces.
Snarky is a research prototype, not a public stable release.

## Why Snarky?

The name acknowledges the historical SNARK language and nods to Snarky Puppy.
The latter also suggests the project's central idea: a fusion of symbolic
rules, constraint filtering, search, and musical applications.

Snarky is not a source-compatible reimplementation of SNARK or BOOJUM.
Historical behavior is identified where sources support it; reconstructed
behavior and modern extensions are documented separately.

## Capabilities

- **Rules:** recursive symbolic terms, variables in every triple position,
  forward chaining, indexed and semi-naive matching, specialized event handlers,
  correlated `EXISTS`/`NOT EXISTS`/`COUNT` premises, rule groups and programs.
- **Finite constraints:** `ALL_DIFFERENT`, `SUM`, `LINEAR_SUM`, comparisons,
  `ELEMENT`, `COUNT`, `NVALUE`, `GCC`, `TABLE` and lexicographic constraints,
  with reversible domain propagation and exact complete-assignment checks.
- **Search and optimization:** feasibility, enumeration, integer branch-and-bound,
  factor objectives, exact rational-product objectives, admissible bounds and
  propagated integer incumbent cuts. Results distinguish a feasible solution,
  a proved optimum and an interrupted search.
- **Mixed models:** positive rules derive properties from assignments; those
  properties can activate constraints or contribute to pure factor scores.
  Facts and domains restore together when search backtracks.
- **Probability queries:** explicit measures, partition functions and exact sampling
  for supported finite models, with a generic backend and an optional regular-BP
  backend. Arithmetic guarantees and backend limits are reported explicitly.
- **Explanations and validation:** rule provenance, domain-removal causes and score
  contributions, plus independent reference implementations, exhaustive oracles
  and rollback tests. Operational `CHOICE` weights remain separate from model
  objectives and probability measures.

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

The core installation includes standalone and mixed finite solving, `.model`
execution, and optimization. For the legacy fact-backed CSP interface and
installed-console `.constraints` validation outside the checkout, also install
the optional companion:

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

## Quick starts

### Rule inference

Use the rule engine to derive a grandparent relation:

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

The same rule can be expressed in the [textual Core language](docs/syntax.md).
It also supports recursive terms and variables in relation position. See the
[rulebase catalogue](rulebases/README.md) and
[triangle-closure example](rulebases/small/triangle_closure/README.md) for larger
examples of incremental matching.

### Pure CSP optimization

Use the finite engine to assign distinct values and minimize an explicit cost:

```python
from snarky import Atom, Number
from snarky.finite import (
    FiniteModel, FiniteVariable, LinearObjective, Query, QueryKind,
    ResultStatus, solve,
)
from snarky.finite.constraints import AllDifferentConstraint

x, y = Atom("x"), Atom("y")
domain = (Number(1), Number(2))
model = FiniteModel(
    "placement",
    (FiniteVariable(x, domain), FiniteVariable(y, domain)),
    (AllDifferentConstraint(Atom("distinct"), (x, y)),),
    objective=LinearObjective(((1, x), (-2, y))),
)
result = solve(model, Query(QueryKind.MINIMIZE))

assert result.status is ResultStatus.OPTIMAL
assert result.incumbent.objective_value == -3
assert result.incumbent.assignment == {x: Number(1), y: Number(2)}
```

No rules or candidate facts are needed. `SOLVE` asks for a feasible solution;
`ENUMERATE` asks for all solutions, subject to declared limits. The
[finite model guide](docs/finite_model_contract.md) documents query statuses,
objectives, factors and backend capabilities.

### Rules and constraints together

The packaged [scheduling model](src/snarky/finite/models/scheduling.model) declares
two slot variables, an all-different constraint, a rule and a guarded constraint.
Choosing setup slot 3 derives `(shift needs overtime)`, which activates a
constraint requiring delivery slot 2. Factors reward a preferred delivery slot
and penalize overtime; the query maximizes their total score.

```python
from importlib.resources import files
from snarky.finite import ResultStatus, parse_model_document

source = files("snarky.finite").joinpath("models/scheduling.model").read_text()
document = parse_model_document(source)
result = document.execute("optimum")

assert result.status is ResultStatus.OPTIMAL
assert result.incumbent.objective_value == 5
```

From the checkout, the same model runs through the console:

```sh
snarky run src/snarky/finite/models/scheduling.model --query optimum --explain
```

See the [`.model` language guide](docs/finite_language.md) for declarations and
[packaged examples](src/snarky/finite/models) for pure, mixed and probabilistic
models.

## Execution model

**Rule execution** uses `ForwardEngine` and inference sessions to maintain facts,
indexes, refraction and provenance. Operational programs retain their ordered
mutation and conflict-resolution semantics. Explicit `CHOICE` search can explore
alternatives using reversible sessions.

**Finite solving** uses `NativeState` for domains and an incident propagation queue,
with a separate search controller for branching and optimization. The controller
keeps the incumbent outside reversible branch state. Pure CSP execution does not
invoke the rule matcher. Here, “native” means the direct Python finite solver,
not compiled machine code.

**Mixed solving** uses `MixedState` to coordinate native domains and an incremental
rule session:

```text
propagate domains
    -> expose singleton assignments as facts
    -> derive properties through positive rule closure
    -> activate guarded constraints
    -> repeat until neither domains nor facts change
    -> branch, score a complete solution, or backtrack
```

Newly forced singleton values can trigger further rules. One coordinated
checkpoint restores domains, facts, derivations and pruning explanations together.
Hard constraints determine feasibility; objectives and factors determine scores;
search selects the exploration order. This coordination is part of the execution
semantics, not a one-time preprocessing pass.

The declarative mixed fragment admits positive, function-free derivations and
comparisons whose variables are already bound. Arbitrary operational rules with
destructive `REMOVE` actions or fresh object creation are not admitted into this closure.
They remain available through the standalone operational engine. See the
[architecture](docs/architecture.md) and [finite contract](docs/finite_model_contract.md).

The older `csp_solver` path encodes domains as candidate facts and combines
persistent constraints with operational `CHOICE` search. It remains supported
for compatibility and existing applications. Its
[`.constraints` templates](docs/persistent_constraints.md) are distinct from the
new finite engine's direct domains and `.model` interface.

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

The [latest CLAIRE benchmarks](docs/performance_csp_alldifferent_masks_2026-09-17.md#fresh-claire-measurements) report
current rule/choice workloads and a separately labelled native-global CSP
formulation, with explicit timing and interpreter limitations.

## Research applications

| Project | Purpose |
|---|---|
| [Finite models](docs/finite_language.md) | Standalone CSP, optimization and mixed rule/constraint models, with packaged examples and reproducible benchmarks |
| [Legacy CSP catalogue](csp_solver/README.md) | Classical puzzles, sequencing, scheduling and coloring through fact-backed domains, rules and choices |
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
- [Operational Core semantics](docs/semantics.md)
- [Architecture: two engines and their coordinator](docs/architecture.md)
- [Finite CSP, optimization and mixed-model contract](docs/finite_model_contract.md)
- [Declarative finite model language](docs/finite_language.md)
- [Runtime boundary tutorials](docs/runtime_tutorial.md)
- [Learned-factor language plan](docs/learned_factor_language_plan.md)
- [Current CSP optimization roadmap](docs/csp_optimization_roadmap_2026-09-16.md)
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
timeouts, and explicit coverage and solver-capability differences. **Prune is
compiled Rust; Snarky's finite solver is implemented in Python.** These timings
compare complete implementations with different search policies and some different
constraint encodings. They do not establish an algorithm-quality ranking or isolate
the cost of either language. Follow-up work separates search effort, propagation
strength and Python implementation overhead; the objective is an efficient Python
CSP engine, with Prune providing an external performance reference.

The [latest all-different optimization](docs/performance_csp_alldifferent_masks_2026-09-17.md)
improves paired process medians **1.69× for queens 50** and **1.75× for incremental
Latin 16**, preserving exact supported values and search counters. Fixed-work
traces reduce peak allocations by about **19–26%** on queens 50/104 and Latin 16.
The full completion score is **52/59 versus Prune's 59/59**; optimization proofs
are **3/5 versus 5/5** at the declared five-second limit. The
[performance ledger](docs/performance_baseline.md) preserves earlier results,
and the [optimization roadmap](docs/csp_optimization_roadmap_2026-09-16.md)
records remaining work on propagation overhead, search bounds and compact domains.

The [latest comparison averages](docs/performance_csp_alldifferent_masks_2026-09-17.md#updated-averages)
are **165.8 ms for Snarky versus 6.29 ms for Prune** on the 52 jointly completed
workloads (26.4×, including startup; seven Snarky timeouts excluded). A fresh
CLAIRE rerun averages **12.2 versus 2.84 ms** on native-CSP queens (4.3×);
Talarian and triangle rule workloads have 22.3× and 2.6× gaps respectively.
CLAIRE timings exclude startup and use its interpreter, so the two suites have
different timing boundaries and must be read separately.

The separate [ALICE-inspired experiment](docs/performance_alice_magic_2026-09-17.md)
compares certified sum cancellation and elimination on magic squares. Its frozen
measurements at `104d903` show a policy-dependent 4×4 gain and slower 5×5 solves;
they do not support enabling blanket symbolic preprocessing in the engine.

Correctness tests compare optimized strategies with the executable reference
implementation across mutation, negation, search, propagation, and
application scenarios.
Microbenchmarks are separate from tests and write machine-readable results
under `benchmarks/results/`.

Run the cross-rulebase benchmark:

```sh
uv run python -m benchmarks.rulebase_suite --repeat 7
```

The legacy classical-CSP benchmark validates and measures magic squares, Latin
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

The [status map](docs/project_status.md) distinguishes the frozen operational
Core from the implemented, experimental finite solver and mixed-model language,
application prototypes and research work. Generic finite probability inference
and the optional regular-BP adapter are implemented; learned parameters and
broader probabilistic extensions remain research.

Validation covers rule matching, CSP support oracles, exact optimization, mixed
fixed points, rollback, explanations and Markov applications. The
[latest solver validation](benchmarks/results/csp_admask_2026-09-17/validation.md)
records 1,113 passing tests and 3 skipped, plus package checks. Historical
[review-fix evidence](docs/project_status.md#review-fix-validation--8-september-2026)
and [runtime tutorials](docs/runtime_tutorial.md) retain the operational behavior
and compatibility checks.

The [Blues research handoff](docs/research/blues_villani_2026-09-16/README.md)
collects ordinary, exotic and Boulez results, performance evidence and LaTeX tables.
The [Markov melody examples](docs/markov_melody_examples.md) cover the four 2011
scoring modes, forbidden patterns, contour control and continuation with explicit
objectives.

The consolidation through parser decomposition and API stabilization is
complete. Work still required before a public tagged release is tracked in
[docs/consolidation_plan.md](docs/consolidation_plan.md), especially explicit
licensing and third-party redistribution decisions.

Feature proposals such as reflective meta-rules, full ATMS support, and
parallel choice search remain research directions rather than current API
commitments.
