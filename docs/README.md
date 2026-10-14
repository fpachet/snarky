# Documentation

Start with the page that answers your question. The repository keeps usage
references, experimental findings and design history for different purposes.
They are not a single reading sequence.

<a id="start-here"></a>

| I want to… | Start here |
|---|---|
| Understand what Snarky is and run a first example | [Project overview](../README.md) |
| Understand the rule engine, finite solver and their coordinator | [Architecture](architecture.md) |
| Write or run a constraint model | [Finite model language](finite_language.md) |
| Learn runtime behavior through examples | [Runtime tutorials](runtime_tutorial.md) |
| Find current benchmark results and reproduction commands | [Benchmark guide](../benchmarks/README.md) |
| Find the latest magic-square results | [Magic-square overview](../benchmarks/README.md#magic-squares) |
| Check compatibility, validation scope and release boundaries | [Project status](project_status.md) |

## Where documents belong

| Location | Role | How to read it |
|---|---|---|
| Root `README.md` | Project overview, installation and quick starts | Begin here |
| `docs/` | Usage guides, reference contracts and indexed design records | Choose a topic below |
| Application directories | Application-specific setup and limitations | Start at that application's README |
| `benchmarks/README.md` | Current results overview and benchmark instructions | Main performance entry point |
| `benchmarks/history/` | Dated measurements, source snapshots and experiment decisions | Follow links from the overview when you need evidence |
| `experiments/` and `docs/research/` | Prototypes, study protocols and research reports | Check each study's scope and promotion decision |

A dated report describes its recorded sources and settings. Its timings and
statements about defaults do not automatically describe today's solver.
A plan records intentions and decisions; its title alone does not establish
whether a feature is implemented. Use the reference guide, status map and
experiment's explicit decision for those questions.

<a id="publication-guides-in-english"></a>

## Usage and reference

These guides explain the language, APIs and runtime contracts. Read the ones
relevant to your work; you do not need the experiment history first.

- [Architecture](architecture.md)
- [Declarative finite model contract](finite_model_contract.md)
- [Finite model language and migration](finite_language.md)
- [Textual syntax](syntax.md)
- [Language validation and formatting](language_tooling.md)
- [Reference semantics](semantics.md)
- [Snarky Core 0.1 baseline](core_0_1_baseline.md)
- [Rule programs and sequential steps](rule_programs.md)
- [Persistent finite-domain constraints](persistent_constraints.md)
- [LORE, LAURE, CLAIRE, and Snarky](caseau_rules_constraints.md)
- [API stability](api_stability.md)
- [Versioning and compatibility](versioning.md)
- [Strategy lifecycle](strategy_lifecycle.md)

## Applications

- [Workforce scheduling](scheduling.md): runnable basic and extended workforce
  examples, optimization bounds, measured performance and modeling limits.
- [Markov constraints](markov_constraints_application.md): exact Blues and melody
  optimization, paper reproductions, control examples and performance records.
- [Finite CSP](../csp_solver/README.md)
- [Sudoku](../sudoku/README.md)
- [Four-part harmonizer](../harmonizer/README.md)
- [Rulebase catalogue](../rulebases/README.md)

The [Bach experiment](../harmonizer/bach_rule_induction/README.md) is a separate
side project with its own learning and generation protocols.
<a id="spinoza"></a>

The [Spinoza project](../spinoza/README.md) and its systematic atlas retain their
French formalization and reports.

## Performance and experiment history

For current results, use the [benchmark guide](../benchmarks/README.md).
The [results archive](../benchmarks/history/README.md) indexes prior experiments,
including which magic-square ideas were enabled, left opt-in or rejected.

The [native residual experiment](../benchmarks/README.md#reusable-residual-kernels--14-october-2026-experimental)
is retained as an opt-in comparison baseline, outside the production solver.
Its setup, commands, first-solution restrictions and cache behavior are described
in that same benchmark guide.

<details>
<summary>Dated performance and implementation reports</summary>

- [Redesign performance baseline](performance_baseline.md): fixed non-Bach workloads,
  fresh timings, comparison protocol, and optimization ledger.
- [Prune CSP comparison](performance_prune_2026-09-16.md): shared models, optimization,
  global constraints, independently validated Rust/Python implementation timings,
  interpretation limits and explicit coverage gaps.
- [First CSP optimization slice](performance_csp_arithmetic_2026-09-16.md):
  slow-case profiles, progress observations, exact arithmetic filtering and
  paired Python/Python performance and compatibility controls.
- [Second CSP optimization slice](performance_csp_equality_2026-09-16.md):
  exact weighted equalities, reusable domain projections, cache ablation and
  repeated performance/compatibility measurements.
- [Native NValue](performance_csp_nvalue_2026-09-16.md): exact distinct-count
  semantics, bounded cover filtering, decomposition ablation and a fresh Prune run.
- [All-different and propagation costs](performance_csp_alldiff_2026-09-16.md):
  exact bitset graph filtering, unchanged-domain shortcut and new measurements.
- [Propagated incumbent cuts](performance_csp_objective_2026-09-17.md): exact
  integer improving cuts, rollback/fixed-point tests and measured optimization impact.
- [Compiled numeric masks](performance_csp_numeric_2026-09-17.md): shared integer
  contributions, direct arithmetic support masks, rollback-safe extrema caches,
  paired timings, memory costs and refreshed Prune measurements.
- [Compiled all-different masks](performance_csp_alldifferent_masks_2026-09-17.md):
  stable value IDs, integer matching repair, exact direct-mask filtering,
  differential oracles and repeated performance/memory comparisons.
- [ALICE-inspired magic-square deductions](performance_alice_magic_2026-09-17.md):
  certified sum cancellation and elimination, with search-policy controls;
  historical timings at `104d903`, without changing engine defaults.
- [Refreshed CLAIRE comparisons](performance_claire_2026-09-16.md): historical
  rule/choice workloads and a separately labelled native-global queens variant.
- [Prune and CLAIRE averages (September 2026)](performance_solver_averages_2026-09-17.md):
  average per-workload medians, explicit timeout treatment and a fresh CLAIRE run
  after numeric-mask optimization, with archived samples and source identity.
- [Redesign implementation evidence](redesign_progress.md)
- [Boulez optimization result](performance_boulez_2026-09-16.md): exact published
  sequence regenerated without a seed, with a completed proof and paired benchmarks.
- [Markov implementation progress](markov_constraints_progress.md): corpus audit,
  exact first-order Blues optimization, and remaining acceptance gates.
- [Scheduling symmetry and workload filtering (28 September 2026)](performance_scheduling_2026-09-28.md): controlled 32-task measurements.
- [Established scheduling assessment](performance_scheduling_standard_2026-09-29.md):
  PSPLIB J30 and OR-Library FT06/LA01–LA05, with validators and raw evidence.
- [Scheduling optimization comparison](performance_scheduling_improvements_2026-09-29.md):
  capacity propagation, numeric alternatives, constructive schedules and proofs.
- [Scheduling proof search](performance_scheduling_proofs_2026-09-29.md): conflict
  cliques and start-domain probing close the two remaining selected cases.
- [Scheduling order search](performance_scheduling_order_2026-09-29.md): local
  improvement, exact precedence search, shared incumbents and remaining proofs.

</details>

## Design and planning records

These documents explain design decisions, implemented plans and research
proposals. Follow their dated status and linked validation evidence.

<details>
<summary>Plans and specifications</summary>

- [Unified redesign plan](redesign_plan.md): final objectives, runtime separation,
  migration phases, and conformance gates.
- [CSP optimization roadmap (September 2026)](csp_optimization_roadmap_2026-09-16.md):
  evidence-based priorities, native NValue, compact domains, diagnostics, search
  and propagation improvements with explicit acceptance gates.
- [Markov constraints action plan](markov_constraints_plan.md): audited LSDB Blues,
  four scoring modes, numerical guarantees, and ordered solver improvements.
- [Learned-factor language plan](learned_factor_language_plan.md)
- [Probabilistic constraint learning and exact generation](probabilistic_constraint_learning_spec.md)
- [Legacy finite-CSP optimization history](solver_optimization_plan.md)
- [Consolidation plan](consolidation_plan.md)

</details>

<a id="focused-french-research-notes"></a>

Older focused French research notes cover rule groups, mutation, arithmetic,
collections, computed objects, conflict resolution, propagation, choice search
and the original design prompts. They remain design history alongside the
English reference guides above.

<a id="external-sources"></a>

## Language and external sources

English is the publication language for the engine, API, architecture,
benchmarks and application guides. The Spinoza corpus remains in French.
Existing French experiment reports keep their original language and provenance;
each document has one primary language.

PDFs, presentations, theses and third-party corpora are reference material.
Their origin and redistribution decisions are recorded in the
[third-party audit](../THIRD_PARTY.md).
